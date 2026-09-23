# Missed Coors warning: findings and build 4

**Build 0.1.0 (4) is available in the First Drive TestFlight group.** Apple processing completed and the group showed Testing. Installation of build 4 on the physical iPhone has not yet been verified.

**Latest update:** build **0.1.0 (5)** is now Testing in First Drive and retains these runtime fixes. Its database contains **1,777 warning locations**, representing all 40 current Albuquerque city-listed approaches. Build 4 can also download the same data with Update now. See [ALBUQUERQUE.md](ALBUQUERQUE.md); the findings below record the original build 4 investigation.

## What was found

- **Missing coverage:** the city lists Coors north of St. Joseph NB/SB, but those approaches were absent from the accepted database. They may correspond to the reported camera north of I-40; the exact device has not been identified. Reviewed road segments now provide explicitly approximate Possible speed camera warnings in both directions. Exact camera coordinates remain unverified. [City source](https://www.cabq.gov/automated-speed-enforcement).
- **Movement detection bug:** when GPS speed was unavailable, the old matcher could suppress every warning even while valid positions showed movement. A failing regression reproduced this; the fix infers speed and bearing from sufficient accurate displacement before checking movement. Jitter, old fixes and implausible jumps are rejected. [Apple speed contract](https://developer.apple.com/documentation/corelocation/cllocation/speed).
- **Old cache masking an app update:** startup picked a saved database before examining the bundled one. A simulator upgrade reproduced the older 1,756-record snapshot taking priority over the newer bundle. Startup now selects the newest valid offline snapshot. The corrected database contains 1,758 warning records.

These are confirmed source/runtime problems. There were no logs from the physical phone, so they do not establish the exact cause of that drive's missed siren.

## Background behavior

Build 4 requests continuous navigation-quality background location, with automatic pauses disabled and a 10 m distance filter. Significant-change updates remain a recovery trigger and share the same matcher. Low Power Mode does not disable monitoring in the app. This prioritizes reliability over battery use, including while stationary. The siren still uses a brief playback audio session that can sound in Silent mode through the selected output.

A timer heartbeat cannot guarantee execution after iOS suspends or terminates an app. Force-quitting, denied permissions, unavailable GPS, phone/audio interruptions and muted output can still prevent a warning. Real-device Low Power Mode, overnight recovery and car-audio audibility remain acceptance tests. [Apple background location](https://developer.apple.com/documentation/corelocation/cllocationmanager/allowsbackgroundlocationupdates), [automatic pauses](https://developer.apple.com/documentation/corelocation/cllocationmanager/pauseslocationupdatesautomatically).

## Evidence

- 14 Swift tests and 10 publisher tests passed locally and in [GitHub CI](https://github.com/aindaco1/road-notice/actions/runs/34913290315), using source commit `fd99484`.
- Both Coors directions passed full locked-screen simulator replays. The expected direction warned once, and the siren recorded playback completion in background state. Low Power Mode was off in these simulations.
- The upgrade test selected the new bundled database while preserving the older saved copy and app settings.
- Diagnostics survived relaunch and showed the latest audio outcome, route, media volume and background state. GPS quality, effective motion, nearest camera and rejection reasons are visible without uploading a trip log.
- The public database was deployed, and its immutable file matched the published SHA-256 checksum.
- The signed 0.1.0 (4) archive passed bundle validation with minimum iOS 27.0. Apple accepted the upload on September 15 at 00:29 UTC (September 14 Mountain time), after a network timeout on the first attempt.

The simulator runs iOS 18 with a development-only deployment override. It cannot establish iOS 27 scheduling or real speaker/Bluetooth/CarPlay audibility.

## Next phone test

1. Install build 5 from TestFlight and open Fine Me Not once.
2. Confirm Camera warnings is on, with **Always** and **Precise Location** enabled. The database should show **1,777 warning locations**.
3. While parked, use **Test warning** on the audio connection used in the car and set an audible media volume.
4. Test the known approach with the screen locked, then repeat with Low Power Mode. Use a passenger to observe; do not handle the app while driving.
5. If it misses again, use **Diagnostics → Copy diagnostics** once parked and share the report here. Camera names may reveal a visited place; the app never uploads this report automatically.
