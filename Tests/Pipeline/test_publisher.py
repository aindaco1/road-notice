import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'Scripts'))
import csv, math, copy, datetime as dt, hashlib, importlib.util, json, pathlib, tempfile, unittest
spec = importlib.util.spec_from_file_location('publisher', pathlib.Path(__file__).resolve().parents[2] / 'Scripts/publish_cameras.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
NOW = dt.datetime(2026, 9, 14, 7, tzinfo=dt.timezone.utc)

def node(n=1, **tags):
    return {'type':'node','id':n,'lat':40.0,'lon':-105.0,'tags':tags or {'highway':'speed_camera'}}
def document(elements):
    return {'elements':elements,'osm3s':{'timestamp_osm_base':'2026-09-14T01:00:00Z'}}
def camera():
    return next(iter(p.osm_records([document([node()])])[0].values()))

class PublisherTests(unittest.TestCase):
    def test_device_identity_survives_relation_addition_and_skeleton(self):
        relation = {'type':'relation','id':5,'tags':{'enforcement':'maxspeed'},'members':[{'type':'node','ref':1,'role':'device'}]}
        records, _ = p.osm_records([document([node()]),document([{'type':'node','id':1,'lat':40.,'lon':-105.},relation])])
        self.assertEqual(list(records), ['osm-node-1']); self.assertEqual(len(records['osm-node-1']['sourceIDs']), 2)
    def test_lens_direction_is_never_used_as_vehicle_direction(self):
        records, _ = p.osm_records([document([node(highway='speed_camera',direction='270')])])
        self.assertNotIn('travelBearing', records['osm-node-1'])
    def test_combined_device_does_not_become_two_alerts(self):
        records, _ = p.osm_records([document([node(highway='speed_camera',enforcement='traffic_signals')])])
        self.assertEqual(len(records), 1); self.assertEqual(records['osm-node-1']['kind'], 'speedAndRedLight')
    def test_close_opposite_approaches_are_not_merged(self):
        a=camera(); b={**a,'id':'other','travelBearing':180}
        records, _, issues = p.reconcile({a['id']:a,b['id']:b},{},{},{},NOW)
        self.assertEqual(len(records),2); self.assertTrue(issues)
    def test_failed_and_mass_drop_fetch_are_rejected(self):
        with self.assertRaises(ValueError): p.valid_source({'remark':'timeout','elements':[node()]})
        with self.assertRaises(ValueError): p.valid_source(document([node()]),document([node(i) for i in range(100)]))
    def test_absence_requires_review_and_tombstone_prevents_resurrection(self):
        a=camera(); old={'cameras':[a]}
        records,state,_=p.reconcile({}, {}, old, {}, NOW)
        self.assertEqual(records,[a]); self.assertEqual(state['missing'][a['id']],1)
        _,state,_=p.reconcile({}, {}, old, state, NOW,complete=False)
        self.assertEqual(state['missing'][a['id']],1)
        records,_,_=p.reconcile({a['id']:a},{'tombstones':{a['id']:'Official removal'}},old,state,NOW)
        self.assertEqual(records,[])
    def test_expired_mobile_is_removed_even_when_source_returns_it(self):
        a={**camera(),'kind':'possibleSpeed','validUntil':'2026-09-13T00:00:00Z'}
        records,_,_=p.reconcile({a['id']:a},{},{},{},NOW); self.assertEqual(records,[])
    def test_metro_requires_reviewed_geometry(self):
        a=camera()
        records,_,_=p.reconcile({a['id']:a},{'reviewBounds':[39,-106,41,-104]},{},{},NOW)
        self.assertEqual(records,[])
    def test_denver_week_boundary_handles_dst(self):
        self.assertEqual(p.week(dt.datetime.fromisoformat('2026-03-09T05:59:00+00:00')),'2026-03-02')
        self.assertEqual(p.week(dt.datetime.fromisoformat('2026-03-09T06:00:00+00:00')),'2026-03-09')
        self.assertEqual(p.week(dt.datetime.fromisoformat('2026-11-02T07:00:00+00:00')),'2026-11-02')
    def test_all_city_inventory_approaches_are_published_with_their_direction(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        with (root/'Data/Review/official-location-register.csv').open() as file:
            listed = {r['research_id']: r for r in csv.DictReader(file) if r['jurisdiction'] == 'Albuquerque'}
        accepted = [c for c in p.read(root/'Data/Overrides/metro.json')['cameras'] if c['id'].startswith('abq-')]
        published = {c['id']: c for c in p.read(root/'Data/Published/cameras.json')['cameras']}
        references = [c['reviewReference'] for c in accepted]
        self.assertEqual(set(references), set(listed))
        self.assertEqual(len(references), len(set(references)))
        for camera in accepted:
            self.assertEqual({k: published[camera['id']][k] for k in camera if k != 'replaces'}, {k: v for k, v in camera.items() if k != 'replaces'})
            self.assertEqual(camera['travelBearing'], {'NB': 0, 'EB': 90, 'SB': 180, 'WB': 270}[listed[camera['reviewReference']]['travel_direction']])
            if camera['kind'] == 'possibleSpeed':
                self.assertIn('approximate area', camera['label'])
                self.assertGreater(len(camera['geometry']), 1)

    def test_accepted_city_area_segments_follow_referenced_osm_road_edges(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        review = p.read(root/'Data/Review/albuquerque-road-areas.json')
        elements = {(e['type'], e['id']): e for e in review['elements']}
        accepted = {c['id']: c for c in p.read(root/'Data/Overrides/metro.json')['cameras']}
        def on_edge(point, a, b):
            scale = math.cos(math.radians(point['latitude']))
            ax, ay = (a['lon']-point['longitude'])*scale*111195, (a['lat']-point['latitude'])*111195
            bx, by = (b['lon']-point['longitude'])*scale*111195, (b['lat']-point['latitude'])*111195
            dx, dy = bx-ax, by-ay
            length2 = dx*dx+dy*dy
            t = max(0, min(1, -(ax*dx+ay*dy)/length2)) if length2 else 0
            return math.hypot(ax+t*dx, ay+t*dy) < .25
        for area in review['areas']:
            if accepted[area['id']].get('positionPrecision') == 'reviewed-osm-device':
                self.assertTrue(any(item['acceptedID'] == area['id'] for item in p.read(root/'Data/Review/metro-point-reconciliation.json')['points']))
                continue
            self.assertEqual(accepted[area['id']]['geometry'], area['geometry'])
            edges = [(elements[('node', a)], elements[('node', b)]) for wid in area['wayIDs']
                     for a, b in zip(elements[('way', wid)]['nodes'], elements[('way', wid)]['nodes'][1:])]
            for a, b in zip(area['geometry'], area['geometry'][1:]):
                self.assertTrue(any(on_edge(a, x, y) and on_edge(b, x, y) for x, y in edges), area['id'])

    def test_coors_field_verification_keeps_geometry_and_direction(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        current = p.read(root/'Data/Published/cameras.json')
        previous = p.read(root/'Data/Published/cameras-2026-09-21-dc315dfa720e-79004776.json')
        old = {c['id']: c for c in previous['cameras']}
        field_verified = {c['id']: c for c in p.read(root/'Data/Published/cameras-2026-09-28-f7d23a339024-c8ba0cd7.json')['cameras']}
        for suffix, bearing in [('nb',0),('sb',180)]:
            identifier='abq-coors-st-joseph-possible-'+suffix
            c=next(c for c in current['cameras'] if c['id']==identifier)
            self.assertEqual(c['kind'],'speed')
            self.assertEqual(c['travelBearing'],bearing)
            self.assertEqual(c['geometry'],old[identifier]['geometry'])
            # The field edit must preserve its original zone. Weekly road-source
            # refreshes may regenerate current zones without moving the camera.
            self.assertEqual(field_verified[identifier]['roadZone'],old[identifier]['roadZone'])
            p.validate_zone(c['roadZone'])
            self.assertEqual(c['speedLimit']['value'],45)
            self.assertEqual(c['speedLimit']['unit'],'mph')
            self.assertEqual(c['speedLimit']['verifiedAt'],'2026-10-01T06:00:00Z')
            self.assertEqual(c['speedLimit']['basis'],'field-verified')
        p.validate(current['cameras'])

    def test_publication_is_immutable_and_checksum_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            for name in p.QUERIES: p.write(root/f'Data/Sources/osm-us-{name}.json',document([node()]))
            first=p.publish(root,NOW); second=p.publish(root,NOW+dt.timedelta(hours=1))
            self.assertEqual(first,second)
            manifest=p.read(root/'Data/Published/manifest.json')
            raw=(root/'Data/Published'/manifest['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['sha256'])
            failed=p.publish(root,NOW+dt.timedelta(days=7),[{'source':'speed','status':'retained'}])
            self.assertEqual(first,failed)
            self.assertEqual(manifest,p.read(root/'Data/Published/manifest.json'))

if __name__ == '__main__': unittest.main()
