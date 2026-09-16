# Release and distribution

**1.0.3 branding update:** source version 1.0.3 (11) matches the app header to
finemenot.xyz. See the dated verification section at the end.

**1.0.2 compatibility update:** version 1.0.2 (10) lowers the minimum to iOS 17.0. The dated 1.0 and 1.0.1 records below describe earlier binaries. See the latest verification section at the end and [supported versions](SUPPORT.md).

**1.0.1 reporting update:** source version 1.0.1 (9). Voluntary public reports change the privacy disclosure; the 1.0 Data Not Collected answer below is historical. See [REPORTING.md](REPORTING.md). Distribution verification is recorded separately from the existing 1.0 submission.

- App: Fine Me Not
- Bundle: `xyz.dustwave.fine-me-not`
- Owner/team: Volver Health LLC (`PWT3Q52LZ2`), explicitly selected by the project owner
- TestFlight: **1.0.3 (11), Testing** in First Drive as of September 16, 2026
- Pending App Store version: 1.0.0 (8)
- App Store: **Waiting for Review** as of September 16, 2026; automatic U.S. release after approval
- Release history: https://github.com/aindaco1/fine-me-not/releases
- Minimum: iOS 17.0 for 1.0.2; earlier binaries require iOS 27.0
- Source: https://github.com/aindaco1/fine-me-not
- Support / privacy: https://finemenot.xyz/
- Category: Utilities (minimal camera proximity warnings)
- Price: Free; no purchases, subscriptions, ads or accounts

## Build

Use Xcode 26.6 or a newer compatible release toolchain. `project.yml` is the project configuration source; regenerate with XcodeGen after changes. The checked-in Xcode project permits building without XcodeGen.

```sh
swift test
python3 -m unittest discover -s Tests/Pipeline -v
xcodebuild -project FineMeNot.xcodeproj -scheme FineMeNot \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath work/FineMeNot.xcarchive -allowProvisioningUpdates archive
python3 Scripts/check_bundle.py work/FineMeNot.xcarchive/Products/Applications/FineMeNot.app --release
```

Simulator and distribution builds must use the deployment target in `project.yml`; do not add a minimum-OS override. Increment the build number for each uploaded binary. Xcode's saved account may create/refresh team signing assets; credentials and provisioning files are never committed.

## App Store Connect

Create or select the app record for the exact bundle ID under Volver Health LLC. Upload a signed App Store Connect distribution with symbols. Confirm Apple has processed the build, export compliance is resolved, and the build is assigned to a test group containing the owner-requested tester. Use internal testing if that tester is already an eligible App Store Connect user; otherwise use external testing and complete Apple’s beta review. Do not grant an App Store Connect role solely to bypass beta review. A successful archive or upload alone is not TestFlight delivery.

Only standard HTTPS is used. `ITSAppUsesNonExemptEncryption=false`. No account is needed to review the app. Version 1.0.1 adds voluntary public support and diagnostic reports; use the reporting privacy categories recorded below and in [REPORTING.md](REPORTING.md). Location stays on the device. Confirm privacy answers against the final binary before submission.

## Suggested beta description

Fine Me Not gives you one brief siren as you approach a mapped speed or red-light camera. Free, open source, no ads or subscriptions. Turn warnings on once, allow Always and Precise Location, and test the warning on your car audio while parked. The app uses your selected audio route and media volume, including in Silent mode. Albuquerque metro coverage and background reliability are being tested; coverage is incomplete and warnings are not guaranteed.

## What to test

Check the siren on iPhone speaker, Bluetooth and CarPlay in Silent mode. Test screen-locked driving, another navigation app open, overnight stationary recovery, direction filtering, no repeat while stopped near a camera, offline warnings, and database updates. Follow [TESTING.md](TESTING.md). Note the public site name, app build and phone/audio state in feedback; do not include personal routes in public GitHub issues.

## Review notes

The app's only background purpose is user-enabled camera proximity warnings. Core Location computes proximity on device; it does not upload locations. The audio background mode is used only for the short audible warning. There is no silent audio loop. Open the app, enable Camera warnings, grant location permissions, and tap Test warning to exercise the sound. No CarPlay UI or critical-alert entitlement is requested. Mobile deployment areas say Possible speed camera because presence is not live-confirmed.

## Gates

1. Source tests and full bundle checks pass.
2. Signed archive passes export and App Store validation.
3. Apple finishes processing; build is available to the owner in TestFlight.
4. Verify installation on a supported iPhone; record the model, iOS version, permission setup and build in the acceptance record.
5. Record physical audio/background results separately from distribution. On September 15, 2026, the owner confirmed a real Bluetooth warning with the screen locked and explicitly requested release of 1.0 before completing the remaining device checks. Low Power Mode, speaker/Silent mode, CarPlay and battery checks remain pending; do not describe them as passed or promise uninterrupted warnings.

## 1.0 release — September 15, 2026

Version **1.0.0 (8)** bundles the current **2,695 warning locations** and expanded speed-limit evidence. The release removes the in-app beta label while preserving the coverage/audio limitations and adds a reminder to follow posted signs. There are no location, matching or audio runtime changes from the latest test build. The owner has authorized publication with the remaining physical checks deferred; see [TESTING.md](TESTING.md).

The [official GitHub release](https://github.com/aindaco1/fine-me-not/releases/tag/v1.0.0) is published at source commit `093e2872036fe0253dd06de8a38b13af40c03314`. The website and weekly database are deployed. Apple received version 1.0.0 (8) at **02:10 MDT on September 15, 2026** and shows **Waiting for Review**. The app is free, initially available in the United States, with automatic release after Apple approval. Mac and Apple Vision Pro availability are disabled. The app remains under the owner-selected Volver Health LLC Apple team; the project maintainer is Alonso Indacochea.

Apple accepted **1.0.0 (8)** at **07:27:51 UTC on September 15, 2026**. Processing completed and the existing First Drive internal group with one tester shows **Testing**. Build-specific device-test instructions are saved. No tester roles changed. The physical phone was last shown on 0.1.0 (7); installation of 1.0 remains unverified.

Validation passed: **21 Swift tests, 63 Python tests**, codesign verification, full release bundle checks (version/build matched to `project.yml`, minimum iOS 27.0, 2,695 cameras), and a simulator compatibility build/install/launch. The signed archive uses Xcode 26.6 / SDK 26.5 without a distribution minimum override. Its bundled database is `2026-09-14-729f56d56437-796706f6`, SHA-256 `5da6f8ec0bfaef2646f26aa8a2bcb09d56f18b802672dd6fea6f2f294b761b8e`.

The completed App Store listing includes the actual 6.9-inch iPhone screenshot (automatically reused for the 6.5-inch slot), description, permission setup instructions, support and privacy links, age rating 4+, Utilities category, build 8 and private App Review contact. The owner confirmed the privacy attestation; **Data Not Collected** is published with `https://finemenot.xyz/#privacy`. Private contact details are stored only in App Store Connect.

Apple confirmed **1 Item Submitted**, followed by **Waiting for Review** for 1.0.0 (8), on September 15, 2026 at 02:10 MDT. Submission ID: `fb55d309-ed07-4e2c-844d-1bc3677a2d17`. Automatic release after approval is selected. Submission does not mean Apple has approved the app or that the public App Store listing is live.

[Release source CI](https://github.com/aindaco1/fine-me-not/actions/runs/34943986572) and [website/data deployment](https://github.com/aindaco1/fine-me-not/actions/runs/34943986798) both passed. The live HTTPS site and immutable database passed `Scripts/check_site.py` with 2,695 locations and 1,305 of 1,765 speed approaches eligible for suppression.

## Release evidence — September 14, 2026

Xcode confirmed **0.1.0 (2) uploaded successfully** to App Store Connect under Volver Health LLC at 22:56 UTC. Apple reported that the uploaded package was processing. Source/build commit: `7cabd13`; bundled snapshot: `2026-09-14-0f9b8c9a0cd0-43142730`, 1,756 warning records. Build 2 adds offline OpenStreetMap attribution. The previous build, 0.1.0 (1), also uploaded successfully.

[Build 2 CI](https://github.com/aindaco1/fine-me-not/actions/runs/34906072688) passed. At approximately 23:06 UTC, App Store Connect showed build **0.1.0 (2)** as **Testing** in the **First Drive** internal group, with the owner-requested tester assigned. The tester was already an eligible team member; no App Store Connect role was added. TestFlight then reported **Installed 0.1.0 (2)** on **iPhone 16 Pro Max / iOS 27.0**. The tester’s email is omitted from this public repository.

The build’s What to Test instructions were saved in TestFlight, covering permissions, audio routes, screen-locked and overnight behavior, direction/repeat filtering, offline operation and database downloads. The group uses manual build assignment; future uploads must be added after validation. This is an internal beta, not a public App Store release.

The archive and exported distribution signed successfully using Xcode’s saved team account. The final archive passed the complete bundle check with MinimumOSVersion 27.0, version 0.1.0, the siren, database, icon, privacy manifest and expected background modes. Processing, tester assignment and the reported device installation were subsequently verified in App Store Connect. Physical background reliability, audio audibility and battery acceptance remain pending; installation alone does not establish those behaviors.

## Icon update — build 3

Build 0.1.0 (3), source `9d975fd`, replaces the ticket with a speed camera and pale-blue prohibition overlay. The 1024 × 1024 opaque icon was checked on the simulator Home Screen, and the signed archive passed the bundle check. Apple confirmed the upload at 23:21 UTC on September 14, 2026. Apple finished processing and the First Drive group now shows build 0.1.0 (3) as Testing. The icon update notes were saved in TestFlight. [CI](https://github.com/aindaco1/fine-me-not/actions/runs/34908349722) passed. Installation of build 3 on the physical phone has not been checked.

## Missed-warning fixes — build 4

Build **0.1.0 (4)**, source `fd99484`, is **Testing** in the First Drive internal group. Apple accepted the upload at 00:29 UTC on September 15, 2026 (September 14 Mountain time), after a network timeout on the first export attempt. Processing completed, the build-specific test instructions were saved, and the existing group with one tester was assigned. No tester roles or access changed. Physical installation of build 4 has not been verified.

This build requests continuous standard background location with automatic pauses disabled, infers movement when reported speed is unavailable, chooses the newest valid saved/bundled database, and adds local diagnostics. It bundles `2026-09-14-971a10f8454e-571f726e` with 1,758 warning records, including approximate Coors/St. Joseph NB/SB warning areas. The city confirms the site and directions, but exact device positions remain unverified.

[CI for the app source](https://github.com/aindaco1/fine-me-not/actions/runs/34913290315) passed all 14 Swift and 10 publisher tests and the simulator bundle checks. The signed archive passed validation with minimum iOS 27.0. Both Coors directions produced one warning and recorded siren completion during locked-screen simulator replays. Real iOS 27 Low Power Mode, long idle recovery, car-audio audibility and battery use still require physical acceptance. See [DEBUGGING.md](DEBUGGING.md) for findings and the next phone test.

## Complete city-list representation — build 5

Build **0.1.0 (5)**, source `632c77b`, is **Testing** in the First Drive internal group. Apple accepted the upload at 01:09:47 UTC on September 15, 2026 (September 14 Mountain time). Processing completed, the build-specific What to Test notes were saved, and the existing group with one tester was assigned. No tester roles changed. Installation of build 5 on the physical phone remains unverified.

The build bundles `2026-09-14-6466b7b09db1-78026b1a` with **1,777 warning records**. The 19 additions bring current Albuquerque city-list representation to **40 of 40 directional approaches: 19 mapped points and 21 approximate areas**. Carlisle uses Delamar Avenue as confirmed by the city certificate. Approximate boundaries follow reviewed OSM road geometry; they are warning buffers, not surveyed equipment positions or enforcement boundaries. See [ALBUQUERQUE.md](ALBUQUERQUE.md) for every city entry. No location/audio runtime code changed for this build.

[Source CI](https://github.com/aindaco1/fine-me-not/actions/runs/34915680253) passed all 15 Swift and 12 publisher tests and the simulator bundle checks. The signed archive passed the full release bundle check with minimum iOS 27.0. [Database publication](https://github.com/aindaco1/fine-me-not/actions/runs/34915680188) succeeded; the live immutable snapshot matched its SHA-256 manifest and all 40 city references. An installed build 4 simulator downloaded it using Update now, then produced exactly one southbound Carlisle warning with playback completed while locked. These checks establish data delivery and simulated behavior. Real iOS 27 car-audio audibility, Low Power Mode, overnight recovery and battery acceptance remain pending.

## Speed check and automated maintenance — build 6

Build **0.1.0 (6)**, source `af60017`, is **Testing** in the First Drive internal group with the existing one tester. Apple accepted the upload at **03:56:29 UTC on September 15, 2026** (September 14 Mountain time). Processing completed, build-specific What to Test notes were saved, and group availability was verified at approximately 04:04 UTC. No tester roles changed. Physical installation and driving acceptance of build 6 remain unverified.

The build adds the default-on Quiet below speed limit setting and diagnostics. It bundles `2026-09-14-263679a7aa6b-9935f9b5` with **2,681 records** and 31 approved SFMTA speed limits. Unknown, stale or conditional limits continue to warn, including Albuquerque where approved camera limits are not yet available. Red-light and combined warnings remain on. A quiet encounter remains armed in case speed subsequently rises.

The signed archive passed codesign verification and the release bundle check (minimum iOS 27.0). [Source CI](https://github.com/aindaco1/fine-me-not/actions/runs/34926802914) passed 20 Swift tests, 39 pipeline tests and the simulator compatibility build. Simulator UI checks verified the upgrade default on, persisted off after relaunch, the Test warning button, and the bundled count. The archive uses Xcode 26.6 / SDK 26.5 with the requested distribution minimum 27.0; simulator deployment overrides are never used for the distribution archive.

The [GitHub source-check run](https://github.com/aindaco1/fine-me-not/actions/runs/34926817137) and subsequent [staged publication](https://github.com/aindaco1/fine-me-not/actions/runs/34927188598) both completed successfully. The latter publishes **2,695 records** in `2026-09-14-352059fee0b5-23bbacd6`, adding 14 Chicago approaches once refreshed source road metadata made their distinct identities clear. Its live SHA-256 matches the manifest. Four watched pages returned HTTP 403, and an OSM alias query returned HTTP 429; previous evidence was retained and failures remain recorded. A green workflow means the resilient pipeline completed, not that every source responded successfully. The Codex maintenance heartbeat was deleted; recurring work now runs entirely in GitHub Actions.

The installed build 6 simulator fetched that newer snapshot using Update now and visibly displayed **2,695 warning locations**, with Quiet below speed limit still enabled. This verifies the download/validation/display path independently of the offline bundle. It does not establish physical background delivery timing or car-audio behavior.

## Custom domain and source research — build 7

Build **0.1.0 (7)**, app source `61938f2`, is **Testing** in the First Drive internal group with the existing one tester. Apple accepted the upload at **04:31:51 UTC on September 15, 2026** (September 14 Mountain time). Processing completed, the build-specific notes were saved, and group availability was verified at approximately 04:43 UTC. No tester roles changed. The physical phone was last reported on build 6; installation and field acceptance of build 7 have not been verified.

This build centralizes website/database URLs in `AppLinks` and moves them directly to `https://finemenot.xyz/`. It bundles **2,695 warning records** in `2026-09-14-352059fee0b5-23bbacd6`, with the existing 31 approved SFMTA limits. No new research speed-limit candidates were approved for suppression. The owner requested no compatibility work for older test builds.

The signed archive passed codesign verification and the release bundle check with minimum iOS 27.0. The simulator compatibility build installed and launched with 2,695 records and the default-on speed check. [App source CI](https://github.com/aindaco1/fine-me-not/actions/runs/34928273608) passed, as did the [research/source-monitor CI](https://github.com/aindaco1/fine-me-not/actions/runs/34929151098) and [site publication](https://github.com/aindaco1/fine-me-not/actions/runs/34929151034). Local pipeline verification passed 39 tests. The archive still uses Xcode 26.6 / SDK 26.5; simulator deployment overrides were not used for distribution.

**Domain activation was resolved at approximately 23:20 Mountain on September 14.** Once public DNS propagated, GitHub's stalled certificate request was restarted. The certificate now covers `finemenot.xyz` and `www.finemenot.xyz`; Pages HTTPS enforcement is on. Both DNS records are now proxied through Cloudflare, matching the other Dust Wave Pages sites, with Full (strict) origin encryption and Always Use HTTPS. The public page and all 2,695 camera records validate over HTTPS through Cloudflare. The privacy text names both hosting providers. No new app binary is required.

The [manual, read-only HTTPS verification run](https://github.com/aindaco1/fine-me-not/actions/runs/34929772047) passed; `Scripts/check_site.py` also passed after Cloudflare proxying was enabled. No recurring schedule was added. Update now and the website link in build 7 still need physical iPhone acceptance. The [website runbook](WEBSITE.md) records the routing contract and certificate recovery procedure.

The [research report](DATA-RESEARCH.md) documents new camera sources and speed-limit APIs. Nine page monitors were added to the existing Sunday GitHub source checks; seven succeeded locally and two returned 403. New camera readers, road matching and approval of additional speed limits remain identified implementation work, not shipped data coverage.

## 1.0.1 (9) reporting verification · September 15, 2026

The signed iOS 27 distribution archive passed the bundle check. Apple accepted
its upload at 02:55 MDT. TestFlight processing/assignment is recorded separately.
Version 1.0.0 (8) remains Waiting for Review and was not cancelled.

- 26 Swift tests and 63 data-pipeline tests pass. Reporting tests cover allowlists,
  text bounds, immutable drafts/expiry, local coalescing, the shared fixture and
  crash-frame filtering. 49 relay tests cover concurrency, ID conflicts, quotas,
  grouping, escaped explanations and the existing apps' adapters.
- Relay `fe3000f` deployed through GitHub Actions as Worker version
  `258d77ed-2fe0-493c-98d2-07623e3eec98`. The owner confirmed adding Fine Me Not
  to the existing GitHub App's selected repositories.
- Synthetic issue #1 verified creation, same-ID retry without recounting, a new-ID
  aggregate, then reopening after closure. Count was three submissions. A
  maintainer note outside the managed block survived. The test issue was closed.
- Native simulator review and Send returned a verified link to issue #2; its body
  matched the reviewed safe projection and synthetic explanation. It was closed.
  No real crash, trip or private user report was published.
- Matching distribution dSYM UUIDs and `atos` symbolication were checked against a
  known app symbol. MetricKit parsing uses synthetic fixtures; actual Apple
  crash/hang delivery on a physical phone remains a separate acceptance check.
- Simulator UI review used an iOS 18 deployment override because the installed SDK
  cannot select a simulator for an iOS 27 target. Distribution remains iOS 27.

TestFlight processing completed for **1.0.1 (9)**. The **First Drive** internal
group shows **Testing**, with its existing one tester. The saved What to Test text
covers review/send, text-only reporting, offline retry and normal camera alerts.
Installation of this build on the physical iPhone is not yet confirmed.

App Store Connect now publishes **Customer Support, Crash Data and Other
Diagnostic Data**, each used for **App Functionality**, conservatively linked to
identity, and **not used for tracking**. The website privacy policy describes
explicit submission, public issues, the safe automatic fields and retention.
No new agreement prompt appeared when publishing these category updates.

The live website passed HTTPS/data/asset validation and a 390-point mobile layout
check without horizontal overflow. Hosted build/tests, website deployment and the
manually verified daily reporting-health Action all passed. The current 1.0
App Store submission remains Waiting for Review; 1.0.1 is distributed through
TestFlight, not submitted as a replacement for that pending version.

The final relay revision `c415d33` passed all 49 tests and
[deployed successfully](https://github.com/aindaco1/ascii-vj-remix/actions/runs/34951613625).
It retains each issue group's retry receipts for the full 30-day window and keeps
cleanup scheduled during ongoing submissions. A repeat of the original live
synthetic report returned its existing issue; the count remained three and the
issue stayed closed. No app binary changes were needed for this relay update.

## 1.0.2 compatibility — September 15, 2026

Version **1.0.2 (10)** lowers the distribution minimum to **iOS 17.0**. iOS 17
uses the two-step location-permission request; iOS 18 and later retain the service
session. Both use the same background location manager, matcher and audio path.

The signed archive was built with Xcode 26.6 / iOS 26.5 SDK, passed release bundle
validation with 2,695 bundled cameras, and has matching app/dSYM UUIDs. The app
source at `3458537` is unchanged by the subsequent CI-tooling commits. All 26 Swift
tests and 63 pipeline tests passed, locally and in the
[hosted checks](https://github.com/aindaco1/fine-me-not/actions/runs/34972228732).
Exact OS integration results and physical-test limits are in [TESTING.md](TESTING.md).

Apple accepted the upload at **04:20:58 MDT**. App Store Connect shows binary
state **Validated**, symbols included, device family **iPhone**, and minimum iOS
**17.0**. Test instructions cover permission setup, database refresh, the siren,
saved settings and optional reports.

The local cleanup removed 15 obsolete generated build/cache/archive directories,
freeing about **703 MiB**. The 1.0.0, 1.0.1 and 1.0.2 release archives and matching
symbols were retained for crash symbolication. Source, camera data and unrelated
work were preserved. Older runtime regression checks now run on GitHub-hosted
Macs, avoiding additional simulator-runtime storage on the development Mac.

By **07:07 MDT**, the existing **First Drive** internal group with one tester was
assigned and App Store Connect showed **1.0.2 (10) — Testing**. Installation of
build 10 on the physical phone is not yet verified; the last reported installed
build was 1.0.1 (9). No tester roles or privacy categories changed. The initial
1.0.0 App Store submission remains **Waiting for Review**, rechecked at 07:07 MDT.

The automatic runtime checks use iOS **17.5, 18.5 and 26.5**. The 17/26 checks
require exactly one background camera siren; the 18 check verifies launch, the
saved Quiet setting and one foreground Test warning. Complete local iOS 18.0
background playback passes. Hosted iOS 18 moving-GPS failures also reproduce in
minimal controls and remain documented diagnostics, not accepted background
results. See [TESTING.md](TESTING.md) for evidence and exact limits.

[Runtime regression evidence](https://github.com/aindaco1/fine-me-not/actions/runs/34972228844) includes the exact scenario and retained journal for each OS.

## 1.0.3 branding — September 16, 2026

Version **1.0.3 (11)** replaces the aperture symbol and vertically separated title
with the website's speed-camera icon and side-by-side, two-line wordmark. The
header uses one canonical icon asset, supports Dynamic Type and exposes one
VoiceOver heading. Monitoring, saved preferences, reporting and audio are unchanged.

Local validation passes **26 Swift tests and 63 pipeline tests**. The iPhone 18
Pro / iOS 27 simulator renders the horizontal header at default text size and the
stacked header at the largest accessibility text size. The simulator bundle
passes resource/version checks with minimum iOS 17.0 and 2,695 warning locations.
Physical installation is a separate check.

Use a build cache outside iCloud if Swift test signing reports “resource fork,
Finder information, or similar detritus not allowed,” for example
`swift test --scratch-path ~/Library/Caches/FineMeNot/swift-build`.

Apple accepted Fine Me Not 1.0.3 (11) on September 16, 2026 at 15:25 MDT.
App Store Connect lists upload completion at 15:26 MDT, binary state Validated,
iPhone, minimum iOS 17.0 and symbols included. The existing First Drive internal
group with one tester shows Testing; What to Test notes are saved. Installation
of build 11 on the physical phone is not yet verified. The previous installed
build was confirmed as 1.0.2 (10) on iPhone 16 Pro Max / iOS 27.

The initial 1.0.0 (8) App Store submission remains Waiting for Review, checked in
App Store Connect during this release. This update is distributed by TestFlight.

Build 11 was archived with Xcode 27.0 (27A266a) / iOS 27 SDK. Signature and release
bundle checks passed with iOS 17.0 minimum and 2,695 camera records. The app and
archived dSYM both have UUID 515AE8F4-B645-305F-AEFC-DE094676B9D5.

[Hosted build/tests](https://github.com/aindaco1/fine-me-not/actions/runs/35152261077)
and [runtime compatibility](https://github.com/aindaco1/fine-me-not/actions/runs/35152261051)
passed for release source `1be858b`: one completed background camera warning on
iOS 17.5 and 26.5, and saved-setting/foreground siren verification on iOS 18.5.
The iOS 27 visual review is saved in `docs/screenshots/1.0.3-settings.png`.

Cleanup moved **17 obsolete generated paths (512 MiB)** to a dated folder in
macOS Trash. The current simulator development build and outside-iCloud Swift
test cache remain. Signed 1.0.0 (8), 1.0.1 (9), 1.0.2 (10) and 1.0.3 (11) archives
with their matching dSYMs are retained under `~/Library/Developer/Xcode/Archives`
for crash symbolication. Compact previous runtime evidence and the current
release/cleanup logs remain in `work/release11`.

The superseded `ci/ios18-patch-check` investigation branch was removed locally
and remotely after saving and verifying a Git recovery bundle in the same Trash
folder. Its runtime selector and filter fixes already exist in main; its unused
Intel-runner experiment is preserved in that bundle. The branding branch was
removed after [PR #3](https://github.com/aindaco1/fine-me-not/pull/3) merged. Only
`main` remains; source, camera data, signing assets and simulator runtimes were
preserved.
