import pathlib
import sys
import tempfile
import unittest
import datetime as dt
import json
import urllib.error
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'Scripts'))
from camera_data import write, read
from fetch_speed_limits import active_osm_shards, road_requests, road_bounds, directional_request_members, directional_coverage, osm_roads, refresh


class RoadSourceRetentionTests(unittest.TestCase):
    def test_partial_replacement_keeps_previous_set_without_renewing_its_dates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            old = root / 'Data/SpeedLimits/osm-roads-old.json'
            write(old, {'checkedAt': '2026-09-15T00:00:00Z', 'elements': []})
            write(root / 'Data/SpeedLimits/osm-roads-new-a.json',
                  {'checkedAt': '2026-09-28T00:00:00Z', 'elements': []})
            previous = {'activeOSMShards': ['osm-roads-old']}
            requested = ['osm-roads-new-a', 'osm-roads-new-b']
            self.assertEqual(active_osm_shards(root, requested, previous), ['osm-roads-new-a','osm-roads-old'])
            self.assertEqual(read(old)['checkedAt'], '2026-09-15T00:00:00Z')
            write(root / 'Data/SpeedLimits/osm-roads-new-b.json',
                  {'checkedAt': '2026-09-28T00:00:00Z', 'elements': []})
            self.assertEqual(active_osm_shards(root, requested, previous), requested)

    def test_first_fetch_does_not_activate_unrelated_historical_caches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            write(root / 'Data/SpeedLimits/osm-roads-unrelated.json',
                  {'checkedAt': '2026-09-28T00:00:00Z', 'elements': []})
            self.assertEqual(active_osm_shards(root, ['osm-roads-requested'], {}), ['osm-roads-requested'])

    def test_queries_cover_all_kinds_and_changes_stay_regional(self):
        cameras=[{'kind':kind,'geometry':[{'latitude':35+i,'longitude':-106}]}
                 for i,kind in enumerate(['speed','possibleSpeed','redLight','speedAndRedLight'])]
        original=road_requests(cameras)
        self.assertEqual(len(original),4)
        self.assertEqual({p['latitude'] for _,ps in original for p in ps},{35,36,37,38})
        added=road_requests(cameras+[{'kind':'redLight','geometry':[{'latitude':40,'longitude':-110}]}])
        self.assertTrue(set(name for name,_ in original).issubset(name for name,_ in added))

    def test_batch_box_contains_every_required_camera_envelope(self):
        import math
        # Include high-latitude US roads: longitude padding must grow northward.
        for latitude in (20,35,50,70):
            points=[{'latitude':latitude,'longitude':-106},
                    {'latitude':latitude+.2,'longitude':-105.8}]
            south,west,north,east=road_bounds(points)
            for p in points:
                # Spherical destination points on the entire 750 m circle.
                lat,lon=map(math.radians,(p['latitude'],p['longitude']))
                radius=750/6_371_000
                for degrees in range(0,360,10):
                    bearing=math.radians(degrees)
                    y=math.asin(math.sin(lat)*math.cos(radius)+math.cos(lat)*math.sin(radius)*math.cos(bearing))
                    x=lon+math.atan2(math.sin(bearing)*math.sin(radius)*math.cos(lat),math.cos(radius)-math.sin(lat)*math.sin(y))
                    self.assertLess(south,math.degrees(y));self.assertLess(math.degrees(y),north)
                    self.assertLess(west,math.degrees(x));self.assertLess(math.degrees(x),east)

    def test_next_budget_fetches_unattempted_region_instead_of_repeating_first(self):
        now=dt.datetime(2026,11,3,tzinfo=dt.timezone.utc)
        requests=[('osm-roads-a',[{'latitude':35,'longitude':-106}]),
                  ('osm-roads-b',[{'latitude':40,'longitude':-110}])]
        with tempfile.TemporaryDirectory() as temporary, patch('fetch_speed_limits.road_requests',return_value=requests), patch('fetch_speed_limits.time.sleep'):
            root=pathlib.Path(temporary)
            for day,expected in [(0,requests[0][1]),(7,requests[1][1])]:
                date=now+dt.timedelta(days=day)
                value={'osm3s':{'timestamp_osm_base':date.isoformat().replace('+00:00','Z')},'elements':[]}
                with patch('fetch_speed_limits.time.monotonic',side_effect=[0,0,1]), patch('fetch_speed_limits.osm_roads',return_value=value) as fetch:
                    report=refresh(root,now=date,osm_only=True,budget=0)
                fetch.assert_called_once_with(expected,root/'work/road-query-cache',0)
            self.assertEqual(report['activeOSMShards'],['osm-roads-a','osm-roads-b'])

    def test_directional_acquisition_covers_every_area_sample_and_keeps_query_hashes(self):
        cameras=[{'id':'area','travelBearing':0,'geometry':[{'latitude':35,'longitude':-106},{'latitude':35.3,'longitude':-106}]},
                 {'id':'red-light','travelBearing':180,'geometry':[{'latitude':36,'longitude':-106}]},
                 {'id':'unknown','geometry':[{'latitude':40,'longitude':-110}]}]
        requests=road_requests(cameras)
        members=directional_request_members(cameras,requests)
        self.assertEqual(set(members),{name for name,_ in requests})
        self.assertEqual(set().union(*map(set,members.values())),{'area','red-light'})
        self.assertTrue(any(not ids for ids in members.values()))
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary)
            before=directional_coverage(root,cameras,members)
            self.assertEqual(before['candidates'],2)
            self.assertEqual(before['complete'],0)
            for name,ids in members.items():
                if ids:write(root/f'Data/SpeedLimits/{name}.json',{'checkedAt':'2026-11-03T00:00:00Z','elements':[]})
            after=directional_coverage(root,cameras,members)
            self.assertEqual(after['complete'],2)
            self.assertTrue(all(not r['pendingShards'] for r in after['records']))
            area=next(r for r in after['records'] if r['id']=='area')
            self.assertGreater(len(area['shards']),1)
            (root/f"Data/SpeedLimits/{area['shards'][0]}.json").unlink()
            self.assertEqual(directional_coverage(root,cameras,members)['complete'],1)

    def test_directional_pass_skips_unknown_only_queries_without_replacing_full_source_set(self):
        cameras=[{'id':'known','travelBearing':0,'geometry':[{'latitude':35,'longitude':-106}]},
                 {'id':'unknown','geometry':[{'latitude':40,'longitude':-110}]}]
        with tempfile.TemporaryDirectory() as temporary, patch('fetch_speed_limits.time.sleep'), patch('fetch_speed_limits.osm_roads',return_value={'elements':[]}) as fetch:
            root=pathlib.Path(temporary)
            write(root/'Data/Published/cameras.json',{'cameras':cameras})
            write(root/'Data/Review/speed-limit-fetch.json',{'activeOSMShards':['osm-roads-prior']})
            report=refresh(root,osm_only=True,directional_only=True)
            fetch.assert_called_once()
            self.assertEqual(len(report['requestedOSMShards']),2)
            self.assertIn('osm-roads-prior',report['activeOSMShards'])
            self.assertEqual(report['directionalCoverage']['complete'],1)
            skipped=next(c for c in report['checks'] if c['status']=='not_requested')
            self.assertNotIn('error',skipped)
            self.assertNotIn('attemptedAt',skipped)

    def test_narrower_road_query_compares_matching_classes_before_drop_guard(self):
        cameras=[{'id':'known','travelBearing':0,'geometry':[{'latitude':35,'longitude':-106}]}]
        name,_=road_requests(cameras)[0]
        road={'tags':{'highway':'primary'}}
        old={'checkedAt':'2026-09-01T00:00:00Z','recordCount':14,
             'elements':[road]*4+[{'tags':{'highway':'footway'}}]*10}
        for remaining,expected in [(3,'downloaded'),(2,'retained')]:
            with tempfile.TemporaryDirectory() as temporary, patch('fetch_speed_limits.time.sleep'), patch('fetch_speed_limits.osm_roads',return_value={'elements':[road]*remaining}):
                root=pathlib.Path(temporary)
                write(root/'Data/Published/cameras.json',{'cameras':cameras})
                path=root/f'Data/SpeedLimits/{name}.json';write(path,old)
                report=refresh(root,osm_only=True,directional_only=True,force=True)
                check=next(c for c in report['checks'] if c['id']==name)
                self.assertEqual(check['status'],expected)
                if expected=='retained':self.assertEqual(read(path),old)

    def test_busy_batch_splits_but_requires_every_response_and_respects_rate_limits(self):
        points=[{'latitude':35+i/1000,'longitude':-106} for i in range(10)]
        at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        def response(date):
            return json.dumps({'osm3s':{'timestamp_osm_base':date.isoformat().replace('+00:00','Z')},
                               'elements':[{'id':1,'type':'way','tags':{'highway':'primary','name':date.isoformat()},'nodes':[1,2],
                                            'geometry':[{'lat':35,'lon':-106},{'lat':35.01,'lon':-106}]}]}).encode()
        busy=urllib.error.HTTPError('https://example.test',502,'Busy',None,None)
        limited=urllib.error.HTTPError('https://example.test',429,'Rate limited',None,None)
        with patch('fetch_speed_limits.time.sleep'), patch('fetch_speed_limits.get',side_effect=[busy,response(at),response(at-dt.timedelta(minutes=1))]) as get:
            result=osm_roads(points)
            self.assertEqual(len(result['elements']),1)
            self.assertEqual(result['elements'][0]['tags']['name'],at.isoformat())
            self.assertEqual(result['osm3s']['timestamp_osm_base'],(at-dt.timedelta(minutes=1)).isoformat().replace('+00:00','Z'))
            self.assertEqual(get.call_count,3)
        for responses in ([busy,response(at),limited],[limited]):
            with patch('fetch_speed_limits.time.sleep'), patch('fetch_speed_limits.get',side_effect=responses) as get:
                with self.assertRaises(urllib.error.HTTPError):osm_roads(points)
                self.assertEqual(get.call_count,len(responses))
        # A later failure preserves successful chunks for the next pass,
        # without making the parent batch available or refreshing source dates.
        with tempfile.TemporaryDirectory() as temporary, patch('fetch_speed_limits.time.sleep'):
            folder=pathlib.Path(temporary)
            with patch('fetch_speed_limits.get',side_effect=[busy,response(at),limited]):
                with self.assertRaises(urllib.error.HTTPError):osm_roads(points,folder)
            self.assertEqual(len(list(folder.glob('*.json'))),1)
            with patch('fetch_speed_limits.get',side_effect=[busy,response(at-dt.timedelta(minutes=1))]) as get:
                result=osm_roads(points,folder)
                self.assertEqual(get.call_count,2)
                self.assertEqual(result['osm3s']['timestamp_osm_base'],(at-dt.timedelta(minutes=1)).isoformat().replace('+00:00','Z'))
        busy.close();limited.close()

    def test_split_retries_stop_at_the_shared_run_deadline(self):
        points=[{'latitude':35+i/1000,'longitude':-106} for i in range(10)]
        busy=urllib.error.HTTPError('https://example.test',502,'Busy',None,None)
        with patch('fetch_speed_limits.time.sleep'), patch('fetch_speed_limits.time.monotonic',side_effect=[0,11]), patch('fetch_speed_limits.get',side_effect=busy) as get:
            with self.assertRaisesRegex(TimeoutError,'time budget reached'):
                osm_roads(points,deadline=10)
            get.assert_called_once()
        busy.close()

    def test_incomplete_way_geometry_cannot_count_as_acquired(self):
        base=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
        way={'id':1,'type':'way','nodes':[1,2,3],
             'geometry':[{'lat':35,'lon':-106},{'lat':35.01,'lon':-106}]}
        value={'osm3s':{'timestamp_osm_base':base},'elements':[way]}
        with patch('fetch_speed_limits.get',return_value=json.dumps(value).encode()):
            with self.assertRaisesRegex(ValueError,'Invalid road geometry'):
                osm_roads([{'latitude':35,'longitude':-106}])

    def test_invalid_replica_date_cannot_count_as_acquired(self):
        now=dt.datetime.now(dt.timezone.utc)
        for date in (None,now-dt.timedelta(days=3),now+dt.timedelta(hours=1)):
            value={'osm3s':{'timestamp_osm_base':date.isoformat() if date else None},'elements':[]}
            with patch('fetch_speed_limits.get',return_value=json.dumps(value).encode()):
                with self.assertRaisesRegex(ValueError,'replica date'):
                    osm_roads([{'latitude':35,'longitude':-106}])


if __name__ == '__main__':
    unittest.main()
