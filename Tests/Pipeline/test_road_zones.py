import copy
import datetime as dt
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'Scripts'))
from road_zones import ZoneBuilder, validate_zone, projection, length, enrich_zones
from camera_data import read, write

NOW=dt.datetime(2026,9,27,tzinfo=dt.timezone.utc)

def point(y,x=-106):return {'latitude':y,'longitude':x}
def road(identifier='osm/way/1',ys=(35,35.01),nodes=(1,2),name='Main Street',**tags):
    return {'id':identifier,'source':'osm','geometry':[point(y) for y in ys],'nodes':list(nodes),'names':[name],
            'tags':{'highway':'primary','oneway':'yes',**tags},'checkedAt':'2026-09-21T00:00:00Z'}
def camera(**extra):
    return {'id':'any-city-1','label':'Main at Second','geometry':[point(35.006)],'travelBearing':0,'sourceIDs':['agency/1'],**extra}

class RoadZoneTests(unittest.TestCase):
    def test_generic_named_road_builds_bounded_directed_zone(self):
        zone,reason=ZoneBuilder([road()],NOW).build(camera())
        self.assertIsNone(reason);validate_zone(zone)
        self.assertAlmostEqual(zone['startMeters'],650,delta=3)
        self.assertLess(length(zone['geometry']),720)
    def test_nodes_not_coordinate_proximity_establish_connectivity(self):
        first=road(ys=(35.004,35.006),nodes=(10,11))
        disconnected=road('osm/way/2',ys=(34.999,35.004),nodes=(1,99),bridge='yes',layer='1')
        c=camera(geometry=[point(35.005)])
        self.assertIsNone(ZoneBuilder([first,disconnected],NOW).build(c)[0])
        connected={**disconnected,'nodes':[1,10]}
        self.assertIsNotNone(ZoneBuilder([first,connected],NOW).build(c)[0])
    def test_missing_direction_overdue_data_and_wrong_oneway_fall_back(self):
        self.assertIsNone(ZoneBuilder([road()],NOW).build(camera(travelBearing=None))[0])
        self.assertIsNotNone(ZoneBuilder([{**road(),'checkedAt':'2025-09-21T00:00:00Z'}],NOW).build(camera())[0])
        self.assertIsNone(ZoneBuilder([road(oneway='-1')],NOW).build(camera())[0])
    def test_ambiguous_parallel_monitored_roads_do_not_guess(self):
        other=road('osm/way/2',nodes=(3,4));other['geometry']=[point(35,-105.99995),point(35.01,-105.99995)]
        self.assertIsNone(ZoneBuilder([road(),other],NOW).build(camera())[0])
    def test_entire_camera_area_must_be_supported(self):
        c=camera(geometry=[point(35.001),point(35.009,-105.999)])
        self.assertIsNone(ZoneBuilder([road()],NOW).build(c)[0])
    def test_distinct_road_is_retained_as_competing_geometry(self):
        other=road('osm/way/2',nodes=(3,4),name='Service Road');other['geometry']=[point(35,-105.9998),point(35.01,-105.9998)]
        zone,_=ZoneBuilder([road(),other],NOW).build(camera())
        self.assertEqual(len(zone['alternatives']),1)
    def test_malformed_zone_rejected(self):
        zone,_=ZoneBuilder([road()],NOW).build(camera())
        for changes in [{'startMeters':-1},{'endMeters':999999},{'halfWidthMeters':200},{'sourceIDs':[]},
                        {'geometry':[point(35),point(35)]},{'endMeters':float('inf')}]:
            with self.assertRaises(AssertionError):validate_zone({**zone,**changes})
    def test_same_name_parallel_way_is_still_an_alternative(self):
        other=road('osm/way/2',nodes=(3,4));other['geometry']=[point(35,-105.9998),point(35.01,-105.9998)]
        zone,_=ZoneBuilder([road(),other],NOW).build(camera())
        self.assertEqual(len(zone['alternatives']),1)
    def test_projection_uses_distance_along_curve(self):
        line=[point(35),point(35.003),point(35.003,-105.997)]
        d,along,_=projection(line[-1],line)
        self.assertAlmostEqual(d,0,delta=.1);self.assertAlmostEqual(along,length(line),delta=.1)

    def test_points_and_areas_need_full_600_meter_approach(self):
        builder=ZoneBuilder([road()],NOW)
        for g in [[point(35.004)], [point(35.001),point(35.004)]]:
            zone,reason=builder.build(camera(geometry=g))
            self.assertIsNone(zone)
            self.assertIn('Insufficient mapped approach',reason)
        zone,_=builder.build(camera(geometry=[point(35.006),point(35.008)]))
        self.assertGreaterEqual(zone['startMeters'],600)

    def test_short_real_road_cannot_be_replaced_by_longer_parallel_road(self):
        short=road(ys=(35.004,35.008),nodes=(1,2))
        long=road('osm/way/2',nodes=(3,4))
        long['geometry']=[point(35,-105.99995),point(35.01,-105.99995)]
        zone,reason=ZoneBuilder([short,long],NOW).build(camera())
        self.assertIsNone(zone)
        self.assertEqual(reason,'Competing monitored-road paths')

    def test_overdue_geometry_keeps_original_evidence_dates(self):
        old='2025-09-21T00:00:00Z'
        zone,_=ZoneBuilder([{**road(),'checkedAt':old}],NOW).build(camera())
        self.assertEqual(zone['verifiedAt'],old)
        self.assertEqual(zone['validUntil'],'2025-10-21T00:00:00Z')
        self.assertIsNone(ZoneBuilder([{**road(),'checkedAt':'2027-01-01T00:00:00Z'}],NOW).build(camera())[0])

    def test_all_camera_kinds_use_shared_builder_outside_metro(self):
        with tempfile.TemporaryDirectory() as directory, patch('road_zones.load_roads',return_value=[road()]):
            root=pathlib.Path(directory)
            records=[camera(id=kind,kind=kind) for kind in ('speed','possibleSpeed','redLight','speedAndRedLight')]
            result=enrich_zones(root,records,NOW)
            self.assertTrue(all(c['roadZone']['startMeters']>=600 for c in result))
            report=read(root/'Data/Review/road-zone-coverage.json')
            self.assertEqual(report['eligible'],4)
            self.assertEqual(report['reviewed'],4)

    def test_failed_refresh_retains_zone_but_moved_camera_does_not(self):
        c=camera(kind='speed')
        zone,_=ZoneBuilder([road()],NOW).build(c)
        with tempfile.TemporaryDirectory() as directory, patch('road_zones.load_roads',return_value=[]):
            root=pathlib.Path(directory)
            write(root/'Data/Published/cameras.json',{'cameras':[{**c,'roadZone':zone}]})
            later=NOW+dt.timedelta(days=180)
            retained=enrich_zones(root,[c],later)[0]
            self.assertEqual(retained['roadZone'],zone)
            report=read(root/'Data/Review/road-zone-coverage.json')
            self.assertEqual(report['retained'],1)
            self.assertEqual(report['sourceChecksDue'],1)
            for changed in [{**c,'travelBearing':180},{**c,'geometry':[point(36)]}]:
                self.assertNotIn('roadZone',enrich_zones(root,[changed],later)[0])

if __name__=='__main__':unittest.main()
