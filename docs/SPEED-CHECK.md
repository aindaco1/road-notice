# Quiet below speed limit

The setting is **on by default**. Switching it off restores speed-camera sirens. Test warning always plays. Red-light and combined cameras always warn.

The current database enriches existing camera identities with agency camera limits, explicit OSM camera tags, road-matched estimates, and conservative lower bounds. It does not add a second camera matcher or a second database. See the generated [coverage report](../Data/Review/speed-limit-coverage.md) and [per-camera evidence](../Data/Review/speed-limit-coverage.json) for current counts, values, sources, alternatives and missing-data reasons. The denominator is speed and possible-speed approaches; red-light/combined records are excluded.

## What can silence a siren

The existing app requires a usable GPS fix no more than three seconds old, a measured nonnegative speed, speed uncertainty of 0–2 m/s, and an unexpired approved value. Measured speed must be **at or below** that value. The uncertainty gate determines whether the measurement is usable; it no longer adds a margin to the posted threshold. Displacement-derived speed cannot suppress a warning. Accelerating before reaching the camera can still trigger its siren; a quiet approach does not consume its alert cooldown.

An approved value has one of five evidence bases:

- **Agency posted:** a current camera-ID or exact reviewed location join to an agency's posted-limit field/table.
- **Field verified:** a dated observation of the posted limit for one reviewed approach, with source and evidence retained. It expires after 30 days and is not renewed by publishing. The November 3 Coors northbound/southbound observations are 45 mph; see [field verification](COORS-FIELD-VERIFICATION.md).
- **OSM posted:** an explicit numeric maxspeed on the camera or its enforcement relation. Bare OSM numbers mean km/h; explicit mph remains mph.
- **Road matched:** an estimate from the named, aligned monitored road or explicit OSM membership. This is not a field-verified sign reading. NMDOT's unit is recorded as an inference from its US roadway/HPMS convention, rather than asserted as an explicit field declaration.
- **Conservative lower bound:** the minimum of fully parsed alternatives or an established reduced school/park limit. For example, a school camera with a 20 mph reduced limit can use 20 throughout the day; this does not assert that its beacon is on. Conflicting credible 30/35 mph values use a 30 mph bound, not an asserted 35 mph limit.

Unknown conditions and variable limits with no known lower bound remain ineligible. A lone directional limit cannot fill the opposite direction. An ordinary street limit cannot replace a known school-camera limit. Numerical enforcement tolerances, advisory/design speeds and citywide defaults are not treated as camera-specific posted limits.

## Road matching

The resolver checks names, distance, approach bearing, available one-way tags and grade separation. Unnamed matches need a road within 12 m, with different-road alternatives at least 15 m farther away. Multiple segments or carriageways of the same named road can supply a conservative minimum only when every plausible segment has usable evidence. Named/member matches must be within 45 m. Approximate warning areas are sampled along their **entire geometry** every 30 m; an uncovered or ambiguous section prevents a road-only approval. A road provider missing an attribute is not a conflicting value when another provider describes the same named and aligned centerline. Unknown limits on a distinct plausible road still block the match.

Fresh direct OSM ways supersede older OSM-derived Overture mirrors. Mirrors are not independent corroboration. Road evidence IDs are separate from camera identity IDs, so an inferred limit cannot become an identity/geometry fact on the next refresh. A moved agency device or a removed agency limit cannot renew the old camera's value.

## Freshness and maintenance

GitHub Actions queries agency pages/feeds, camera-local OSM roads, NMDOT, Seattle and NYC streets on **Sunday at 21:00 America/Denver**, before Monday's midnight publication. It also checks Overture's latest public release and rebuilds resumable regional camera-local extracts when the release or camera geometry changes. Each region keeps its own evidence date; failed regions cannot discard successful ones. Overture releases are monthly; weekly checks do not invent weekly map observations. Requests contain public camera coordinates only.

Limits expire 30 days after their evidence check. Overture additionally has a hard expiry 45 days after its release date. Source edit dates, release dates and source lineage remain in the evidence report: a successful download is not a new sign inspection. Failed, incomplete, rate-limited or suspiciously smaller responses retain the last successful source without advancing its date. Acquisition has time, response-size, memory and scratch-disk limits; the maintenance report records failures and backoff.

Chicago's current school/park policy was also reviewed in the browser because its automated code endpoint returned HTTP 403. The recorded review date is not renewed by a failed fetch; that policy will expire if regular retrieval remains unavailable. HPMS timed out during repeated probes, and Mapillary sign-feature access needs authenticated API access; neither is silently represented as an active fallback.

Albuquerque city currently has two unresolved areas: southbound Carlisle between Hilton and Delamar, and southbound Unser near Gwin. Available road evidence does not cover each entire warning area; nearby studies describe different road sections or Gwin Road itself. These areas continue warning. See the generated report for the wider metro and national gaps.

## App compatibility and verification

Build 7 already decodes these optional `speedLimit` values and ignores the added evidence metadata. `conditional: false` describes an unconditional **suppression bound** when `semantics` is `conservative-suppression-bound`; it does not claim the original posted limit is unconditional. Unknown actual conditions are never sent to the app as an approved higher limit.

No new TestFlight binary is required for this data update. Open Settings and tap **Update now** to download it. Offline operation uses the downloaded snapshot. A phone that has not downloaded it still has its previous coverage.

Pipeline tests exercise units, variable/conditional values, source expiry/removal/movement, street names, direction, grade separation, ambiguous parallel roads, full corridors, conflicting values and separate identities. Swift tests decode the actual published snapshot with the app's current schema and verify that red-light/combined cameras remain unsuppressed. These checks do not replace real-device driving/audio acceptance.

Apple: [CLLocation.speed](https://developer.apple.com/documentation/corelocation/cllocation/speed), [speedAccuracy](https://developer.apple.com/documentation/corelocation/cllocation/speedaccuracy). Source research: [DATA-RESEARCH.md](DATA-RESEARCH.md).
