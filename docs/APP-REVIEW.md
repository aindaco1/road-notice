# App Review: September 22, 2026

Status: Road Notice 1.0.4 (12) was uploaded on September 22, 2026. The listing,
review reply and final resubmission still need to be applied in App Store Connect.
See [release status](RELEASE.md). Jev is a separate [plan](JEV-PLAN.md).

## What Apple rejected

The owner's one-page App Store Connect capture shows **iOS App 1.0.0, build 8**,
status **Rejected**, reason **5.0.0 Legal: Preamble**. Apple's message says:

> The app encourages a fraudulent or reckless activity. Specifically, your app facilitate evade radar-detection.

Its next step says apps encouraging fraudulent or reckless activity are not
allowed. The PDF does not identify a crash, permission bug, background-mode
violation, particular jurisdiction or particular screen. It does not classify
this as a metadata-only rejection. The later 1.0.3 (11) TestFlight build is not
the rejected build. This assessment uses the supplied capture, not a fresh
authenticated inspection of App Store Connect.

Source: `screencapture-appstoreconnect-apple-apps-6812094105-distribution-reviewsubmissions-details-fb55d309-ed07-4e2c-844d-1bc3677a2d17-2026-09-22-17_21_16.pdf`
on the owner's Desktop. It is an image-only PDF, inspected visually; the original
has not been changed or copied into the repository.

## Why Radarbot is relevant, and what it cannot establish

Apple's current U.S. [Radarbot listing](https://apps.apple.com/us/app/radarbot-speed-camera-gps-app/id1099797635)
advertises speed/red-light camera alerts, offline camera information, background
warnings and avoiding fines. That is a real comparison, including some of the
same marketing tension. It supports asking Apple to distinguish database camera
awareness from prohibited encouragement of reckless driving.

We cannot inspect Radarbot's review history or infer a special exemption,
grandfathering, or why this reviewer reached a different conclusion. Another
listing is useful context, not a guarantee or the main argument for approval.

[Guideline 5](https://developer.apple.com/app-store/review/guidelines/#legal)
requires compliance with local law and prohibits promoting criminal or clearly
reckless conduct. Guideline 1.4.4 separately addresses reckless driving and DUI
checkpoint information; this app has no DUI checkpoint feature. The cited rules
do not state a blanket ban on all camera-location alerts. That is our reading of
the published text, not a legal determination or an assurance of approval.

## Diagnosis and the smallest useful revision

The submitted name, crossed-out camera icon, and prominent “Keep your cash” slogan
can collectively read as enforcement avoidance. That is a plausible contributor,
not a reason Apple specifically identified. A disclaimer buried below that
message is a weak response to a concern about the app's purpose.

The implementation is a GPS/database proximity utility. `MonitoringController`
passes fixes to `AlertEngine`; `AlertPresenter` delivers the brief siren and
notification. It neither senses radar nor interferes with enforcement equipment.
It has no live police-reporting feature, evasion routes, enforcement-tolerance
calculator or instruction to accelerate after passing a camera. Those facts help
clarify its functionality, but camera alerts themselves remain visible to review.

Implemented locally:

- Apply the owner-approved Road Notice name and neutral road-and-marker icon.
- Replace the cash-saving slogan in Settings, the website and README with
  “Camera awareness. Follow posted limits.”
- Put parked setup and compliance guidance at the top of Settings and the website.
  Explain next to the Quiet setting that silence does not establish lawful speed.
- Clarify the website's use of a saved camera list and its inability to sense
  radar or establish current camera operation. Qualify background delivery.
- Prepare the listing and review notes below, including current iOS 17 support
  and explicit voluntary public reporting disclosures.

This is a presentation revision. Camera matching, alert thresholds, data,
default-on Quiet setting, audio, permissions and reporting behavior are unchanged.
There is no evidence in the rejection that adding maps, removing the Quiet
setting, removing mobile-site data, or adding a new speedometer would resolve it.
Keep approximate/mobile sites explicitly described; do not disguise the product
as a general navigation or continuous speed-limit app.

## Selected name and icon

The owner approved **Road Notice** and the repository/directory name
`road-notice`. The display name, permissions wording, app header, website and
listing draft now use Road Notice. The shared icon shows a white road and a
pale-blue roadside marker, without a prohibition symbol or radar imagery.
The existing bundle ID, saved-data paths, reporting contract, domain and App
Store Connect record stay unchanged so this remains the same app for updates.

RoadCue was the initial choice, but a public check found an existing
[camera-alert product using that name](https://www.roadcue.ca/) and the owner
accepted the alternative. This is a practical naming decision, not trademark
clearance. App Store Connect name availability still needs to be confirmed when
saving the listing; do not claim it has already been reserved.

Subtitle: **Speed & red-light alerts**. The limited camera scope remains explicit;
no navigation, certified-safety or hardware-detection capability is implied.

## Suggested path to resubmission

1. Reply to the existing rejection with the factual clarification below. Ask
   which feature or presentation creates the concern and whether the proposed
   revision addresses it. Avoid making Radarbot the sole argument.
2. Use the approved Road Notice name and neutral icon consistently in the
   actual app, public website, metadata and screenshots. A new name alone cannot
   cure a substantive concern about the camera-alert function.
3. Build the final chosen revision using the existing release process, increment
   its build number, and keep the App Store version field consistent with the
   uploaded archive. The new candidate is 1.0.4 (12); select that build and set the editable
   App Store version to 1.0.4. Build 11 must not be uploaded again.
4. Validate the archive and reproduce setup, default Quiet behavior, stationary
   Test warning and one controlled approach on the exact candidate. Use existing
   core, pipeline and runtime checks. Record physical audio/background evidence
   separately; outstanding field scenarios remain in [TESTING.md](TESTING.md).
   Earlier release authorization deferred some field checks; this revision does
   not silently convert them into passes or impose a new blanket release hold.
5. Replace the old screenshot and listing, deploy the matching site, select the
   new binary in the rejected submission, and include concise review notes.
   A short evidence clip may show parked setup and Test warning; clearly label
   simulator replay separately from physical driving. It cannot prove universal
   reliability. Keep the existing U.S. distribution scope and recheck the saved
   release setting, privacy answers and selected build before submitting.
6. If Apple maintains the same broad objection after clarification, request a
   review call or submit one focused appeal describing compliance with the cited
   rule and the concrete behavior. Include screenshots and their response.
   Do not repeatedly resubmit an unchanged build without addressing the concern.

Apple documents [replies and supporting attachments](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/reply-to-app-review-messages)
and [review support and appeals](https://developer.apple.com/app-store/review/).
Metadata-only rejections can sometimes use the same binary; this revision changes
in-app text, so it needs a new uploaded build. No reply, publication, upload or
resubmission has been performed as part of this work.

## Draft reply to Apple: usable before uploading the revision

Hello App Review,

Thank you for the feedback under Guideline 5. We would like to clarify the
camera-warning functionality and address the concern about encouraging reckless
driving.

The app, previously named Fine Me Not, compares the iPhone's location with a saved list of published speed
and red-light camera locations. It does not detect radar signals, interfere with
enforcement equipment, provide evasion routes, or tell drivers that it is safe
to speed. Some listed locations are approximate or mobile deployment areas;
these are labeled “Possible speed camera” rather than presented as confirmed
live equipment.

We recognize that the “Keep your cash” wording could convey the wrong purpose.
We have prepared a local revision removing that wording and making guidance to
follow traffic laws and posted limits prominent. It also states that silence
does not mean the driver's speed is lawful. The revision is named Road Notice,
with a neutral road-and-marker icon. These changes have not yet been uploaded
for review.

Could you clarify whether the concern is the current presentation or the
underlying use of published camera locations, and identify any specific feature
that must change? We would appreciate guidance on whether the described revision
addresses your concern before submitting the updated binary and screenshots.

Thank you.

## Proposed listing: apply only with the matching final binary

The text below uses the owner-approved **Road Notice** branding. Save it with
the matching binary and new screenshots after confirming name availability.

- Name: Road Notice
- Subtitle: Speed & red-light alerts
- Category: Utilities (existing selection; no category change needed to answer this rejection)
- Availability: United States (existing scope)
- Keywords: speed,camera,red light,driving,traffic,alert,road,awareness,Albuquerque
- Support: https://finemenot.xyz/#support
- Marketing: https://finemenot.xyz/
- Privacy: https://finemenot.xyz/#privacy
- Price: Free; no in-app purchases

### Promotional text

Speed and red-light camera awareness for iPhone. One brief audible reminder, an
offline camera list, and no ads. Follow posted limits wherever you drive.

### Description

Camera awareness. Follow posted limits.

Road Notice gives a brief audible reminder as you approach a listed speed or
red-light camera. Set it up while parked, put your phone away, and keep your
attention on driving. Follow traffic laws and road conditions everywhere,
whether or not a warning sounds.

ONE-TIME SETUP
Enable Camera warnings and allow Always and Precise Location. Monitoring can
continue with the screen locked or another app open when iOS permits. Use Test
warning while parked to check your selected audio connection and media volume.
Reopen the app after force-quitting or restarting your iPhone.

ONE BRIEF SOUND
Warnings use your iPhone's selected speaker or car audio connection. The siren
plays as media; your media volume and car input matter. Audio interruptions can
prevent a warning. There is no CarPlay dashboard interface.

QUIET WHEN THE DATA SUPPORTS IT
Quiet below speed limit is on by default for speed cameras. It can suppress a
siren when measured speed is reliably below an applicable limit or conservative
estimate. Unknown speed or limit information still produces a warning. Red-light
and combined-camera warnings remain on. Silence does not mean your speed is lawful;
posted signs and current conditions always take priority.

PUBLIC CAMERA INFORMATION
The saved U.S. camera list combines OpenStreetMap and agency information with
reviewed locations. Coverage is incomplete. Approximate locations and published
mobile deployment areas are labeled Possible speed camera. The app cannot sense
radar or confirm whether equipment is operating. Weekly source updates are
downloaded when your phone can connect; the saved list works offline with GPS.

LOCATION STAYS ON YOUR PHONE
Camera matching happens on your iPhone, without uploading your location or
keeping a trip history. There are no ads, analytics SDKs, subscriptions or accounts.
Optional problem reports let you review an explanation and location-free technical
details before explicitly sending them to a public GitHub issue. Submitted report
text is public. The privacy policy explains reports and hosting connection logs.

Free and open source. Requires iOS 17 or later. Maintained by Alonso Indacochea.

Warnings and speed-limit information may be missing, delayed or incorrect. GPS,
permissions, iOS background limits, battery state and audio conditions affect
delivery. Background location uses battery. Avoid abrupt reactions to a siren;
keep your attention on driving and follow traffic laws on every road.

### Notes for Review

No account or payment is required. This is a GPS/database camera-awareness utility.
The submitted revision replaces ticket-saving language with camera-awareness
wording and prominent guidance to obey traffic laws regardless of warnings.
Quiet below speed limit explains that silence does not establish lawful speed.
The app is now named Road Notice and uses a neutral road-and-marker icon.

The app does not detect or interfere with radar, provide evasion routes, or offer
live police or DUI checkpoint reports. It includes listed fixed cameras and
published mobile/approximate areas labeled Possible speed camera; those areas
do not establish live equipment presence.

To review while stationary: enable Camera warnings, approve location and
notification requests, and select Always and Precise in location settings if
needed. Turn up media volume and tap Test warning for the original 1.8-second
siren. Test warning exercises audio only; a real proximity alert requires movement
near a listed camera. The bundled database works offline; Update now fetches the
public HTTPS database. No location is uploaded.

Background location supports the user-enabled proximity feature. Audio runs
briefly for alerts, with no silent-audio keepalive or critical-alert entitlement.
Bluetooth/CarPlay support means the system-selected audio route, not a CarPlay UI.
The default Quiet setting applies only to eligible speed-camera warnings;
unknown data and red-light/combined cameras continue warning.

Report a problem is optional and requires reviewing the exact report before
explicitly sending it to a public issue. Privacy disclosures should remain the
published Customer Support, Crash Data and Other Diagnostic Data categories,
subject to checking the final binary. This revision does not add data collection.

## Verification of this local revision

Results are recorded after the local checks in [TESTING.md](TESTING.md).
Stale iCloud conflict copies have been isolated for the owner-requested cleanup.
The deployment candidate is 1.0.4 (12). App identity and the camera matching
behavior remain unchanged. Repository/reporting rename verification is recorded
in [REPORTING.md](REPORTING.md).
