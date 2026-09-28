# Road-following warning zones

September 27, 2026. Local implementation candidate; not released or field accepted.

The alert engine now separates **distance along the monitored road** from **distance across to another road**. Faster travel extends the warning lead along the road, up to the existing 600 m maximum; it does not widen the corridor. This addresses the reproducible I-40 westbound / Menaul–Vassar false association without using uncertain phone altitude or adding a map SDK.

## General behavior

An optional `roadZone` accompanies the existing camera record. It contains a directed centerline, the monitored point/area's start and end along that line, nearby alternative roads, and dated source references. The same algorithm handles every location; there are no Albuquerque coordinates or camera IDs in the runtime matcher.

- Project the fix onto the centerline and check its local direction, remaining along-road distance, and lateral separation. The corridor has a 20 m half-width, with at most 10 m additional GPS tolerance. Road matching waits if horizontal accuracy exceeds 25 m.
- Reject positions clearly closer to an aligned alternative road. At an overlapping crossing, require recent clear evidence of the monitored approach; otherwise wait for a distinguishable position. The latest clear evidence wins. The bounded history is at most 16 fixes from the last 10 seconds, in memory only, never saved or uploaded.
- Preserve the existing movement, speed-limit, encounter, cooldown and rearming rules. Entering while below a reliable speed limit does not consume the encounter: accelerating inside the zone can still produce the warning. Unknown speed limits retain the existing conservative warning policy.
- Keep the existing matcher for cameras with absent or expired zones. That preserves coverage but also preserves its nearby-road false-positive risk at those locations. An ambiguous fix within a current zone waits; it does not bypass road matching through the fallback.

This is a compact local-road check, not a complete navigation map matcher. Identical stacked geometry cannot always be resolved, particularly on a cold start. Phone altitude is not used as a substitute for missing road evidence.

## Automatic generation and staged coverage

`Scripts/road_zones.py` extends the single publisher and reuses the existing road cache, spatial index, name matching and projection primitives. It requires a known monitored direction, a close named-road or explicit source match, and fresh direct OSM geometry. Paths connect through actual shared source node IDs, respect one-way travel, and stop at ambiguous forks. Every camera-area segment must fit the path. Guessed straight extensions and proximity-based road joins are excluded. Other nearby ways remain alternatives even when their names match the monitored road.

Each zone is bounded to the useful approach and monitored area. Source checks expire after 30 days. Both publisher and app validate geometry, dimensions and dates. Weekly regeneration can remove an unsupported zone while retaining its camera record. The optional schema field is backward compatible with existing apps, which ignore it.

The first rollout uses the existing reviewed Albuquerque metro register: **54 zones from 71 reviewed approaches**, within the unchanged **2,701 camera records**. All other camera fields, IDs, speed limits and source metadata remain unchanged. [Coverage report](../Data/Review/road-zone-coverage.json) lists each eligible approach and every fallback reason.

The included zones cover **Coors north of St. Joseph in both directions**, **Alameda between Guadalupe Trail and Rio Grande**, and **Menaul west of Vassar westbound**. Coors at Montaño and Coors Bypass retain the existing matcher because this input set does not support an unambiguous connected approach.

National expansion should apply these same evidence gates and automated replays to newly eligible data. It does not require driving every camera location, nor does passing a local field drive certify all source geometry. Field testing checks representative scenarios—divided road, parallel road, curved approach, crossing, and parked departure—while the publisher and corpus tests check each generated zone. Reviewed Albuquerque coverage is the initial rollout boundary, not an algorithmic restriction.

## Size and dependencies

The local snapshot `2026-09-21-dc315dfa720e-79004776` grows from **2,978,201 to 3,556,528 bytes**, an increase of **578,327 bytes** (about 0.58 MB). The measured gzip increase is **42,236 bytes**; that is a data-compression comparison, not an App Store download measurement. These figures include the nearby alternative roads, not just the monitored centerlines. Only the current snapshot is bundled. No map SDK, nationwide map tiles, online matching service or new runtime dependency is added. The eventual nationwide payload depends on eligible geometry and needs measurement when that rollout is generated.

## Verification and remaining acceptance

Swift fixtures cover curved-road lead distance, GPS uncertainty, wrong direction, parallel roads, overlapping geometry, recent turns, expired/missing data, speed changes inside a zone, and encounter rearming. A corpus replay checks every published zone for a valid approach and rejection of opposite or distant traffic. The cached I-40 location that previously triggered Menaul at 55 and 65 mph now produces no warning for that camera; the Menaul positive control still warns. These are synthetic tests, not the user's recorded journey.

Python tests cover source-node connectivity, direction, stale sources, ambiguous parallel candidates, same-name alternatives, complete area coverage and malformed geometry. The existing pipeline, camera and support suites also run. Build and simulator results are recorded in [TESTING.md](TESTING.md).

On Coors and Alameda, use normal lawful driving with Quiet configured as appropriate for testing, and compare the warning with the actual monitored road/direction. Include the nearby-road negative case and an overnight parked-to-driving departure with the phone locked. The battery and recovery acceptance procedure is in [BATTERY-MONITORING.md](BATTERY-MONITORING.md). Physical wake timing, GPS accuracy on departure, battery savings and actual audibility remain unverified for this candidate.
