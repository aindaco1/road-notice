# Shared support migration

Road Notice 1.0.5 (13) pins Apple Support 0.1.0 through
`platform-support.json`. `SupportCore` remains the app-owned schema and policy
layer. Only bounded HTTP delivery, receipt checks and MetricKit JSON projection
come from Platform; importing it does not resolve Sparkle.

The existing report preview, explicit send action, local journal/subscriber,
endpoint, report fields, failure messages, retention and allowlisted binary name
remain local. The camera database updater and camera warning behavior are
unchanged. Transport characterization covers valid, duplicate, mismatched,
malformed, oversized, rejected and unavailable responses. Crash projection and
golden report fixtures run before and after extraction.

Validation: `swift test`, the iOS 17 minimum simulator build and the signed
Release archive. Apple upload, TestFlight processing and App Store availability
are recorded separately in the release record.

Deployment: Apple processed 1.0.5 (13) as VALID, the existing First Drive group
contains build 13, and App Store Connect confirmed Waiting for Review on
September 25, 2026. Automatic release after approval is selected. See the
[submission record](RELEASE.md#shared-support-maintenance--september-25-2026).

Rollback: revert the migration commit to restore the prior standalone transport
and projection. There is no local data or relay schema migration. Keep dSYMs for
every distributed build, including the preceding 1.0.4 (12).
