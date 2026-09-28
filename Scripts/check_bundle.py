#!/usr/bin/env python3
"""Validate the delivered bundle, including resources a compile cannot check."""
import json, pathlib, plistlib, re, sys, wave
app = pathlib.Path(sys.argv[1])
for name in ['Info.plist','FineMeNot','Assets.car','siren.wav','cameras.json','PrivacyInfo.xcprivacy']:
    assert (app/name).is_file(), f'Missing app resource: {name}'
info=plistlib.loads((app/'Info.plist').read_bytes())
expected_database = sys.argv[sys.argv.index('--database-url') + 1] if '--database-url' in sys.argv else ''
assert info.get('CameraDatabaseURL', '') == expected_database, 'Unexpected camera database channel'
assert info['CFBundleIdentifier']=='xyz.dustwave.fine-me-not'
assert set(info['UIBackgroundModes'])=={'audio','location','fetch'}
assert info['NSLocationRequireExplicitServiceSession'] is True
assert info['CFBundleIcons']['CFBundlePrimaryIcon']['CFBundleIconName']=='AppIcon'
project=(pathlib.Path(__file__).resolve().parents[1]/'project.yml').read_text()
minimum=re.search(r'^\s+iOS: "([^"]+)"$', project, re.MULTILINE)
assert minimum, 'Missing deployment target in project.yml'
assert info['MinimumOSVersion']==minimum.group(1), 'MinimumOSVersion differs from project.yml'
if '--release' in sys.argv:
    for plist_key, setting in [('CFBundleShortVersionString', 'MARKETING_VERSION'), ('CFBundleVersion', 'CURRENT_PROJECT_VERSION')]:
        expected=re.search(r'^\s+'+setting+r': "([^"]+)"$', project, re.MULTILINE)
        assert expected, f'Missing release setting: {setting}'
        assert info[plist_key]==expected.group(1), f'{plist_key} differs from project.yml'
with wave.open(str(app/'siren.wav')) as sound:
    assert 1 <= sound.getnframes()/sound.getframerate() <= 2
snapshot=json.loads((app/'cameras.json').read_text())
assert len(snapshot['cameras']) > 1000
assert len({c['id'] for c in snapshot['cameras']})==len(snapshot['cameras'])
assert any(c['id'].startswith('abq-') for c in snapshot['cameras'])
support=app/'FineMeNotCore_SupportCore.bundle'
assert (support/'report-contract.json').is_file(), 'Missing reporting contract resource'
privacy=plistlib.loads((app/'PrivacyInfo.xcprivacy').read_bytes())
assert not privacy['NSPrivacyTracking']
assert {v['NSPrivacyCollectedDataType'] for v in privacy['NSPrivacyCollectedDataTypes']} == {'NSPrivacyCollectedDataTypeCrashData','NSPrivacyCollectedDataTypeOtherDiagnosticData','NSPrivacyCollectedDataTypeCustomerSupport'}
print(f"Bundle verified: {len(snapshot['cameras'])} records; siren, icons, privacy, background modes; minimum iOS {info['MinimumOSVersion']}")
