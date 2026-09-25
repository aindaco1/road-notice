# App Store listing — 1.0

**Current release:** Road Notice 1.0.4 is available free on the
[U.S. App Store](https://apps.apple.com/us/app/road-notice/id6812094105) as of
September 25, 2026. See the [approved listing](APP-REVIEW.md#submitted-listing--version-104-12)
and [release record](RELEASE.md). The copy below is retained as submission history.

**Historical submitted copy.** Apple rejected 1.0.0 (8) on September 22, 2026
under Guideline 5 (Legal), as shown in the owner's rejection PDF. The listing
below preserves the original submission; it is not the next submission's copy.
Use [the approved resubmission and response](APP-REVIEW.md) for the current listing.

**1.0.1 reporting update:** source version 1.0.1 (9). Voluntary public reports change the privacy disclosure; the 1.0 Data Not Collected answer below is historical. See [REPORTING.md](REPORTING.md). Distribution verification is recorded separately from the existing 1.0 submission.

Submitted September 15, 2026 at 02:10 MDT: **1.0.0 (8), Waiting for Review**. Free U.S. distribution and automatic release after approval are saved. The original Data Not Collected answer was later replaced for the 1.0.1 reporting feature; private review contact details remain only in App Store Connect. See [the release record](RELEASE.md).

## Listing fields

- Name: Fine Me Not
- Subtitle: Free speed camera warnings
- Version: 1.0.0
- Category: Utilities
- Price: Free
- Initial availability: United States (the camera database covers the United States)
- Support URL: https://finemenot.xyz/#support
- Marketing URL: https://finemenot.xyz/
- Privacy policy URL: https://finemenot.xyz/#privacy
- Copyright: 2026 Alonso Indacochea
- Keywords: speed,camera,red light,warning,driving,traffic,alert,Albuquerque,free
- Sign-in required: No
- Release: Automatically after Apple approval

## Promotional text

Speed cameras ahead. Keep your cash. Free camera warnings for iPhone, with a brief siren, weekly camera-list updates, and no ads or subscriptions.

## Description

Speed cameras ahead. Keep your cash.

Fine Me Not gives you a heads-up when you're approaching a listed speed or red-light camera. One brief siren. A few settings. That's the app.

It's free and open source. No ads, subscriptions, accounts or maps to fuss with. Maintained by Alonso Indacochea.

TURN IT ON ONCE
Enable Camera warnings, allow Always and Precise Location, and let Fine Me Not monitor while you drive. It uses background location so it can warn you with the screen locked or another app open, when iOS permits. You don't have to start a session for every drive.

HEAR THE WARNING
The siren uses your iPhone speaker or selected car audio connection, including Bluetooth and CarPlay audio. It plays as media, so Silent mode doesn't mute active playback. Your media volume and car input still matter. Use Test warning while parked. There is no CarPlay dashboard app.

FEWER UNNECESSARY SIRENS
Quiet below speed limit is on by default. For speed cameras, it can hold the siren when your measured speed is safely below a reliable applicable limit. If your speed or the limit is unknown, it still warns. Red-light warnings stay on. Posted signs always take priority.

A CAMERA LIST THAT KEEPS IMPROVING
The database combines public U.S. camera information with reviewed Albuquerque metro locations. Some locations are approximate and labeled as possible cameras. Weekly updates bring in source changes and speed-limit information; your phone downloads them when it can. You can also tap Update now. The saved list works offline when GPS is available.

YOUR LOCATION STAYS ON YOUR PHONE
Location and speed are processed on your iPhone. Fine Me Not doesn't upload your route or keep a trip history. There's no advertising or analytics SDK. The privacy policy explains website and download hosting logs.

SET IT UP BEFORE YOU DRIVE
Requires iOS 27 or later. Allow Always and Precise Location, allow notifications, turn up media volume, and test your usual audio connection while parked. Setup instructions are at finemenot.xyz.

Camera information can be incomplete, outdated or approximate. GPS, permissions, iOS background limits, battery state and audio interruptions can prevent a warning. Continuous background location uses battery. Reopen the app after force-quitting or restarting your phone. Fine Me Not doesn't guarantee a warning, a correct speed limit or that you'll avoid a ticket. Follow posted signs, traffic laws and road conditions, and keep your attention on driving.

## Review notes

No account, payment, subscription or sign-in is required. The app is a camera proximity warning utility, not a navigation or radar-detection app. It needs Always and Precise Location for background approaches. All camera matching and speed checks run on the phone; coordinates and routes are not uploaded.

Enable Camera warnings and grant the requested location and notification permissions. If the initial location prompt only offers While Using, choose it, then use Open location settings to select Always and Precise. Use Test warning while stationary to hear the original 1.8-second siren. Turn up media volume first.

Background location is the core feature. Audio is only activated briefly for warnings; there is no silent-audio keepalive. The app does not request the critical-alert entitlement. CarPlay support means routing audio through the system-selected car connection, not a CarPlay interface.

The bundled database works offline. Update now downloads a public HTTPS manifest and camera database from finemenot.xyz. Approximate locations are marked Possible speed camera. Quiet below speed limit is on by default for speed-only cameras; unknown speed/limit data and red-light/combined cameras continue to warn.

## Privacy answers and supporting evidence

The app has no advertising, tracking, analytics or account SDK and does not transmit location, speed, camera encounters or diagnostic reports automatically. Camera matching is local. The on-device latest audio record and user preferences are not collected by the developer. Copy diagnostics only places a report on the clipboard; the user decides whether to share it. The public hosting providers may process ordinary connection logs, as explained in the privacy policy. Confirm the final App Store questions against these behaviors and the shipped privacy manifest.

## Distribution notes

The Apple developer team remains Volver Health LLC, as the owner explicitly selected. Project maintenance and copyright credit are Alonso Indacochea. Private App Review contact details are entered in App Store Connect and must not be committed here. Screenshots must show the actual release UI, with no fabricated device-test claims.

## Published privacy update for 1.0.1

On September 15, 2026, Customer Support, Crash Data and Other Diagnostic Data
were published for App Functionality, linked to identity and not used for tracking.
This replaces the historical 1.0 Data Not Collected label above. The categories
match the 1.0.1 privacy manifest. Support text may identify someone; automatic
fields exclude location, camera IDs/names, speeds and accessory names. All uploads
require reviewing a report and explicitly tapping Send report.

Suggested 1.0.1 What's New:

> Found something weird? You can now report a problem right from Settings. Add
> an optional explanation, choose whether to include technical details, review
> everything and send it to the public GitHub issue tracker. No GitHub account
> needed. Failed sends keep a draft so you can retry. The website has clearer
> setup, troubleshooting and privacy information too.

## Prepared compatibility update — 1.0.2 (10)

Minimum iOS 17.0. This compatibility update was initially distributed through TestFlight. The approved 1.0.4 listing now says “Requires iOS 17 or later” and retains the reporting privacy categories published for 1.0.1. The original 1.0.0 listing above is historical.

Suggested What's New:

> Older iPhone? You're in. Fine Me Not now supports iOS 17 and later, including iOS 18 and 26. Same simple setup, background camera warnings and optional problem reports.
