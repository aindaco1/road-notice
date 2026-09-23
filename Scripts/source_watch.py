#!/usr/bin/env python3
"""Fetch registered agency sources before publication; retain facts and review changes.

Geocoded agency locations are explicitly approximate. Page monitors do not
automatically manufacture cameras. No account, API key, browser, or paid service.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, re
import urllib.parse, urllib.request
from html.parser import HTMLParser
from camera_data import ROOT, UTC, read, encode, write, stamp, valid_point, distance
import json
import time
import urllib.error
import xml.etree.ElementTree as ET

USER_AGENT = 'FineMeNot/0.1 (+https://github.com/aindaco1/road-notice)'
BEARINGS = {'NB': 0, 'NEB': 45, 'EB': 90, 'SEB': 135, 'SB': 180, 'SWB': 225, 'WB': 270, 'NWB': 315}


def request(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': '*/*'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000: raise ValueError('Source exceeds 20 MB')
            return raw
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2: raise
            if error.code == 429:
                retry = error.headers.get('Retry-After', '30')
                delay = max(30, int(retry)) if retry.isdigit() else 30
                if delay > 60: raise  # Leave the source for the next run.
            else: delay = 2 ** attempt
            time.sleep(delay)
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2: raise
            time.sleep(2 ** attempt)


def json_request(url, **params):
    separator = '&' if '?' in url else '?'
    data = json.loads(request(url + separator + urllib.parse.urlencode(params)))
    if isinstance(data, dict) and data.get('error'): raise ValueError('Upstream API error')
    return data


class Page(HTMLParser):
    """Extract visible text and table facts, excluding scripts and navigation."""
    def __init__(self):
        super().__init__(); self.skip = 0; self.parts = []; self.rows = []
        self.row = None; self.cell = None; self.links = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'svg', 'nav', 'header', 'footer'): self.skip += 1
        if self.skip: return
        if tag in ('p', 'li', 'tr', 'br', 'h1', 'h2', 'h3', 'div'): self.parts.append('\n')
        if tag == 'tr': self.row = []
        if tag in ('td', 'th'): self.cell = []
        for key, value in attrs:
            if key in ('href', 'src') and value and any(x in value.lower() for x in ('.pdf', 'arcgis.com/', 'maps/d/')):
                self.links.append(value)
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg', 'nav', 'header', 'footer'): self.skip = max(0, self.skip - 1)
        if self.skip: return
        if tag in ('td', 'th') and self.cell is not None:
            if self.row is not None: self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None: self.rows.append(self.row); self.row = None
        if tag in ('p', 'li', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'div'): self.parts.append('\n')
    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)
            if self.cell is not None: self.cell.append(value)
    @property
    def text(self):
        return '\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())


def parse_page(raw):
    page = Page(); page.feed(raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else raw); return page


def direction(value):
    value = (value or '').upper().replace('/', '').replace('-', '')
    for word, short in (('NORTHEASTBOUND','NEB'), ('NORTHWESTBOUND','NWB'), ('SOUTHEASTBOUND','SEB'),
                        ('SOUTHWESTBOUND','SWB'), ('NORTHBOUND','NB'), ('SOUTHBOUND','SB'), ('EASTBOUND','EB'), ('WESTBOUND','WB')):
        value = value.replace(word, short)
    matches = set(re.findall(r'\b(?:NEB|NWB|SEB|SWB|NB|SB|EB|WB)\b', value))
    return BEARINGS[next(iter(matches))] if len(matches) == 1 else None


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).lower()).strip('-')


def make_camera(source, identifier, label, kind, lat, lon, bearing=None, limit=None, conditional=False):
    lat, lon = float(lat), float(lon)
    if not valid_point(lat, lon): raise ValueError('Invalid source coordinate')
    key = slug(identifier) if identifier is not None else ''
    if not key or not label: raise ValueError('Missing source identity/label')
    camera = {'id': f"agency-{source['id']}-{key}", 'siteID': f"agency-{source['id']}-{key}",
        'label': str(label)[:200], 'kind': kind, 'geometry': [{'latitude': lat, 'longitude': lon}],
        'sourceIDs': [f"agency/{source['id']}/{identifier}"], 'positionPrecision': 'agency-published-point',
        'evidence': f"{source['name']}: published coordinates, not independently surveyed. Source: {source.get('page', source['url'])}"}
    # Keep the published address/intersection separate from display decoration.
    camera['locationKey'] = str(label).split(' · ')[0]
    if re.match(r'^\d+\s', camera['locationKey']):
        camera['roadNames'] = [re.sub(r'^\d+\s+', '', camera['locationKey'])]
    if bearing is not None: camera['travelBearing'] = bearing
    if kind == 'possibleSpeed': camera['evidence'] += ' Listed deployment point; equipment presence is not live-confirmed.'
    if limit is not None:
        match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:MPH)?', str(limit).strip(), re.I)
        if match and 5 <= float(match[1]) <= 85:
            camera['speedLimitCandidate'] = {'value': float(match[1]), 'unit': 'mph',
                'sourceID': camera['sourceIDs'][0], 'conditional': conditional,
                'suppressionApproved': False}
    return camera


def arcgis_rows(url):
    ids = json_request(url + '/query', where='1=1', returnIdsOnly='true', f='json').get('objectIds')
    if not isinstance(ids, list) or len(ids) > 50_000 or len(set(ids)) != len(ids): raise ValueError('Invalid feature ID response')
    rows = []
    for start in range(0, len(ids), 200):
        data = json_request(url + '/query', objectIds=','.join(map(str, sorted(ids)[start:start+200])),
                            outFields='*', outSR=4326, f='json')
        if data.get('exceededTransferLimit'): raise ValueError('Partial feature response')
        rows.extend(data.get('features', []))
    if len(rows) != len(ids): raise ValueError('Feature count changed during fetch')
    return rows


def kml_rows(raw):
    namespace = {'k': 'http://www.opengis.net/kml/2.2'}
    document = ET.fromstring(raw)
    rows = []
    for marker in document.findall('.//k:Placemark', namespace):
        coordinate = marker.findtext('k:Point/k:coordinates', namespaces=namespace)
        if not coordinate: continue  # Blank placeholders are not camera positions.
        lon, lat, *_ = coordinate.strip().split(',')
        description = parse_page(marker.findtext('k:description', default='', namespaces=namespace)).text
        rows.append({'description': description, 'latitude': float(lat), 'longitude': float(lon)})
    return rows


def normalize(source, rows, now, sf_status=None):
    cameras = []; skipped = []; sid = source['id']
    for row in rows:
        a = row.get('attributes', row); g = row.get('geometry', {})
        cs = []; reason = None
        if sid.startswith('chicago-'):
            label = a.get('address') or a.get('intersection')
            live = a.get('go_live_date')
            if not live or live[:10] > now.date().isoformat(): reason = 'Not operational yet'
            else:
                for field in ('first_approach', 'second_approach', 'third_approach'):
                    if not a.get(field) or a[field] == 'NA': continue
                    bearing = direction(a[field])
                    if bearing is None: raise ValueError('Unrecognized Chicago monitored approach')
                    identity = str(a.get('location_id') or label) + '-' + str(bearing)
                    cs.append(make_camera(source, identity, f"{label} · {a[field]}",
                        'speed' if sid == 'chicago-speed' else 'redLight', a['latitude'], a['longitude'], bearing))
        elif sid == 'dc':
            if a['ACTIVE_STATUS'] != 'Active' or a['CAMERA_STATUS'] not in ('Live', 'Warning'): reason = 'Not operational'
            elif a['ENFORCEMENT_TYPE'] not in ('Speed', 'Red Light'): reason = 'Not speed/red-light enforcement'
            else:
                kind = 'redLight' if a['ENFORCEMENT_TYPE'] == 'Red Light' else ('speed' if a['DEVICE_MOBILITY'] == 'Fixed' else 'possibleSpeed')
                cs = [make_camera(source, a['ENFORCEMENT_SPACE_CODE'], a['LOCATION_DESCRIPTION'], kind,
                    a['CAMERA_LATITUDE'], a['CAMERA_LONGITUDE'], direction(a['LOCATION_DESCRIPTION']), a['SPEED_LIMIT'])]
        elif sid == 'seattle':
            if a['Camera_Type'] not in ('Red Light', 'Fixed School Zone'): reason = 'Not speed/red-light enforcement'
            else:
                for n in (1, 2):
                    begin, end = [a.get(f'Deactivation_Period_{n}_{part}') for part in ('Begin', 'End')]
                    if begin and dt.datetime.strptime(begin, '%m/%d/%Y').date() <= now.date() and (not end or dt.datetime.strptime(end, '%m/%d/%Y').date() >= now.date()): reason = 'Deactivated'
                if not reason:
                    cs = [make_camera(source, a['Site_ID'], a['SPD_Camera_Name'] or a['School_Name'],
                        'redLight' if a['Camera_Type'] == 'Red Light' else 'speed',
                        a['Cam_Lat'], a['Cam_Long'], direction(a['SPD_Camera_Name']))]
        elif sid == 'arlington':
            if a['Active'] != 'Yes' or a.get('Retired'): reason = 'Not active / retired'
            elif not a.get('Installed') or a['Installed']/1000 > now.timestamp(): reason = 'Not installed yet'
            else:
                cs = [make_camera(source, a['ID'], f"{int(a['AddressNumber'])} {a['Street']} · {a['Direction']} · {a['School']}",
                    'speed', g['y'], g['x'], direction(a['Direction']), a.get('BeaconSpeedLimit'), conditional=True)]
        elif sid == 'tacoma':
            if a['cameratype'] not in ('Speed', 'Red Light', 'School Zones'): reason = 'Unsupported enforcement type'
            elif not a.get('location') or not a.get('address'): reason = 'Unidentified point; operational identity needs review'
            else:
                cs = [make_camera(source, a['location'], a['address'] + ' · ' + (a.get('direction_of_travel') or ''),
                    'redLight' if a['cameratype'] == 'Red Light' else 'speed', g['y'], g['x'],
                    direction(a.get('direction_of_travel')), a.get('speed_limit'), conditional=a['cameratype']=='School Zones')]
        elif sid == 'phoenix-points':
            label = a['description'].splitlines()[0]
            cs = [make_camera(source, label, label, 'possibleSpeed', a['latitude'], a['longitude'], direction(label))]
        elif sid == 'sf':
            status = (sf_status or {}).get(str(a['Id']))
            if not status: raise ValueError('SFMTA point absent from current operational table')
            if status[3] not in ('Issuing Violations', 'Issuing Warnings'): reason = 'Not operational'
            else:
                cs = [make_camera(source, a['Id'], status[1], 'speed', g['y'], g['x'], direction(status[1]), status[2])]
        else: raise ValueError('No adapter for source')
        cameras += cs
        if reason: skipped.append({'sourceRecord': str(a.get('ID', a.get('Id', a.get('OBJECTID', a.get('ObjectId', a.get('objectid', '')))))), 'reason': reason})
    if len({c['id'] for c in cameras}) != len(cameras): raise ValueError('Duplicate source identity')
    return sorted(cameras, key=lambda c: c['id']), skipped


def inside_ring(point, ring):
    x, y = point['longitude'], point['latitude']; inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax: inside = not inside
    return inside


def inside_geometry(point, geometry):
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return any(inside_ring(point, rings[0]) and not any(inside_ring(point, hole) for hole in rings[1:]) for rings in polygons)


def watch_value(source, raw):
    if source['adapter'] == 'document':
        if not raw.startswith(b'%PDF-'): raise ValueError('Expected a PDF, not an error/consent page')
        return {'contentHash': hashlib.sha256(raw).hexdigest()}
    page = parse_page(raw)
    if len(page.text) < source.get('minimumContentCharacters', 100) or source.get('requiredText', '').lower() not in page.text.lower(): raise ValueError('Missing expected page content')
    if source['adapter'] == 'abq-list':
        # Only the actual camera list matters: banners, menus and site chrome do not.
        html = raw.decode('utf-8', errors='replace')
        match = re.search(r'Camera locations\s*:?.*?<ol\b[^>]*>(.*?)</ol>', html, re.S | re.I)
        if not match: raise ValueError('City camera list structure changed')
        facts = [parse_page(part).text for part in re.findall(r'<li\b[^>]*>(.*?)</li>', match[1], re.S | re.I)]
        if len(facts) < 20 or any(not re.search(r'\((?:north|south|east|west)bound\)', f, re.I) for f in facts): raise ValueError('Incomplete city approach list')
        return {'contentHash': hashlib.sha256(encode(sorted(facts))).hexdigest(), 'items': sorted(facts)}
    # Hash prose instead of redistributing pages. Also catch changed linked maps/certificates.
    return {'contentHash': hashlib.sha256(encode([page.text, sorted(set(page.links))])).hexdigest(),
            'contentCharacters': len(page.text)}


def fetch_one(source, root, now):
    folder = 'Watch' if source.get('monitorOnly') else 'External'
    path = root / f"Data/{folder}/{source['id']}.json"; old = read(path)
    try:
        if source.get('monitorOnly'):
            value = watch_value(source, request(source['url']))
            current = {'id': source['id'], 'url': source['url'], 'checkedAt': stamp(now), **value}
            baseline = old.get('baseline', {k: old[k] for k in ('contentHash', 'items') if k in old}) if old else value
            current['baseline'] = baseline
            changed = value['contentHash'] != baseline['contentHash']
            detail = {'added': sorted(set(value.get('items', []))-set(baseline.get('items', []))),
                      'removed': sorted(set(baseline.get('items', []))-set(value.get('items', [])))}
        else:
            if source['adapter'] == 'text-locations':
                from text_camera_sources import rows as text_rows
                rows = text_rows(source, request(source['url']))
            elif source['adapter'] == 'socrata':
                rows = json_request(source['url'], **{'$limit': 50000})
                count = int(json_request(source['url'], **{'$select': 'count(*)'})[0]['count'])
                if len(rows) != count or count >= 50000: raise ValueError('Partial Socrata response')
            elif source['adapter'] == 'kml': rows = kml_rows(request(source['url']))
            else: rows = arcgis_rows(source['url'])
            if len(rows) < source['minimumRows'] or (old and len(rows) < old['rowCount']*.75): raise ValueError('Unexpected count drop; retaining last good source')
            status = None
            if source['adapter'] == 'sf':
                status = {r[0]: r for r in parse_page(request(source['page'])).rows if len(r) >= 4 and r[0].isdigit()}
                if len(status) != len(rows): raise ValueError('SFMTA operational table/map counts differ')
            if source['adapter'] == 'text-locations':
                from text_camera_sources import normalize as text_normalize
                cameras, skipped = text_normalize(source, rows, root, now)
            else:
                cameras, skipped = normalize(source, rows, now, status)
            if not cameras or (old and len(cameras) < len(old['cameras'])*.75):
                raise ValueError('Unexpected active camera drop; retaining last good source. ' + '; '.join(c['reason'] for c in skipped[:3]))
            region = next(f['geometry'] for f in read(root/'Data/Regions/metros.geojson')['features'] if f['properties']['GEOID'] == source['metro'])
            if any(not inside_geometry(c['geometry'][0], region) for c in cameras): raise ValueError('Camera outside declared Census metro')
            current = {'id': source['id'], 'url': source['url'], 'checkedAt': stamp(now), 'rowCount': len(rows),
                       'cameras': cameras, 'excluded': skipped}
            prior = {c['id']: c for c in (old or {}).get('cameras', [])}; fresh = {c['id']: c for c in cameras}
            detail = {'added': sorted(fresh.keys()-prior.keys()), 'removed': sorted(prior.keys()-fresh.keys()),
                      'changed': sorted(k for k in fresh.keys() & prior.keys() if fresh[k] != prior[k])}
            changed = bool(old and any(detail.values()))
        write(path, current)
        return {'id': source['id'], 'name': source['name'], 'url': source['url'], 'status': 'changed' if changed else 'ok',
            'checkedAt': stamp(now), 'records': len(current.get('cameras', [])), 'monitorOnly': bool(source.get('monitorOnly')),
            'reviewRequired': bool(changed and source.get('monitorOnly')), **detail}
    except Exception as error:
        return {'id': source['id'], 'name': source['name'], 'url': source['url'], 'status': 'failed',
            'attemptedAt': stamp(now), 'lastGoodAt': (old or {}).get('checkedAt'), 'error': str(error), 'reviewRequired': True}


def refresh(root=ROOT, now=None, only=None):
    now = now or dt.datetime.now(UTC)
    sources = read(root/'Data/source-registry.json')['sources']
    if only:
        if set(only) - {s['id'] for s in sources}: raise ValueError('Unknown source ID')
        sources = [s for s in sources if s['id'] in only]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(lambda s: fetch_one(s, root, now), [s for s in sources if s['adapter'] != 'text-locations']))
    checks += [fetch_one(s, root, now) for s in sources if s['adapter'] == 'text-locations']
    if only:
        prior = read(root/'Data/Review/source-watch.json', {}).get('checks', [])
        checks = [c for c in prior if c['id'] not in only] + checks
    return save_report(root, checks, now)

def save_report(root, checks, now):
    report = {'checkedAt': stamp(now), 'checks': checks, 'reviewRequired': [c['id'] for c in checks if c['reviewRequired']]}
    write(root/'Data/Review/source-watch.json', report)
    lines = ['# Source checks', '', f"Checked: {stamp(now)}", '', '| Source | Status | Records | Review |', '|---|---|---:|---|']
    for c in checks: lines.append(f"| [{c['name']}]({c['url']}) | {c['status']} | {c.get('records', '—')} | {'Required' if c['reviewRequired'] else '—'} |")
    lines += ['', 'Failed sources retain their last good data and original verification date. Changed pages remain pending until explicitly acknowledged after review. A successful page request does not verify every camera in the metro.', '']
    (root/'Data/Review/source-watch.md').write_text('\n'.join(lines))
    print(f"Checked {len(checks)} sources; {len(report['reviewRequired'])} require review.")
    for c in checks:
        if c['status'] == 'failed': print(f"::warning::{c['id']}: {c['error']}")
    return report


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=__import__('pathlib').Path, default=ROOT)
    parser.add_argument('--only', nargs='+'); parser.add_argument('--acknowledge', nargs='+')
    args = parser.parse_args()
    if args.acknowledge:
        for sid in args.acknowledge:
            if sid != slug(sid): raise ValueError('Invalid source ID')
            path = args.root/f'Data/Watch/{sid}.json'; value = read(path)
            if not value: raise ValueError('No successful source snapshot to acknowledge')
            value['baseline'] = {k: value[k] for k in ('contentHash', 'items') if k in value}
            write(path, value)
        report = read(args.root/'Data/Review/source-watch.json', {})
        for check in report.get('checks', []):
            if check['id'] in args.acknowledge and check['status'] == 'changed':
                check.update(status='ok', reviewRequired=False, added=[], removed=[], acknowledgedAt=stamp(dt.datetime.now(UTC)))
        if report: save_report(args.root, report['checks'], dt.datetime.now(UTC))
    else: refresh(args.root, only=args.only)


if __name__ == '__main__': main()
