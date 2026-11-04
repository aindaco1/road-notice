# Test and acceptance record

## 1.0.7 (20) alert corrections — November 3, 2026

**96 Python pipeline tests, five regional-extract tests, 46 Swift package tests (40 camera + six support),
and 16 app-hosted tests pass, with zero app-hosted skips.** The new incident
regressions first failed against the old runtime. They now cover overdue zones
and 180-day offline use, the I-40/Menaul negative and monitored-road positive,
both Coors directions during course dropout, exact-limit Quiet suppression and
full lead distance for the three incident approaches. Their mapped-path replays
at 50 mph each warn 250–340 m before the monitored area, including after 180
days offline. The existing per-zone
corpus and reviewed-area replays pass against the refreshed 2,728-camera bundle,
including every one of its 701 zones and the fixed historical 54-zone corpus.

Pipeline checks cover all camera kinds, speed-aware lead requirements (including
a 350 m approach accepted at 45 mph and rejected at 65 mph), closed loops,
stacked and parallel roads, retention without renewed source dates, invalidation
after camera moves or direction changes, and resumable acquisition. Failed,
partial, stale and future-dated responses cannot complete a batch. Extract tests
cover checksums, complete crossing ways, source dates and adjoining-region coverage.
Distribution-feed compatibility and immutable-byte checks
pass. The shared support dependency pins and generated project pass validation.

The final iPhone 18 Pro / iOS 27 simulator app-hosted run completed in 23.9 seconds.
It exercises both bundled Coors directions through `MonitoringController` at
40/44/45 mph (quiet), 46 mph (warning), and unknown speed accuracy (warning).
Notification tests confirm the existing time-sensitive interruption level and
no log entry for a Quiet approach. The result is
`~/Library/Developer/XcodeBuildMCP/workspaces/road-notice-f91eaf62e6fc/result-bundles/test_sim_2026-11-04T05-52-20-298Z_pid53567_b0c6337f.xcresult`.
The simulator bundle passes resource, 1.0.7 (20) version, camera-count and iOS 17
minimum checks. No signed archive or App Store upload is claimed by these tests.

The final acquisition audit verifies 1,071 of 1,071 candidates and 117 of 117
required batches, with no pending shards. All 2,728 camera IDs, geometries,
directions and classifications are preserved. The 15,226,599-byte current feed
and its legacy projection pass the existing 20 MB download bound and digest
checks. The three incident zones retain 650 m of approach. The all-kind shorter
zone replay warns 300–335 m ahead at 50 mph and rejects adjacent/opposing traffic.

The first expanded-data CI run passed source checks and the complete iOS 17.5
and 18.5 jobs. Its iOS 26.5 monitoring suite passed, but the background-audio
check failed: the saved journal shows monitoring switched off before the route.
Its later diagnostic foreground replay produced a completed warning. A second
run with switch-state assertions caught an ignored initial tap before driving;
the exported input event targeted the actual switch, but its value never changed.
The shared UI setup now starts disabled, enables warnings through real opt-in,
and confirms each requested switch state, including Quiet before relaunch. It
retries one ignored input only when that state was not applied. The required
switch-state and exactly-one-background-siren assertions remain intact. These
failed runs remain evidence, not passing background results; the PR records the
final compatibility rerun.

The simplified setup passes the local iOS 27 foreground/settings/siren UI test
with zero skips. Its completed result is
`~/Library/Developer/XcodeBuildMCP/workspaces/road-notice-f91eaf62e6fc/result-bundles/test_sim_2026-11-04T06-46-13-592Z_pid53567_afa3859a.xcresult`.

The staged website was visually checked at 320, 390 and 1,440 px widths,
including the expanded Do Not Disturb FAQ; no horizontal overflow or broken
section anchors was found. Both staged data feeds retain all 2,728 records.
The website has new-release copy without an “upcoming” label at the owner's
request. Production deployment is tracked separately in [RELEASE.md](RELEASE.md).

This does not establish physical iOS 27.2 audibility under Focus, battery use or
background GPS delivery. The owner's parked Test warning succeeding under Do
Not Disturb is recorded separately from the missing real camera alert. The
existing physical acceptance matrix remains open. See [ALERT-FIXES.md](ALERT-FIXES.md).

## Public build 19 — October 4, 2026

Local 41 Swift package tests (including a second fixed-corpus case) and 77 Python
pipeline tests pass. The source-refresh regression is fixed: all 54 road zones
are identical to build 17. Current Coors zone, geometry, bearing and verified
45 mph assertions pass; no zone-count threshold was lowered.

Two new source tests cover retaining the previous active shard set when a newly
hashed query set is incomplete, switching only after it is complete, preserving
source dates and ignoring unrelated historical caches. Both distribution feeds
pass checksum, camera-preservation and immutable-byte checks. The released 1.0.5
validator accepted the staged legacy feed during preparation.

Build 19's signed archive and complete bundle checks pass. All 16 app-hosted
tests pass with no failures or skips. [Source CI](https://github.com/aindaco1/road-notice/actions/runs/37250068571)
and [runtime CI](https://github.com/aindaco1/road-notice/actions/runs/37250068496)
pass for `ce2a45d`, including every iOS 17.5, 18.5 and 26.5 job. The merge
`0665f9e` has the same tree. Hosted iOS 18 uses its documented foreground/audio
scenario; it is not claimed as moving-background-GPS acceptance.

The same compiled build passes the saved-notification UI replay on local iOS
18.0: a new Gibson alert is posted at **01:28:49 UTC on October 5**, the app
terminates/relaunches, and the UI opens that new entry with its saved 40 mph
limit. The completed result is `/tmp/road-notice-release19-log-ios18.xcresult`.
The rendered attachment, new-entry timestamp and journal are in
`work/release19/ios18-log-attachments/`, `ios18-posted-alert.json` and
`ios18-journal.json`. The app-hosted result is
`/tmp/road-notice-release19-unit.xcresult`.

Additional local iOS 27 UI replays failed on fresh and retained simulators,
including after reboot. Their routes complete one background siren, but system
notification authorization/settings calls do not return and no alert is saved.
System logs show accepted entitlement checks and forwarded requests without
callbacks. The unchanged notification implementation works in the iOS 18 replay;
this points to the local iOS 27 notification service, but does not establish
physical iOS 27 acceptance. The failures are not counted as passes. Transcripts,
system logs and result summaries remain in `work/release19/`; one raw failure
bundle remains at `/tmp/road-notice-release19-log-after-reboot.xcresult`.

Build 18 was superseded and not selected for App Review. Its initial UI failure
summary remains in `work/release18/ui-failure-summary.json`; obsolete raw build
and result bundles were pruned. Physical overnight battery/departure timing and
normal phone notification taps remain open. See [release status](RELEASE.md) for
the separate website deployment, Apple upload and submission boundaries.

## Notification crash and log styling — October 2, 2026

The owner submitted TestFlight feedback for **1.0.6 (16)** on iPhone 16 Pro Max,
iOS 27.0.1: tapping a notification crashed the foregrounding app. The downloaded
symbolicated report shows SIGABRT on thread 2 in UIKit's
`_performBlockAfterCATransactionCommitSynchronizes:`, called by the compiler-generated
completion for `AppDelegate.userNotificationCenter(_:didReceive:)`. Build 17
uses explicit completion callbacks, with routing and completion on the main actor.
Raw feedback remains in ignored local `work/release17/testflight-feedback/`.

- **41 Swift package tests and 74 pipeline tests pass.** The local CloudDocs
  scratch directory initially hit macOS resource-fork signing restrictions;
  the successful Swift run uses `/tmp/road-notice-core17`.
- **16 app-hosted tests pass on a clean iOS 27.0 simulator**, including old
  build-16 log decoding and a full bundled Coors replay through
  `MonitoringController` for both directions. At 40 mph with 0.5 m/s uncertainty
  the approaches are quiet; 44/45 mph and unknown uncertainty each warn once.
- The signed build 17 archive passes signature and bundle checks, with the
  unchanged private database URL, 2,701 cameras, iOS 17 minimum and both 45 mph
  field observations. No speed threshold, geometry or evidence expiry changed.
- Initial iOS 18 notification-tap attempts did not open the app from Notification
  Center and are retained as failures. Its combined app-hosted invocation stalled
  before executing tests; it is not counted as a pass. Initial iOS 27 UI tests
  were blocked by a location permission prompt; the test setup now handles the
  explicit simulator permission buttons before beginning its route.

The final iOS 27 saved-entry UI test passes with a completed `.xcresult`: a real
Core Location route posts the alert, then the app terminates/relaunches and opens
the saved camera details. Its rendered screenshot confirms the blue styling,
monospaced heading, Done button and saved 40 mph Gibson limit. Evidence is in
`work/release17/log-final-attachments/` and `/tmp/road-notice-after17-log-final.xcresult`.
An earlier successful test body stalled in Xcode result finalization; the fresh
completed invocation is the acceptance result.

The final iOS 27 Notification Center check **opens the matching entry after app
termination without crashing**. `testColdNotificationDefaultAction` drives the
real route, terminates the app, scrolls the notification into view and invokes
its default action. The simulator required swipe-right opening after the initial
tap; this does not establish single-tap behavior on a physical phone. XCTest
reports one test with zero failures in 98.463 seconds, and the resulting screen
was visually verified. Xcode then stalled during result-bundle finalization and
was stopped after several minutes; this run is supported by its test transcript
and screenshot, **not a completed `.xcresult`**. Evidence:
`work/release17/cold-final.log` and `work/release17/cold-notification-opened.jpg`.
Earlier failed exploratory attempts remain preserved locally.

[Source CI](https://github.com/aindaco1/road-notice/actions/runs/37055355209) and
[runtime CI](https://github.com/aindaco1/road-notice/actions/runs/37055359022)
both pass for the shipped app source `bb227d5`. All three runtime jobs (iOS 17.5,
18.5 and 26.5) pass, including app-hosted tests and the selected driving/audio
checks. The documented hosted iOS 18 moving-GPS limitation remains separate.
The new cold notification UI check is local evidence, not part of that CI run.
Normal taps with the app backgrounded and terminated remain in the physical
First Drive checklist for build 17.


## Coors verification and on-device alert log — October 1, 2026

The owner reported that build 14's Albuquerque approach zones and Quiet below
speed limit worked well, and verified both existing Coors north of St. Joseph
cameras and their 45 mph limit. This field report does not measure battery use or
establish every physical audio/wake scenario in the historical checklists below.
Build 16 preserves their geometry, bearing, IDs and road zones. The dated source
and expiry policy are in [COORS-FIELD-VERIFICATION.md](COORS-FIELD-VERIFICATION.md).

- **41 Swift package tests pass** (35 CameraCore, 6 SupportCore), including Coors
  below-limit suppression, near-limit warning, uncertain-speed warning and all
  existing road-zone corpus cases.
- **74 pipeline tests pass**, including fresh field observations, conflicts and
  expiry, and preservation of the Coors warning geometry.
- **14 app-hosted tests pass on local iOS 18.0**, including notification payload
  persistence and deduplication, denied/failed requests, quiet approaches, the
  500-entry cap, clearing and cold payload restoration. Backup exclusion is
  asserted; the Data Protection assertion runs only on physical iOS because the
  simulator uses the Mac filesystem.
- The real Core Location Gibson eastbound replay on iOS 18.0 emitted a camera
  notification, completed its background siren and saved one matching log entry.
- The build 16 signed archive passes signature and private-channel bundle checks.
  [Clean-checkout source CI](https://github.com/aindaco1/road-notice/actions/runs/36878134469)
  also passes. Earlier build 15 CI exposed an accidentally included local iCloud
  duplicate resource; build 16 excludes it. The initial runtime dispatch failed
  fetching the shared submodule before tests and was replaced by a fresh run.

[Runtime CI](https://github.com/aindaco1/road-notice/actions/runs/36878141832) at
app source `159a5e3` passes **14/14 app-hosted tests on each of iOS 17.5, 18.5 and
26.5**, plus iOS 17.5/26.5 background approach/siren replays and iOS 18.5 foreground
settings/audio. The latter retains the documented hosted GPS limitation.

The local iOS 18.0 UI test `testCameraNotificationPersistsInAlertLog` also passes:
a real route posts a camera notification, the app terminates/relaunches, and the
saved entry opens to its camera type, road label and time. Its screenshot is
retained in `work/release16/ui-attachments/`. Encounter cooldown state is reset
through test launch arguments so a reused simulator can replay the same route.

**Notification Center cold-tap acceptance remains open.** The initial reused
simulator attempt selected an older notification; the fresh-notification and
post-reboot attempts both displayed the notification but the automated taps did
not reopen the app. This is not a passing end-to-end cold-tap result. Payload
restoration and navigation state pass in app-hosted tests, and the saved-entry
screen passes the separate UI test; the physical tap from a closed app is explicit
in the TestFlight checklist. The unsuccessful exploratory UI test and all failed
results are preserved under `work/release16/notification-tap-investigation.swift`
and `work/alert-log-cold-tap*`, rather than installed as a claimed passing gate.

Local evidence is in `work/alert-log-*` and `work/release16/`. The initial
XcodeBuildMCP iOS 27 test invocation timed out; it is not counted as passing.
Physical testing of build 16 remains separate from the owner's successful build
14 field report. Windows work is a subsequent scope after this iPhone test.

## Road zones and stationary power candidate — September 27, 2026

The private 1.0.6 (14) candidate implements [road-following zones](ROAD-ZONES.md)
and [automatic stationary pause/resume](BATTERY-MONITORING.md). Source is under
[PR #7](https://github.com/aindaco1/road-notice/pull/7); distribution progress is
recorded in [RELEASE.md](RELEASE.md). No public database deployment is performed
as part of private candidate preparation.

Apple has processed this candidate and the existing First Drive internal group
shows **Testing**, with one tester and the phone checklist saved. Installation
and the physical acceptance checks below remain unverified.

- **40 Swift tests pass:** 34 CameraCore tests and 6 SupportCore tests, including
  the new road-matching and location-session cases. All 54 generated zones have
  a positive approach and reject opposite/distant traffic in the corpus replay.
  The synthetic I-40/Menaul failure is rejected at both 55 and 65 mph, and the
  correct-road control still warns.
- **72 Python pipeline tests pass**, including automatic road-path validation,
  actual source-node connectivity, stale and ambiguous fallback, and parallel
  ways that share the monitored road's name.
- Xcode 27 builds the combined simulator app with the actual **iOS 17.0 minimum**.
  `check_bundle.py` verifies 2,701 camera records, siren, icon, privacy declaration,
  background modes and support resources. The pinned support-package check and
  `git diff --check` pass.
- The snapshot contains 54 zones from 71 reviewed metro approaches. Comparing
  every camera with the baseline confirms all non-zone fields remain unchanged.
  The local immutable snapshot and manifest are
  `2026-09-21-dc315dfa720e-79004776`; no nationwide rollout is implied.

Command evidence is under the ignored local directory
`work/battery-road-investigation-2026-09-27/` (`combined-swift.txt`,
`combined-python.txt`, `combined-build.txt`). A fresh iPhone SE simulator running
iOS 27.0 (24A434) completed the Gibson eastbound replay with Safari in front:
exactly one background siren start and completion, with speed inferred from the
timed location positions. Evidence is in `background-27/` and `simulator-27.txt`.
Always access was pre-granted as a test fixture.

### Repeatable wake regression suite

The subsequent `MonitoringTests` target runs nine deterministic scenarios through
`MonitoringController`, including its real async consumption/retry loop, fix
filtering, engine and persistence. Only the OS service, time, camera input and
warning output are replaced. All **9/9 pass on iOS 27.0 (24A434)** and **9/9 on
iOS 18.0 (22A3351)**, with zero failures or skips. The 40 Swift package tests and
72 pipeline tests still pass after introducing the service boundary.

The same refactored app then passed a fresh **real Core Location** Gibson replay
on iOS 27.0 with Safari in front: exactly one background siren start and
completion, with no duplicate. That run uses Apple's live service, not the
injected test source. Its result, journal and route are in
`wake-suite/live-background-27/`. The complete bundle check also passes.

The suite covers overnight pause/resume, missing/stale/coarse fixes, slow
movement, off/on races, stream completion and failure, cancelled retries,
permission loss/restoration, recovery-manager errors, and encounter persistence
across controller recreation. The initial run's three failures came from fixtures
reusing the parked timestamp after restart: the engine correctly rejected those
as duplicate fixes. Corrected fixtures advance the clock before delivering a new
fix; no duplicate-position protection was relaxed.

`Scripts/monitoring_smoke.py` runs the suite on a fresh simulator and rejects
failed, skipped or missing tests. The compatibility workflow now includes it for
iOS 17.5, 18.5 and 26.5, saving its evidence separately from real GPS/audio tests.
All nine passed on each hosted runtime with no failures or skips in
[the candidate CI run](https://github.com/aindaco1/road-notice/actions/runs/36359847376).
The separate iOS 17.5 background replay and iOS 18.5 foreground settings/audio
check passed. The first iOS 26.5 background attempt failed before route injection:
the Home-button action did not establish the required background state. The
recording still showed the app visible; the journal contained no background
transition before teardown. Its failed evidence is retained, and only that
runtime job was rerun with unchanged source and assertions. That second attempt
passed, including exactly one completed background warning, and the overall
workflow passed. Instructions and exact test boundaries are in
[BATTERY-MONITORING.md](BATTERY-MONITORING.md).

Private candidate preparation adds a tenth app-hosted test for database-channel
isolation: a newer cached public snapshot still loads in the normal channel but
cannot replace the private candidate's bundled records. The nine wake contracts
remain unchanged. The standard public cache directory is preserved for upgrades.

The final app commit `17eac6e` passes **10/10 tests on each hosted iOS 17.5,
18.5 and 26.5 runtime**, with no failures or skips. The same run passes the
separate iOS 17.5/26.5 background approach checks (one siren start and completion
each) and the iOS 18.5 foreground settings/audio check. The iOS 18.5 check does
not replay moving GPS; the hosted runtime's documented limitation remains.
[Final runtime CI](https://github.com/aindaco1/road-notice/actions/runs/36361637870)
passes on its first attempt; [source CI](https://github.com/aindaco1/road-notice/actions/runs/36361637837)
also passes all 40 Swift and 72 Python tests. Final downloaded results are in
`work/release14/final-ci/`.

Local evidence is under `work/battery-road-investigation-2026-09-27/wake-suite/`:
`ios27-summary.json`, `ios18/`, and the core/pipeline logs. The original Xcode 27
result is `test_sim_2026-09-27T22-44-06-077Z_pid16463_89fd2204.xcresult` under the
XcodeBuildMCP workspace's `result-bundles` directory. This proves the app's response
to simulated OS events; it does not force Core Location to pause the actual GPS
hardware or wake a suspended physical phone.

### Locked parked-to-driving simulation

A fresh installation of the same candidate, with development-only location
logging, ran on the iOS 27.0 simulator without an attached debugger. The simulator
hardware Lock button was pressed; a screenshot confirmed the screen was off.
It remained at the public Gibson fixture's starting position for **300 seconds**,
then drove eastbound without opening the app or unlocking the phone.

The parked journal contained **zero audio events** and `notMoving`. After departure
the journal recorded **one siren start and one completion**, both in the background,
with no repeat. The app stayed in the background throughout. Simulated fixes were
accepted at 5 m horizontal accuracy. Notification permission was denied in this
fixture; direct background siren playback still completed through the simulated
speaker. This is not a physical audibility or notification-prompt test.

**Stationary power-state acceptance is still open:** no live update reported
`stationary=true` during the idle interval. The simulator continued supplying
stationary-position fixes, so this run verifies locked idle-to-motion delivery
and warning behavior, not wake-up from a real system stationary pause. Host
`simctl` calls also introduced irregular delivery intervals; the route and log
timestamps must not be presented as an iPhone wake-latency measurement.

Evidence, including the setup, screen-off image, parked/departed journals, location
log, route, reproduction script and result, is in
`work/battery-road-investigation-2026-09-27/locked-departure/`.

A source or simulator pass does not
establish real-device stationary drain, movement wake latency, first-camera lead
time or locked-screen audio. Those remain explicit physical acceptance checks.

## Public availability — September 25, 2026

Apple's public product page and catalog confirm Road Notice 1.0.4 is available
free in the U.S. App Store for iOS 17 and later. See the [release record](RELEASE.md).
App Store installation and the physical acceptance gaps below remain unverified;
public availability does not turn those checks into passes.

## Road Notice 1.0.4 (12) — September 22, 2026

The candidate passes 26 Swift tests and 63 Python pipeline tests after syncing the
September 21 published camera data. The signed release and simulator bundles
pass checks with 2,701 records and minimum iOS 17.0. App/dSYM UUIDs match; Xcode
confirmed successful upload; App Store Connect confirmed processing complete.
The actual 1320 x 2868
simulator screenshot is saved in `docs/screenshots/1.0.4-settings.png`.

The [hosted build and tests](https://github.com/aindaco1/road-notice/actions/runs/35811525214)
and [runtime compatibility checks](https://github.com/aindaco1/road-notice/actions/runs/35811525239)
passed. iOS 17.5 and 26.5 each completed one background camera warning; iOS 18.5
passed the saved Quiet setting and foreground Test warning scenario. The hosted
iOS 18 moving-GPS limitation below still applies.

The live site passes icon/database/manifest verification after deployment.
Physical acceptance gaps below remain unchanged. Current logs and the cleanup
manifest are retained under `work/release12/`; obsolete earlier work folders are
in the dated Trash cleanup folder. The revised metadata, screenshot and build 12
were verified in App Store Connect, and the response to the rejection was posted.
The resubmission showed **Waiting for Review** at 23:27 CDT on September 22, 2026.
Build 12 is assigned to First Drive; physical installation remains unverified.

## App Review wording revision — September 22, 2026 (pre-submission checks)

The [review revision](APP-REVIEW.md) changes Settings and website wording. No new runtime or pipeline test was added for
this copy change. Existing **26 Swift tests** (5 SupportCore, 21 CameraCore) and
**63 Python pipeline tests** pass. Xcode 27.0 built the simulator app at the
actual iOS 17.0 minimum; `check_bundle.py` passed with 2,695 bundled records.

The revised Settings screen was installed and visually inspected on iPhone 18
Pro / iOS 27.0 at default and largest accessibility text size. Text wraps and
the existing scroll view reaches the controls. The staged website was inspected
at 390 x 844; its content width is 390 pixels with no horizontal overflow.
The draft subtitle, promotional text, description and Apple reply fit their
respective metadata/message character limits.

Local logs and development screenshots are under `work/review-2026-09-22/`.
The existing 1.0/1.0.3 store screenshots remain historical; new store screenshots
must come from the final branding/build. No signed archive, TestFlight upload,
website deployment, Apple reply or resubmission was performed. Earlier physical
and OS runtime acceptance below is unchanged, not repeated by these layout checks.
Jev remains a documented plan; no evaluation requests were sent.

The subsequent neutral icon revision also builds and passes `check_bundle.py`.
Its 1024 x 1024 PNG is opaque. The canonical app icon, existing header symbolic
link and staged website asset have identical bytes. No runtime behavior changed.
The owner subsequently selected Road Notice. Rename verification is recorded
below separately from these earlier layout checks.

## Road Notice rename — September 22, 2026 (pre-submission checks)

From the renamed `road-notice` directory, 26 Swift tests and 63 Python pipeline
checks pass. Xcode 27.0 builds, installs and launches the revised app on iPhone
18 Pro / iOS 27; the bundle check passes with 2,695 records and minimum iOS 17.
The compiled display name is Road Notice; bundle ID and executable are unchanged.
Default and largest accessibility text sizes were visually inspected: the shared
header switches from side-by-side to stacked without clipping the new wordmark.
The staged site fits a 390 x 844 viewport with no horizontal overflow. Canonical,
header and staged-site icon bytes match. Logs/screenshots use the `road-notice-`
prefix under the existing local review directory.

GitHub retains repository ID `1370595336`, history and Pages custom domain
`finemenot.xyz`; the old repository API URL resolves to `aindaco1/road-notice`.
The local origin uses the new canonical URL. The live HTTPS site remains
reachable, and its 2,701-record database snapshot matches the published manifest
SHA-256 (the local app bundle still contains 2,695 records). The required reporting adapter
change was separately tested and deployed; see [REPORTING.md](REPORTING.md).
The app, website branding and listing remain local changes, without a new Apple
build, submission or live website publication.

## Version 1.0.2 (10) compatibility — September 15, 2026

The app, generated Xcode project and shared Swift package now target iOS 17.0. These checks use that actual minimum, without a simulator-only override.

| Runtime | Simulator | Result |
| --- | --- | --- |
| iOS 17.5 (21F79) | iPhone SE (3rd generation), GitHub macOS 15 runner | XCUITest replay passed; exactly one background siren start and completion |
| iOS 18.5 (22F77) | iPhone SE (3rd generation), GitHub macOS 15 runner | Launch, default Quiet setting, saved setting after relaunch, and one foreground Test warning passed; hosted background GPS is not accepted |
| iOS 26.5 (23F77) | iPhone SE (3rd generation), GitHub macOS 26 runner | XCUITest replay passed; exactly one background siren start and completion |
| iOS 18.0 (22A3351) | iPhone SE (3rd generation), local | Installed and launched; permission prompts, settings and report review passed; locked-screen approach produced one siren with background playback completion |
| iOS 26.5 (23F77) | iPhone 17 Pro, local | Installed and launched; permission prompts, persisted Quiet setting, database update and report review passed; locked-screen approach produced one siren with background playback completion |

For both local replays, the route was the public Gibson eastbound fixture from 35.05822,-106.6045 to 35.05822,-106.5900, at 25 m/s. The matching eastbound warning appeared on the lock screen. The journal recorded one background audio start and completion; the westbound approach was rejected. Test warning also recorded foreground completion. Low Power Mode was off and the simulated route was Speaker.

The initial While Using and notification prompts were accepted through the UI. Always access was then applied with `simctl privacy` as test setup. The setup link and the Always setting were inspected on iOS 18. The report form scrolls and reaches its review screen on the small SE display; these compatibility checks did not publish a report. A transient first launch on the freshly booted iOS 26 simulator waited in Core Location initialization; subsequent launches completed normally.

The hosted runtime Action builds one simulator app at the shipped minimum. iOS 17 and 26 use Apple's `XCUIDevice.location` proxy with `Tests/Fixtures/camera-approach.json`, press Home, and independently require exactly one completed background siren in the app journal. iOS 18 checks launch, the default Quiet setting, persistence after relaunch, and one completed **foreground** Test warning. The result names the scenario; a green foreground check is not background-location acceptance. iOS 17/18 use macOS 15 runners and iOS 26 uses macOS 26. Always access is pre-granted as a fixture.

The [hosted iOS 17.5 and 26.5 background jobs](https://github.com/aindaco1/road-notice/actions/runs/34967044388) passed with the same app binary; the iOS 18.0 job in that run failed and the overall run is red. The [current regression run](https://github.com/aindaco1/road-notice/actions/runs/34972228844) uses the explicit foreground/background scenarios described here. The tests add no location-injection path to the shipping app. Each job saves its journal, result and `.xcresult`. The collector resolves the app container after Xcode testing because Xcode can reinstall the app into a new container; the initial collector used an obsolete path, and the corrected complete local iOS 18 check passed.

**Hosted iOS 18 GPS limitation:** the command-line route driver delivered only the starting position in the independent control app on [iOS 18.0 and 18.5](https://github.com/aindaco1/road-notice/actions/runs/34963205019). Fine Me Not's UI-test route also failed to produce a background siren on hosted [18.0](https://github.com/aindaco1/road-notice/actions/runs/34967044388), [18.5 on Apple silicon](https://github.com/aindaco1/road-notice/actions/runs/34968826617), and [18.5 on Intel](https://github.com/aindaco1/road-notice/actions/runs/34970044303). Their journals stayed at the starting `tooFar` state. Removing the distance filter did not fix the [independent control](https://github.com/aindaco1/road-notice/actions/runs/34970606006): both 10 meters and `kCLDistanceFilterNone` yielded one fix, and the applied values were verified. This does not support changing the shipping app's location settings.

The same GitHub-built app passes a complete local iOS 18.0 replay, as does the local UI-test driver. The exact hosted simulator cause remains unknown. Keep the failed runs as evidence; they are not app acceptance passes. The manual background scenario and `Simulator GPS diagnostic` workflow retain the reproductions. Earlier UI-test failure probes relaunched the app without the launch-only warnings preference; that probe now explicitly enables monitoring. The control-app results above do not depend on that probe.

Physical older-OS, Silent mode, Low Power Mode, Bluetooth and CarPlay acceptance are not established by simulator playback. Keep the physical acceptance table below separate. The owner's earlier Bluetooth/locked-screen report remains the available field evidence.

## Automated checks

Run `swift test`, `python3 -m unittest discover -s Tests/Pipeline -v`, and `Scripts/check_bundle.py` against the built `.app` (add `--release` for an archive). CI exercises the shared warning engine, publisher, complete simulator bundle and embedded resources.

Core cases: approaching vs receding, opposite direction, stale/inaccurate fixes, one alert until leaving/rearming, process restart/corrected coordinates with stable IDs, long mobile corridors, expiry, unknown course, missing speed with real movement vs GPS jitter, published Coors areas in both directions, and Denver DST transitions.

Publisher cases: duplicate relation/device identity, preserved full-node tags despite skeleton responses, combined red-light/speed devices, opposing approaches, camera-facing direction, partial/mass-drop responses, missing-source retention, tombstones, expiry, metro review quarantine, immutable files and checksum.

## Earlier simulator checks (before 1.0.2)

Development compatibility build: iPhone 16 Pro Max simulator on iOS 18, built with Xcode 26.6 / iOS 26.5 SDK using an explicit development-only minimum override. This checks implementation and layout; it does not establish iOS 27 compatibility or physical background reliability.

- App starts with a real offline database and all resources.
- Settings screen readable with the intended midnight-blue design. Build 2 was rebuilt, installed and opened; its offline OpenStreetMap attribution is visible in the footer.
- Test warning starts the 1.8-second siren and returns to ready state.
- Notification and location permission prompts passed; While Using correctly reports that Always access is needed. App-specific Settings link opens the correct settings.
- Always permission granted in the simulator: simulated Gibson Boulevard driving generated a lock-screen camera notification and persisted the encounter while the app was backgrounded. This proves the simulated delivery path, not real-device scheduling, audibility, or CarPlay.
- The simulator did not provide usable course accuracy; this exposed opposite-direction ambiguity. The engine now derives travel direction from sufficient accurate displacement, covered by a regression test.
- Database public HTTPS/manifest/checksum verified. Manual Update now downloaded and installed the live snapshot `2026-09-14-0f9b8c9a0cd0-43142730` with 1,756 records, replacing the bundled copy.
- Final directional simulation while locked: eastbound Gibson encounter refreshed at 22:44:45 UTC; westbound stayed armed with its older 22:41:04 UTC timestamp. The correction warns only for the inferred travel direction.
- Fresh-source workflow run `34905568952` downloaded the speed and enforcement inputs; an alias-source HTTP 504 retained the last good aliases. The combined dataset stayed at 1,756 records and deployment succeeded. This exercised the real failure-retention path, not just fixtures.

## TestFlight installation

On September 14, 2026 at approximately 23:06 UTC, App Store Connect showed build 0.1.0 (2) Testing in the First Drive internal group and the requested tester’s device as **Installed 0.1.0 (2), iPhone 16 Pro Max, iOS 27.0**. The first-drive instructions were saved in TestFlight. This confirms Apple’s installation record; the behavior checks below remain pending.

## Physical TestFlight acceptance — partially verified

On September 15, 2026, Alonso reported hearing a real camera warning over Bluetooth while the iPhone screen was locked. This confirms physical audibility for that reported combination. The exact installed build, camera, lock duration, Silent mode, Low Power Mode, and whether music or a podcast was playing were not supplied. It does not establish the remaining scenarios below.

Use a passenger or a controlled stationary setup for observation; do not interact with the phone while driving. Record app build, iOS build, hardware, start/end time, connection, state and outcome. No route history needs to be uploaded.

| Scenario | Acceptance | Result |
| --- | --- | --- |
| Bluetooth, screen locked | Real camera warning is audible | Passed — owner reported September 15, 2026; exact build and other conditions not recorded |
| Speaker, Silent mode on | One audible brief siren; no duplicate notification sound | Pending |
| Bluetooth with music/podcast playing | Siren heard; playback ducks then resumes | Pending |
| Wired CarPlay | Siren heard with screen locked and navigation active | Pending |
| Wireless CarPlay | Same, including disconnect/reconnect | Pending |
| Zero volume / inactive car audio input | Status and test explain the limitation | Pending |
| Screen locked for 30+ minutes | Warning before the known approach | Pending |
| Another navigation app foreground | Same | Pending |
| Overnight stationary, next drive | Monitoring resumes automatically | Pending |
| Restart then first unlock and reopen | Monitoring restores saved preference | Pending |
| Force-quit then reopen | Preference restores; no always-on guarantee while terminated | Pending |
| Permission revoked / Precise off | Honest degraded status; no false monitoring claim | Pending |
| Poor GPS / tunnel / old fix | No stale-location warning; recovers on usable fix | Pending |
| Wrong direction / adjacent road | No wrong-direction alert; document unresolved parallel-road false positives | Pending |
| Stoplight / stopped beside camera | Only one siren | Pending |
| Leave >850m and return after 60s | New approach warns again | Pending |
| Database update near a camera | Stable identity prevents a second siren | Pending |
| No network / failed update | Bundled or last good database continues working | Pending |
| Monday midnight across DST | Server scheduled in Denver; phone catches up later if suspended | Pending |
| Low Power Mode / Background Refresh off | Measure actual delivery and battery behavior | Pending |
| Phone call or Siri interruption | No crash or stale siren replay after interruption | Pending |
| 1-hour drive and 8-hour stationary | Record battery consumption before release claims | Pending |

## Coverage acceptance

Reconcile every listed metro approach, preserve documented mobile corridors, exclude pending installations and retired cameras. Drive-test representative city, county and Rio Rancho sites in both directions. The first bundle is incomplete; a lack of an alert is not evidence that a road is camera-free.

## Missed-warning investigation — build 4

The report was a missed siren on Coors north of I-40, probably with the screen locked. No physical-device logs were available. The city-listed Coors/St. Joseph approaches were absent from the previous accepted database; the exact device passed is not confirmed. Reviewed approximate areas are now included, with the uncertainty stated in their labels and source evidence.

A regression reproduced total warning suppression when speed stayed unavailable even though accurate positions showed movement. Movement and bearing now use a shared displacement fallback before the movement gate. Jitter, stale anchors and implausible jumps do not count as driving. Fourteen Swift tests and ten publisher tests pass.

Continuous standard background location replaces the original async provider; automatic pausing is disabled. This is a reliability change whose real-device effect must be measured, not proof that the previous provider caused this incident. Audio still uses a brief `.playback` / `.duckOthers` session. The app retains only the latest audio attempt with timestamp, camera label, app/power state, route, volume and completion/error. Diagnostics also expose GPS quality, effective movement, match rejection and notification settings.

An upgrade test initially kept an old downloaded 1,756-record snapshot even with the new bundle installed. Startup now selects the newest valid snapshot across the download, backup and bundle. Retesting the upgrade preserved settings and selected the new 1,758-record snapshot without a manual download. The public manifest and immutable file checksum were verified after successful Pages deployment in run `34912766050`.

Build 4 locked-screen simulator route: northbound Coors generated the expected NB warning at 00:22:16 UTC on September 15 (September 14 Mountain time), with persisted audio status `Playback completed`, app state `background / locked`, speaker output and 60% media volume. No SB encounter was created during that northbound run. The simulator had Low Power Mode off. This proves simulated matching and audio completion; it is not a physical audibility test.

The southbound locked-screen replay generated only its SB warning at 00:23:28 UTC, with audio completion persisted. The diagnostics panel showed build 4, the corrected database, Always/Precise state, current GPS/match details and the prior background siren after relaunch. Resetting the simulator app's location authorization produced the normal location prompt again.

Apple completed build 4 processing and First Drive showed **0.1.0 (4), Testing**. [App source CI](https://github.com/aindaco1/road-notice/actions/runs/34913290315) passed. Build 4 installation and the physical acceptance matrix remain pending.

## City coverage expansion — build 5

All 40 city-listed approaches are represented by stable production IDs (19 mapped camera points, 21 approximate warning areas). Fifteen Swift and twelve publisher tests pass. The new checks compare every city inventory row against the actual published snapshot and verify its monitored direction; validate every added area segment against referenced OSM road edges; and replay all 21 city areas to require one matching-direction warning and no opposite-direction warning for that record. Geometry was also inspected in three road/junction review sheets.

The database contains 1,777 records in version `2026-09-14-6466b7b09db1-78026b1a`. Carlisle’s source typo was resolved using the official certificate’s Delamar Avenue description, and the Eubank certificate and Juan Tabo documents clarify the side of the cross street. This validates representation and simulated behavior; the physical camera positions and the phone acceptance matrix remain unverified. No location/audio runtime code changes were made for build 5.

[Build 5 source CI](https://github.com/aindaco1/road-notice/actions/runs/34915680253) passed for `632c77b`. [Database/website publication](https://github.com/aindaco1/road-notice/actions/runs/34915680188) succeeded. The public immutable snapshot matched its SHA-256 manifest and contained exactly one record for each ABQ-01 through ABQ-40 reference. The installed build 4 simulator downloaded it through **Update now**, changing from 1,758 to 1,777 locations. This confirms that existing build 4 installations can receive the coverage expansion without waiting for a new binary. The build 5 signed archive passed the bundle check with minimum iOS 27.0 and 1,777 cameras.

After that live download, a southbound Carlisle replay produced exactly the new `abq-carlisle-hilton-delamar-possible-sb` encounter at 01:05:02 UTC on September 15 (September 14 Mountain time). The app recorded **Playback completed**, **background / locked**, speaker output, and 60% media volume. This demonstrates the new data’s full simulated matching/audio path in build 4; physical audibility and actual hardware coordinates remain unverified.

Apple completed build 5 processing and the First Drive group showed **0.1.0 (5), Testing**, with its test instructions saved. Physical installation and the device acceptance matrix remain pending.

## Agency source expansion — September 14, 2026

The live-source pass fetched all three national OSM queries and all eight coordinate adapters. Four page monitors returned HTTP 403; they retained their previous snapshot when one existed and were recorded as review failures. The staged-pass freshness check reused the completed source pass for publication.

Local validation: **28 Python pipeline tests and 16 Swift matcher tests pass**. Coverage includes partial API responses, source-count drops, last-good retention, sticky page changes, map boundaries, unknown/conditional limit candidates, nearby/opposing approaches, explicit identity aliases, moved/renamed agency records, staged refresh age, and Denver daylight-saving offsets. Replay covers 20 city plus nine county road areas and the tightened Eubank point with unavailable reported speed/course. The expanded snapshot decodes through the existing app model.

These changes update data and maintenance tooling. No app runtime code or TestFlight binary was changed. Existing installations receive the new database using Update now or their permitted automatic download; the bundled fallback remains the database from their installed build. Physical audibility and location-delivery acceptance remain separate from these checks. The optional speed-check toggle remains a documented follow-up, not a shipped setting.

The [source build and compatibility CI](https://github.com/aindaco1/road-notice/actions/runs/34920018736) and [public database deployment](https://github.com/aindaco1/road-notice/actions/runs/34920018690) passed for implementation commit `005317c`. The live manifest and immutable snapshot were independently downloaded and matched SHA-256 `9c6e0a803ba695164220c6458cde701e641cb0f3fd7acc0d16cb0cd1c84d575c`, version `2026-09-14-fc86266ce021-24309b02`, with 2,653 records.

The [new prepublication source-check workflow](https://github.com/aindaco1/road-notice/actions/runs/34920063583) was also manually exercised on GitHub and completed successfully, staging its checks without a Pages deployment. Individual source failures remain listed in the source report; workflow completion does not claim every agency request succeeded.


## 1.0.3 branding verification — September 16, 2026

Version 1.0.3 (11) passes 26 Swift and 63 pipeline tests. The iPhone 18 Pro / iOS
27 simulator was visually reviewed at default and largest accessibility text
sizes; the header switches from horizontal to stacked without clipping its icon
or wordmark. The release and simulator bundles preserve the iOS 17.0 minimum.

[Hosted runtime checks](https://github.com/aindaco1/road-notice/actions/runs/35152261051)
passed on iOS 17.5, 18.5 and 26.5 using the same compiled simulator app. The 17/26
scenarios require one completed background camera siren; 18 verifies the saved
Quiet setting and foreground Test warning. This preserves the separate iOS 18
background-testing limitation described above. Build 11 is Testing in First
Drive; physical installation and new physical audio tests remain unverified.
