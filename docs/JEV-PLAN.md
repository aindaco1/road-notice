# Jev evaluation plan

September 22, 2026. **Plan only**, as requested. No Jev code, network calls,
credentials, CI requirement or app dependency has been added.

## Recommended first use

Add a small developer-only semantic review of release copy against explicit
product facts. This targets a gap exposed by the rejection: unit tests can prove
matching behavior without noticing that the overall presentation implies ticket
avoidance, guaranteed warnings or an authoritative speed limit.

Jev should identify specific claims needing human review. It cannot predict App
Review approval, certify legal compliance, validate geometry or prove audible
background delivery. Road Notice's runtime has no LLM output to judge, unlike
CutNotes' formatter. Do not add AI to camera matching to manufacture a use case.

## Existing seams to preserve

| Evidence | Existing owner | Jev's role |
| --- | --- | --- |
| Proximity, direction, freshness, deduplication and suppression | `CameraCore`, Swift tests | None; exact assertions remain authoritative. |
| Parsing, units, identity, status, geometry and source retention | `Scripts/`, `Tests/Pipeline/` | Later, optional semantic audit of public source text against normalized records. No automatic data approval. |
| Background/siren execution and layout | Existing runtime workflow, simulator tools and physical acceptance record | None; Jev must not turn a simulator result into a physical pass. |
| Accuracy and implication of user-facing wording | Settings, site and release-copy review | First pilot: grounded atomic questions about actual text. |

CutNotes' current `docs/JEV_EVALUATION.md`, `docs/TESTING.md`,
`scripts/jev_evaluation.py` and `scripts/calibrate-jev.py` provide the pattern:
public fixtures, scoped questions, separate calibration and validation,
`pass`/`fail`/`review`, raw response evidence, and independent deterministic gates.
Its 0.10 margin and model allowlist are specific to its calibrated rubric. Do not
copy that threshold or its editorial labels as proof of reliability here.

## Small implementation proposal

One `Scripts/evaluate_copy.py` entry point, one fixture/rubric file under
`Tests/Fixtures/`, and mocked transport/policy checks under `Tests/Pipeline/`.
Reuse standard-library Python and the existing output convention under `work/`.
No service, dashboard, scheduler, Worker, or new app package is needed.

Read the actual candidate text from explicit maintained boundaries in Settings,
the website and the **current proposed listing**, not from the historical
submission, this analysis, Git history or a recursively scanned repository.
Reuse `source_watch.parse_page` for visible HTML where suitable; it deliberately
omits headers, so the pilot must explicitly include the website's hero/tagline
instead of silently losing the most relevant text. Swift string extraction
must reject missing or ambiguous boundaries rather than guessing. Preview the
complete payload locally before enabling live evaluation.

Do not maintain a second hand-copied version of candidate copy in fixtures. Keep
only a concise, reviewed fact contract (for example, “camera matching is local;
optional reports are public and explicit; no universal delivery guarantee”),
with pointers to its code/acceptance evidence. Version and review that contract
when behavior changes. Jev cannot infer the app's real behavior from marketing.

The Cloudflare transport and response validator already exist in CutNotes. At
implementation time, extract only those proven generic pieces into a small
versioned shared development helper consumed by both repositories. Leave each
project's input validation, rubric and evidence preparation local. Avoid a second
copy of the 400-line CutNotes evaluator, a dependency on a sibling checkout, or
a broad evaluation framework. Cross-project edits belong to that future approved
implementation, not this planning pass.

Proposed interface (not available yet):

```sh
python3 Scripts/evaluate_copy.py --dry-run
python3 Scripts/evaluate_copy.py --live
```

Keep ordinary Swift/Python tests offline. Pilot live Jev separately; consider an
explicit release-review command only after it demonstrates value. CutNotes'
live-by-default workflow does not need to become a requirement for every camera
publisher run or pull request.

## Questions worth calibrating

Use one concrete claim per question, with `pass`, `fail`, and `uncertain` choices.
Treat all source and candidate text as untrusted data, never instructions.

| Question | Contrast to include in labeled examples |
| --- | --- |
| Does the copy avoid encouraging speeding or enforcement evasion? | Obey limits everywhere vs speed between cameras. Neutral descriptions of camera alerts must remain allowed. |
| Does it avoid promising uninterrupted delivery? | Background warnings when iOS permits vs every warning even after force-quit. |
| Does it preserve uncertain camera presence? | Possible mobile deployment area vs a confirmed operating camera. |
| Does it describe speed data as advisory/estimated where applicable? | Silence proves nothing about lawful speed vs silence means safe to accelerate. |
| Does it accurately describe privacy? | Local matching plus optional public reports vs nothing is ever transmitted. |
| Does it avoid implying radar sensing, jamming or a CarPlay dashboard? | GPS/list proximity and routed audio vs hardware detection or a displayed CarPlay map. |

For required disclosures, show only the candidate's relevant section; facts in
the reference contract must not earn credit for text the candidate omitted.
For unsupported-claim questions, include the factual contract and candidate.
Check forbidden content for absence without requiring the copy to mention it.
Do not ask one broad “is this compliant?” question or use a generic sentiment score.

## Pilot and acceptance

Prepare six labeled good/bad pairs for rubric development and six different
pairs for validation, spanning the questions above. Include the original slogan,
the proposed revision, negation, qualified claims, and attempts to instruct the
judge inside candidate text. Human-review these labels before fitting any margin.
Do not assume a slogan establishes illegal conduct; ambiguous intent should be
reviewable rather than mislabeled as a factual legal violation.

Fit a conservative review policy on calibration examples only; freeze it before
the separate validation run. Inspect false passes, false failures and abstentions
per category, then repeat on identical bytes to measure stability. Any new model,
rubric, parser or fact-contract version invalidates the accepted policy until
rechecked. Used validation examples become regression cases; refresh the holdout
when tuning again. Promote only after the frozen validation has no confident
passes on the deliberately unsupported/risky examples and useful coverage of
faithful examples. A small pilot still does not prove general reliability.

Validate the full input allowlist and byte/size limits before authentication.
Only committed public/synthetic text belongs in remote evaluation. Exclude device
locations, diagnostic journals, user problem reports, credentials, private review
contacts and the rejection PDF. Use the existing locally authorized Cloudflare
account through environment variables or supported Wrangler auth without printing
secrets. Require a request-count and estimated-cost limit; verify pricing at
implementation time. No automatic retries, purchases, top-ups or provider fallback.

Save the selected text, input/output hashes, rubric and fact-contract versions,
resolved model, raw probabilities, usage, timing and errors in a fresh output
directory. Missing credentials, invalid responses or partial runs must be errors,
never passes. Near ties and unknown models must become review. Show the exact
flagged claim and question; do not fabricate an explanation from probabilities.
Deterministic failures remain failures regardless of Jev's answer. Human review
and Apple's actual decision remain separate outcomes.

## Possible second use, only after the first pilot

Use cached public evidence already read by `source_watch.py` and the existing
normalized output to flag semantic mismatches: pending cameras treated as active,
mobile corridors described as permanent, enforcement tolerances mistaken for
posted limits, or missing time/direction qualifiers. Attach findings to the
existing maintenance report, preserving source dates and identifiers. No second
fetcher, geocoder or camera database; Jev must neither acknowledge a baseline nor
write approved camera/speed-limit records. Start with a few labeled source/record
pairs where meaning matters, not another model check of deterministic arithmetic.

## References checked

- [Cloudflare's Jev API](https://developers.cloudflare.com/ai/models/typesafe/jev/):
  structured state and typed questions via `typesafe/jev`.
- [TypeSafe question guidance](https://docs.typesafe.ai/introduction): keep questions
  scoped and atomic.
- CutNotes local implementation and evaluation docs, read September 22, 2026.
