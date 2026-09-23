#!/usr/bin/env python3
"""Replay a public camera fixture on a NEW simulator; never use a personal device.

This checks real Core Location / audio integration while another app is in front.
Permissions are pre-granted test fixtures, not a test of Apple's prompt UI. It
does not establish locked-screen, physical audibility, Bluetooth or CarPlay results.
"""
import argparse
import json
import math
import pathlib
import plistlib
import subprocess
import time

BUNDLE = 'xyz.dustwave.fine-me-not'
OUTPUT = pathlib.Path('build/compatibility')
ROUTE = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'Tests/Fixtures/camera-approach.json').read_text())
LATITUDE, START_LONGITUDE, END_LONGITUDE = (ROUTE[k] for k in ('latitude', 'startLongitude', 'endLongitude'))
SPEED = ROUTE['speedMetersPerSecond']


def sim(*args, timeout=180):
    print('simctl ' + ' '.join(args), flush=True)
    return subprocess.check_output(['xcrun', 'simctl', *args], text=True, timeout=timeout).strip()


def replay_route(device, evidence_name):
    # Timed positions exercise Core Location and the displacement fallback.
    # Use elapsed time so slow simctl calls cannot make the car move too fast.
    meters = math.radians(END_LONGITUDE - START_LONGITUDE) * 6_371_000 * math.cos(math.radians(LATITUDE))
    duration = meters / SPEED
    started = time.monotonic()
    positions = []
    while True:
        elapsed = time.monotonic() - started
        fraction = min(elapsed / duration, 1)
        longitude = START_LONGITUDE + (END_LONGITUDE - START_LONGITUDE) * fraction
        sim('location', device, 'set', f'{LATITUDE:.5f},{longitude:.7f}')
        positions.append({'elapsedSeconds': round(elapsed, 3), 'latitude': LATITUDE, 'longitude': longitude})
        if fraction == 1:
            break
        time.sleep(2)
    (OUTPUT / evidence_name).write_text(json.dumps(positions, indent=2) + '\n')


def diagnose_failure(device, journal, replay=True):
    """Keep the failing evidence, then probe foreground delivery; never retry to pass."""
    if not journal or not journal.exists():
        return
    (OUTPUT / 'journal.json').write_bytes(journal.read_bytes())
    command = ['xcrun', 'simctl', 'spawn', device, 'log', 'show', '--last', '5m', '--info',
               '--style', 'compact', '--predicate', 'process == "locationd" OR process == "FineMeNot"']
    with (OUTPUT / 'location-service.log').open('w') as log:
        try:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=30, check=False)
        except subprocess.TimeoutExpired:
            log.write('\nLocation-service log capture timed out.\n')
    if not replay:
        return
    try:
        print('Diagnostic foreground probe after failure (does not change test outcome)', flush=True)
        sim('launch', device, BUNDLE, '-warnings.enabled', 'YES')
        replay_route(device, 'foreground-probe-route.json')
        time.sleep(10)
        (OUTPUT / 'foreground-probe-journal.json').write_bytes(journal.read_bytes())
    except (OSError, subprocess.SubprocessError) as error:
        (OUTPUT / 'probe-error.txt').write_text(str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('app_path')
    parser.add_argument('test_run', nargs='?')
    parser.add_argument('--scenario', choices=('background', 'foreground'), default='background')
    args = parser.parse_args()
    version, app_path = args.version, args.app_path
    test_runs = [args.test_run] if args.test_run else []
    if args.scenario == 'foreground' and not test_runs:
        parser.error('The foreground UI/siren check requires a .xctestrun file')
    expected_state = args.scenario
    app = pathlib.Path(app_path).resolve()
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in ('result.json', 'journal.json', 'location-service.log', 'foreground-probe-journal.json',
                 'probe-error.txt', 'cleanup-warning.txt', 'setup-error.txt', 'route.json', 'foreground-probe-route.json'):
        (OUTPUT / name).unlink(missing_ok=True)
    runtimes = json.loads(sim('list', 'runtimes', '-j'))['runtimes']
    runtime = next(r for r in runtimes if r['version'] == version and r['isAvailable'] and r['name'].startswith('iOS'))
    device = sim('create', f'Road Notice compatibility {version}',
                 'com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation', runtime['identifier'])
    journal = None
    try:
        sim('boot', device)
        sim('bootstatus', device, '-b', timeout=600)
        sim('install', device, str(app))
        sim('privacy', device, 'grant', 'location-always', BUNDLE)
        container = pathlib.Path(sim('get_app_container', device, BUNDLE, 'data'))
        journal = container / 'Library/Application Support/FineMeNot/Support/journal.json'

        def events():
            if not journal.exists():
                return []
            return json.loads(journal.read_text())['events']

        def wait_for(predicate, timeout=90):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if predicate(events()):
                    return
                time.sleep(1)
            raise AssertionError('Simulator did not reach expected state; see journal artifact')

        if test_runs:
            test_method = 'testForegroundSirenAndSettings' if expected_state == 'foreground' else 'testBackgroundCameraApproach'
            try:
                subprocess.run(['xcodebuild', 'test-without-building', '-xctestrun', test_runs[0],
                                '-destination', f'platform=iOS Simulator,id={device}',
                                f'-only-testing:CompatibilityUITests/CameraApproachTests/{test_method}',
                                '-parallel-testing-enabled', 'NO',
                                '-resultBundlePath', str(OUTPUT / f'UITests-{time.time_ns()}.xcresult')],
                               check=True, timeout=900)
            finally:
                # Xcode may reinstall the target app into a new data container.
                # Read the actual post-test journal, including after a failure.
                container = pathlib.Path(sim('get_app_container', device, BUNDLE, 'data'))
                journal = container / 'Library/Application Support/FineMeNot/Support/journal.json'
        else:
            sim('location', device, 'set', '35.05822,-106.6045')
            sim('launch', device, BUNDLE, '-warnings.enabled', 'YES')
            wait_for(lambda rows: any(r['event']['values'].get('location') == 'always' for r in rows))
            sim('launch', device, 'com.apple.mobilesafari')
            wait_for(lambda rows: any(r['event']['code'] == 'lifecycle' and r['event']['values'].get('appState') == 'background' for r in rows))
            replay_route(device, 'route.json')
        wait_for(lambda rows: any(r['event']['code'] == 'audio' and r['event']['values'].get('audio') == 'completed' and r['event']['values'].get('appState') == expected_state for r in rows))
        # Allow a quiet interval and check for repeated sirens.
        time.sleep(10)
        audio = [r for r in events() if r['event']['code'] == 'audio']
        starts = sum(r['count'] for r in audio if r['event']['values'].get('audio') == 'started')
        completions = sum(r['count'] for r in audio if r['event']['values'].get('audio') == 'completed')
        assert starts == completions == 1, audio
        assert all(r['event']['values'].get('audio') in ('started', 'completed') for r in audio), audio
        assert all(r['event']['values'].get('appState') == expected_state for r in audio), audio
        summary = {'runtime': runtime['name'], 'runtimeBuild': runtime['buildversion'],
                   'device': 'iPhone SE (3rd generation)', 'appVersion': info['CFBundleShortVersionString'],
                   'appBuild': info['CFBundleVersion'], 'minimumOS': info['MinimumOSVersion'],
                   'permissionSetup': 'simctl pre-granted Always',
                   'scenario': args.scenario,
                   'foregroundApp': 'Road Notice' if expected_state == 'foreground' else ('Home screen' if test_runs else 'Safari'),
                   'locationDriver': 'not replayed' if expected_state == 'foreground' else (f'XCUITest CLLocation proxy at {SPEED:g} m/s' if test_runs else f'timed simctl positions at {SPEED:g} m/s; speed inferred from displacement'),
                   'sirenStarts': starts, 'sirenCompletions': completions,
                   'physicalDeviceTest': False}
        (OUTPUT / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
    except Exception as error:
        (OUTPUT / 'setup-error.txt').write_text(f'{type(error).__name__}: {error}\n')
        diagnose_failure(device, journal, replay=expected_state == 'background')
        raise
    finally:
        if journal and journal.exists() and not (OUTPUT / 'journal.json').exists():
            (OUTPUT / 'journal.json').write_bytes(journal.read_bytes())
        # Hosted runners may have no display surface; screenshots can hang even
        # after a successful playback test. The journal and result are evidence.
        try:
            subprocess.run(['xcrun', 'simctl', 'shutdown', device], timeout=30, check=False)
        except subprocess.TimeoutExpired:
            (OUTPUT / 'cleanup-warning.txt').write_text('Simulator shutdown timed out; hosted runner cleanup will reclaim it.\n')


if __name__ == '__main__':
    main()
