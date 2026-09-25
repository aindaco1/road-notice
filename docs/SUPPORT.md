# Supported iOS versions and iPhones

Road Notice **1.0.4 requires iOS 17.0 or later** and is available free on the [U.S. App Store](https://apps.apple.com/us/app/road-notice/id6812094105). The supported release families are iOS 17, 18, 26 and 27. There is no Apple Intelligence requirement. The iOS 17 minimum was introduced in 1.0.2 (10); earlier binaries required iOS 27. See [release status](RELEASE.md).

## Supported models

- iPhone XS, XS Max and XR on iOS 17 or 18.
- iPhone 11 and newer, running a supported iOS version available for that model.
- iPhone SE (2nd generation and later).

Check **Settings → General → About** for the model and iOS version. iPhone X, iPhone 8 and the first-generation SE cannot run iOS 17 and are not supported. There is no iPad, Mac, Apple Watch or Android version. CarPlay support means audio through the selected car connection; there is no separate dashboard app.

Apple documents [iOS 17 availability](https://www.apple.com/newsroom/2023/09/ios-17-is-available-today/), [iOS 18 devices](https://support.apple.com/en-sg/104985), [iOS 26 devices](https://support.apple.com/en-us/123705) and [iOS 27 devices](https://www.apple.com/os/ios/). Hardware eligibility does not mean each model has been individually tested. Future iOS versions are not yet verified.

## Verification

The compatibility record in [TESTING.md](TESTING.md) names the exact runtime, device and result. Simulator checks establish installation, runtime integration and background playback completion; they do not prove audibility in a car or unrestricted background execution. The owner previously confirmed a real camera warning over Bluetooth with the screen locked. Physical tests on iOS 17, 18 and 26 remain separate.

The automatic `iOS runtime compatibility` GitHub Action builds one simulator app and checks it on iOS 17.5, 18.5 and 26.5 after relevant app changes and on pull requests. iOS 17 and 26 must complete exactly one background siren during a public camera approach. iOS 18 checks launch, persisted settings and Test warning playback; its hosted GPS simulation remains an unresolved test-environment limitation, also reproduced in a minimal control app. The complete local iOS 18 background replay passes. A manual background scenario remains available for diagnosis. Each run uses the shipped minimum and saves its diagnostic journal, result and Xcode evidence. Permission grants are fixtures; prompt UI, lock-screen behavior, Silent mode, Low Power Mode and vehicle audio need the additional manual checks.

## Location compatibility

The original iOS 27 minimum was a project choice. On iOS 18 and later, the app retains a `CLServiceSession` for Always authorization. On iOS 17 it requests When In Use access, then requests the Always upgrade while active. Both paths share one location manager, camera matcher, restart handling and siren implementation. No silent-audio heartbeat or duplicate location pipeline is used.

## Required settings

Enable Camera warnings once. Grant **Always** location access and **Precise Location**. Allow notifications. Turn media volume up and use Test warning while parked on the actual car connection. See the [setup instructions](https://finemenot.xyz/#setup).

The brief siren uses the playback audio category, so Silent mode does not mute active playback. The app cannot override zero media volume, a muted or disconnected car input, phone calls or all audio interruptions. Bluetooth and wired/wireless CarPlay must be checked with the vehicle.

Continuous location monitoring uses battery. Low Power Mode does not turn monitoring off in app code, but iOS controls background execution and recovery. Reopen the app after restarting the phone or force-quitting. No iOS version can guarantee every warning. A saved camera database works offline; network access and Background App Refresh help downloads catch up.

## Toolchain

Version 1.0.2 uses Xcode 26.6 / iOS 26.5 SDK with an iOS 17.0 deployment target. The SDK and the minimum OS are different settings: building with a newer SDK does not require users to install that SDK's OS version. The generated Xcode project and Swift package both target iOS 17, and bundle validation checks the minimum against `project.yml`.

App Store validation, Apple processing, TestFlight availability and physical acceptance are separate release gates. See [Apple's Xcode requirements](https://developer.apple.com/xcode/system-requirements).
