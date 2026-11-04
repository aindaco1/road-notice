# Coors field verification — October 1, 2026

The project owner reported successful Albuquerque testing of the private build,
including approaching road zones and Quiet below speed limit, with no observed
issues. They confirmed the northbound and southbound speed cameras on Coors
north of I-40 and a posted **45 mph** limit at both approaches. They reported
that the existing warning locations are correct and requested no geometry change.

This update applies to the existing Coors north of St. Joseph records, city
references ABQ-37 and ABQ-38:

- `abq-coors-st-joseph-possible-nb`, travel bearing 0 degrees.
- `abq-coors-st-joseph-possible-sb`, travel bearing 180 degrees.

Both are classified as speed cameras. Their stable IDs, reviewed road polylines,
road zones and alert extents are retained. The legacy `possible` substring in
the IDs is an identity key, not the current classification. Device coordinates
were not surveyed; the labels continue to identify an approximate area.

Each record carries a dated, approach-specific `speedLimitObservation` and
`presenceVerifiedAt`. The speed-limit resolver accepts field observations through
the same evidence, conflict and 30-day expiry rules as other limits. Republishing
does not renew a field observation. Unknown speed, excessive GPS uncertainty,
expired limits and speeds inside the existing uncertainty margin still warn.

This is the owner's field report, not an independent survey or a measured battery
test. It does not establish physical acceptance for other cities or devices.

## October 2 follow-up

The owner questioned whether build 16 detects these limits. Inspection of the
retained signed archive confirmed both 45 mph records and the intended private
database URL. Their validity ends October 31, 2026 at 06:00 UTC. The existing
GPS uncertainty rule is unchanged: measured speed plus at least 1 m/s
(about 2.24 mph), or the reported uncertainty when larger, must be strictly
below 45 mph. Thus a measured 44 mph still warns; 40 mph with good speed
accuracy can be quiet. Unknown speed accuracy also warns. The report alone
does not establish which condition occurred on the phone. New log entries
show their saved speed-check limit to make the loaded data visible.

## November 3 confirmation and threshold correction

The owner explicitly confirmed that **both Coors north of St. Joseph approaches remain posted at 45 mph**. New dated speed-limit observations use November 3, 2026 (00:00 MST / 07:00 UTC), retaining camera identities and warning-area geometry. This is a new owner observation, not an automatic extension of October evidence. The corrected Quiet rule suppresses usable measured speeds at or below 45 mph and warns above it; unknown/expired limits and unusable measurements still warn. Road geometry itself no longer stops working when a source recheck becomes due. See [the implementation record](ALERT-FIXES.md).
