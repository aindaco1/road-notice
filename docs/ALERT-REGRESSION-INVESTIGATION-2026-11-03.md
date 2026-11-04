# October 28 alert regressions — investigation, November 3, 2026

**Historical investigation, before the 1.0.7 fixes.** The findings, live-data
status, sign-check status and proposed follow-up below describe the November 3
investigation of 1.0.6, not the current implementation. The owner subsequently
reconfirmed both Coors limits; PR #8 merged, road acquisition completed for all
1,071 candidates, and 701 approaches passed the zone checks. See
[implemented corrections and remaining limits](ALERT-FIXES.md) and the
[1.0.7 submission record](RELEASE.md) for current status.

The released engine can reproduce the reported wrong-road warning and two separate opposing-direction Coors warnings. The road-zone fix stops applying when its evidence expires, while failed maintenance has left every published zone expired. Quiet also behaves differently from the owner's intended at-or-below-limit rule. These are verified code/data mechanisms consistent with the reports, not a reconstruction of the phone's actual GPS fixes.

Investigation only: no app implementation, production camera records, workflows, release, or deployment changed. Existing local edits to the App Store/release documents were preserved.

## Reports and confirmed scope

The owner reports the latest App Store release, probably iOS 27.2, with **Quiet below speed limit enabled**:

| Local time (America/Denver) | Report |
|---|---|
| October 28, 2026, 09:41:49 MDT | Traveling westbound on I-40; warned for Menaul west of Vassar, westbound. |
| October 28, 2026, approximately 19:51 MDT | Probably traveling northbound on Coors; heard two warnings and saw two alert entries for Coors north of St. Joseph NB/SB. |

The October 1 field record already establishes 45 mph for both Coors approaches. The owner is checking the signs again; this investigation does not manufacture a new observation date. Exact installed build, downloaded database, measured speed, and GPS uncertainties for the October 28 events remain unavailable.

The owner clarified the desired future behavior: with a trustworthy limit and usable measured speed, **stay quiet at or below the limit and warn only above it**. The clarification covers the threshold; it does not establish a new policy for unavailable speed or limit evidence. Red-light approach applicability remains a separate question from speed suppression.

## Release and live data verified

- The [public App Store listing](https://apps.apple.com/us/app/road-notice/id6812094105) lists version 1.0.6, released October 8. Repository release documentation identifies its submitted public binary as build 19; the phone's exact build was not inspected.
- Local `main` is `087253a`; fetched `origin/main` is `73d5a45`, six data-only commits ahead. Runtime, publisher, and test source are unchanged from tag `v1.0.6` through that remote head.
- The [live v2 manifest](https://finemenot.xyz/data/v2/manifest.json) points to `cameras-2026-10-19-49463424717f-730d153a.json`, generated October 19 at 11:32:07 UTC, containing **2,728 cameras**. Downloaded bytes match both its SHA-256 and `origin/main:Data/Published/cameras.json`.
- SHA-256: `0131e37601dddc8cf26c36d7060c109ce8039adcc1cbad4285b9034a724a0efe`.

| Snapshot | Cameras | Zones present | Zone expiry |
|---|---:|---:|---|
| Build 19 bundle / tag v1.0.6 | 2,701 | 54 | October 15 or October 21 |
| October 5 public update | 2,711 | 54 | Same original evidence dates |
| October 12 public update | 2,719 | 54 | Same original evidence dates |
| October 19 public update, still live | 2,728 | 24 | All October 21, 08:57:50 UTC |

Consequently neither the bundled data nor any of these public updates supplies a current road zone on October 28. A successful download of this live feed cannot restore those protections by itself.

## 1. Expiry restores the I-40 false positive

[`AlertEngine.evaluate`](../Sources/CameraCore/AlertEngine.swift) uses `RoadZone.assess` only while `zone.isCurrent(at: now)` is true. Otherwise it runs the older distance/direction matcher. That matcher lets speed increase a proximity radius to 150–600 m; it has no independent road-membership requirement.

The existing cached I-40 fixture at `35.1071565, -106.6128987`, heading 283.6 degrees, is about 317 m from the Menaul warning area. At synthetic 55 and 65 mph it falls inside that radius. The exact same camera, fix quality, and source code reject the highway at the snapshot date but warn at the reported date:

| Synthetic replay, Quiet on | At snapshot generation | October 28 |
|---|---:|---:|
| I-40 WB, 55 mph | 0 Menaul warnings | **1 false Menaul warning** |
| I-40 WB, 65 mph | 0 Menaul warnings | **1 false Menaul warning** |

Both the bundled and current live snapshots reproduce this. Correct-road Menaul WB still warns at synthetic 50 mph; the eastbound control does not. Test speeds are inputs, not estimates of the owner's speed.

## 2. Missing direction can warn for both Coors approaches

In the fallback matcher, the wrong-direction rejection runs only if course is known. Within 100 m, missing course also bypasses the approach-evidence check. Both Coors polylines are close enough to a vehicle on either carriageway to qualify. The two records have independent encounter state.

`MonitoringController.consume` deliberately passes no course when Core Location course accuracy is invalid or above 45 degrees. The engine can derive direction from displacement, but requires at least 30 m with two 5 m-accuracy fixes; it does not retain a previous measured course as a fallback.

The following two synthetic northbound fixes reproduce **two separate warning batches**, not just two labels in a grouped notification:

1. At 44 mph with usable northbound course and good speed accuracy: NB warns.
2. One second and approximately 19.7 m farther north, with course unavailable: SB warns; NB is already in cooldown.

The app presents each nonempty batch separately. A cold fix with both course and speed accuracy unavailable can also select NB and SB together. These are two possible mechanisms, not evidence that either specific GPS condition occurred on the phone. Current zones require direction and prevent this permissive fallback while active.

## 3. Quiet's current threshold differs from the requested behavior

[`SpeedCheck.shouldSuppress`](../Sources/CameraCore/SpeedCheck.swift) requires measured speed **plus at least 1 m/s (2.24 mph)** to be strictly below the limit. It also requires a fix no more than three seconds old, speed uncertainty in 0–2 m/s, and a current limit.

For the actual Coors records at the October 28 evening time:

| Synthetic input, Quiet on | Result |
|---|---|
| 40 mph, usable course, 0.5 m/s speed accuracy | Quiet |
| 44 mph, otherwise identical | Warn |
| 40 mph, unavailable speed accuracy | Warn |
| 40 mph, usable course/accuracy, November 3 date | Warn because the limit expired |

Both 45 mph field observations were valid through **October 31, 06:00 UTC** (midnight MDT). Their expiry does **not** explain the October 28 speed behavior, although it does explain why those published values no longer silence warnings now. Without event-level measurements, there is no evidence that an accurate 40 mph fix with a current 45 mph limit wrongly passed the existing speed rule.

The future comparison should implement the owner's explicit `measuredSpeed <= limit` preference once speed/limit evidence is usable. Keep that rule in the existing SpeedCheck owner and test exact equality as well as below/above values.

## 4. Maintenance is blocked, and fresh road downloads can be ignored

The October 26 and November 2 source-check/publication workflows failed. Examined logs from [October 26 publication](https://github.com/aindaco1/road-notice/actions/runs/40318022077) and [November 2 source checks](https://github.com/aindaco1/road-notice/actions/runs/41442869883) show the same failure: `test_coors_field_verification_keeps_geometry_and_direction` requires the current Coors zone to equal September's zone byte for byte. October 19 legitimately changed the generated zone, causing subsequent runs to stop in their pre-fetch test stage. Each examined run reports 77 tests with one failure.

There is a second refresh constraint. `active_osm_shards` activates replacement query hashes only when the entire requested batch set exists. One incomplete region can therefore keep the previous national set active. This protects against wholesale coverage loss, but repeated partial refreshes can strand newer usable roads outside the active set until the old set expires. For example, cached Coors ways have an October 12 retrieval that is inactive; active copies remain September 21 or older. Menaul also has a newer September 28 copy outside the active set. No dates were advanced during this investigation.

An existing draft [PR #8](https://github.com/aindaco1/road-notice/pull/8), head `2455b9e`, already corrects the frozen zone comparison and the Swift corpus's fixed minimum count. At inspection it is unmerged; build/tests pass, while the iOS 17.5 monitoring wake job fails. It changes tests and documentation, not data or runtime. Reuse that work; it does not by itself resolve expiry fallback, stale active shards, warning thresholds, or national coverage. Further expiry must also be allowed to remove optional zones/limits without making maintenance tests impossible to pass.

## 5. Approach length is not guaranteed

The engine requests 15 seconds of lead, clamped to 150–600 m. A zone can only provide that warning where its sourced centerline actually reaches upstream. The builder imposes a minimum 150 m approach for point records but **not for multi-point warning areas**.

| Live October 19 zone | Mapped distance before approximate area | Travel time at 45 mph |
|---|---:|---:|
| Menaul WB | 251.13 m | 12.5 seconds |
| Coors NB | 113.36 m | 5.6 seconds |
| Coors SB | **0 m** | **0 seconds** |

These distances describe mapped pre-area geometry, not observed warning times or distance to a surveyed camera pole. Endpoint tolerance, GPS, competing roads and actual camera placement affect real delivery. The bundled Coors SB zone previously had 154.18 m before its area; the regenerated zone has none. Five of the 24 published zones have less than 150 m of mapped approach.

Use one lead-distance rule for both point and area cameras. Retain the current 15-second/150–600 m target initially, require sourced upstream geometry sufficient to support it, and report short approaches explicitly. Do not lengthen a corridor with an invented straight line. Coors and Menaul are approximate 750 m warning areas, so claims of exact seconds before the hardware also require better camera positions.

## 6. Expansion to other cameras

The runtime RoadZone matcher is generic and does not hard-code Albuquerque or camera kinds. The publisher's `enrich_zones` explicitly restricts generation to IDs in the reviewed metro register. In addition, `fetch_speed_limits.refresh` requests OSM roads only around **speed/possible-speed** cameras, excluding red-light and combined records. Its 80 m camera-local queries can return long complete ways, but do not guarantee a connected 600 m upstream approach and all competing roads.

The live database's direction evidence is:

| Kind | Total records | Known monitored direction |
|---|---:|---:|
| Speed | 1,605 | 498 |
| Possible speed | 186 | 159 |
| Red light | 742 | 375 |
| Combined | 195 | 39 |
| **Total** | **2,728** | **1,071** |

The other **1,657** records need direction evidence before this directional builder can use them. Known direction is a prerequisite, not proof of complete geometry or rollout readiness. Do not infer monitored traffic direction from which way a camera lens faces.

A read-only dry run invoked the unchanged builder for every record, bypassing only the metro allowlist in the audit script:

- Using active caches at the October 19 publication time: **30 candidates**, comprising the existing 24 plus six Phoenix possible-speed approaches; none were red-light/combined. These candidates still need approach-length and corpus acceptance.
- At October 28 or November 3: **zero candidates**, because the selected direct-OSM road set has no fresh ways. This describes the current cache, not the eventual national capacity of the algorithm.

Recommended expansion: repair incremental source refresh; acquire bounded connected approach geometry for all four camera kinds through the existing cache; derive or retain defensible monitored directions; then run the same builder across all eligible records. Emit one coverage report with direction, geometry, lead length, freshness, and fallback reasons per camera. Keep road applicability common to speed and red-light cameras; their speed-warning policies remain distinct.

## Smallest coherent follow-up

1. Finish the existing maintenance-test correction, make freshness/coverage losses visible, and fix partial source activation so successful bounded regions can contribute without erasing retained coverage elsewhere. Rebuild and validate fresh data.
2. In the existing alert engine, require directional evidence for directional cameras and prevent expired road zones from silently reopening broad proximity matching. Define a conservative stale-geometry/degraded-coverage behavior explicitly; merely extending dates would hide the problem.
3. Apply the confirmed at-or-below-limit Quiet comparison in SpeedCheck. Refresh the Coors field evidence when the new sign verification is complete; do not renew it merely by publishing.
4. Enforce upstream lead requirements for both points and areas, then remove the metro-only rollout restriction where the same evidence checks succeed. Add red-light/combined road acquisition through the shared pipeline.
5. Validate with time-advanced/offline replays, two successive missing-course fixes, both Coors directions, I-40 negatives, below/equal/above-limit inputs, refresh failures, and per-zone lead measurements. Then verify representative real-phone routes and actual warning timing.

This keeps one publisher, road builder, location stream, matcher, and speed policy. No map SDK, second matcher, per-camera runtime exceptions, or routine trip recording is needed.

## Evidence and limits

All **35 existing CameraCore tests passed** against the local release snapshot using an external scratch directory. This is useful baseline evidence but does not contradict the regressions: the published-highway test evaluates at `snapshot.generatedAt`, the corpus calls `zone.assess` directly, and existing expiry tests explicitly preserve the legacy fallback. They do not assert the reported behavior weeks later.

Local evidence is retained in ignored `work/alert-investigation-2026-11-03/`: `main.swift`, `replay-results.txt`, `live-manifest.json`, `live-cameras.json`, two failed workflow logs, `swift-core-tests.log`, `coverage_audit.py`, and per-date coverage reports. The original `latest/` audit extract contained 299 files identical to revision `73d5a45`; it was moved to the dated macOS Trash folder during the November 4 cleanup. It can also be reconstructed from that revision's `Data`, `Scripts` and `Tests` directories.

The original synthetic replay commands below require the pre-fix 1.0.6 source
and saved investigation inputs. Running them against current source tests the
corrected engine instead. The coverage audit also requires restoring `latest/`.

```sh
swiftc Sources/CameraCore/*.swift work/alert-investigation-2026-11-03/main.swift -o /tmp/road-notice-investigation-2026-11-03
/tmp/road-notice-investigation-2026-11-03
python3 work/alert-investigation-2026-11-03/coverage_audit.py
```

The ordinary alert log retains notification time and camera/limit snapshots, not the GPS fix, measured speed, course, uncertainty, build, or database version needed to attribute an old event conclusively. The user report is therefore the field evidence; the replay establishes matching failure modes. No new simulator, physical-driving, audio, or iOS 27.2 acceptance is claimed.
