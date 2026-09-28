#!/usr/bin/env python3
"""Run deterministic pause/resume contracts on a fresh iOS simulator.

These inject OS events into the real controller. They do not claim to force a
system low-power pause, suspend the process, or measure hardware wake latency.
"""
import argparse
import json
import pathlib
import subprocess
import time
from simulator_smoke import sim

OUTPUT = pathlib.Path('build/monitoring')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('test_run')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = OUTPUT / 'result.json'
    result.unlink(missing_ok=True)
    runtimes = json.loads(sim('list', 'runtimes', '-j'))['runtimes']
    runtime = next(r for r in runtimes if r['version'] == args.version and r['isAvailable'] and r['name'].startswith('iOS'))
    device = sim('create', f'Road Notice wake contracts {args.version}',
                 'com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation', runtime['identifier'])
    evidence = OUTPUT / f'Wake-{time.time_ns()}.xcresult'
    try:
        sim('boot', device)
        sim('bootstatus', device, '-b', timeout=600)
        with (OUTPUT / 'xcodebuild.log').open('w') as log:
            subprocess.run(['xcodebuild', 'test-without-building', '-xctestrun', str(pathlib.Path(args.test_run).resolve()),
                            '-destination', f'platform=iOS Simulator,id={device}',
                            '-only-testing:MonitoringTests', '-parallel-testing-enabled', 'NO',
                            '-resultBundlePath', str(evidence)], stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=900)
        summary = json.loads(subprocess.check_output(
            ['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', str(evidence)], text=True))
        (OUTPUT / 'test-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        assert summary['passedTests'] >= 10 and summary['failedTests'] == 0 and summary['skippedTests'] == 0, summary
        result.write_text(json.dumps({'runtime': runtime['name'], 'runtimeBuild': runtime['buildversion'],
                                     'passedTests': summary['passedTests'], 'scenario': 'injected OS pause/resume contract',
                                     'realSystemStationaryPauseTested': False, 'physicalDeviceTest': False}, indent=2) + '\n')
        print(result.read_text())
    finally:
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], timeout=30, check=False)


if __name__ == '__main__':
    main()
