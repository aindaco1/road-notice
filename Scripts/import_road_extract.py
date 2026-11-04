#!/usr/bin/env python3
"""Fill missing road caches from checksum-verified, current Geofabrik PBFs.

Optional dependencies are in requirements-data.txt. This imports public OSM
facts into the existing cache format; the publisher and matcher are unchanged.
"""
import argparse
import datetime as dt
import hashlib
import pathlib

from camera_data import ROOT, UTC, ROAD_TYPES, read, write, stamp, encode
from fetch_speed_limits import road_requests, directional_request_members, road_bounds


def import_extracts(root, index, extracts, now=None):
    import osmium
    from osmium.replication import get_replication_header
    from shapely.geometry import shape, box, LineString
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    now=now or dt.datetime.now(UTC)
    features={f['properties']['id']:f for f in index['features']}
    sources=[];polygons=[]
    for region,path in extracts:
        feature=features[region];url=feature['properties']['urls']['pbf']
        expected=path.with_name(path.name+'.md5').read_text().split()[0]
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'md5').hexdigest()
        if actual!=expected:raise ValueError('Extract checksum mismatch: '+region)
        at=get_replication_header(str(path)).timestamp
        if at is None or not dt.timedelta(0)<=now-at<=dt.timedelta(days=2):
            raise ValueError('Extract replication date is missing, future or more than two days old')
        polygon=shape(feature['geometry'])
        if polygon.is_empty or not polygon.is_valid:raise ValueError('Invalid extract clipping polygon')
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        sources.append({'region':region,'url':url,'checkedAt':stamp(at),'sha256':digest,
                        'clipSHA256':hashlib.sha256(encode(feature['geometry'])).hexdigest()})
        polygons.append(polygon)
    # Adjacent extracts must describe the same OSM state before they can jointly
    # certify a border-spanning query envelope.
    dates={s['checkedAt'] for s in sources}
    if len(dates)!=1:raise ValueError('Combined extracts must have the same replication timestamp')
    coverage=unary_union(polygons)
    cameras=read(root/'Data/Published/cameras.json')['cameras']
    requests=road_requests(cameras);members=directional_request_members(cameras,requests)
    selected=[];rectangles=[]
    for name,points in requests:
        if not members[name] or read(root/f'Data/SpeedLimits/{name}.json',{}).get('checkedAt'):continue
        south,west,north,east=road_bounds(points);rectangle=box(west,south,east,north)
        # The stable query contract is every original 750 m camera envelope,
        # not the empty corners between far-apart points in a batch's box.
        def envelope(point):
            s,w,n,e=road_bounds([point]);return box(w,s,e,n)
        if all(coverage.covers(envelope(point)) for point in points):
            selected.append((name,[south,west,north,east],points));rectangles.append(rectangle)
    if not selected:return []
    tree=STRtree(rectangles);rows=[{} for _ in selected]

    class Roads(osmium.SimpleHandler):
        def way(self,way):
            if way.tags.get('highway') not in ROAD_TYPES:return
            geometry=[{'lat':node.lat,'lon':node.lon} for node in way.nodes]
            if len(geometry)<2:raise ValueError('Incomplete road geometry in extract')
            matches=tree.query(LineString([(p['lon'],p['lat']) for p in geometry]),predicate='intersects')
            if not len(matches):return
            value={'type':'way','id':way.id,'version':way.version,'timestamp':stamp(way.timestamp),
                   'nodes':[node.ref for node in way.nodes],'geometry':geometry,'tags':dict(way.tags)}
            for i in matches:
                old=rows[i].get(way.id)
                if old is not None and old!=value:raise ValueError('Conflicting way in same-date extracts')
                rows[i][way.id]=value

    handler=Roads()
    for _,path in extracts:handler.apply_file(str(path),locations=True)
    # No cache is activated until every input has parsed successfully, including
    # all referenced nodes. Full ways are retained even when their nodes lie
    # outside a query box; crossing segments count as road evidence.
    imported=[]
    for (name,bounds,points),ways in zip(selected,rows):
        path=root/f'Data/SpeedLimits/{name}.json'
        if read(path,{}).get('checkedAt'):continue  # A concurrent API pass won.
        if not ways:raise ValueError('Unexpected empty road extract: '+name)
        involved=[s for s,p in zip(sources,polygons) if p.intersects(box(bounds[1],bounds[0],bounds[3],bounds[2]))]
        value={'generator':'Road Notice OSM regional extract',
               'osm3s':{'timestamp_osm_base':next(iter(dates))},'checkedAt':next(iter(dates)),
               'sourceURL':involved[0]['url'],'extracts':involved,
               'queryPoints':points,'queryRadiusMeters':750,
               'recordCount':len(ways),'elements':[ways[k] for k in sorted(ways)]}
        write(path,value,compact=True);imported.append(name)
        print(name,'imported',len(ways),flush=True)
    return imported


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=pathlib.Path,required=True,help='Downloaded Geofabrik index-v1.json')
    parser.add_argument('--extract',action='append',required=True,help='REGION_ID=PATH; adjacent .md5 file required')
    args=parser.parse_args()
    extracts=[(region,pathlib.Path(path)) for region,path in (value.split('=',1) for value in args.extract)]
    import_extracts(ROOT,read(args.index),extracts)
