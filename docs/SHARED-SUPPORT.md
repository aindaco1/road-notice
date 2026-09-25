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

Rollback: revert the migration commit to restore the prior standalone transport
and projection. There is no local data or relay schema migration. Keep dSYMs for
every distributed build, including the preceding 1.0.4 (12).
