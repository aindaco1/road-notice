# Reviewed reports · 1.0.1

The Settings action **Report a problem** opens a category, optional explanation
(up to 2,000 Unicode scalars / 8 KiB), and per-report technical-details toggle.
The toggle defaults on; it is not consent to automatic uploads. A report is frozen
with a random ID before review. **Full report** exposes every transmitted field.
Only **Send report** performs an upload. Offline/timeout errors keep the immutable
draft for an explicit retry; edits create a new ID. No account or phone-side
GitHub credential is required. Report while parked.

## Data contract

`Sources/SupportCore/Resources/report-contract.json` owns allowed event/state values.
`SupportReport.swift` validates the complete bounded envelope before preview/send.
The shared relay has byte-identical contract and fixture copies; daily GitHub
Actions compare them. Unexpected fields fail validation on both sides.

Automatic details include version/build/iOS/model, permissions, background state,
Low Power Mode, bucketed fix age/accuracy, stable match reasons, audio route class,
volume bucket and playback result, database version/count/stage/result, and up to
40 recent diagnostic transitions. There are no coordinates, camera IDs/names,
roads, speed/heading/distance, accessory names, raw errors/URLs/paths, trip logs or
persistent device/user identifiers. The local **Copy local diagnostics** string
is deliberately separate and is never the input to a public report.

Crash/hang evidence uses Apple's MetricKit subscriber and cached payloads. The
filter retains the original app version/build, diagnostic period end, bounded
numeric signal/exception and up to 32 app-relative frames with binary UUIDs.
Raw JSON, system frames/paths, addresses and exception text are discarded.
Apple does not deliver a diagnostic for every termination; no event means unknown,
not proof that the app did not crash. Background does not establish screen lock.

The actor-owned reporting journal caps events at 500 / 24 hours / 256 KiB, crash
records at five / seven days, and drafts at five / seven days. The combined file
is bounded, excluded from backups and protected until first unlock. Adjacent
same-state events coalesce; no extra GPS polling, background task or audio loop
is introduced. Storage failure does not interrupt warnings. Expired items are
pruned on the next journal access; deleting local history does not delete public
GitHub issues. New diagnostic events can accumulate after clearing the journal.

## Relay and grouping

Endpoint: `https://crash.dustwave.xyz/v1/fine-me-not/reports`.
Implementation lives in `aindaco1/ascii-vj-remix/crash-relay`; reuse the existing
Worker, GitHub App and `ReviewedReportGroup`, not a second service.

The fixed destination is `aindaco1/road-notice`. The repository was renamed from
`fine-me-not` on September 22, 2026. The legacy endpoint, contract and on-device
paths are retained for existing installations. A product-scoped serial ID ledger
keeps receipts for 30 days and rejects ID reuse with a changed payload, including
changes that produce a different fingerprint. Each issue group also retains its
own receipts for that full retry window, including after more than 1,000 reports.
Expired group receipts are removed by daily cleanup; new reports do not postpone
an already scheduled cleanup. The product ledger never evicts a young receipt
for capacity: 10,000 entries cause temporary refusal. An hourly, keyed IP hash
limits requests to 10; a separate atomic product quota permits 25 new issues per
UTC day. Existing issues can still receive new reports when that quota is full.
No report body or raw IP is written to application logs. Hosting providers may
retain ordinary connection information.

Crash grouping uses original binary UUID and app-relative frames. Audio/database
failures group only when the user selects the related recorded event. Notes,
report IDs, patch versions and current after-drive state are not technical causes.
Ambiguous/text-only reports get separate needs-triage issues. Counts mean reports,
not unique people or prevalence. The first and four latest distinct explanations
are retained, with older ones counted as omitted; extreme escaping expansion may
reduce the displayed set to stay within GitHub's body limit.

The relay serializes external GitHub awaits, persists increments before sending,
and searches an exact fingerprint marker after an uncertain create. It does not
blindly create a second issue. New reports can reopen closed issues; labels
`duplicate`, `do-not-reopen`, and `fixed-in-build:N` control this. Reports from an
older crash build don't reopen a fixed issue. Maintainer content outside the bot
block is preserved. User text is escaped literal content and must never become
an agent instruction, shell command or workflow input.

## Operations and recovery

- Deploy through ASCII VJ Remix's manual **Deploy Crash Relay** GitHub Action.
- Disable intake with `FINE_ME_NOT_REPORTS_ENABLED=false` and redeploy. Never roll
  back migrations or delete Durable Objects to recover a failed upload.
- Road Notice's daily **Reporting service health** GitHub Action checks endpoint
  configuration and contract equality. It opens/reopens/closes one incident only
  on state change. This does not prove issue-write permission or native delivery;
  verify those with explicitly marked synthetic reports after relay changes.
- If a GitHub POST's outcome is uncertain and search cannot find its marker, the
  creation guard intentionally leaves that group pending. Inspect the provider
  and exact fingerprint before resolving storage; do not bypass the guard blindly.
- Public issue copies may persist indefinitely. Report receipts expire, but issue
  aggregates and public GitHub reports have no automatic deletion promise.

## Symbolication and release checks

Retain every distribution archive and dSYM. Run:

```sh
python3 Scripts/symbolicate_report.py reviewed-report.json FineMeNot.app.dSYM
```

The command refuses mismatched UUIDs, then resolves app-relative offsets with
`atos`. A synthetic parser fixture is not proof of Apple's on-device delivery.
Test a diagnostic from a physical iPhone when one is available. Do not ship a
crash button or induce a crash while driving.

Run `swift test`, pipeline tests, simulator build/UI review, release bundle check,
relay tests/dry-run, and synthetic creation/retry/aggregation/provider receipt
checks. Keep TestFlight upload/processing, App Store privacy publication and
physical-device behavior separately recorded in `RELEASE.md`.

## Privacy disclosure

Version 1.0.1 introduces developer collection only when a person sends a report.
The manifest declares Crash Data, Other Diagnostic Data and Customer Support for
App Functionality, without tracking. It conservatively marks these linked because
free-form explanations can identify someone and attach diagnostic evidence to
that explanation. There is no anonymous-data guarantee. This supersedes 1.0's
Data Not Collected answer for the new reporting build. Update App Store Connect
before public distribution; do not infer an exemption merely from optional send.

Primary references: [Apple MetricKit](https://developer.apple.com/documentation/metrickit),
[privacy manifest data types](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacycollecteddatatypes/nsprivacycollecteddatatype),
[Cloudflare Workers practices](https://developers.cloudflare.com/workers/best-practices/workers-best-practices/).

## Repository rename — September 22, 2026

The existing relay adapter now targets `road-notice` and displays Road Notice.
The [focused relay commit](https://github.com/aindaco1/ascii-vj-remix/commit/e101f81)
passed all 49 relay tests and the deployment dry run. The
[Deploy Crash Relay run](https://github.com/aindaco1/ascii-vj-remix/actions/runs/35796216339)
succeeded. The read-only health and published-contract check passes; no public
synthetic report was sent in this rename pass. Existing namespaces, receipts,
fingerprints, schema and endpoint remain unchanged.
