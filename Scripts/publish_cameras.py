#!/usr/bin/env python3
"""One stdlib-only camera publisher. Geocoded locations remain explicit estimates.

Source fetches are transactional. Missing records retain their last accepted value
until an explicit tombstone; consecutive complete absences produce a review item.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, json, math, pathlib, re
import urllib.parse, urllib.request
from zoneinfo import ZoneInfo

from camera_data import ROOT, UTC, read, encode, write, stamp, valid_point, distance, OVERPASS_URL
from agency_cameras import combine, coverage_report, audit_metro_points
from speed_limits import enrich
OSM_URL = 'https://www.openstreetmap.org/copyright'
QUERIES = {
    'speed': 'node(area.us)["highway"="speed_camera"];out body;',
    'enforcement': '(nwr(area.us)["enforcement"~"(^|;)(maxspeed|traffic_signals)(;|$)"];);out body;>;out skel qt;',
    'aliases': '(node(area.us)["enforcement"~"red_light_camera|speed_camera"];node(area.us)["camera:type"~"red_light|speed"];);out body;',
}
PREFIX = '[out:json][timeout:180];area["ISO3166-1"="US"]["admin_level"="2"]->.us;'


def week(now):
    local = now.astimezone(ZoneInfo('America/Denver'))
    return (local.date() - dt.timedelta(days=local.weekday())).isoformat()


def valid_source(incoming, previous=None):
    if not isinstance(incoming, dict) or 'remark' in incoming:
        raise ValueError('Overpass error or partial result')
    elements = incoming.get('elements')
    if not isinstance(elements, list) or not elements or len(elements) > 500_000:
        raise ValueError('Invalid source size')
    timestamp = incoming.get('osm3s', {}).get('timestamp_osm_base')
    dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if previous:
        if timestamp < previous['osm3s']['timestamp_osm_base']:
            raise ValueError('Source timestamp moved backwards')
        if len(elements) < .75 * len(previous['elements']):
            raise ValueError('Source lost more than 25%; retaining last good input')
    for e in elements:
        if e.get('type') not in ('node', 'way', 'relation') or not isinstance(e.get('id'), int):
            raise ValueError('Invalid OSM element')
        if e['type'] == 'node' and not valid_point(e.get('lat'), e.get('lon')):
            raise ValueError('Invalid OSM coordinate')
    return incoming


def fetch_sources(root):
    results = []
    for name, query in QUERIES.items():
        path = root / f'Data/Sources/osm-us-{name}.json'
        previous = read(path)
        try:
            data = urllib.parse.urlencode({'data': PREFIX + query}).encode()
            req = urllib.request.Request(OVERPASS_URL, data=data,
                headers={'User-Agent': 'FineMeNot/0.1 (+https://github.com/aindaco1/road-notice)'})
            with urllib.request.urlopen(req, timeout=220) as response:
                raw = response.read(50_000_001)
            if len(raw) > 50_000_000: raise ValueError('Source too large')
            incoming = valid_source(json.loads(raw), previous)
            write(path, incoming)
            results.append({'source': name, 'status': 'downloaded', 'checkedAt': stamp(dt.datetime.now(UTC))})
        except Exception as error:
            if previous is None: raise
            results.append({'source': name, 'status': 'retained', 'error': str(error)})
    return results


def point(e):
    return {'latitude': e['lat'], 'longitude': e['lon']}


def bearing(a, b):
    lat1, lat2 = map(math.radians, (a['lat'], b['lat']))
    dlon = math.radians(b['lon'] - a['lon'])
    return math.degrees(math.atan2(math.sin(dlon) * math.cos(lat2),
        math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon))) % 360


def kind(tags):
    values = set(tags.get('enforcement', '').split(';')) | set(tags.get('camera:type', '').split(';'))
    speed = bool(values & {'maxspeed', 'speed_camera', 'speed'}) or tags.get('highway') == 'speed_camera'
    red = bool(values & {'traffic_signals', 'red_light_camera', 'red_light'})
    if speed and red: return 'speedAndRedLight'
    if speed: return 'speed'
    if red: return 'redLight'
    return None


def excluded(tags):
    # Unsupported mobility/area enforcement and explicit uncertainty need review.
    return (any(key in tags for key in ('fixme', 'FIXME', 'disused:highway', 'removed:highway'))
        or tags.get('camera:mount') in ('vehicle', 'mobile')
        or tags.get('camera:type') in ('mobile', 'portable')
        or tags.get('enforcement') in ('average_speed', 'section')
        or tags.get('highway') in ('proposed', 'construction')
        or tags.get('disused') == 'yes')


def osm_records(documents):
    elements = {}
    for d in documents:
        for e in d['elements']:
            key = (e['type'], e['id'])
            # A recursive skeleton must not erase a full tagged node.
            old = elements.get(key, {})
            elements[key] = {**old, **e, 'tags': {**old.get('tags', {}), **e.get('tags', {})}}
    records = {}; issues = []; device_relations = collections.defaultdict(list)
    for e in elements.values():
        tags = e.get('tags', {})
        if e['type'] != 'relation' or not kind(tags): continue
        if excluded(tags):
            issues.append({'id': f"osm-relation-{e['id']}", 'reason': 'Unsupported or uncertain relation'}); continue
        for member in e.get('members', []):
            if member['type'] == 'node' and member.get('role') == 'device':
                device_relations[member['ref']].append(e)
    for e in elements.values():
        if e['type'] != 'node': continue
        tags = e.get('tags', {}); relations = device_relations[e['id']]
        k = kind(tags)
        if not k and not relations: continue
        identifier = f"osm-node-{e['id']}"
        if excluded(tags):
            issues.append({'id': identifier, 'reason': 'Uncertain, removed, or unsupported tags'}); continue
        kinds = {kind(r['tags']) for r in relations} | ({k} if k else set())
        k = 'speedAndRedLight' if len(kinds) > 1 or 'speedAndRedLight' in kinds else next(iter(kinds))
        direction = None
        # Vehicle direction is inferred only from a single explicit node from/to pair.
        directions = []
        for r in relations:
            members = r.get('members', [])
            ends = [[m for m in members if m.get('role') == role] for role in ('from', 'to')]
            if all(len(x) == 1 and x[0]['type'] == 'node' for x in ends):
                a, b = [elements.get(('node', x[0]['ref'])) for x in ends]
                if a and b and distance(point(a), point(b)) > 10: directions.append(bearing(a, b))
        if directions and max(directions) - min(directions) < 10: direction = round(directions[0], 1)
        label = tags.get('name') or tags.get('ref') or next((r['tags']['name'] for r in relations if r['tags'].get('name')), 'Mapped camera')
        sources = [f"osm/node/{e['id']}"] + [f"osm/relation/{r['id']}" for r in relations]
        records[identifier] = {'id': identifier, 'siteID': identifier, 'label': label[:200], 'kind': k,
            'geometry': [point(e)], 'sourceIDs': sorted(sources),
            'evidence': 'OpenStreetMap mapped device; not independently field-verified. Camera-facing direction is not treated as vehicle direction.'}
        if direction is not None: records[identifier]['travelBearing'] = direction
        if tags.get('addr:street'): records[identifier]['roadNames'] = [tags['addr:street']]
        if tags.get('name'): records[identifier]['locationKey'] = tags['name']
    return records, issues


def reconcile(records, overrides, previous, prior_state, now, complete=True):
    issues = []; records = dict(records); tombstones = set(overrides.get('tombstones', {}))
    # Metro admits only reviewed identities: old red-light and mobile markers cannot leak in as fixed.
    bounds = overrides.get('reviewBounds')
    if bounds:
        south, west, north, east = bounds
        for key, c in list(records.items()):
            p = c['geometry'][0]
            if south <= p['latitude'] <= north and west <= p['longitude'] <= east:
                records.pop(key)
                issues.append({'id': key, 'reason': 'Metro source requires explicit reconciliation'})
    for c in overrides.get('cameras', []):
        c = dict(c)
        for alias in c.pop('replaces', []): records.pop(alias, None); tombstones.add(alias)
        records[c['id']] = c
    missing = {}; old = {c['id']: c for c in previous.get('cameras', [])}
    for key, c in old.items():
        if key in records or key in tombstones: continue
        if c.get('validUntil') and c['validUntil'] <= stamp(now): continue
        count = prior_state.get('missing', {}).get(key, 0) + (1 if complete else 0)
        missing[key] = count
        records[key] = c
        issues.append({'id': key, 'reason': 'Missing from complete fetch; retained pending review', 'consecutiveAbsences': count})
    for key in tombstones: records.pop(key, None)
    for key, c in list(records.items()):
        if c.get('validUntil') and c['validUntil'] <= stamp(now): records.pop(key)
    # Proximity only creates review candidates. It never merges opposing approaches.
    cells = collections.defaultdict(list)
    for key, c in sorted(records.items()):
        p = c['geometry'][0]; cell = (int(p['latitude'] * 500), int(p['longitude'] * 500))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in cells[(cell[0] + dx, cell[1] + dy)]:
                    if distance(p, other['geometry'][0]) < 100:
                        issues.append({'id': key, 'near': other['id'], 'reason': 'Nearby records; no automatic proximity merge'})
        cells[cell].append(c)
    return sorted(records.values(), key=lambda x: x['id']), {'missing': missing}, issues


def validate(records):
    if not 1 <= len(records) <= 100_000: raise ValueError('Invalid camera count')
    if len({c['id'] for c in records}) != len(records): raise ValueError('Duplicate identity')
    for c in records:
        assert c['id'] and c['siteID'] and c['label'] and c['sourceIDs'] and c['evidence']
        assert c['kind'] in ('speed', 'redLight', 'speedAndRedLight', 'possibleSpeed')
        g = c['geometry']; assert 1 <= len(g) <= 2000
        assert all(valid_point(p['latitude'], p['longitude']) for p in g)
        assert len(g) == 1 or c['kind'] == 'possibleSpeed'
        assert all(distance(g[0], p) < 50_000 for p in g)
        if 'travelBearing' in c: assert 0 <= c['travelBearing'] < 360
        if 'validUntil' in c: dt.datetime.fromisoformat(c['validUntil'].replace('Z', '+00:00'))
        if limit := c.get('speedLimit'):
            assert c['kind'] in ('speed', 'possibleSpeed')
            assert limit['unit'] in ('mph', 'km/h') and math.isfinite(limit['value'])
            assert 5 <= limit['value'] <= (85 if limit['unit'] == 'mph' else 140)
            assert limit['sourceID'] in c.get('speedLimitEvidenceIDs',c['sourceIDs']) and limit['conditional'] is False
            start, end = [dt.datetime.fromisoformat(limit[k].replace('Z', '+00:00')) for k in ('verifiedAt', 'validUntil')]
            assert dt.timedelta(0) < end-start <= dt.timedelta(days=90)


def publish(root, now, fetched=None):
    documents = [valid_source(read(root / f'Data/Sources/osm-us-{name}.json')) for name in QUERIES]
    records, issues = osm_records(documents)
    previous = read(root / 'Data/Published/cameras.json', {})
    agency_fresh = any(read(path).get('checkedAt', '') > previous.get('generatedAt', '') for path in (root/'Data/External').glob('*.json'))
    limit_fresh = any(read(path).get('checkedAt', '') > previous.get('generatedAt', '') for path in (root/'Data/SpeedLimits').glob('*.json'))
    if fetched and all(r['status'] != 'downloaded' for r in fetched) and previous.get('cameras') and not agency_fresh and not limit_fresh:
        report = read(root / 'Data/Review/publisher-report.json', {})
        report.update({'generatedAt': stamp(now), 'fetches': fetched,
                       'publication': 'All upstream fetches failed; published snapshot left unchanged.'})
        write(root / 'Data/Review/publisher-report.json', report)
        print('All upstream fetches failed; keeping the published database and its original date.')
        return previous
    overrides = read(root / 'Data/Overrides/metro.json', {})
    audit_metro_points(root, documents, overrides, now)
    records, agency_sources, agency_review, replaced = combine(root, records, previous, now)
    overrides['tombstones'] = {**overrides.get('tombstones', {}), **{k: 'Reviewed agency identity' for k in replaced}}
    issues += agency_review
    prior_state = read(root / 'Data/Review/publisher-state.json', {})
    # Only new successful source snapshots count toward consecutive absence.
    source_version = '-'.join(d['osm3s']['timestamp_osm_base'] for d in documents)
    complete = all(r['status'] == 'downloaded' for r in (fetched or [])) and source_version != prior_state.get('sourceVersion')
    records, state, review = reconcile(records, overrides, previous, prior_state, now, complete)
    records, limit_sources, limit_report = enrich(root, records, documents, now)
    validate(records); issues += review
    coverage_report(root, records, now)
    state['sourceVersion'] = source_version
    digest = hashlib.sha256(encode(records)).hexdigest()[:12]
    version = f'{week(now)}-{digest}'
    # Same-week source recheck can update provenance without mutating an immutable version file.
    source_dates = [d['osm3s']['timestamp_osm_base'] for d in documents]
    sources = [{'id': 'osm', 'name': 'OpenStreetMap contributors', 'url': OSM_URL, 'license': 'ODbL-1.0',
        'checkedAt': min(source_dates), 'status': 'Community coverage; incomplete. Source timestamps: ' + ', '.join(source_dates)}]
    sources += overrides.get('sources', []) + agency_sources + limit_sources
    coverage = 'U.S. community data plus reviewed Albuquerque and agency supplements in Census metros. Coverage is incomplete; see Sources.'
    snapshot = {'schemaVersion': 1, 'version': version, 'generatedAt': stamp(now), 'coverage': coverage, 'sources': sources, 'cameras': records}
    # Timestamp/provenance is part of identity so each manifest always names immutable bytes.
    version += '-' + hashlib.sha256(encode(sources)).hexdigest()[:8]
    snapshot['version'] = version
    immutable = root / f'Data/Published/cameras-{version}.json'
    if immutable.exists(): snapshot = read(immutable)
    else: write(immutable, snapshot)
    write(root / 'Data/Published/cameras.json', snapshot)
    raw = encode(snapshot)
    write(root / 'Data/Published/manifest.json', {'schemaVersion': 1, 'version': version,
        'generatedAt': snapshot['generatedAt'], 'file': immutable.name, 'recordCount': len(records), 'sha256': hashlib.sha256(raw).hexdigest()})
    limit_report['version']=version
    write(root/'Data/Review/speed-limit-coverage.json',limit_report)
    write(root/'Data/Published/speed-limit-coverage.json',{k:v for k,v in limit_report.items() if k!='records'})
    write(root / 'Data/Review/publisher-state.json', state)
    write(root / 'Data/Review/publisher-report.json', {'generatedAt': stamp(now), 'fetches': fetched or [],
        'counts': dict(collections.Counter(c['kind'] for c in records)), 'records': len(records), 'review': issues})
    print(f'Published {len(records)} warning records; {len(issues)} review items; version {version}')
    return snapshot


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--staged', action='store_true', help='Use prepublication fetch status for completeness accounting')
    parser.add_argument('--root', type=pathlib.Path, default=ROOT)
    args = parser.parse_args(); fetched = fetch_sources(args.root) if args.fetch else None
    if args.staged and not args.fetch: fetched = read(args.root/'Data/Review/prepublication-check.json', {}).get('osmFetches')
    publish(args.root, dt.datetime.now(UTC), fetched)
    if fetched and any(r['status'] != 'downloaded' for r in fetched):
        print('::warning::One or more upstream sources failed; last good data retained. See publisher-report.json.')

if __name__ == '__main__': main()
