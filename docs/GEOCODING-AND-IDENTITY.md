# Location estimates and camera identity

## Free coordinate lookup

The [Census Geocoder](https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/census-geocoder.html) provides free US address lookup without an account or API key. Its API also supports batches of up to 10,000 addresses. The result is **interpolated along an address range**, not a surveyed camera position. Road Notice uses it only for numbered locations explicitly published as camera locations by an agency. It validates the street, state, coordinate and Census metro boundary before accepting a result.

For an intersection, the pipeline requests named OSM roads inside a bounded jurisdiction and finds their shared road nodes. A divided intersection can have several nodes; the estimate is their center, provided they are within 180 m of one another. Disconnected crossings, absent roads and widely separated matches remain unresolved. An agency’s omitted compass prefix is allowed in the search; a conflicting explicit prefix is not. School-building centroids are never substituted for enforcement locations.

Successful estimates are cached for 180 days. A failed lookup is cached for one day to avoid repeated requests for multiple approaches. An upstream failure retains the last successful estimate and its original lookup date. New or changed location descriptions receive a new cache key. The official camera source is still fetched weekly; the cache does not freeze its location list. Changing an estimate by more than 100 m requires review.

Coordinates retain provider, source location, precision class and evidence. A speed-camera estimate says Possible speed camera; red-light intersection labels explicitly say approximate location. These estimates improve warning coverage but do not prove pole location, enforcement range, equipment presence, or survey accuracy.

[Overpass public instances and usage guidance](https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances) document the free road-query service. Geometry requests are serialized, bounded and cached; the public Private.coffee instance handles these small road lookups. Camera refreshes retain the established OSM source pipeline. HTTP retries respect rate limits and stop after three attempts. The app itself never calls a geocoder and never transmits a driver’s position.

The public [Nominatim service policy](https://operations.osmfoundation.org/policies/nominatim/) discourages recurring bulk geocoding, requires caching/identification, caps ordinary use at one request per second and regular scripts at four per minute. It is **not** used by this pipeline. A self-hosted Nominatim/Photon instance or licensed provider is an option if this project outgrows the free services.

## Deduplication rules

Distance opens a comparison; it does not establish identity. Records preserve stable app IDs and source provenance so database corrections do not reset encounter cooldowns.

1. Explicit reviewed aliases have priority. Previously accepted source-to-app identities persist across refreshes.
2. A new source can match an existing point through a shared device identity, or through the same normalized listed location and monitored approach within 60 m, or the same named road and monitored approach within 30 m. The distance ceiling is 75 m. The match must be mutually unique.
3. Opposing monitored approaches remain separate, including agencies that place multiple approaches at the same coordinate. Explicitly different roads remain separate. Speed and red-light functions are not discarded to create a match.
4. Coincident OSM points within 1 m can share one warning record only when kind, label and travel-bearing semantics are identical. All original source IDs survive. This consolidates redundant warnings; it is not a claim about how many physical cameras exist.
5. Ambiguous overlaps remain queued. New agency or OSM records within 150 m of an existing unresolved identity are withheld, while already accepted coverage remains usable. Movement over 100 m is reviewed. Missing records are retained until explicit retirement, rather than deleted during an outage.

The reconciliation report records automatic decisions and unresolved candidates. The tests cover opposing approaches, parallel roads, two nearby intersections, ambiguous one-to-many matches, stable IDs and provenance. Approximate road areas remain separate from precise point matching. Camera-facing/lens direction is never silently interpreted as vehicle direction.
