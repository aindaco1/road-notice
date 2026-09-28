# Stationary location power and automatic driving recovery

September 27, 2026. Implementation candidate; physical battery and departure tests remain open.

Monitoring now keeps one `CLLocationUpdate.liveUpdates(.automotiveNavigation)` sequence running for the enabled feature's lifetime. Core Location can stop delivering redundant fixes after sustained stationary activity and automatically resume the same automotive navigation configuration when movement returns. The app keeps listening during the stationary period, including while suspended with the screen locked. It does not break the sequence, lower its configuration to coarse positioning, wait for a foreground timer, or wait until the warning engine considers the speed high enough.

Apple documents automatic pause/resume and waking a suspended app for subsequent live updates. The automotive configuration is tuned for a car following a road network. Unlike `CLLocationManager`, it exposes no separate `desiredAccuracy` or distance-filter control; we use its automotive navigation configuration throughout. This is the platform's navigation positioning request, not a guarantee that each fix has navigation-quality accuracy or arrives instantaneously. Satellite acquisition, permissions, system scheduling, and the environment still affect the first usable fix. [Live-update lifecycle](https://developer.apple.com/videos/play/wwdc2023/10180/), [automotive configuration](https://developer.apple.com/documentation/corelocation/cllocationupdate/liveconfiguration/automotivenavigation), [energy guidance](https://developer.apple.com/documentation/xcode/accessing-the-device-s-location-efficiently).

## Implementation boundaries

- `CLBackgroundActivitySession` stays retained during pauses and retries. The iOS 18+ Always `CLServiceSession` stays retained during the stream; iOS 17 retains the existing two-step permission request. The enabled preference still recreates monitoring in the existing app launch delegate, including a permitted background relaunch. [Background location contract](https://developer.apple.com/documentation/corelocation/handling-location-updates-in-the-background).
- The old continuously running `CLLocationManager` provider is removed. That manager remains solely for permission status and significant-change recovery. Its fixes use the same `consume` method and alert engine. Significant-change delivery is supplementary recovery, not the movement wake-up mechanism.
- Stationary state now means an explicit system stationary-pause event. Missing speed, missing GPS, or a short traffic stop no longer makes the app independently declare itself parked. No Core Motion permission or extra motion subsystem is added.
- A resumed event clears stationary state before the accuracy/freshness gate. A poor first fix cannot leave monitoring stuck in idle. Actual camera matching retains its existing usable-fix requirement; receiving an event does not certify its accuracy.
- Repeated starts cannot create duplicate streams. Stop, authorization denial, and replacement sessions invalidate the previous task's identity. Late completion from an old task cannot stop or schedule a retry for a new task. Unexpected sequence completion retries through the existing ten-second error-recovery task; that task is not used for waking from stationary operation.
- Core Location diagnostics distinguish permission, precision, unavailable-location, and background-access failures on iOS 18+. iOS 17 uses the older stationary accessor and authorization callbacks. The UI shows “Ready · waiting for movement” during a system-confirmed idle period even when its last fix has aged.
- The existing text diagnostic reports active automotive positioning or stationary automatic resume, plus the first resumed fix's accuracy and delay until a usable fix. These small values stay in memory and contain no coordinates or route history. The delay begins at the first nonstationary Core Location event, **not** at actual physical departure; the phone test must measure that earlier interval separately.
- Debug builds also emit local `Location` log events with the system stationary flag, fix presence, horizontal accuracy and fix age. They contain no coordinates and are excluded from release builds. This lets the locked-simulator test observe delivery without attaching a debugger or injecting app state.

The previous live-update implementation was replaced in `fd99484` while investigating missed Coors warnings. That investigation also fixed missing coverage, bad motion inference, and stale database selection. It did not establish from physical logs that automatic pause/resume caused the reported miss. This change preserves those engine and data fixes and adds explicit session/lifecycle checks. [Original investigation](DEBUGGING.md).

## Verification

Six `LocationStreamStateTests` cover an eight-hour synthetic stationary interval without ending the stream, a coarse first resumed fix followed by a usable fix, unavailable fixes without invented stationary evidence, stale task completion after off/on, failure/restart, and repeated pause/resume diagnostics. These exercise app state handling; they do not simulate Apple's sensor wake-up or suspension policy.

The iOS `MonitoringTests` target adds nine controller-level regression tests.
They inject operating-system events through `MonitoringLocationService` while
running the production controller's async consumer, retry task, accuracy gates,
alert engine and saved encounters. Test fixtures replace the camera store and
warning presenter to keep network requests and audio out of the deterministic
suite. A controlled clock advances an eight-hour idle interval without waiting
in real time. The same controller requests `.automotiveNavigation` in production
and in these tests; there is no test-only matching or resume algorithm.

The production `CoreLocationService` owns the retained background/authorization
sessions and adapts Apple's events. Cancelling the consumer cancels the adapter's
producer. Tests can verify that the controller keeps the service armed through a
pause and cancels the obsolete stream, but cannot substitute for actual OS session
retention, sensor wake-up, process suspension or relaunch delivery.

| Contract regression | What must remain true |
|---|---|
| Eight-hour pause, no fixes, coarse first fix, accurate fix | One navigation stream remains armed; idle clears before quality filtering; one warning follows recovery |
| Missing or stale fixes | No warning from invalid data; later good data still recovers |
| Slow departure | Navigation stays requested at 0.5 m/s, before the warning movement threshold |
| Off/on during a pause | Events and completion from the old session cannot modify the new session |
| Stream completion or error | A controlled retry recreates navigation monitoring and can warn |
| Cancellation while retry waits | The old retry cannot create a third provider |
| Permission denial/restoration | Stop on denial, then recover from the enabled preference with background application state |
| Significant-change manager errors | A healthy paused live stream is not torn down |
| Recreated controller with saved encounter | Monitoring resumes and the same approach does not warn again |

All nine pass locally on **iOS 18.0 and 27.0**, with zero skipped tests. The 40
Swift package tests and 72 Python tests also pass. The existing compatibility
workflow now runs the nine contracts on **iOS 17.5, 18.5 and 26.5** before the
separate real-location/UI scenario. All nine passed on all three hosted runtimes
with zero failures or skips in [candidate CI](https://github.com/aindaco1/road-notice/actions/runs/36359847376).
The distinct GPS/audio checks and any failed attempts are recorded in
[TESTING.md](TESTING.md).

Private TestFlight preparation adds a separate database-channel isolation case,
bringing the app-hosted suite to ten tests. The runner requires all ten to pass;
the original nine wake contracts are unchanged. All **10/10 pass on each hosted
iOS 17.5, 18.5 and 26.5 runtime** for the final app commit `17eac6e`, with no
failures or skips in [final candidate CI](https://github.com/aindaco1/road-notice/actions/runs/36361637870).

To reproduce with the installed runtime, build test products and run the bounded
runner (replace `18.0` with an installed iOS runtime):

```sh
xcodebuild -project FineMeNot.xcodeproj -scheme FineMeNot \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO ARCHS=arm64 ONLY_ACTIVE_ARCH=YES \
  -derivedDataPath build build-for-testing
python3 Scripts/monitoring_smoke.py 18.0 build/Build/Products/*.xctestrun
```

The runner creates a fresh simulator and saves Xcode's `.xcresult`, test summary
and a result explicitly labeled **injected OS pause/resume contract** under
`build/monitoring/`. It rejects failed, skipped or fewer than ten passing tests.
No pause injection, mock service, test camera or forced power setting is exposed
through the app UI or launch arguments; fixtures live in the separate test target.

The combined candidate also passes a five-minute locked, parked-to-driving iOS 27
simulation: no parked warning and one completed background siren after movement,
without reopening the app. The simulator never reported a system stationary
pause, so that result does not validate actual low-power wake-up. Full evidence
and the simulator's timing limits are in [TESTING.md](TESTING.md).

The following remain physical acceptance checks before claiming a battery improvement or dependable departure timing:

1. Compare the currently shipped build and this candidate on the same iPhone/iOS: eight hours parked and locked, then a drive without opening Road Notice. Record battery use, actual departure time, first resumed event/fix quality, time to a usable fix, and first camera lead time. Repeat with Low Power Mode and offline data.
2. Park near a camera, wait for “Ready · waiting for movement,” then depart with the phone locked. Exercise both Coors directions and Alameda where practical. The first camera must not depend on a significant-change event, manual foregrounding, or reaching the warning speed threshold before navigation positioning resumes.
3. Include short traffic stops, slow departure, GPS-poor parking/garage exit, and a moving interval with missing speed/course. Record delayed/ambiguous fixes rather than counting an active stream as a successful warning.
4. Check supported iOS 17, 18, and current-device versions; warnings off/on; permission denial/restoration; and permitted system termination/relaunch. Force-quit recovery is not promised. Verify real locked-screen audio output separately.

No battery percentage, maximum wake latency, physical overnight pass, or release acceptance is claimed by the unit tests or a simulator build. The private TestFlight candidate is 1.0.6 (14), with the existing iOS 17 minimum. Distribution progress is recorded in [RELEASE.md](RELEASE.md).
