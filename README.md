# Road Notice

Formerly Fine Me Not. The app keeps its existing bundle identity and saved settings.

**Camera awareness. Follow posted limits.**

Free, open-source camera warnings for iPhone. One switch, one brief siren. No maps, ads, subscriptions, accounts or trip history.

Road Notice 1.0.4 targets **iOS 17+**, including iOS 18, 26 and 27. It automatically monitors after one-time opt-in, including permitted background operation. It never promises uninterrupted execution in every iPhone state. The owner has confirmed an audible real-camera warning over Bluetooth with the screen locked; other device checks remain documented in [the acceptance record](docs/TESTING.md). See [release status](docs/RELEASE.md) for Apple availability.

Available free on the **[U.S. App Store](https://apps.apple.com/us/app/road-notice/id6812094105)**. Maintained by **Alonso Indacochea**. [Website and setup instructions](https://finemenot.xyz/) · [Release notes](CHANGELOG.md).

- [Supported iOS versions and iPhones](docs/SUPPORT.md)
- [Data coverage and reconciliation](docs/DATA.md)
- [Census metro coverage and weekly source checks](docs/METRO-COVERAGE.md)
- [Speed-check behavior and coverage](docs/SPEED-CHECK.md)
- [Build and TestFlight release](docs/RELEASE.md)
- [App Review findings and approved resubmission](docs/APP-REVIEW.md)
- [Jev integration plan](docs/JEV-PLAN.md)
- [Tests and physical acceptance](docs/TESTING.md)
- [Research and implementation plan](docs/PLAN.md)
- [Sources, privacy and support](https://finemenot.xyz/)

## Run

Open `FineMeNot.xcodeproj` in Xcode, select your signing team and an iPhone running iOS 17 or later. `project.yml` is maintained with XcodeGen; the generated project is committed. The shared core is a local Swift package with no third-party app dependencies.

```sh
swift test
python3 -m unittest discover -s Tests/Pipeline -v
python3 Scripts/publish_cameras.py
```

Build checks use the same iOS 17.0 minimum as distribution. The iOS runtime compatibility Action builds one simulator app and tests that binary on iOS 17.5, 18.5 and 26.5 after relevant app changes and on pull requests; manual runs are also available. iOS 17 and 26 replay a camera approach and require exactly one completed background siren. iOS 18 checks launch, the saved Quiet setting and foreground Test warning playback: hosted moving-GPS delivery also fails in a separate control app, while the complete local iOS 18 background replay passes. The hosted iOS 18 background replay remains available as a manual diagnostic. Every check saves its journal, result and Xcode evidence. These checks do not replace permission-prompt or physical car-audio tests. See [supported versions](docs/SUPPORT.md) and [the acceptance record](docs/TESTING.md).

## Background and audio

Continuous standard location updates support automotive background monitoring. iOS 17 uses the two-step location-permission request; iOS 18 and later use a retained Core Location service session. Significant-change monitoring supports permitted relaunch/recovery. Every fix uses one on-device alert engine. Alerts are one original 1.8-second siren, using the system-selected audio route and media volume, with brief audio ducking. No silent-audio keepalive, location uploads, or claimed critical-alert entitlement.

## Weekly database

Upstream source checks run Sunday at 9 p.m. Denver time, with automatic reconciliation and durable review reports in GitHub Actions. The publisher is scheduled for Monday at 12:00 a.m. `America/Denver` (Sunday night), including daylight saving. GitHub and iOS can delay execution/download. Invalid data retains the last good snapshot. The live database combines national OSM data, reviewed Albuquerque metro locations and agency feeds. The installed app downloads updates through Update now and caches them for offline use. Each release also bundles its release-time snapshot. Coverage is incomplete; all published camera records include provenance.

## License

Code, original icon and siren: [MIT](LICENSE). Camera database: [ODbL 1.0](Data/LICENSE.md), © OpenStreetMap contributors, with source-linked municipal facts.

The **Quiet below speed limit** setting is on by default. It only suppresses speed-camera warnings when both the measured speed and applicable limit are reliable; unknown limits and red-light cameras still warn. See [speed check](docs/SPEED-CHECK.md), [geocoding and identity](docs/GEOCODING-AND-IDENTITY.md), and [source maintenance](docs/MAINTENANCE.md).

## Problem reports

Version 1.0.1 adds **Report a problem** in Settings: optional explanation, reviewed
location-free technical details, optional Apple crash evidence, and explicit
submission to public GitHub issues. Nothing uploads automatically. See
[reporting and operations](docs/REPORTING.md).
