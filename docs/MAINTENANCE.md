# GitHub maintenance

All recurring work runs in GitHub Actions. The Fine Me Not Codex heartbeat was deleted; no Mac, open browser, Codex session, paid geocoder or API secret is required for weekly data maintenance.

- **Sunday 21:00 America/Denver:** `source-checks.yml` retrieves registered camera feeds, OSM inputs and agency pages, normalizes supported formats, geocodes new/changed textual locations, and reconciles identities. It commits reproducible caches and review reports to main.
- **Monday 00:00 America/Denver:** `data.yml` publishes the camera snapshot and website. It reuses a completed source pass from the last 12 hours or catches up before publication. Both workflows share a concurrency group. GitHub can delay scheduled jobs, so this is a schedule, not an exact completion-time guarantee.
- **On the phone:** download the published snapshot when iOS permits, on activation, during monitoring or using Update now. Offline warnings use the last valid saved/bundled snapshot.

The pattern follows the owner’s [RSS digest workflow](https://github.com/aindaco1/rss-feed-digest/blob/main/.github/workflows/daily-digest.yml): explicit Denver timezone, bounded network retries, validation, concurrency control, manual dispatch and artifacts saved even when a run fails. Its [September 14 successful run](https://github.com/aindaco1/rss-feed-digest/actions/runs/34882122103) was verified during this change.

The [restaurant-locations pipeline](https://github.com/aindaco1/restaurant-locations/blob/main/.github/workflows/pipeline.yml) is a second verified example: tests before retrieval, dataset validation, commits only when data changes, and 30-day evidence artifacts. Its latest three scheduled runs succeeded, including [September 14](https://github.com/aindaco1/restaurant-locations/actions/runs/34818742807). Fine Me Not explicitly deploys in its publication job instead of depending on a bot commit to trigger another workflow.

## Regression fixtures

Field-verification tests compare the original edited snapshot with its immutable
pre-edit baseline. The current weekly snapshot may regenerate road zones; it
must retain camera geometry, direction and field-verified speed limits and pass
zone validation, without matching every historical road edge or source date.
The Swift replay retains the fixed 54-zone corpus and checks every current zone
against the generated coverage report rather than an obsolete minimum count.

## Review queue

Start with [maintenance.md](../Data/Review/maintenance.md) and its full [JSON](../Data/Review/maintenance.json). Each workflow retains a 30-day artifact. Git history preserves earlier reports and source caches. Source changes, added/removed list entries, unresolved coordinates, aliases and failures remain inspectable. The Sunday job summary links those findings; monitoring does not automatically certify a whole metro.

The Albuquerque page monitor compares the sorted camera-location list, so unrelated navigation changes and list reordering do not cause false changes. Other page/document monitors detect text, map-link or PDF changes. Deterministic readers handle the supported feeds and Philadelphia/Hillsborough lists; newly discovered website formats still require adding a reader or reviewing source evidence. The workflow does not invent a camera from arbitrary changed prose.

Failed fetches retain the original successful source and evidence dates. Major count drops, malformed responses, moved locations, ambiguous overlaps and removals require review. Accepted records remain until explicit retirement. A source that has never succeeded contributes no cameras. Manual review can update `Data/Overrides/agency-aliases.json`, reviewed metro geometry, or explicit tombstones, then run the publisher/tests. To acknowledge a reviewed page baseline:

```sh
python3 Scripts/source_watch.py --acknowledge SOURCE_ID
```

Commit the reviewed changes. Do not acknowledge a failed or unreviewed source merely to clear the report. Geo estimates retain provider evidence; see [geocoding and identity](GEOCODING-AND-IDENTITY.md).

## Further sources researched for this release

See the [September 14 follow-up investigation](DATA-RESEARCH.md) for NMDOT, Seattle and NYC road-speed API probes and additional camera sources. Nine new page monitors now cover Scottsdale, Mesa, Fairfax, Prince George’s red-light locations, Snellville, Wheat Ridge, CDOT locations/applicability and NYC DOT’s quarterly report index. Seven succeeded in the initial local pass; Prince George’s and NYC DOT returned HTTP 403. These monitors detect changes for review; they do not yet add cameras or approved speed limits. Their next checks use the existing Sunday workflow.

| Source | Recurring use | Decision |
|---|---|---|
| [Philadelphia Parking Authority](https://philapark.org/speed-cameras/) | Current location lists, future activation dates, program changes | Added numbered camera blocks through Census estimates. Unresolved intersections/segments and street mismatches remain queued. |
| [Hillsborough County](https://hcfl.gov/government/codes-and-ordinances/red-for-a-reason/red-light-cameras) | Six red-light intersections and ten monitored approaches | Added a road-intersection reader; validated OSM shared-node estimates are accepted after reconciliation. |
| [Montgomery County Police](https://www.montgomerycountymd.gov/montgomery-county-police-department/how-do-i/speed-ticket-payment/speed-camera-locations) | Current page links dated location/corridor PDFs | Added page monitoring. The police ArcGIS organization also exposes 462 speed and 55 red-light features in datasets named 2024. Their age, current-list reconciliation and restrictive reuse statement need resolution before adopting them as the open master feed. |
| [Maryland SafeZones](https://www.safezones.maryland.gov/ase/Pages/locations.aspx?PageId=2) | Current work-zone deployment map | Added monitoring. Rotating/mobile locations and variable work-zone limits require a dedicated applicability reader; do not import historical citation points as fixed cameras. |
| [Albuquerque speed-limit GIS](https://dmdmaps.cabq.gov/serverext/rest/services/Public/SpeedLimits/MapServer/layers) | Potential posted-limit source | Both public speed-limit endpoints returned empty layer lists; no suppression values imported. Historical traffic-study limits are not substituted. |
| [NYC “speed cameras” dataset](https://data.cityofnewyork.us/City-Government/speed-cameras/hk4g-zwnh) | Historical violation data | Not a current camera inventory. Do not promote citation locations without current device and operational evidence. |
| Municipal Socrata, ArcGIS and agency-linked KML feeds already registered | Stable IDs and explicit coordinates; source-specific status/type filters | Continue Chicago, DC, Arlington, Seattle, Tacoma, San Francisco and Phoenix refreshes. |

No new single complete, open and authoritative US camera inventory was found. Coverage remains the Census top 20 metros plus Albuquerque, with uneven source quality. The source registry is extensible; current coverage counts are generated in [metro-coverage.json](../Data/Review/metro-coverage.json).

## Durable road zones

Road-zone geometry remains active until replaced or its camera geometry/direction changes. Its 30-day date schedules a source review; it does not remove the road constraint. The shared road cache now covers every camera kind with wider, bounded regional queries. Partial refreshes activate completed queries alongside the previous set; per-way timestamps select newer evidence without inventing new dates. Missing and least-recently-attempted regions get the next acquisition budget. The road-zone coverage report lists every camera, retained short approaches and overdue checks; maintenance findings summarize those gaps. Tests pin historical field edits separately from current data, so routine regeneration and speed-limit expiry cannot freeze the updater.

### Completing directional road acquisition

Run `python3 Scripts/fetch_speed_limits.py --osm-only --directional-only --budget-seconds 10800` for a complete candidate pass. It selects existing regional batches that cover known-direction cameras, preserving query hashes and the full active-source set. Every 500 m sample along a warning area must have its batch acquired. `directionalCoverage` in `Data/Review/speed-limit-fetch.json` records each candidate, required batches, pending batches and completion; acquiring a batch does not itself certify a road-zone match. Retry failed batches with the same command; successful caches are reused. `--overpass-url` can select another public HTTPS mirror when the configured service is unavailable; each cache records its actual source URL and replica date. Respect the selected provider’s usage policy.

Queries use the same automotive road classes as the resolver. A padded bounding box covers every original 750 m camera envelope in a batch, using one spatial query. Full road geometry and source node IDs are returned without output clipping; the bounding box is only an acquisition filter, never a generated road. Overpass checks crossing segments as well as interior nodes ([implementation](https://github.com/drolbr/Overpass-API/blob/master/src/overpass_api/data/bbox_filter.cc)). Temporary large-query failures and oversized responses split into batches of at most five points, then single points if necessary, with complete-response checks and delays. Successful pieces are cached under ignored `work/road-query-cache/`, keyed by endpoint and selection query; retries reuse them with their original source dates. A parent batch becomes available only when all pieces succeed. Rate-limit responses still stop acquisition for backoff. A partial response never counts as a completed batch. Queries reserve 64 MiB and allow the service’s capacity wait to finish; memory/time failures still split into smaller requests. Recursive retries share the run deadline. The routine weekly time budget remains bounded; the explicit longer pass is for completing the initial rollout.


For a large initial acquisition or prolonged Overpass outages, `Scripts/import_road_extract.py` fills missing caches from [Geofabrik OSM extracts](https://download.geofabrik.de/technical.html). Install the optional readers in `Scripts/requirements-data.txt`; download `index-v1.json`, the needed `.osm.pbf` files and each adjacent `.md5` file. For example:

```sh
python3 Scripts/import_road_extract.py --index work/geofabrik-index.json --extract us/illinois=work/illinois-latest.osm.pbf
```

Repeat `--extract` for adjoining regions. Every original camera query envelope must fit inside the supplied clipping polygons, and adjoining extracts must share a replication timestamp. The importer verifies checksums, rejects missing/future/over-two-day-old snapshots, preserves complete ways and shared node IDs, and keeps the actual snapshot date. It writes the existing road-cache format with source-file and clipping-polygon digests, so the same zone builder, direction checks and speed-limit evidence rules apply. It does not overwrite a completed API cache. Re-run the directional fetch command afterward to refresh the per-camera acquisition report. The separate `Tests/Extracts` suite runs in CI; the core pipeline remains stdlib-only.
