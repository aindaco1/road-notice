# Road-following warning zones

Introduced September 27, 2026; public release preparation October 4. See [release status](RELEASE.md).

The alert engine now separates **distance along the monitored road** from **distance across to another road**. Faster travel extends the warning lead along the road, up to the existing 600 m maximum; it does not widen the corridor. This addresses the reproducible I-40 westbound / Menaul–Vassar false association without using uncertain phone altitude or adding a map SDK.

## General behavior

An optional `roadZone` accompanies the existing camera record. It contains a directed centerline, the monitored point/area's start and end along that line, nearby alternative roads, and dated source references. The same algorithm handles every location; there are no Albuquerque coordinates or camera IDs in the runtime matcher.

- Project the fix onto the centerline and check its local direction, remaining along-road distance, and lateral separation. The corridor has a 20 m half-width, with at most 10 m additional GPS tolerance. Road matching waits if horizontal accuracy exceeds 25 m.
- Reject positions clearly closer to an aligned alternative road. At an overlapping crossing, require recent clear evidence of the monitored approach; otherwise wait for a distinguishable position. The latest clear evidence wins. The bounded history is at most 16 fixes from the last 10 seconds, in memory only, never saved or uploaded.
- Preserve the existing movement, speed-limit, encounter, cooldown and rearming rules. Entering while below a reliable speed limit does not consume the encounter: accelerating inside the zone can still produce the warning. Unknown speed limits retain the existing conservative warning policy.
- Validated zones remain active offline and after their source recheck date. Only cameras without a zone use the existing matcher; directional cameras always require course or sufficient displacement evidence. An ambiguous fix waits instead of bypassing the road constraint.

This is a compact local-road check, not a complete navigation map matcher. Identical stacked geometry cannot always be resolved, particularly on a cold start. Phone altitude is not used as a substitute for missing road evidence.

## Automatic generation and staged coverage

`Scripts/road_zones.py` extends the single publisher and reuses the existing road cache, spatial index, name matching and projection primitives. It requires a known monitored direction, a close named-road or explicit source match, and dated direct OSM geometry. Paths connect through actual shared source node IDs, respect one-way travel, and stop at ambiguous forks or cycles. A closed loop cannot inflate approach length or repeat an exit with conflicting directions. The planned warning approach must include a position distinguishable from aligned alternative roads; fully overlapping stacked approaches remain unsupported. Every camera-area segment must fit the path. Guessed straight extensions and proximity-based road joins are excluded. Other nearby ways remain alternatives even when their names match the monitored road.

New zones require approximately 15 seconds of sourced approach geometry at the highest usable camera or matched-road speed, bounded to 150–600 m and rounded up to 25 m. For example, 45 mph requires 325 m and 65 mph requires 450 m. Conditional road limits use their highest known alternative for this geometry decision; a school-zone suppression bound cannot shorten ordinary-road lead. When no numeric speed is available, the minimum is 325 m, or 600 m on motorway/trunk roads. These fallback distances do not assert a posted speed limit. Up to 650 m is retained wherever the mapped path supports it; the app still uses actual travel speed for warning timing. Source checks become due after 30 days; geometry does not expire. Both publisher and app validate geometry, dimensions and dates. If a refresh cannot produce a complete replacement, the publisher retains the prior zone only while camera geometry and travel direction remain unchanged. Short retained approaches and overdue checks are explicit in the coverage report. Camera retirement and changes to its geometry/direction still invalidate the old association. The optional schema field is backward compatible: pre-zone apps ignore it, while 1.0.6 understands zones but still applies the old expiry cutoff.

The September candidate used the reviewed Albuquerque metro register: **54 zones from 71 reviewed approaches**, within the unchanged **2,701 camera records**. All other camera fields, IDs, speed limits and source metadata remain unchanged. [Coverage report](../Data/Review/road-zone-coverage.json) lists each eligible approach and every fallback reason.

The September zones covered **Coors north of St. Joseph in both directions**, **Alameda between Guadalupe Trail and Rio Grande**, and **Menaul west of Vassar westbound**. At that stage, Coors at Montaño and Coors Bypass retained the existing matcher because the September input set did not support an unambiguous connected approach.

The November implementation applies these same evidence gates to every camera kind and region. Road acquisition is complete for all 1,071 direction-known candidates across 117 batches. The current snapshot has **701 zones**: 334 speed, 45 possible-speed, 321 red-light and one combined camera. The other 370 candidates fail road association, connectivity, lead or ambiguity checks; 1,657 additional cameras have unknown monitored direction. Acquisition uses 750 m query envelopes, bounded regional batches and incremental activation of successful results. It does not require driving every camera location, nor does passing a local field drive certify all source geometry. Field testing checks representative scenarios—divided road, parallel road, curved approach, crossing, and parked departure—while the publisher and corpus tests check each generated zone. Reviewed Albuquerque coverage was the initial rollout boundary, not an algorithmic restriction.

## Size and dependencies

The November snapshot `2026-11-02-849ee6ac8b27-d0ef599a` is **15,226,599 bytes**, or **1,039,938 bytes** with gzip. It fits the app's existing 20 MB feed limit. These figures include nearby alternative roads, not just monitored centerlines; gzip is a data-compression comparison, not an App Store download measurement. Only the current snapshot is bundled. No map SDK, nationwide map tiles, online matching service or new runtime dependency is added. Optional PBF/geometry readers run only during bulk source acquisition.

## Verification and remaining acceptance

Swift fixtures cover curved-road lead distance, GPS uncertainty, wrong direction, parallel roads, overlapping geometry, recent turns, expired/missing data, speed changes inside a zone, and encounter rearming. A corpus replay checks every published zone for a valid approach and rejection of opposite or distant traffic. The cached I-40 location that previously triggered Menaul at 55 and 65 mph now produces no warning for that camera; the Menaul positive control still warns. These are synthetic tests, not the user's recorded journey.

Python tests cover source-node connectivity, direction, stale sources, ambiguous parallel candidates, same-name alternatives, complete area coverage and malformed geometry. The existing pipeline, camera and support suites also run. Build and simulator results are recorded in [TESTING.md](TESTING.md).

On Coors and Alameda, use normal lawful driving with Quiet configured as appropriate for testing, and compare the warning with the actual monitored road/direction. Include the nearby-road negative case and an overnight parked-to-driving departure with the phone locked. The battery and recovery acceptance procedure is in [BATTERY-MONITORING.md](BATTERY-MONITORING.md). Physical wake timing, GPS accuracy on departure, battery savings and actual audibility remain unverified for this candidate.

## Historical October 4 public feed preparation

The public candidate retains all 54 zones, byte-for-byte identical to build 17.
An incomplete road-source refresh initially hid valid cached geometry because
new query hashes replaced the entire active cache list. The fetcher now retains
the last active set until every replacement batch is available. Dates and expiry
remain unchanged; unrelated inactive shards are not reintroduced.

Version 1.0.6 reads `/data/v2/`; the original feed retains classifications accepted
by older validators. Both feeds are produced together from the same camera data.

## November 3 correction

The October 28 regressions and implementation evidence are in [ALERT-FIXES.md](ALERT-FIXES.md). The wire field `validUntil` is retained for compatibility, but is now a source-review deadline, not a runtime geometry cutoff. Earlier binaries still enforce the old cutoff and need an app update. Speed-limit and mobile-camera expiration rules are separate and unchanged.
