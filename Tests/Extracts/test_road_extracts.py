import datetime as dt
import hashlib
import pathlib
import sys
import tempfile
import unittest

import osmium

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'Scripts'))
from camera_data import read, write
from fetch_speed_limits import road_requests
from import_road_extract import import_extracts

NOW=dt.datetime(2026,11,3,13,tzinfo=dt.timezone.utc)
AT=NOW-dt.timedelta(hours=1)
CAMERA={'id':'test','travelBearing':90,'geometry':[{'latitude':35,'longitude':-106}]}


def fixture(root,region='test',bounds=(-107,34,-105,36),at=AT):
    path=root/(region+'.osm.pbf');header=osmium.io.Header()
    if at:header.set('osmosis_replication_timestamp',at.isoformat().replace('+00:00','Z'))
    writer=osmium.SimpleWriter(path,header=header)
    for identifier,lon,lat in [(1,-106.02,35),(2,-105.98,35),(3,-106,34.98),(4,-106,35.02)]:
        writer.add_node(osmium.osm.mutable.Node(id=identifier,location=(lon,lat),version=1,timestamp=AT))
    writer.add_way(osmium.osm.mutable.Way(id=100,nodes=[1,2],version=1,timestamp=AT,
                   tags={'highway':'primary','name':'Main Street','oneway':'-1','maxspeed':'45 mph'}))
    writer.add_way(osmium.osm.mutable.Way(id=101,nodes=[3,4],version=1,timestamp=AT,tags={'highway':'footway'}))
    writer.close()
    path.with_name(path.name+'.md5').write_text(hashlib.md5(path.read_bytes()).hexdigest()+'  '+path.name)
    w,s,e,n=bounds
    feature={'properties':{'id':region,'urls':{'pbf':'https://download.geofabrik.de/'+path.name}},
             'geometry':{'type':'Polygon','coordinates':[[[w,s],[e,s],[e,n],[w,n],[w,s]]]}}
    write(root/'Data/Published/cameras.json',{'cameras':[CAMERA]})
    return feature,(region,path)


class RoadExtractTests(unittest.TestCase):
    def test_crossing_way_keeps_full_geometry_shared_nodes_direction_and_dates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary);feature,source=fixture(root)
            names=import_extracts(root,{'features':[feature]},[source],now=NOW)
            self.assertEqual(names,[road_requests([CAMERA])[0][0]])
            cache=read(root/f'Data/SpeedLimits/{names[0]}.json')
            self.assertEqual(cache['recordCount'],1)
            way=cache['elements'][0]
            self.assertEqual(way['nodes'],[1,2])
            self.assertEqual(way['geometry'],[{'lat':35,'lon':-106.02},{'lat':35,'lon':-105.98}])
            self.assertEqual(way['tags']['oneway'],'-1')
            self.assertEqual(cache['checkedAt'],'2026-11-03T12:00:00Z')
            before=(root/f'Data/SpeedLimits/{names[0]}.json').read_bytes()
            self.assertEqual(import_extracts(root,{'features':[feature]},[source],now=NOW),[])
            self.assertEqual((root/f'Data/SpeedLimits/{names[0]}.json').read_bytes(),before)

    def test_checksum_failure_does_not_activate_a_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary);feature,source=fixture(root)
            with source[1].open('ab') as stream:stream.write(b'corrupt')
            with self.assertRaisesRegex(ValueError,'checksum'):
                import_extracts(root,{'features':[feature]},[source],now=NOW)
            self.assertFalse((root/'Data/SpeedLimits').exists())

    def test_stale_future_or_missing_replication_dates_are_rejected(self):
        for at in [NOW-dt.timedelta(days=3),NOW+dt.timedelta(hours=1),None]:
            with tempfile.TemporaryDirectory() as temporary:
                root=pathlib.Path(temporary);feature,source=fixture(root,at=at)
                with self.assertRaisesRegex(ValueError,'replication date'):
                    import_extracts(root,{'features':[feature]},[source],now=NOW)
                self.assertFalse((root/'Data/SpeedLimits').exists())

    def test_complete_way_does_not_certify_missing_neighboring_road_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary)
            left,one=fixture(root,'left',(-107,34,-106,36))
            right,two=fixture(root,'right',(-106,34,-105,36))
            index={'features':[left,right]}
            self.assertEqual(import_extracts(root,index,[one],now=NOW),[])
            names=import_extracts(root,index,[one,two],now=NOW)
            self.assertEqual(len(names),1)
            cache=read(root/f'Data/SpeedLimits/{names[0]}.json')
            self.assertEqual(cache['recordCount'],1)
            self.assertEqual(len(cache['extracts']),2)

    def test_border_extracts_must_share_a_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=pathlib.Path(temporary)
            left,one=fixture(root,'left',(-107,34,-106,36))
            right,two=fixture(root,'right',(-106,34,-105,36),at=AT-dt.timedelta(hours=1))
            with self.assertRaisesRegex(ValueError,'same replication timestamp'):
                import_extracts(root,{'features':[left,right]},[one,two],now=NOW)
            self.assertFalse((root/'Data/SpeedLimits').exists())


if __name__=='__main__':unittest.main()
