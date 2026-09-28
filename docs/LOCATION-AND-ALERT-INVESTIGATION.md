# Battery use and nearby-road alerts

September 27, 2026. Historical investigation of source commit `61f7169` and checked-in camera snapshot `2026-09-21-f03293b9ac43-79004776` (2,701 records). The findings below describe that baseline. The subsequently authorized local implementation is documented in [ROAD-ZONES.md](ROAD-ZONES.md) and [BATTERY-MONITORING.md](BATTERY-MONITORING.md); it has not been released.

The reported westbound I-40 / Menaul–Vassar false alert is reproducible in the current alert engine using a synthetic drive on cached road geometry. Stationary battery optimization is also a real opportunity: movement currently gates warnings but does not reduce the requested location accuracy or update frequency.

## What the baseline app does

| Concern | Current behavior | Evidence |
|---|---|---|
| Location power | Requests navigation accuracy, a 10 m distance filter, background updates, and no automatic pauses. The pause callback immediately restarts updates. | [MonitoringController](../App/MonitoringController.swift), initialization and pause delegate |
| Movement | Uses GPS speed or sufficiently large recent displacement. At least 2.5 m/s (about 5.6 mph) marks movement; that evidence keeps the alert movement gate open for 120 seconds. | [AlertEngine](../Sources/CameraCore/AlertEngine.swift), `evaluate` and `travelMotion` |
| Driving classification | No Core Motion automotive classifier. `.automotiveNavigation` configures Core Location; it is not an app-side determination that the person is in a car. | [MonitoringController](../App/MonitoringController.swift) |
| Stationary UI | Shows “Ready · waiting for movement” below the speed threshold, including when effective speed is unavailable. This does not put GPS into a low-power mode. | `consume` and `status` in MonitoringController |
| Warning distance | 15 seconds of estimated travel, clamped to 150–600 m, measured to the nearest point of camera geometry. Direction and approach filters then apply. | `evaluate` in AlertEngine |
| Camera zones | Supports points and road polylines, but no independently configured lateral corridor width, monitored-road membership, or runtime road matching. | [Camera](../Sources/CameraCore/Camera.swift), [Geometry](../Sources/CameraCore/Geometry.swift) |
| Elevation | The alert fix contains no altitude or vertical accuracy; camera records contain no surveyed elevation. | LocationFix and Camera |
| Speed policy | Quiet below speed limit is on by default. It suppresses speed/possible-speed warnings only when measured speed plus uncertainty is strictly below an approved, unexpired value. Unknown/unreliable values, red-light and combined cameras still warn. | [SpeedCheck](../Sources/CameraCore/SpeedCheck.swift), [speed policy](SPEED-CHECK.md) |
| Recovery | Significant-change location monitoring supports permitted recovery through the same controller and engine. | MonitoringController |

The data pipeline already matches **cameras to roads to infer their speed limits**, including direction and grade-separation checks. That happens in [speed_limits.py](../Scripts/speed_limits.py), before publication. It does not match the **phone to its current road** while driving. These are separate problems.

The project remains an offline, on-device warning app with one controller and one alert engine, iOS 17+ support, stable camera IDs, and no routine route uploads. The relevant context is in [README](../README.md), [original plan](PLAN.md), [data](DATA.md), [Albuquerque coverage](ALBUQUERQUE.md), [identity](GEOCODING-AND-IDENTITY.md), [debugging](DEBUGGING.md), [tests](TESTING.md), [support](SUPPORT.md), and [release history](RELEASE.md). Older build/count statements in historical documents are not current acceptance evidence.

## I-40 / Menaul–Vassar reproduction

The city's current source lists **Menaul west of Vassar, westbound**. The app record is `abq-menaul-vassar-possible-wb`, reference ABQ-30. It represents a **750 m approximate section of Menaul**, starting at Vassar and extending west, because the exact camera position is unverified. Its current checked-in limit is **45 mph, inferred from the monitored road**, not a surveyed camera sign. [City location list](https://www.cabq.gov/automated-speed-enforcement/automated-speed-enforcement), [accepted geometry](../Data/Overrides/metro.json), [road-area evidence](../Data/Review/albuquerque-road-areas.json), [limit evidence](../Data/Review/speed-limit-coverage.json).

A standalone Swift probe compiled the unchanged files in `Sources/CameraCore` and replayed the full checked-in camera index. The I-40 coordinates came from cached Overture segment `6420a208-4d98-448c-ae7b-c34946c2df59`, Coronado Freeway, derived from OSM ways `172991495` and `1118008231`. The cache records Overture release `2026-08-19.0`, checked September 15. Locations were interpolated at intervals of at most 20 m with synthetic speed, 5 m horizontal accuracy, 0.5 m/s speed uncertainty, and fresh timestamps on September 27. This is a deterministic geometry replay, not a recorded drive or an iOS location-delivery test. [Cached road geometry](../Data/SpeedLimits/Overture/79dd4274b9005814.json).

| Synthetic scenario | Menaul warning count |
|---|---:|
| I-40 westbound at 65 mph, Quiet on | **1 — false road association** |
| I-40 westbound at 55 mph, Quiet on | **1 — false road association** |
| Menaul westbound at 50 mph, Quiet on | 1 |
| Menaul westbound at 40 mph, Quiet on | 0 |
| Menaul eastbound at 50 mph, Quiet on | 0 |

Both highway runs warned at `35.1071565, -106.6128987`: **316.9 m from the Menaul area**, heading **283.6°**. At 65 mph, warning distance is **435.9 m**; at 55 mph it is **368.8 m**. Both satisfy the current distance/direction checks. Both speeds also exceed the Menaul record's 45 mph value, so Quiet does not suppress the wrong-road warning. These chosen speeds are test inputs, not an estimate of the user's speed.

The engine therefore has a confirmed false-positive mechanism consistent with the report. The precise alert on the phone remains unverified because its event diagnostics, installed build, database version, and actual location fixes were not inspected. Fresh road retrieval attempts timed out/returned HTTP 406, and the live database request returned HTTP 403; the replay deliberately uses the identified checked-in snapshots rather than claiming live or surveyed road verification.

Local reproduction files are under `work/battery-road-investigation-2026-09-27/`: `main.swift`, `results.txt`, and the compiled `probe`. To rerun from the repository root:

```sh
swiftc Sources/CameraCore/*.swift work/battery-road-investigation-2026-09-27/main.swift -o work/battery-road-investigation-2026-09-27/probe
work/battery-road-investigation-2026-09-27/probe
```

All **21 existing CameraCore tests passed** using `swift test --filter CameraCoreTests` with a temporary scratch directory outside iCloud Drive. The first default-path attempt failed during test-bundle signing because of filesystem metadata; the clean scratch build passed. Logs are saved beside the replay. The existing tests cover expected-road approaches and opposite directions, but do not contain this nearby I-40 negative case. A future fix should retain this replay as a regression fixture.

## Recommended camera-zone change

Implement **directional approach corridors evaluated on the phone**. Keep the current spatial index to find candidates, then require evidence that the phone is on the road the camera monitors.

1. Separate distance **along the road** from distance **across the road**. Speed may increase look-ahead along the approach; it should not widen a Menaul zone hundreds of metres sideways toward I-40. For a first prototype, compare lateral widths around 25–40 m against GPS uncertainty, carriageway width, and neighboring roads. These are trial values, not validated defaults. Poor accuracy must produce an ambiguous match rather than unbounded widening.
2. Use each reviewed polyline as the starting road corridor. For point cameras, add separately sourced approach-road geometry instead of treating the device coordinate as the entire approach. Preserve camera IDs, point coordinates, provenance, and the approximate-area label where applicable.
3. Keep a short, in-memory sequence of recent fixes to score road continuity and direction. Include nearby competing roads and their connectivity. This helps distinguish parallel streets and bridges where one position alone is ambiguous. A turn from a ramp onto the monitored street must be able to change the match; do not permanently exclude highway drivers or all bridges.
4. Carry relevant source road IDs, direction, bridge/tunnel and crossing-level relationships through the publisher to the offline runtime. Reuse existing road acquisition caches, while checking that they cover competing roads: camera-local speed-limit extracts were not designed as a complete driving network. Validate freshness and missing metadata explicitly. The smallest first release can cover reviewed Albuquerque approaches, with existing behavior retained and documented elsewhere.
5. Evaluate the qualifying conditions on every usable fix while inside the zone. Do not require only an outside-to-inside crossing: the first fix may already be inside, or the driver may enter below the limit and accelerate later. A synthetic 40-to-50 mph change inside Menaul already demonstrates that the current engine correctly allows the later warning. Keep that behavior and one-warning-per-encounter handling; zone jitter must not rearm it repeatedly.

For an adequately mapped camera, the decision becomes: **usable moving fix → applicable road/approach zone → applicable speed policy → encounter not already warned**. A confident match to a different road rejects the camera. An ambiguous match needs an explicit fallback policy and diagnostics; silently choosing the nearest road would recreate this problem.

These app-defined zones do not need to be thousands of iOS geofences. Apple's system condition monitoring is limited to **20 simultaneous conditions** and is designed around boundary events, with settling and possible relaunch delays. It can assist recovery, but it should not be the timing source for every camera siren. [Apple region monitoring](https://developer.apple.com/documentation/corelocation/monitoring-the-user-s-proximity-to-geographic-regions), [Apple engineer explanation](https://developer.apple.com/forums/thread/818908).

**Speed-policy distinction:** the requested “only when above the limit” rule is stricter than today's “quiet when reliably below.” Enforcing it literally would also silence unknown/expired limits and uncertain speeds. The wrong-road fix does not require that policy change. Recommended first step: preserve the existing conservative policy while adding road applicability; define any strict above-limit behavior separately, including its treatment of unknown limits and red-light cameras.

## Where elevation helps

Altitude could support a road match if both the device's altitude and the road-deck elevation are trustworthy and use compatible references. The current camera data cannot supply that comparison. Phone altitude alone cannot establish which nearby road is being traveled, and a ground-terrain elevation is not necessarily a bridge-deck elevation.

Apple describes `verticalAccuracy` as altitude uncertainty, approximately one standard deviation; it is not a guaranteed error bound. A difference comparable to that uncertainty cannot reliably distinguish two road levels. Road topology and bridge/tunnel metadata should therefore come first, with altitude an optional confidence signal. [Apple vertical accuracy](https://developer.apple.com/documentation/corelocation/cllocation/verticalaccuracy), [altitude reference](https://developer.apple.com/documentation/corelocation/cllocation/altitude).

OSM `layer` describes ordering where features cross; it is **not metres of elevation**. Overture exposes bridge/tunnel flags and relative levels, which can help preserve that topology. Absence of a tag is not proof that two roads share an elevation. [OSM layer semantics](https://wiki.openstreetmap.org/wiki/Key:layer), [Overture road flags](https://docs.overturemaps.org/schema/reference/transportation/types/road_flag/).

## Recommended battery investigation

Apple recommends requesting only the accuracy and update frequency required. Core Location chooses its sensors; a 10 m distance filter is a request about delivery, not an exact schedule of GPS calls. The current app explicitly requests its most demanding navigation accuracy throughout the enabled session. [Apple location power guidance](https://developer.apple.com/documentation/corelocation/getting-the-current-location-of-a-device).

Use a measured comparison between two candidates, preserving one active location provider and the shared engine:

| Candidate | Benefit to investigate | Main constraint |
|---|---|---|
| Adapt the existing manager | Lower requested accuracy and increase distance filter after sustained reliable stationary evidence; restore driving precision promptly on movement. Also compare ordinary best accuracy with navigation accuracy. | Coarse fixes must trigger precision escalation before the engine's 75 m accuracy filter rejects them. A stale/unknown speed or a stoplight must not count as a parked car. Wake-up delay needs measurement. |
| Re-evaluate `CLLocationUpdate.liveUpdates(.automotiveNavigation)` | Apple's API provides stationary auto-pause and movement auto-resume, including suspension handling. It is available within the iOS 17+ scope. | Must correctly retain the observation/session and restore it after permitted relaunch. Re-test the earlier missed-warning cases and supported OS versions before replacement. |

The second option is particularly relevant to overnight idle use. Apple explicitly documents pause/resume behavior for live updates; keep consuming the sequence through stationary periods rather than breaking the loop. This is different from assuming that a paused `CLLocationManager` will automatically restart. [Apple live-update lifecycle](https://developer.apple.com/videos/play/wwdc2023/10180/), [current energy guidance](https://developer.apple.com/documentation/xcode/accessing-the-device-s-location-efficiently), [manager pause contract](https://developer.apple.com/documentation/corelocation/cllocationmanager/pauseslocationupdatesautomatically).

History matters: commit `fd99484` replaced live updates with the continuous manager while fixing the Coors missed-warning report. That investigation also proved missing camera data, a movement-detection bug, and stale cache selection. It had no physical phone logs establishing that automatic pausing caused the missed warning. Re-evaluation is justified, but an untested rollback is not evidence of reliable recovery. [Original investigation](DEBUGGING.md).

Avoid relying on Core Motion alone to turn GPS back on. Its activity callbacks are best-effort and are not delivered while an app is suspended. Also, `automotive` and `stationary` can both be true at a red light. Core Motion could supplement a power decision, but adds a permission and does not solve background wake-up by itself. [Apple activity delivery](https://developer.apple.com/documentation/coremotion/cmmotionactivitymanager/startactivityupdates(to:withhandler:)), [activity flags](https://developer.apple.com/documentation/coremotion/cmmotionactivity).

Significant-change monitoring alone is also too coarse for a prompt first-camera warning: Apple describes changes around 500 m and says not to expect updates more frequently than every five minutes. Keep it as recovery support, not a substitute for driving fixes. [Apple significant-change service](https://developer.apple.com/documentation/corelocation/cllocationmanager/startmonitoringsignificantlocationchanges()).

## Acceptance and order of work

Recommended order: **road-specific zones first**, then a separately measured battery change. The zone defect has a reproducible case; battery savings and recovery latency still need device evidence.

- Road regression cases: westbound I-40 stays silent for Menaul; the correct Menaul approach still warns once; opposite travel stays silent; turns from ramps work; overpasses and parallel roads remain distinct; poor accuracy and missing course are explicit; starting or accelerating inside a zone still works; return journeys rearm correctly.
- Power comparison: current build versus each candidate on the same iPhone/iOS under comparable conditions. Record eight-hour stationary drain, a one-hour drive, time to the first usable fix after departure, and first-camera warning lead time. Include an overnight locked phone, parking near a camera, short traffic stops, offline use, Low Power Mode, and denied/unavailable motion permission if Core Motion is used.
- Preserve the iOS 17/18/26 compatibility checks and test the owner's current iOS version physically. Unit tests and synthetic replays cannot prove power savings, overnight recovery, or car-audio audibility.
- Keep diagnostic state and aggregate timing local. Any detailed route capture should be an explicit development session; normal use does not need a stored trip history.

No battery percentage improvement is claimed. The existing physical acceptance record already lists idle drain, driving drain, and overnight recovery as unmeasured. This investigation changes documentation only.
