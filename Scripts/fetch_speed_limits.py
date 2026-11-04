#!/usr/bin/env python3
"""Bounded, cached public road/limit acquisition before weekly publication.

Only public camera coordinates are queried. No user/device location is involved.
Failed/partial responses preserve original checkedAt and last successful evidence.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
import urllib.error

from camera_data import ROOT, UTC, read, write, stamp, encode, distance, valid_point
from source_watch import parse_page, USER_AGENT

# The public FOSSGIS service supplied fresh complete Coors geometry on November 3.
# Keep bounded queries/backoff and validate replica age on every response.
OVERPASS = 'https://overpass-api.de/api/interpreter'
ABQ = 'https://www.cabq.gov/automated-speed-enforcement/camera-data'
NMDOT = 'https://gis.dot.nm.gov/epermit/rest/services/EGIS/EgisViewer/MapServer'
SEATTLE = 'https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Seattle_Streets_1/FeatureServer/0'
NYC = 'https://data.cityofnewyork.us/resource/inkn-q76z.json'
PHILLY = 'https://philapark.org/speed-cameras/'
PHILLY_REPORT = 'https://philapark.org/wp-content/uploads/2026-Speed-Camera-Enforcement-Program-State-Report.pdf'
PHILLY13 = 'https://philapark.org/2026/04/60-day-warning-period-for-automated-speed-enforcement-cameras-on-stretch-of-route-13-in-northeast-philadelphia-will-begin-monday-april-13th/'
TACOMA_SCHOOL = 'https://tacoma.gov/government/departments/public-works/transportation/neighborhood-programs/safe-routes-to-school/engineering/'
CHICAGO = 'https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2645297'
CHICAGO_SCHOOL = 'https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2645301'
CHICAGO_PARK = 'https://codelibrary.amlegal.com/codes/chicago/latest/chicago_il/0-0-0-2645310'
SCHOOL = 'https://seattle.gov/police/community-policing/community-programs/red-light-cameras/school-zone-enforcement'


def get(url, params=None, post=False):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(url if post or not params else url+'?'+data.decode(),
        data=data if post else None, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=50) as response:
        raw = response.read(25_000_001)
    if len(raw) > 25_000_000: raise ValueError('Response exceeds 25 MB')
    return raw


def api(url, **params):
    value = json.loads(get(url, params))
    if isinstance(value, dict) and (value.get('error') or value.get('remark')):
        raise ValueError('Upstream error/partial response')
    return value


def samples(geometry, spacing=60):
    """Sample complete warning corridors; never interpolate only their endpoints."""
    result = [geometry[0]]
    for a,b in zip(geometry, geometry[1:]):
        n = max(1, math.ceil(distance(a,b)/spacing))
        for i in range(1,n+1):
            result.append({k:a[k]+(b[k]-a[k])*i/n for k in ('latitude','longitude')})
    return result


def abq_limits():
    import re
    text = parse_page(get(ABQ)).text
    pairs = re.findall(r'([^\n]+)\nSpeed limit:\s*(\d+)\s*MPH', text, re.I)
    if len(pairs)<18 or len({name for name,_ in pairs})!=len(pairs):
        raise ValueError('Albuquerque camera/limit page changed')
    return {'limits':[{'label':name.strip(),'value':int(value),'unit':'mph'} for name,value in pairs]}


def school_policy():
    text = parse_page(get(SCHOOL)).text
    import re
    values=re.findall(r'(\d+)\s*mph school zone speed limit',text,re.I)
    if set(values)!={'20'} or 'flashing beacons' not in text.lower():
        raise ValueError('Seattle school policy changed')
    return {'value':20,'unit':'mph','conditional':True,
            'evidence':'Fixed school-zone cameras enforce 20 MPH while beacons operate; use 20 as a conservative lower bound, never a higher ordinary-road limit.'}


def philly_report():
    import io,re
    from pypdf import PdfReader
    html=get(PHILLY).decode()
    matches=re.findall(r'https://philapark.org/wp-content/uploads/(\d{4}[^"\s<>]*Speed[^"\s<>]*Report\.pdf)',html,re.I)
    if not matches:raise ValueError('Current PPA annual report link not found')
    url='https://philapark.org/wp-content/uploads/'+sorted(set(matches))[-1]
    reader=PdfReader(io.BytesIO(get(url)))
    text='\n'.join(p.extract_text() or '' for p in reader.pages[:25])
    pairs=re.findall(r'(\d+\s+(?:[NS]\.\s+)?(?:Broad Street|Old York Road))\s+Northbound\s*&\s*Southbound\s+\d+\s+(\d+)\s+MPH',text)
    if len(pairs)<15 or len(set(a for a,_ in pairs))!=len(pairs):raise ValueError('PPA posted-limit table changed')
    return {'limits':[{'label':' '.join(a.split()),'value':int(v),'unit':'mph'} for a,v in pairs],
            'reportURL':url,'reportYear':int(url.split('/')[-1][:4]),'evidence':'Current linked PPA annual report, posted speed limit table for Route 611; exact address and both monitored directions.'}


def program_limit(url, phrases, value, conditional=False, locations=None):
    import re
    text=' '.join(parse_page(get(url)).text.lower().split())
    pattern=r'the speed limit on this stretch.{0,500}?is (\d+) miles-per-hour' if locations else r'(\d+) mph school zone speed limit'
    if {int(v) for v in re.findall(pattern,text)}!={value}:raise ValueError('Program numeric limit changed or ambiguous')
    if not all(p.lower() in text for p in phrases):raise ValueError('Program limit evidence changed')
    if locations and not all(p.lower() in text for p in locations):raise ValueError('Listed camera locations changed')
    return {'value':value,'unit':'mph','conditional':conditional,'locations':locations or [],
            'evidence':'Reviewed source phrases and exact named locations; no enforcement tolerance included.'}


def chicago_policy():
    checks=[(CHICAGO,'not to less than 20 miles per hour'),
            (CHICAGO_SCHOOL,'in excess of 20 miles per hour'),
            (CHICAGO_PARK,'in excess of 20 miles per hour')]
    evidence=[]
    for url,phrase in checks:
        raw=get(url);text=' '.join(parse_page(raw).text.lower().split())
        if phrase not in text:raise ValueError('Chicago speed rules changed')
        evidence.append({'url':url,'sha256':hashlib.sha256(raw).hexdigest()})
    return {'value':20,'unit':'mph','conditional':True,'pages':evidence,
            'evidence':'Conservative bound for the official school/park camera program; never assume the ordinary 30 MPH street limit or interpret child-presence schedules.'}


def nmdot_names(folder):
    routes={x['attributes']['RouteID'] for x in read(folder/'nmdot-roads.json',{}).get('features',[])}
    features=[]
    routes=sorted(routes)
    for start in range(0,len(routes),75):
        literals=','.join("'"+str(r).replace("'","''")+"'" for r in routes[start:start+75])
        value=arcgis_lines(NMDOT+'/11',[-107,34.7,-106.3,35.6],f'ToDate IS NULL AND RouteID IN ({literals})',
            'OBJECTID,RouteID,RoadLabel,Alias1_name,Alias2_name,Alias3_name,FromMeasure,ToMeasure',geometry=False)
        features.extend(value['features'])
    return {'features':features}


def arcgis_lines(url, bounds, where='1=1', fields='*', geometry=True):
    params = dict(f='json',where=where,geometry=','.join(map(str,bounds)),
        geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects')
    ids = api(url+'/query',**params,returnIdsOnly='true').get('objectIds')
    if not isinstance(ids,list) or len(ids)>100000: raise ValueError('Invalid road IDs')
    result=[]
    for start in range(0,len(ids),75):
        value=api(url+'/query', f='json',objectIds=','.join(map(str,sorted(ids)[start:start+75])),
                  outFields=fields,outSR=4326,returnGeometry=str(geometry).lower())
        if value.get('exceededTransferLimit'): raise ValueError('Truncated road geometries')
        result.extend(value.get('features',[]))
    if len(result)!=len(ids): raise ValueError('Road count changed during fetch')
    return {'features':result}


def nyc_lines(bounds):
    rows=[]
    west,south,east,north=bounds
    for offset in range(0,20000,500):
        batch=api(NYC, **{'$select':'physicalid,full_street_name,posted_speed,trafdir,modified_date,the_geom',
                         '$where':f'within_box(the_geom,{north},{west},{south},{east})', '$order':'physicalid', '$limit':500,'$offset':offset})
        if not isinstance(batch,list): raise ValueError('Invalid NYC rows')
        rows.extend(batch)
        if len(batch)<500:return {'rows':rows}
    raise ValueError('NYC road result exceeded bound')


def osm_roads(points):
    # 600 m upstream look-ahead plus the competing-road corridor. This is a
    # source query envelope, never invented runtime road geometry.
    queries=''.join(f'way(around:750,{p["latitude"]:.6f},{p["longitude"]:.6f})[highway];' for p in points)
    try:
        value=json.loads(get(OVERPASS,{'data':'[out:json][timeout:40];('+queries+');out meta geom;'},post=True))
    except (urllib.error.HTTPError,TimeoutError) as error:
        if len(points)<=25 or (isinstance(error,urllib.error.HTTPError) and error.code not in (502,503,504)):raise
        chunks=[]
        for start in range(0,len(points),25):
            time.sleep(5);chunks.append(osm_roads(points[start:start+25]))
        return {'osm3s':{'timestamp_osm_base':min(x['osm3s']['timestamp_osm_base'] for x in chunks)},
                'elements':list({e['id']:e for x in chunks for e in x['elements']}.values())}
    if value.get('remark') or not isinstance(value.get('elements'),list):
        raise ValueError('Incomplete Overpass road result')
    base=value.get('osm3s',{}).get('timestamp_osm_base')
    if not base or dt.datetime.now(UTC)-dt.datetime.fromisoformat(base.replace('Z','+00:00'))>dt.timedelta(days=2):
        raise ValueError('Overpass replica is more than two days stale')
    for e in value['elements']:
        if e.get('type')!='way' or not isinstance(e.get('id'),int) or not e.get('geometry'):
            raise ValueError('Invalid road geometry')
        if not all(valid_point(p.get('lat'),p.get('lon')) for p in e['geometry']):
            raise ValueError('Invalid road coordinate')
        # Editor usernames are unnecessary for this public fact extract.
        for key in ('user','uid','changeset'):e.pop(key,None)
    return value


def road_requests(cameras):
    # Regional batches avoid invalidating the entire country's query hashes when
    # one camera changes. All kinds need road applicability, including red lights.
    regions={}
    for camera in cameras:
        for point in samples(camera['geometry'],500):
            key=(math.floor(point['latitude']*4),math.floor(point['longitude']*4))
            region=regions.setdefault(key,{})
            region[(round(point['latitude'],6),round(point['longitude'],6))]=point
    result=[]
    for key,region in sorted(regions.items()):
        points=[region[k] for k in sorted(region)]
        for start in range(0,len(points),25):
            batch=points[start:start+25]
            name='osm-roads-'+hashlib.sha256(encode({'radius':750,'points':batch})).hexdigest()[:12]
            result.append((name,batch))
    return result


def active_osm_shards(root, requested, previous):
    # Query hashes change when camera inputs change. A partial replacement set
    # must not disconnect still-valid roads from the last complete source set.
    complete = all(read(root / f'Data/SpeedLimits/{name}.json', {}).get('checkedAt')
                   for name in requested)
    if complete:return requested
    # Use successful parts immediately, while preserving coverage for failed
    # regions. load_roads already picks the newest observation of each source way.
    available=[name for name in requested if read(root / f'Data/SpeedLimits/{name}.json', {}).get('checkedAt')]
    return sorted(set(previous.get('activeOSMShards', [])) | set(available)) or requested


def refresh(root=ROOT, now=None, force=False, budget=900, osm_only=False):
    now=now or dt.datetime.now(UTC); checks=[]; started=time.monotonic()
    previous=read(root/'Data/Review/speed-limit-fetch.json',{})
    attempts={c['id']:c.get('attemptedAt',c.get('checkedAt',previous.get('checkedAt','')))
              for c in previous.get('checks',[]) if c.get('attemptedAt') or c.get('status')!='deferred'}
    folder=root/'Data/SpeedLimits'; folder.mkdir(parents=True,exist_ok=True)
    def cached(name,url,fetch,minimum=0):
        path=folder/(name+'.json');old=read(path,{})
        if not force and old.get('checkedAt') and dt.timedelta(0)<=now-dt.datetime.fromisoformat(old['checkedAt'].replace('Z','+00:00'))<dt.timedelta(days=6):
            checks.append({'id':name,'status':'retained' if old.get('automatedCheckError') else 'cached','checkedAt':old['checkedAt'],
                **({'error':old['automatedCheckError'],'lastGoodAt':old['checkedAt']} if old.get('automatedCheckError') else {})});return
        if time.monotonic()-started>budget:
            checks.append({'id':name,'status':'deferred','error':'Run acquisition time budget reached',
                           **({'attemptedAt':attempts[name]} if name in attempts else {})})
            return
        try:
            value=fetch()
            count=len(value.get('elements',value.get('features',value.get('rows',value.get('limits',[])))))
            if count<minimum:raise ValueError('Source below minimum expected count')
            previous_count=old.get('recordCount',0)
            if previous_count and count<.75*previous_count:raise ValueError('Source lost over 25%; retained for review')
            at=value.get('osm3s',{}).get('timestamp_osm_base',stamp(dt.datetime.now(UTC)))
            value.update(sourceURL=url,checkedAt=at,recordCount=count)
            write(path,value,compact=True);checks.append({'id':name,'status':'downloaded','records':count,'checkedAt':value['checkedAt']})
        except Exception as error:
            checks.append({'id':name,'status':'retained' if old else 'unavailable','lastGoodAt':old.get('checkedAt'),'error':str(error)})
        checks[-1]['attemptedAt']=stamp(now)
        print(name,checks[-1]['status'],checks[-1].get('error',''),flush=True)
    if not osm_only:
        cached('abq-camera-limits',ABQ,abq_limits,18)
        cached('seattle-school-policy',SCHOOL,school_policy)
        cached('chicago-school-park-policy',CHICAGO,chicago_policy)
        cached('philadelphia-report-limits',PHILLY_REPORT,philly_report,15)
        cached('philadelphia-route13-limits',PHILLY13,lambda:program_limit(PHILLY13,['speed limit','25 miles-per-hour'],25,locations=['9900 Frankford Ave','8300 Frankford Ave','7000 Frankford Ave','6400 Frankford Ave','3100 Levick St','2100 Robbins St']))
        cached('tacoma-school-policy',TACOMA_SCHOOL,lambda:program_limit(TACOMA_SCHOOL,['20 mph school zone speed limit','flashing beacons'],20,conditional=True))
        cached('nmdot-roads',NMDOT+'/33',lambda:arcgis_lines(NMDOT+'/33',[-107,34.7,-106.3,35.6],
            'ToDate IS NULL','OBJECTID,RouteID,FromMeasure,ToMeasure,FromDate,ToDate,SpeedLimit,last_edited_date,LocError'),100)
        cached('nmdot-names',NMDOT+'/11',lambda:nmdot_names(folder),1)
    cameras=read(root/'Data/Published/cameras.json',{}).get('cameras',[])
    if not osm_only:
        for prefix,url,bbox in [('seattle-roads',SEATTLE,[-122.46,47.47,-122.22,47.75]),('nyc-roads',NYC,[-74.3,40.45,-73.65,40.96])]:
            tiles=set()
            for c in cameras:
                if c['kind'] not in ('speed','possibleSpeed'):continue
                p=c['geometry'][0];x,y=p['longitude'],p['latitude']
                if bbox[0]<=x<=bbox[2] and bbox[1]<=y<=bbox[3]:tiles.add((math.floor(x*20),math.floor(y*20)))
            for x,y in sorted(tiles):
                bounds=[x/20-.002,y/20-.002,(x+1)/20+.002,(y+1)/20+.002]
                name=f'{prefix}-{x}-{y}'
                cached(name,url,(lambda bounds=bounds:nyc_lines(bounds)) if prefix=='nyc-roads' else
                    (lambda bounds=bounds:arcgis_lines(SEATTLE,bounds,'1=1','OBJECTID,ONSTREET,SPEEDLIMIT,ONEWAY,ONEWAYDIR')))
    requests=road_requests(cameras)
    shards=[name for name,_ in requests];backoff=False
    # Missing/unattempted regions first; oldest attempts next. A failing region
    # cannot consume every week's acquisition budget and starve the rest.
    for name,ps in sorted(requests,key=lambda r:(attempts.get(r[0],''),r[0])):
        if backoff:
            checks.append({'id':name,'status':'deferred','error':'Overpass backoff after upstream refusal; retry on next run',
                           **({'attemptedAt':attempts[name]} if name in attempts else {})})
        else:
            cached(name,OVERPASS,lambda ps=ps:osm_roads(ps))
            backoff=any(x in checks[-1].get('error','') for x in ('429','Connection refused','rate limit'))
            if checks[-1]['status'] not in ('cached','deferred'):time.sleep(10)
    if osm_only:
        checks=[x for x in previous.get('checks',[]) if not x['id'].startswith('osm-roads-')]+checks
    active=active_osm_shards(root,shards,previous)
    report={'checkedAt':stamp(now),'activeOSMShards':active,'requestedOSMShards':shards,
            'retainedPreviousOSMShards':active!=shards,'checks':checks}
    write(root/'Data/Review/speed-limit-fetch.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--force',action='store_true');p.add_argument('--osm-only',action='store_true')
    args=p.parse_args();refresh(force=args.force,osm_only=args.osm_only)
