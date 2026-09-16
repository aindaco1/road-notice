# Release notes

## 1.0.3 — September 16, 2026

The app now matches [finemenot.xyz](https://finemenot.xyz/): the speed-camera icon
sits beside the bold, two-line Fine Me Not wordmark. The header adapts to larger
text sizes. Camera warnings, settings and the siren work as before.

## 1.0.2 — September 15, 2026

Older iPhone? You're in. Fine Me Not now supports **iOS 17 and later**, including iOS 18 and 26.

- Added the iOS 17 location-permission flow while keeping the same camera warnings, settings and siren.
- Added automatic compatibility checks on iOS 17.5, 18.5 and 26.5 for app changes and pull requests. These cover background camera warnings on 17/26, and launch, saved settings and Test warning on 18. The test record explains the hosted iOS 18 GPS limitation.
- Updated the website's supported iPhones and setup information.

See [release availability](docs/RELEASE.md) and [test results](docs/TESTING.md). Simulator checks do not replace testing the sound on your phone and car connection.

## 1.0.1 — September 15, 2026

Found something weird? Use **Report a problem** to describe it, add optional diagnostics, review exactly what will be shared, and send it. Reports are public; sending is always your choice. Failed sends keep a draft for retry.

The website now has shorter setup and troubleshooting instructions and explains voluntary reports in the privacy policy.

## 1.0.0 — September 15, 2026

Speed cameras ahead. Keep your cash.

Fine Me Not's first 1.0 release brings free, open-source camera warnings to iPhone, with a settings screen and one brief siren. No maps, ads, subscriptions or accounts.

- Automatic camera monitoring after you enable warnings and grant Always and Precise Location.
- Speed-camera and red-light-camera warnings, including clearly labeled possible-camera areas.
- One brief siren per approach, using your selected audio connection and media volume.
- Quiet below speed limit, enabled by default for speed cameras when the phone's speed and the applicable limit are reliable. Unknown limits and red-light cameras still warn.
- An offline database with 2,695 warning locations and expanded speed-limit evidence, including reviewed Albuquerque metro coverage.
- Weekly source checks and publication through GitHub Actions, plus Update now on your phone.
- Setup, sources, privacy and support at [finemenot.xyz](https://finemenot.xyz/).

Requires iOS 27 or later. Maintained by Alonso Indacochea.

Camera coverage is incomplete, and warnings are not guaranteed. Always follow posted signs. The owner has confirmed a real Bluetooth warning with the screen locked. Low Power Mode, speaker/Silent mode, CarPlay and battery checks remain pending and will continue with 1.0. Apple availability is tracked separately in [the release record](docs/RELEASE.md).
