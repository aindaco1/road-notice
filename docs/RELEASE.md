# Release and distribution

## 1.0.7 (20) upload — November 4, 2026

[PR #8](https://github.com/aindaco1/road-notice/pull/8) merged as `fb2ad15`.
The [website and camera deployment](https://github.com/aindaco1/road-notice/actions/runs/41790954702)
succeeded. Both public feeds pass canonical HTTPS, immutable snapshot, digest,
record-count and coverage checks. The current database has **2,728 cameras and
701 road zones**; the website includes the current Quiet, persistent-zone and
Do Not Disturb guidance.

The signed **1.0.7 (20)** archive was built from `55e3459` with Xcode 27.2,
retaining the project minimum **iOS 17.0** and public `/data/v2/` channel.
Apple accepted its standard App Store Connect upload with symbols at
**00:26:41 MST (07:26:41 UTC)** and began processing it. This is not an
internal-only TestFlight build. Processing completion and App Review submission
remain pending verification.

Release-bundle and signature checks pass. The app and dSYM share UUID
`0C649BD3-F8F3-34A7-852A-4EF9B68B7521`. Bundled snapshot
`2026-11-02-849ee6ac8b27-d0ef599a` exactly matches the live modern feed, with
SHA-256 `bca51a4fd9045fbd8c649d269d517d94f68774c6dbc783c579f5525fb62398df`.
The complete archive is retained at
`~/Library/Developer/Xcode/Archives/2026-11-04/RoadNotice-1.0.7-20.xcarchive`;
prepared listing copy, verification and upload evidence are in ignored
`work/release20/` in the release worktree.

The [alert correction record](ALERT-FIXES.md) retains the regression and road-data
acquisition evidence. Critical Alerts are not added. Physical battery, overnight
departure and normal phone notification-tap checks remain separate acceptance
items; archive and upload success do not establish those results.

## App Store submission — October 7, 2026

**Road Notice 1.0.6 (19) is Waiting for Review.** Apple confirmed one item
submitted at **17:40 MDT (23:40 UTC)**. The
[submission](https://appstoreconnect.apple.com/apps/6812094105/distribution/reviewsubmissions/details/da791fd7-1e17-462b-a334-05dec756bdd0)
contains standard build `c5761094-66b0-4f6a-a807-6d6e74f37b9f`.
The saved description, What's New and review notes cover the local alert log,
road-aware approaches, stationary recovery and notification-opening crash fix.
Existing screenshots and published privacy disclosures were verified. Automatic
release after approval and immediate updates remain selected. Version 1.0.5 (13)
remains Ready for Distribution; submission does not establish approval or public
availability of 1.0.6.

Source/runtime CI, the retained archive signature and release-bundle checks were
reverified. Both live public feeds pass their website and data checks with 2,711
records; the submitted bundle retains its 2,701 records and 54 road zones.
Physical battery, overnight departure and normal phone notification-tap checks
remain open. No TestFlight group assignment changed. Confirmation and the
submission record are retained in ignored `work/release19/`.

## Public 1.0.6 deployment — October 4, 2026

[Version 1.0.6](https://github.com/aindaco1/road-notice/releases/tag/v1.0.6)
is the latest GitHub release. [PR #7](https://github.com/aindaco1/road-notice/pull/7)
merged as `0665f9e`; its tree matches tested source `ce2a45d`. The signed
**1.0.6 (19)** archive passed signature and bundle checks, and Apple accepted its
standard App Store Connect upload, including symbols, at **19:09:46 MDT**.

The [website/database deployment](https://github.com/aindaco1/road-notice/actions/runs/37251699477)
completed successfully. Both live feeds pass website, digest, immutable snapshot,
count and speed-limit coverage checks. The `/data/v2/` snapshot
`2026-09-28-161eb14e875c-1f615099` exactly matches the uploaded archive's camera
bytes; the actual released 1.0.5 validator accepts all 2,701 legacy-feed records.

**At deployment, Apple submission was pending.** The last verified App Store version was
1.0.5 (13), Ready for Distribution. Upload success does not establish build 19's
processing, selection for App Review, submission, or First Drive assignment;
the October 7 record above establishes the subsequent submission.
Prepared description, What's New, review notes and test instructions are in
ignored `work/release19/`. Existing distributed betas remain available until the
replacement is assigned. GitHub and website publication are separate from App
Store availability.

The owner requested promotion of the latest candidate and publication. App Store
Connect was verified as **1.0.5 (13), Ready for Distribution**. Internal-only
build 17 cannot be promoted to App Review, so **1.0.6 (19)** packages its features
for standard App Store Connect distribution, with iOS 17 minimum.

The release uses `https://finemenot.xyz/data/v2/`, replacing the private pinned
candidate feed. The normal local cache and saved user settings remain compatible.
One publisher supplies both public feeds. The original `/data/` feed projects
confirmed speed-camera polylines to the older `possibleSpeed` classification,
preserving IDs, coordinates, directions, limits and all other camera fields.
This avoids older validators rejecting the entire download. Each projection gets
its own immutable filename and checksum; previously published bytes remain intact.

All **2,701 cameras and 54 road zones** are retained. Every zone is identical to
build 17, including Coors, and both field-verified 45 mph observations remain.
Release preparation found an incomplete September 28 road-source refresh had
replaced the active cache index with a mostly unavailable query set. The fetcher
now activates a replacement query set only when all its cached batches exist;
otherwise it retains the last active set with its original dates and expiry.
Build 18 was uploaded during preparation but is superseded and is not the release
candidate. Its reduced 38-zone snapshot was never deployed to the public feed.

Source tests cover partial replacement, complete replacement and unrelated caches.
Physical battery, overnight departure and normal phone notification-tap checks
remain open in the acceptance record. Release evidence is in ignored
`work/release19/`; the signed archive is retained in Xcode Archives after packaging.

### Cleanup completed

Only `main` remains locally and on origin; the merged `battery-road-zones` branch
was removed. Obsolete local artifacts and three duplicate test simulators freed
approximately **11.8 GB**. The superseded build 18 archive was removed only after
its dSYMs and archive metadata were copied and UUID-verified. Older signed archives
were already absent when this task began; historical retention entries below do
not describe the current inventory.

Kept: the complete build 19 signed archive, uploaded-build symbols, current
simulator derived data (`/tmp/road-notice-sim19`), current Swift package cache
(`/tmp/road-notice-core18`), build 19 prepared test products, final app-hosted and
iOS 18 UI results, one iOS 27 failure result, and two simulators for local iOS 18
and iOS 27 testing. Release logs, selected screenshots, source snapshots and
immutable published camera files remain. The separate shared-support worktree
was retained because it belongs to another task.

The cleanup inventories are `work/release19/cleanup-inventory.json` and
`work/release19/github-cleanup.json`. Current release CI/deployment artifacts are
retained; **64** superseded GitHub Actions artifacts (**170 MB**) were removed.
No App Store release
or distributed TestFlight build was deleted or expired.

## Local artifact retention — October 2, 2026

After build 17 delivery, obsolete local build caches, exports, repeated result
bundles, test videos and generated site previews were removed at the owner's
request. The complete signed build 17 archive remains in Xcode Archives. Older
build 14–16 archives were replaced by their verified dSYMs and archive metadata
in ignored `work/release-symbols/`; historical archive paths below describe what
was retained at delivery and no longer imply the full older binaries exist.

Current simulator development output (`/tmp/road-notice-fix17`), the Swift test
cache (`/tmp/road-notice-core17`), and the final app-hosted and saved-entry UI
results (`/tmp/road-notice-after17-unit.xcresult` and
`/tmp/road-notice-after17-log-final.xcresult`) remain available. Test transcripts,
selected screenshots and the original TestFlight crash report are preserved.
Older raw result bundles and duplicate videos referenced in historical testing
records were pruned. The local inventory is `work/cleanup-2026-10-02/inventory.json`.
The generated project remains committed and can be reopened normally in Xcode.

Only `main` and the active `battery-road-zones` branch exist locally and on origin;
no stale branch needed deletion. Local `main` was fast-forwarded to `origin/main`.
This cleanup did not expire or change any distributed TestFlight build.

## Notification-crash follow-up — October 2, 2026

**1.0.6 (17)** is **Testing** in the existing **First Drive** internal group,
with its one tester. Apple accepted the upload with symbols at **13:41 MDT**;
processing, saved phone instructions, group assignment and the refreshed
`Build 17 Internal · Testing · First Drive · 1 invite` row are verified.
Apple build ID: `442b7b29-ab42-4a2b-b161-5e8b5e525182`.

The binary corrects build 16's off-main notification completion identified by
the owner's TestFlight crash report. Both log screens use the main app's styling,
and new entries display their saved, eligible speed-check limit. Old entries
remain readable. Coors data and warning thresholds are unchanged: the signed
archive includes both verified 45 mph limits, and full controller replays verify
below-limit suppression. The signed archive and dSYM are retained at
`~/Library/Developer/Xcode/Archives/2026-10-02/RoadNotice-1.0.6-17-private.xcarchive`.
The app source is `bb227d5`; `368f12d` only adjusts the test/acceptance record.
The internal-only export retains build 16's immutable private database URL and
cannot be used for App Store or external TestFlight distribution.

[Source CI](https://github.com/aindaco1/road-notice/actions/runs/37055355209) and
[runtime CI](https://github.com/aindaco1/road-notice/actions/runs/37055359022) pass,
including all iOS 17.5, 18.5 and 26.5 jobs.
Local 41 Swift, 74 pipeline and 16 app-hosted tests pass, as do signed-bundle checks.
The saved-entry UI test opens the styled details after a real route and app
relaunch. A separate iOS 27 check opens the matching entry from Notification
Center after termination without crashing, using swipe-right opening. Its test
body passes, but Xcode stalled finalizing that result bundle; the transcript and
rendered screen are preserved. Normal notification taps must still be confirmed
on the phone. The updated First Drive checklist is saved. See
[the acceptance record](TESTING.md) for the evidence and limitations.
No public database deployment, App Store submission or tester-access change was made.


## Private Coors verification and alert-log candidate — October 1, 2026

**1.0.6 (16)** is **Testing** in the existing First Drive internal group, from [PR #7](https://github.com/aindaco1/road-notice/pull/7),
app source `159a5e318c97a30ed5611e2b934fb16dbe8e91d3`. The owner reported successful
Albuquerque field use of build 14's approach zones and Quiet below speed limit.
The two Coors north of St. Joseph approaches now retain those same warning
locations with confirmed speed-camera classification and field-verified 45 mph
limits. The new [local alert log](ALERT-LOG.md) stores posted camera notifications
and routes notification taps to their saved entries.

Apple accepted the internal-only upload at **08:43 MDT (14:43 UTC) on October 1**.
Processing is complete and build-specific test instructions are saved. A refreshed
Helium App Store Connect view verifies **Build 16 Internal · Testing · First Drive · 1 invite**.
Tester access and roles are unchanged; physical installation remains unverified. Apple build ID:
`53261023-131d-45fc-88db-7d37cbccab6e`. This is not a public App Store submission or
public database deployment. Build 15 was uploaded before a clean-checkout packaging
fix; it remains unassigned. Build 16 excludes the pre-existing local `Info 2.plist`
iCloud duplicate from XcodeGen resources, preserving that file on disk.

The signed archive and dSYM are retained at
`~/Library/Developer/Xcode/Archives/2026-10-01/RoadNotice-1.0.6-16-private.xcarchive`.
Signature and release-bundle checks pass with iOS 17 minimum, 2,701 cameras and
54 road zones. The immutable private feed is
`https://raw.githubusercontent.com/aindaco1/road-notice/b751e4b7a832e08ef0700264520481b4241aab14/Data/Published/`.
Snapshot `2026-09-28-f7d23a339024-c8ba0cd7` has SHA-256
`923b6db9cf2feb5b00d2e2faefedee7fc3b484805a2d528e81ab70aec1a0e7e1`.
The dated field limits expire October 31 under the existing freshness policy.
Older public validators reject speed-camera polylines, so this snapshot stays on
the private channel until a compatible public app rollout is coordinated.

[Source CI](https://github.com/aindaco1/road-notice/actions/runs/36878134469) passes.
See [the test record](TESTING.md) for app-hosted and runtime results. Local archive,
upload and test-instruction evidence is retained in `work/release16/`.

## Private stationary-power and road-zone candidate — September 27, 2026

**1.0.6 (14)** is **Testing** in the existing First Drive internal TestFlight group.
Source is [PR #7](https://github.com/aindaco1/road-notice/pull/7), app commit
`17eac6ebf6c45f5ccae02b7d706e3f5cd24b9e67`. This is a private candidate, not an
App Store submission or a public database deployment. At preparation time,
App Store Connect lists the preceding 1.0.5 (13) as Ready for Distribution.

Apple accepted the upload at **18:32 MDT on September 27 (00:32 UTC September
28)**. Processing completed, the build-specific phone checklist was saved, and
First Drive was assigned with its existing one tester. A refreshed TestFlight
record verifies **Build 14 Internal · Testing · First Drive · 1 invite**.
No tester roles or access changed. Apple build ID:
`73a1a59c-ff56-4757-925d-893cc70b4a06`. Physical installation remains unverified.

The Xcode 27 signed archive passes signature and release bundle checks with the
existing iOS 17 minimum, 2,701 cameras, and 54 reviewed road zones. It contains no
test bundles. Its matching dSYM is retained in
`~/Library/Developer/Xcode/Archives/2026-09-27/RoadNotice-1.0.6-14-private.xcarchive`.
The bundled snapshot is `2026-09-21-dc315dfa720e-79004776`, SHA-256
`0b8937317ddb88f8b52446cc12164d33492ad63afce027757fd3a5a56f2cfebe`.

[Hosted source checks](https://github.com/aindaco1/road-notice/actions/runs/36361637837)
pass: 40 Swift core tests, 72 pipeline tests, the support-package check and app
build. [Final runtime CI](https://github.com/aindaco1/road-notice/actions/runs/36361637870)
passes all ten app-hosted tests on iOS 17.5, 18.5 and 26.5, the iOS 17.5/26.5
background approach replays, and iOS 18.5 foreground settings/audio. The ten
tests include the nine wake contracts and private database-channel isolation.
Earlier attempts and the simulator's physical limits are recorded in
[TESTING.md](TESTING.md). The exported IPA is 2,479,791 bytes; this is not Apple's
processed download size. The export enables `testFlightInternalTestingOnly`, which makes this
binary ineligible for external TestFlight or App Store distribution.

Physical installation, overnight locked departure, Low Power Mode, battery use,
and Coors/Alameda/I-40 road checks remain open. This private archive pins
`CAMERA_DATABASE_URL` to the immutable candidate directory at
`https://raw.githubusercontent.com/aindaco1/road-notice/231a1ad9cef6a3bb2cc08ab65de99a48b8dd3af6/Data/Published/`.
It uses the normal downloader and checksum validation, but a weekly public update
cannot remove the candidate zones during a field test. Normal builds leave this
setting empty and use the existing public feed. The bundle checker requires an
explicit `--database-url` for a custom channel, preventing an accidental candidate
channel in a standard release. Road zones still expire according to source age;
this test build does not freeze the clock or relax expiry validation.
Local archive, CI, upload and test-instruction evidence is in `work/release14/`.

## Earlier release records

**September 25, 2026:** **Road Notice 1.0.4 is available free on the
[U.S. App Store](https://apps.apple.com/us/app/road-notice/id6812094105)** for
iPhone running iOS 17 or later. Automatic release after approval published the
submitted 1.0.4 (12) build. Apple's public catalog records the release at
**00:57:48 CDT (05:57:48 UTC)**.
See [the findings and submitted response](APP-REVIEW.md). The dated records below
preserve the earlier rejection, validation and submission history.
The repository and project directory are renamed
`road-notice`; bundle identity, saved data and `finemenot.xyz` remain unchanged.

Earlier build records below are historical. The current release includes iOS 17
support and voluntary public problem reports; the original 1.0 Data Not Collected
answer was replaced by the disclosures in [REPORTING.md](REPORTING.md).

- App: Road Notice (formerly Fine Me Not)
- Bundle: `xyz.dustwave.fine-me-not`
- Owner/team: Volver Health LLC (`PWT3Q52LZ2`), explicitly selected by the project owner
- TestFlight: **1.0.5 (13)** processing complete and assigned to First Drive; physical installation is unverified
- Previous rejected App Store version: 1.0.0 (8)
- App Store: **1.0.4, available for download**; free U.S. distribution, released September 25, 2026
- Release history: https://github.com/aindaco1/road-notice/releases
- Minimum: iOS 17.0 since 1.0.2; earlier binaries require iOS 27.0
- Source: https://github.com/aindaco1/road-notice
- Support / privacy: https://finemenot.xyz/
- Category: Utilities (minimal camera proximity warnings)
- Price: Free; no purchases, subscriptions, ads or accounts

## Shared support maintenance — September 25, 2026

**1.0.5 (13) is Waiting for Review**, submitted at **09:12 CDT (14:12 UTC)**
with automatic release after approval. Version 1.0.4 remains the public release.
Apple processed build 13 as VALID, and its assignment to the existing First Drive
internal group was independently verified. Build-specific test instructions are
saved; tester access and roles are unchanged. Submission ID:
`fd7951c3-c767-4976-991b-0e2dc9eec1e6`.

[Source PR #4](https://github.com/aindaco1/road-notice/pull/4) adopts the shared
Apple support transport and MetricKit projection at source
`804f8818b7528260890d60d43b110a270e478266`. Report review and explicit sending,
the report schema, iOS 17 minimum, database updates and camera-warning behavior
remain unchanged. See [migration and rollback evidence](SHARED-SUPPORT.md).
The signed archive passed the release bundle check with 2,701 camera records;
its dSYMs and the preceding distributed build's symbols are retained.

App Store approval, public availability of 1.0.5, physical installation and
remaining audio/background acceptance are separate checks and are not claimed
by this submission record.

## Public App Store release — September 25, 2026

The public [product page](https://apps.apple.com/us/app/road-notice/id6812094105)
and [Apple catalog lookup](https://itunes.apple.com/lookup?id=6812094105&country=us)
confirm Road Notice, version 1.0.4, price Free, minimum iOS 17.0 and seller
Volver Health LLC. Both catalog release timestamps are `2026-09-25T05:57:48Z`.
This verifies public U.S. availability; installation from the App Store and the
remaining physical audio/background scenarios are separate acceptance checks.

The website download link and documentation can be updated through the existing
GitHub Pages deployment without a new app build, version or App Review submission.

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

The [official GitHub release](https://github.com/aindaco1/road-notice/releases/tag/v1.0.0) is published at source commit `093e2872036fe0253dd06de8a38b13af40c03314`. The website and weekly database are deployed. Apple received version 1.0.0 (8) at **02:10 MDT on September 15, 2026** and shows **Waiting for Review**. The app is free, initially available in the United States, with automatic release after Apple approval. Mac and Apple Vision Pro availability are disabled. The app remains under the owner-selected Volver Health LLC Apple team; the project maintainer is Alonso Indacochea.

Apple accepted **1.0.0 (8)** at **07:27:51 UTC on September 15, 2026**. Processing completed and the existing First Drive internal group with one tester shows **Testing**. Build-specific device-test instructions are saved. No tester roles changed. The physical phone was last shown on 0.1.0 (7); installation of 1.0 remains unverified.

Validation passed: **21 Swift tests, 63 Python tests**, codesign verification, full release bundle checks (version/build matched to `project.yml`, minimum iOS 27.0, 2,695 cameras), and a simulator compatibility build/install/launch. The signed archive uses Xcode 26.6 / SDK 26.5 without a distribution minimum override. Its bundled database is `2026-09-14-729f56d56437-796706f6`, SHA-256 `5da6f8ec0bfaef2646f26aa8a2bcb09d56f18b802672dd6fea6f2f294b761b8e`.

The completed App Store listing includes the actual 6.9-inch iPhone screenshot (automatically reused for the 6.5-inch slot), description, permission setup instructions, support and privacy links, age rating 4+, Utilities category, build 8 and private App Review contact. The owner confirmed the privacy attestation; **Data Not Collected** is published with `https://finemenot.xyz/#privacy`. Private contact details are stored only in App Store Connect.

Apple confirmed **1 Item Submitted**, followed by **Waiting for Review** for 1.0.0 (8), on September 15, 2026 at 02:10 MDT. Submission ID: `fb55d309-ed07-4e2c-844d-1bc3677a2d17`. Automatic release after approval is selected. Submission does not mean Apple has approved the app or that the public App Store listing is live.

[Release source CI](https://github.com/aindaco1/road-notice/actions/runs/34943986572) and [website/data deployment](https://github.com/aindaco1/road-notice/actions/runs/34943986798) both passed. The live HTTPS site and immutable database passed `Scripts/check_site.py` with 2,695 locations and 1,305 of 1,765 speed approaches eligible for suppression.

## Release evidence — September 14, 2026

Xcode confirmed **0.1.0 (2) uploaded successfully** to App Store Connect under Volver Health LLC at 22:56 UTC. Apple reported that the uploaded package was processing. Source/build commit: `7cabd13`; bundled snapshot: `2026-09-14-0f9b8c9a0cd0-43142730`, 1,756 warning records. Build 2 adds offline OpenStreetMap attribution. The previous build, 0.1.0 (1), also uploaded successfully.

[Build 2 CI](https://github.com/aindaco1/road-notice/actions/runs/34906072688) passed. At approximately 23:06 UTC, App Store Connect showed build **0.1.0 (2)** as **Testing** in the **First Drive** internal group, with the owner-requested tester assigned. The tester was already an eligible team member; no App Store Connect role was added. TestFlight then reported **Installed 0.1.0 (2)** on **iPhone 16 Pro Max / iOS 27.0**. The tester’s email is omitted from this public repository.

The build’s What to Test instructions were saved in TestFlight, covering permissions, audio routes, screen-locked and overnight behavior, direction/repeat filtering, offline operation and database downloads. The group uses manual build assignment; future uploads must be added after validation. This is an internal beta, not a public App Store release.

The archive and exported distribution signed successfully using Xcode’s saved team account. The final archive passed the complete bundle check with MinimumOSVersion 27.0, version 0.1.0, the siren, database, icon, privacy manifest and expected background modes. Processing, tester assignment and the reported device installation were subsequently verified in App Store Connect. Physical background reliability, audio audibility and battery acceptance remain pending; installation alone does not establish those behaviors.

## Icon update — build 3

Build 0.1.0 (3), source `9d975fd`, replaces the ticket with a speed camera and pale-blue prohibition overlay. The 1024 × 1024 opaque icon was checked on the simulator Home Screen, and the signed archive passed the bundle check. Apple confirmed the upload at 23:21 UTC on September 14, 2026. Apple finished processing and the First Drive group now shows build 0.1.0 (3) as Testing. The icon update notes were saved in TestFlight. [CI](https://github.com/aindaco1/road-notice/actions/runs/34908349722) passed. Installation of build 3 on the physical phone has not been checked.

## Missed-warning fixes — build 4

Build **0.1.0 (4)**, source `fd99484`, is **Testing** in the First Drive internal group. Apple accepted the upload at 00:29 UTC on September 15, 2026 (September 14 Mountain time), after a network timeout on the first export attempt. Processing completed, the build-specific test instructions were saved, and the existing group with one tester was assigned. No tester roles or access changed. Physical installation of build 4 has not been verified.

This build requests continuous standard background location with automatic pauses disabled, infers movement when reported speed is unavailable, chooses the newest valid saved/bundled database, and adds local diagnostics. It bundles `2026-09-14-971a10f8454e-571f726e` with 1,758 warning records, including approximate Coors/St. Joseph NB/SB warning areas. The city confirms the site and directions, but exact device positions remain unverified.

[CI for the app source](https://github.com/aindaco1/road-notice/actions/runs/34913290315) passed all 14 Swift and 10 publisher tests and the simulator bundle checks. The signed archive passed validation with minimum iOS 27.0. Both Coors directions produced one warning and recorded siren completion during locked-screen simulator replays. Real iOS 27 Low Power Mode, long idle recovery, car-audio audibility and battery use still require physical acceptance. See [DEBUGGING.md](DEBUGGING.md) for findings and the next phone test.

## Complete city-list representation — build 5

Build **0.1.0 (5)**, source `632c77b`, is **Testing** in the First Drive internal group. Apple accepted the upload at 01:09:47 UTC on September 15, 2026 (September 14 Mountain time). Processing completed, the build-specific What to Test notes were saved, and the existing group with one tester was assigned. No tester roles changed. Installation of build 5 on the physical phone remains unverified.

The build bundles `2026-09-14-6466b7b09db1-78026b1a` with **1,777 warning records**. The 19 additions bring current Albuquerque city-list representation to **40 of 40 directional approaches: 19 mapped points and 21 approximate areas**. Carlisle uses Delamar Avenue as confirmed by the city certificate. Approximate boundaries follow reviewed OSM road geometry; they are warning buffers, not surveyed equipment positions or enforcement boundaries. See [ALBUQUERQUE.md](ALBUQUERQUE.md) for every city entry. No location/audio runtime code changed for this build.

[Source CI](https://github.com/aindaco1/road-notice/actions/runs/34915680253) passed all 15 Swift and 12 publisher tests and the simulator bundle checks. The signed archive passed the full release bundle check with minimum iOS 27.0. [Database publication](https://github.com/aindaco1/road-notice/actions/runs/34915680188) succeeded; the live immutable snapshot matched its SHA-256 manifest and all 40 city references. An installed build 4 simulator downloaded it using Update now, then produced exactly one southbound Carlisle warning with playback completed while locked. These checks establish data delivery and simulated behavior. Real iOS 27 car-audio audibility, Low Power Mode, overnight recovery and battery acceptance remain pending.

## Speed check and automated maintenance — build 6

Build **0.1.0 (6)**, source `af60017`, is **Testing** in the First Drive internal group with the existing one tester. Apple accepted the upload at **03:56:29 UTC on September 15, 2026** (September 14 Mountain time). Processing completed, build-specific What to Test notes were saved, and group availability was verified at approximately 04:04 UTC. No tester roles changed. Physical installation and driving acceptance of build 6 remain unverified.

The build adds the default-on Quiet below speed limit setting and diagnostics. It bundles `2026-09-14-263679a7aa6b-9935f9b5` with **2,681 records** and 31 approved SFMTA speed limits. Unknown, stale or conditional limits continue to warn, including Albuquerque where approved camera limits are not yet available. Red-light and combined warnings remain on. A quiet encounter remains armed in case speed subsequently rises.

The signed archive passed codesign verification and the release bundle check (minimum iOS 27.0). [Source CI](https://github.com/aindaco1/road-notice/actions/runs/34926802914) passed 20 Swift tests, 39 pipeline tests and the simulator compatibility build. Simulator UI checks verified the upgrade default on, persisted off after relaunch, the Test warning button, and the bundled count. The archive uses Xcode 26.6 / SDK 26.5 with the requested distribution minimum 27.0; simulator deployment overrides are never used for the distribution archive.

The [GitHub source-check run](https://github.com/aindaco1/road-notice/actions/runs/34926817137) and subsequent [staged publication](https://github.com/aindaco1/road-notice/actions/runs/34927188598) both completed successfully. The latter publishes **2,695 records** in `2026-09-14-352059fee0b5-23bbacd6`, adding 14 Chicago approaches once refreshed source road metadata made their distinct identities clear. Its live SHA-256 matches the manifest. Four watched pages returned HTTP 403, and an OSM alias query returned HTTP 429; previous evidence was retained and failures remain recorded. A green workflow means the resilient pipeline completed, not that every source responded successfully. The Codex maintenance heartbeat was deleted; recurring work now runs entirely in GitHub Actions.

The installed build 6 simulator fetched that newer snapshot using Update now and visibly displayed **2,695 warning locations**, with Quiet below speed limit still enabled. This verifies the download/validation/display path independently of the offline bundle. It does not establish physical background delivery timing or car-audio behavior.

## Custom domain and source research — build 7

Build **0.1.0 (7)**, app source `61938f2`, is **Testing** in the First Drive internal group with the existing one tester. Apple accepted the upload at **04:31:51 UTC on September 15, 2026** (September 14 Mountain time). Processing completed, the build-specific notes were saved, and group availability was verified at approximately 04:43 UTC. No tester roles changed. The physical phone was last reported on build 6; installation and field acceptance of build 7 have not been verified.

This build centralizes website/database URLs in `AppLinks` and moves them directly to `https://finemenot.xyz/`. It bundles **2,695 warning records** in `2026-09-14-352059fee0b5-23bbacd6`, with the existing 31 approved SFMTA limits. No new research speed-limit candidates were approved for suppression. The owner requested no compatibility work for older test builds.

The signed archive passed codesign verification and the release bundle check with minimum iOS 27.0. The simulator compatibility build installed and launched with 2,695 records and the default-on speed check. [App source CI](https://github.com/aindaco1/road-notice/actions/runs/34928273608) passed, as did the [research/source-monitor CI](https://github.com/aindaco1/road-notice/actions/runs/34929151098) and [site publication](https://github.com/aindaco1/road-notice/actions/runs/34929151034). Local pipeline verification passed 39 tests. The archive still uses Xcode 26.6 / SDK 26.5; simulator deployment overrides were not used for distribution.

**Domain activation was resolved at approximately 23:20 Mountain on September 14.** Once public DNS propagated, GitHub's stalled certificate request was restarted. The certificate now covers `finemenot.xyz` and `www.finemenot.xyz`; Pages HTTPS enforcement is on. Both DNS records are now proxied through Cloudflare, matching the other Dust Wave Pages sites, with Full (strict) origin encryption and Always Use HTTPS. The public page and all 2,695 camera records validate over HTTPS through Cloudflare. The privacy text names both hosting providers. No new app binary is required.

The [manual, read-only HTTPS verification run](https://github.com/aindaco1/road-notice/actions/runs/34929772047) passed; `Scripts/check_site.py` also passed after Cloudflare proxying was enabled. No recurring schedule was added. Update now and the website link in build 7 still need physical iPhone acceptance. The [website runbook](WEBSITE.md) records the routing contract and certificate recovery procedure.

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
[hosted checks](https://github.com/aindaco1/road-notice/actions/runs/34972228732).
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

[Runtime regression evidence](https://github.com/aindaco1/road-notice/actions/runs/34972228844) includes the exact scenario and retained journal for each OS.

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

[Hosted build/tests](https://github.com/aindaco1/road-notice/actions/runs/35152261077)
and [runtime compatibility](https://github.com/aindaco1/road-notice/actions/runs/35152261051)
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
removed after [PR #3](https://github.com/aindaco1/road-notice/pull/3) merged. Only
`main` remains; source, camera data, signing assets and simulator runtimes were
preserved.


## Road Notice 1.0.4 (12) — September 22, 2026

This revision replaces the prior name, prohibition icon and ticket-saving slogan
with Road Notice, a neutral road-and-marker icon and camera-awareness guidance.
It keeps the bundle identity, iOS 17 minimum, saved settings and report contract.
The source includes the September 21 published database with 2,701 records.
Jev remains a developer-only integration plan, with no runtime dependency.

The release and simulator builds pass resource checks; all 26 Swift tests and
63 Python pipeline tests pass. Xcode 27.0 (27A266a) archived the signed release.
The app and dSYM share UUID `F4FB5903-B7BB-330F-A26C-EEC108006C6A`.
The current archive is `~/Library/Developer/Xcode/Archives/2026-09-22/RoadNotice-1.0.4-12.xcarchive`.
Release logs and ready-to-paste listing fields are in `work/release12/`.

Apple accepted the upload at **21:43:07 CDT on September 22, 2026** and reported
that processing had begun. Xcode export/upload succeeded with symbols enabled.
App Store Connect subsequently confirmed processing complete, and build 12 was
assigned to the existing First Drive internal group. No tester access changed.


The [website deployment](https://github.com/aindaco1/road-notice/actions/runs/35811525222)
succeeded for release source `c559c8e`. The public `finemenot.xyz` icon, HTTPS
page and 2,701-record immutable database passed `Scripts/check_site.py`, including
manifest SHA-256 and speed-limit coverage consistency. The site keeps its existing
domain so older installed builds continue to receive database updates.

The owner-requested cleanup moved 14 obsolete paths (469 MiB) to a dated folder
in macOS Trash. This includes old development builds/caches, stale exports and
review folders, iCloud conflict copies, and the 1.0.0–1.0.3 full archives. Their
four dSYM sets and archive metadata were copied and byte-verified under
`~/Library/Developer/Xcode/RoadNoticeSymbols/` before the old archives were moved.
The current signed 1.0.4 archive, current simulator development build, Swift test
cache and `work/release12/` evidence remain. `main` is the only branch locally and
remotely; no branch deletion was needed. Published release history, signing
credentials and simulator runtimes were preserved.

The App Store update was completed through Helium. Apple accepted the Road Notice
name and subtitle. The saved 1.0.4 version selects build 12, revised promotional
text/description/keywords/review notes, and `1.0.4-settings.png`; the obsolete
screenshot was removed, with 6.5-inch reuse of the 6.9-inch screenshot retained.
Utilities, the $0.00 U.S.-only storefront, existing privacy disclosures and
automatic release after approval were verified and preserved.

The response to the rejection was posted at **23:26 CDT**. Resubmission succeeded
at **23:27 CDT on September 22, 2026**, with both the submission and version shown
as **Waiting for Review**. Submission ID:
`fb55d309-ed07-4e2c-844d-1bc3677a2d17`; build ID:
`90ac966f-dcf8-499d-8e04-4067f9fadcd2`. The confirmation screenshot and submitted
copy are retained locally in `work/release12/app-store/`. This confirms receipt
for review, not approval or public App Store release.


[Hosted source build and tests](https://github.com/aindaco1/road-notice/actions/runs/35811525214)
passed. [Runtime compatibility](https://github.com/aindaco1/road-notice/actions/runs/35811525239)
passed on iOS 17.5, 18.5 and 26.5. The 17.5 and 26.5 scenarios each verify one
completed background camera warning; 18.5 verifies saved Quiet settings and the
foreground Test warning because of the documented hosted moving-GPS limitation.
These simulator results do not replace physical-device audibility acceptance.
No further release build was created after the accepted upload.
