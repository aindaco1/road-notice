"""Compact, optional road zones built from source-connected OSM ways.

The same evidence gates apply to every camera kind and region. Source age makes
geometry due for review; it does not remove a validated road constraint.
No driver locations or online requests are involved.
"""
import collections
import datetime as dt
import math

from camera_data import distance, read, stamp, write, UTC, valid_point, projection
from camera_identity import angle
from fetch_speed_limits import samples
from speed_limits import RoadIndex, camera_names, same_road, load_roads, numeric, mps


def approach_requirement(camera, road):
    """Plan geometry for the existing 15-second warning target, not Quiet.

    A school/conditional suppression bound must not shorten ordinary-road lead.
    Keep the full available path (up to 650 m) even when this minimum is smaller.
    """
    speeds=[]
    camera_limit=camera.get('speedLimit') or {}
    if camera_limit.get('basis')!='conservative-lower-bound' and not camera_limit.get('conditional'):
        value=numeric(camera_limit.get('value'),camera_limit.get('unit'))
        if value:speeds.append(mps(value))
    road_limit=road.get('limit') or {}
    for raw in road_limit.get('alternatives',[road_limit]):
        value=numeric(raw.get('value'),raw.get('unit'))
        if value:speeds.append(mps(value))
    if speeds:
        return {'meters':25*math.ceil(min(600,max(150,15*max(speeds)))/25),
                'basis':'15 seconds at the highest sourced camera/road limit, rounded up to 25 m'}
    return {'meters':600 if road['tags'].get('highway') in ('motorway','trunk') else 325,
            'basis':'Unknown speed: maximum lead on motorway/trunk; approximately 15 seconds at 45 mph elsewhere'}


def length(line): return sum(distance(a,b) for a,b in zip(line,line[1:]))


def clip(line,start,end):
    result=[];along=0
    for a,b in zip(line,line[1:]):
        size=distance(a,b)
        if size and along+size>=start and along<=end:
            for t in (max(0,(start-along)/size),min(1,(end-along)/size)):
                p={k:round(a[k]+t*(b[k]-a[k]),7) for k in ('latitude','longitude')}
                if not result or p!=result[-1]:result.append(p)
        along+=size
    return result


class ZoneBuilder:
    def __init__(self,roads,now):
        # Direct OSM retains shared-node connectivity and one-way semantics.
        self.roads=[r for r in roads if r['source']=='osm' and len(r['geometry'])>=2
                    and len(r['nodes'])==len(r['geometry'])
                    and r.get('checkedAt') and r['checkedAt']<=stamp(now)]
        self.index=RoadIndex(self.roads);self.ends=collections.defaultdict(list)
        for r in self.roads:
            self.ends[r['nodes'][0]].append((r,False))
            self.ends[r['nodes'][-1]].append((r,True))

    @staticmethod
    def oriented(road,reverse):
        tag=road['tags'].get('oneway')
        if (tag in ('yes','1') and reverse) or (tag=='-1' and not reverse):return None
        return (list(reversed(road['geometry'])),list(reversed(road['nodes']))) if reverse else (road['geometry'],road['nodes'])

    def path(self,seed,reverse,camera):
        geometry,nodes=self.oriented(seed,reverse);geometry=list(geometry);nodes=list(nodes)
        used={seed['id']};at=[seed['checkedAt']]
        extent=min(49000,length(camera['geometry'])+1500)
        for prepend in (True,False):
            added=0
            while added<extent:
                end=nodes[0] if prepend else nodes[-1];choices=[]
                for road,at_end in self.ends[end]:
                    if road['id'] in used:continue
                    if not any(same_road(a,b) for a in seed['names'] for b in road['names']):continue
                    oriented=self.oriented(road,not at_end if prepend else at_end)
                    if not oriented:continue
                    g,n=oriented
                    # A closed loop cannot be an entire upstream approach: its
                    # repeated junction makes nearest-segment direction ambiguous.
                    if set(n[:-1] if prepend else n[1:]).intersection(nodes):continue
                    heading=projection(g[-2] if prepend else g[1],g)[2]
                    current=projection(geometry[0] if prepend else geometry[-1],geometry)[2]
                    if angle(heading,current)<=60:choices.append((road,g,n))
                if len(choices)!=1:break  # A fork is evidence to stop, not guess.
                road,g,n=choices[0];used.add(road['id']);at.append(road['checkedAt']);added+=length(g)
                if prepend:geometry=g[:-1]+geometry;nodes=n[:-1]+nodes
                else:geometry+=g[1:];nodes+=n[1:]
        return geometry,used,min(at)

    def build(self,camera):
        bearing=camera.get('travelBearing')
        if bearing is None:return None,'Unknown monitored direction',None
        g=camera['geometry'];middle=g[len(g)//2];names=camera_names(camera)
        members=set(camera['sourceIDs']);device_nodes={int(x.rsplit('/',1)[1]) for x in members if x.startswith('osm/node/')}
        choices=[]
        for road in self.index.nearby(middle):
            if len(set(road['nodes']))!=len(road['nodes']):continue
            d,_,heading=projection(middle,road['geometry'])
            explicit=road['id'] in members or bool(device_nodes & set(road['nodes']))
            if d>25 or not (explicit or any(same_road(a,b) for a in names for b in road['names'])):continue
            reverse=angle(heading,bearing)>90
            if not self.oriented(road,reverse) or min(angle(heading,bearing),angle((heading+180)%360,bearing))>45:continue
            if not explicit and (road['tags'].get('bridge')=='yes' or road['tags'].get('tunnel')=='yes' or road['tags'].get('layer','0')!='0'):continue
            path,used,at=self.path(road,reverse,camera)
            checks=[projection(p,path) for p in samples(g,30)]
            if any(v[0]>25 for v in checks):continue
            lo=min(v[1] for v in checks);hi=max(v[1] for v in checks)
            start=max(0,lo-650);end=min(length(path),hi+60)
            path=clip(path,start,end)
            if not 2<=len(path)<=2000:continue
            choices.append((not explicit,d,path,used,at,lo-start,hi-start,road))
        choices.sort(key=lambda c:(c[0],c[1]))
        if not choices:return None,'No unambiguous connected approach geometry',None
        chosen=choices[0]
        if any(not chosen[3].intersection(c[3]) and c[1]-chosen[1]<10 for c in choices[1:]):
            return None,'Competing monitored-road paths',None
        _,_,path,used,at,lo,hi,seed=chosen
        required=approach_requirement(camera,seed)
        # Establish the correct road before checking lead length; a longer
        # neighboring road must not win merely because the real approach is short.
        if lo<required['meters']:return None,f"Insufficient mapped approach ({required['meters']} m required)",required
        # Include other ways even when their names match: frontage roads and
        # separate carriageways must not become proof of road membership.
        alternatives={}
        for point in samples(path,40):
            for road in self.index.nearby(point):
                if road['id'] in used:continue
                d,progress,_=projection(point,road['geometry'])
                if d>75:continue
                part=clip(road['geometry'],max(0,progress-120),progress+120)
                if len(part)>=2:
                    old=alternatives.get(road['id'])
                    alternatives[road['id']]=(road,min(old[1],progress-120) if old else progress-120,max(old[2],progress+120) if old else progress+120)
        if len(alternatives)>80:return None,'Too many competing roads for a bounded zone',required
        others=[]
        for road,start,end in sorted(alternatives.values(),key=lambda v:v[0]['id']):
            others.append({'geometry':clip(road['geometry'],max(0,start),end),
                           'oneWay':road['tags'].get('oneway') in ('yes','1','-1')})
            if road['tags'].get('oneway')=='-1':others[-1]['geometry'].reverse()
            at=min(at,road['checkedAt'])
        # Stacked roads can coincide throughout the approach. Require at least
        # one distinguishable position inside the planned warning lead; otherwise
        # the runtime cannot establish membership even with perfect GPS.
        clear=False
        for point in samples(clip(path,max(0,lo-required['meters']),lo),20):
            heading=projection(point,path)[2]
            ambiguous=False
            for other in others:
                d,_,bearing=projection(point,other['geometry'])
                difference=angle(heading,bearing) if other['oneWay'] else min(angle(heading,bearing),angle(heading,(bearing+180)%360))
                if d<=5 and difference<=60:ambiguous=True;break
            if not ambiguous:clear=True;break
        if not clear:return None,'No distinguishable approach among overlapping roads',required
        zone={'geometry':path,'startMeters':round(lo,2),'endMeters':round(hi,2),'halfWidthMeters':20,
              'alternatives':others,'sourceIDs':sorted(used|set(alternatives)),
              'verifiedAt':at,'validUntil':stamp(dt.datetime.fromisoformat(at.replace('Z','+00:00'))+dt.timedelta(days=30))}
        validate_zone(zone)
        return zone,None,required


def validate_zone(zone):
    def valid_line(g):
        return (2<=len(g)<=2000 and all(valid_point(p['latitude'],p['longitude']) for p in g)
                and 0<length(g)<50000)
    g=zone['geometry'];assert valid_line(g)
    assert math.isfinite(zone['startMeters']) and math.isfinite(zone['endMeters'])
    assert 0<=zone['startMeters']<=zone['endMeters']<=length(g)+1
    assert math.isfinite(zone['halfWidthMeters']) and 5<=zone['halfWidthMeters']<=40
    assert zone['sourceIDs'] and len(zone['alternatives'])<=80
    start=dt.datetime.fromisoformat(zone['verifiedAt'].replace('Z','+00:00'))
    end=dt.datetime.fromisoformat(zone['validUntil'].replace('Z','+00:00'))
    assert dt.timedelta(0)<end-start<=dt.timedelta(days=30)
    for road in zone['alternatives']:
        assert valid_line(road['geometry']) and isinstance(road['oneWay'],bool)


def enrich_zones(root,records,now):
    previous={c['id']:c for c in read(root/'Data/Published/cameras.json',{}).get('cameras',[])}
    builder=ZoneBuilder(load_roads(root,now),now);report=[];result=[]
    for camera in records:
        camera=dict(camera);camera.pop('roadZone',None)
        zone,reason,required=builder.build(camera)
        status='eligible' if zone else 'fallback'
        old=previous.get(camera['id'],{})
        # A failed/incomplete refresh must not reopen nearby-road warnings.
        # Camera moves/direction changes explicitly invalidate the old association.
        if not zone and old.get('roadZone') and all(camera.get(k)==old.get(k) for k in ('geometry','travelBearing')):
            validate_zone(old['roadZone'])
            zone=old['roadZone'];status='retained'
        if zone:camera['roadZone']=zone
        report.append({'id':camera['id'],'label':camera['label'],'kind':camera['kind'],
                       'status':status,'reason':reason,'vertices':len(zone['geometry']) if zone else 0,
                       'approachMeters':zone['startMeters'] if zone else None,
                       'requiredApproachMeters':required['meters'] if required else None,
                       'leadBasis':required['basis'] if required else None,
                       'sourceCheckDue':bool(zone and zone['validUntil']<=stamp(now))})
        result.append(camera)
    write(root/'Data/Review/road-zone-coverage.json',{'generatedAt':stamp(now),'scope':'All camera kinds and regions',
          'eligible':sum(r['status']!='fallback' for r in report),
          'generated':sum(r['status']=='eligible' for r in report),
          'retained':sum(r['status']=='retained' for r in report),
          'sourceChecksDue':sum(r['sourceCheckDue'] for r in report),
          'approachPolicy':'15 seconds at sourced approach speed, 150–600 m; retain up to 650 m of available geometry',
          'reviewed':len(report),'totalCameras':len(records),'records':report})
    return result
