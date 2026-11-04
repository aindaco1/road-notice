import pathlib
import sys
import tempfile
import unittest
import datetime as dt
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'Scripts'))
from camera_data import write, read
from fetch_speed_limits import active_osm_shards, road_requests, refresh


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
                fetch.assert_called_once_with(expected)
            self.assertEqual(report['activeOSMShards'],['osm-roads-a','osm-roads-b'])


if __name__ == '__main__':
    unittest.main()
