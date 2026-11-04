# October 28 alert regressions — November 3, 2026

The owner reported a Menaul west of Vassar westbound warning while driving
westbound on I-40 at 09:41:49 MDT, and both Coors north of St. Joseph warnings
at about 19:51 MDT while probably traveling northbound. Both sounds and both
log entries were observed at Coors. Quiet was enabled in the App Store release.
The owner reconfirmed both Coors approaches at 45 mph on November 3.

The alert log does not retain the GPS fix or database/build used for each event.
These regressions reproduce plausible failure paths from the shipped data and
code; they are not a replay of a recorded drive or proof of each incident's cause.

## Corrections

- **Keep road constraints active.** Shipped zones reached their source-review
  deadlines before October 28. The old app then reverted to broad proximity
  matching, reproducing the I-40/Menaul false warning at 55 and 65 mph. The app
  now keeps validated geometry after that deadline, including months offline.
  A future-dated or ambiguous road match waits instead of bypassing the zone.
- **Require direction evidence.** A directional camera without usable course
  or enough measured displacement waits. Losing course after a Coors warning
  can no longer admit the opposing approach through the legacy close-range path.
- **Use the posted threshold.** Quiet suppresses a speed-camera warning at or
  below a usable limit. GPS uncertainty still decides whether speed is usable,
  but no longer adds a margin to the measured speed. Unknown/expired limits and
  unusable speed still warn; red-light and combined warnings remain enabled.
  Quiet does not consume the encounter, so accelerating above the limit can warn.
- **Use one zone builder everywhere.** All camera kinds and regions use the
  existing source-connected road matcher. New zones require at least 600 m
  before the monitored point or area. Paths follow actual shared OSM nodes,
  respect one-way travel, stop at ambiguous forks and keep nearby road alternatives.
  A longer adjacent road cannot replace a closer road with insufficient lead.
- **Preserve evidence through incomplete updates.** Successful regional road
  downloads activate immediately alongside the previous active set. An unchanged
  camera can retain its last validated zone when a replacement cannot be built;
  changed camera geometry or direction invalidates that retained association.
  Original source dates are preserved. Overdue checks and short retained zones
  appear in maintenance reports instead of silently reopening broad matching.
  Bounded acquisition prioritizes unattempted regions, then the oldest attempts,
  so repeated failures do not monopolize the weekly budget.

The wire field `validUntil` remains for compatibility but represents a source
review deadline for road geometry. **The new app binary is required** to stop
runtime expiry; older binaries retain their previous behavior. Speed-limit
evidence and temporary-camera expiration remain separate and unchanged.

## Data and limits

The candidate snapshot generated at **2026-11-04 03:34:10 UTC** (November 3
Mountain time) retains **2,728 cameras** and contains **56 road zones**:
40 generated with at least 600 m of approach and 16 retained from prior evidence.
It covers 26 speed, 24 possible-speed and six red-light records. Menaul/Vassar
and both Coors/St. Joseph zones each provide **650 m** of sourced approach.
The existing warning target remains about 15 seconds, bounded to 150–600 m.

The remaining 2,672 cameras lack a zone: 1,657 have unknown monitored direction,
654 lack a clear connected path in the available cache, 358 lack the required
lead and three have competing candidate paths. No combined camera yet passes
all gates. Fifty-one zone source checks remain overdue; retaining their dates
does not imply a fresh source verification. The bounded fetch completed fresh
regional downloads but did not finish nationwide acquisition. Weekly checks
continue the same queue. See the [coverage report](../Data/Review/road-zone-coverage.json).

Both Coors field observations now use the owner's November 3 confirmation,
valid through December 3 for Quiet. Camera IDs, monitored geometry and travel
bearings were preserved. The source refresh can independently change other
speed-limit evidence; it does not infer limits from the owner's Coors report.

## Do Not Disturb and Focus

Critical Alerts are deliberately not added. Existing notifications remain
time-sensitive and subject to the user's notification/Focus permissions.
Do Not Disturb can silence them unless Road Notice or time-sensitive
notifications are allowed. Driving Focus has different controls.

The owner reports that both the camera siren and notification were missing,
while parked Test warning still played. The siren uses media playback separately
from notification delivery. This observation does not establish that Focus
blocked playback, nor does a successful Test warning verify background GPS or
camera matching. App settings, support docs and the website explain that limit.
See [Apple's Focus controls](https://support.apple.com/guide/iphone/allow-or-silence-notifications-for-a-focus-iph21d43af5b/ios).

## Validation

New regression tests first failed against the old runtime. The corrected suite
covers I-40 negatives with a Menaul positive control, both Coors directions,
course dropout with and without zones, offline geometry after 180 days, current
incident-zone lead length, 40/44/45 mph silence and above-limit warnings. Pipeline
tests cover all camera kinds, source retention, camera moves, lead length,
parallel roads and fair continuation after the fetch budget is exhausted.

Current results and remaining physical-device acceptance are recorded in
[TESTING.md](TESTING.md). Website wording describes the new release without an
“upcoming” label at the owner's request; [RELEASE.md](RELEASE.md) separately
records packaging, deployment and App Store status.
