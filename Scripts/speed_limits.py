"""One evidence resolver for posted limits and conservative suppression bounds.

Unknown/conflicting values never become high-confidence posted limits. The minimum
of fully parsed, applicable alternatives is a separate conservative bound; it
cannot assert which time-dependent limit is currently posted.
"""
import collections
import datetime as dt
import math
import re

from camera_data import read, write, stamp, UTC, distance, projection
from geocode_locations import road_key
from camera_identity import angle
from fetch_speed_limits import samples, ABQ, SCHOOL, NYC, SEATTLE, NMDOT, CHICAGO, PHILLY13, PHILLY_REPORT, TACOMA_SCHOOL

SPEED_KINDS = {'speed','possibleSpeed'}
ROAD_TYPES = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential',
              'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
ABQ_JOIN = {
    'abq-gibson-carlisle-san-mateo-eb':'Gibson at San Mateo (EB)',
    'abq-gibson-carlisle-san-mateo-wb':'Gibson at San Mateo (WB)',
    'abq-unser-tower-nb':'Unser at Tower', 'abq-coal-cornell-eb':'Coal at Cornell',
    'abq-central-tingley-new-york-wb':'Central at New York', 'abq-lomas-virginia-wb':'Lomas at Virginia',
    'abq-unser-flor-del-sol-nb':'Unser at Flor del Sol',
    'abq-san-mateo-montgomery-sb':'San Mateo at Montgomery',
    'abq-eubank-central-nb':'Eubank at Buena Ventura', 'abq-lomas-third-eb':'Lomas at 3rd',
    'abq-98th-tower-central-nb':'98th at Tower',
    'abq-ellison-black-diversion-eb':'Ellison & Black Diversion Channel',
    'abq-wyoming-academy-nb':'Wyoming at Academy', 'abq-coors-bypass-ellison-sb':'Coors Bypass at Ellison',
    'abq-coors-montano-paseo-nb':'Coors at La Orilla',
    'abq-paseo-louisiana-wb':'Paseo del Norte at Louisiana', 'abq-broadway-iron-sb':'Broadway at Iron',
}


def numeric(raw, default_unit='km/h'):
    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(mph|km/h|kmh|kph)?',str(raw).strip(),re.I)
    if not m:return None
    unit=m[2].lower() if m[2] else default_unit
    unit='km/h' if unit in ('kmh','kph') else unit
    value=float(m[1])
    if unit not in ('mph','km/h') or not (5 if unit=='mph' else 8)<=value<=(85 if unit=='mph' else 140):return None
    return {'value':value,'unit':unit}


def mps(value): return value['value']*(.44704 if value['unit']=='mph' else 1/3.6)


def tag_limit(tags):
    """Bare OSM numbers are km/h. Parse every limit alternative, never tolerances."""
    if tags.get('maxspeed:type') in ('signals','variable') or tags.get('source:maxspeed')=='signals':
        return None,'Variable limit without a known lower bound'
    if any('variable' in k and v not in ('no','0') for k,v in tags.items() if k.startswith('maxspeed')):
        return None,'Variable limit without a known lower bound'
    if any(k in tags for k in ('fixme','FIXME','construction','proposed:highway')):
        return None,'Uncertain or construction road'
    # No travel direction is guessed from camera-facing direction. Taking both
    # explicitly mapped directions is conservative when their orientation is unknown.
    values=[];conditional=False
    keys=[k for k in tags if k=='maxspeed' or k.startswith(('maxspeed:forward','maxspeed:backward','maxspeed:conditional','maxspeed:lanes'))]
    if not keys:return None,'No posted limit'
    for key in keys:
        raw=tags[key]
        if 'conditional' in key:
            conditional=True
            # Split rules only after a complete condition, not semicolons inside it.
            parts=re.split(r';\s*(?=\d+(?:\.\d+)?\s*(?:mph|km/h)?\s*@)',raw)
            for part in parts:
                if '@' not in part:return None,'Unparsed conditional limit'
                value,condition=part.split('@',1)
                # Reject an embedded second rule that the split did not understand.
                if not condition.strip() or '@' in condition:return None,'Unparsed conditional limit'
                parsed=numeric(value)
                if not parsed:return None,'Unknown conditional limit value/unit'
                values.append(parsed)
        else:
            for part in re.split(r'[|;]',raw):
                parsed=numeric(part)
                if not parsed:return None,'Unknown posted limit value/unit'
                values.append(parsed)
    # A lone forward/backward value cannot establish the other direction.
    if 'maxspeed' not in tags and not ('maxspeed:forward' in tags and 'maxspeed:backward' in tags):
        return None,'Incomplete directional/base limit'
    result=min(values,key=mps).copy()
    result['basis']='conservative-lower-bound' if conditional or len({round(mps(v),3) for v in values})>1 else 'osm-posted'
    result['alternatives']=values;result['conditional']=conditional
    return result,None


def fresh(at,now,days=30):
    try:return dt.timedelta(0)<=now-dt.datetime.fromisoformat(at.replace('Z','+00:00'))<dt.timedelta(days=days)
    except (ValueError,AttributeError,TypeError):return False


def evidence(value,source_id,url,at,basis,reason,**extra):
    return {**value,'sourceID':source_id,'sourceURL':url,'checkedAt':at,'basis':basis,'reason':reason,**extra}


def name_key(value):
    value=re.sub(r'^\d+\s+(?:(?:BLK|BLOCK)(?:\s+OF)?\s+)?','',value,flags=re.I)
    value=re.sub(r'\b(?:N/?B|S/?B|E/?B|W/?B|NEB|NWB|SEB|SWB)\b','',value,flags=re.I)
    words=road_key(value).split()
    ordinals={'first':'1st','second':'2nd','third':'3rd','fourth':'4th','fifth':'5th','sixth':'6th','seventh':'7th','eighth':'8th','ninth':'9th','tenth':'10th'}
    words=[ordinals.get(w,w) for w in words]
    compass={'n','s','e','w','ne','nw','se','sw'}
    return ' '.join(w for w in words if w not in compass)


def camera_names(camera):
    values=camera.get('roadNames',[])
    if not values:
        label=camera['label'].split(' · ')[0].split(':',1)[0]
        values=[re.split(r'\s+(?:between|near|just|north of|south of|west of|east of|at|and)\s+|\s*@\s*',label,flags=re.I)[0]]
    return {name_key(v) for v in values if v and v!='Mapped camera'}


def same_road(a,b):
    a,b=name_key(a),name_key(b)
    suffixes={'st','ave','blvd','rd','dr','ln','pkwy','hwy','ct','pl','way'}
    def base(x):
        words=x.split();return ' '.join(words[:-1]) if words and words[-1] in suffixes else x
    return bool(a and b and (a==b or base(a)==base(b)))


def closest(point,line):
    separation,_,bearing=projection(point,line)
    return separation,bearing


class RoadIndex:
    def __init__(self,roads):
        self.roads=roads;self.cells=collections.defaultdict(set)
        for i,road in enumerate(roads):
            for p in samples(road['geometry'],50):
                self.cells[(math.floor(p['latitude']*1000),math.floor(p['longitude']*1000))].add(i)
    def nearby(self,point):
        lat,lon=math.floor(point['latitude']*1000),math.floor(point['longitude']*1000)
        ids=set().union(*(self.cells[(lat+x,lon+y)] for x in range(-2,3) for y in range(-2,3)))
        return [self.roads[i] for i in sorted(ids)]


def overture_limit(rules):
    if not rules:return None,'No road limit'
    values=[];base=False;conditional=False
    for rule in rules:
        if rule.get('is_max_speed_variable'):return None,'Variable limit without a known lower bound'
        raw=rule.get('max_speed') or {}
        value=numeric(str(raw.get('value'))+' '+str(raw.get('unit')))
        if not value:return None,'Unknown Overture maximum limit'
        full=not rule.get('between') or rule['between']==[0,1]
        base |= full and not rule.get('when')
        conditional |= bool(rule.get('when')) or not full
        values.append(value)
    if not base:return None,'Incomplete conditional or segment limit'
    result=min(values,key=mps).copy()
    result['basis']='conservative-lower-bound' if conditional or len({mps(v) for v in values})>1 else 'road-matched'
    result['alternatives']=values;result['conditional']=conditional
    return result,None


def additional_roads(root,now):
    folder=root/'Data/SpeedLimits';roads=[]
    names=collections.defaultdict(list)
    for row in read(folder/'nmdot-names.json',{}).get('features',[]):
        a=row['attributes'];names[a['RouteID']].append(a)
    d=read(folder/'nmdot-roads.json',{});name_at=read(folder/'nmdot-names.json',{}).get('checkedAt',d.get('checkedAt'))
    for row in d.get('features',[]):
        a=row['attributes']
        if (a.get('FromDate') or 0)>now.timestamp()*1000 or a.get('ToDate') is not None or a.get('LocError') not in (None,'NO ERROR','No Error','') :continue
        labels=set()
        for n in names[a['RouteID']]:
            if max(a['FromMeasure'],n['FromMeasure'])>=min(a['ToMeasure'],n['ToMeasure']):continue
            labels.update(n[k] for k in ('RoadLabel','Alias1_name','Alias2_name','Alias3_name') if n.get(k))
        for part,line in enumerate(row.get('geometry',{}).get('paths',[])):
            value=numeric(a.get('SpeedLimit'),'mph')
            roads.append({'id':f'nmdot/{a["OBJECTID"]}/{part}','source':'nmdot-roads','sourceURL':NMDOT+'/33',
                'names':sorted(labels),'geometry':[{'latitude':p[1],'longitude':p[0]} for p in line],
                'nodes':[],'tags':{},'limit':value,'checkedAt':min(d['checkedAt'],name_at),
                'sourceUpdatedAt':a.get('last_edited_date'), 'unavailableReason':None if value else 'No road limit',
                'unitBasis':'MPH inferred from NMDOT US roadway values and HPMS reporting convention; road-matched estimate, not a camera-specific posted-limit assertion.'})
    idx=read(folder/'overture-roads.json',{})
    documents=[read(folder/path,{}) for path in idx.get('tiles',[])] if idx.get('tiles') else [idx]
    for d in documents:
        release=d.get('release','')[:10]
        expires=stamp(dt.datetime.fromisoformat(release).replace(tzinfo=UTC)+dt.timedelta(days=45)) if release else None
        for row in d.get('roads',[]):
            if row.get('class') not in ROAD_TYPES:continue
            value,reason=overture_limit(row.get('limits'));line=row['geometry']
            if line.get('type')!='LineString':continue
            lineage=row.get('sources') or [];aliases=[]
            for source in lineage:
                match=re.fullmatch(r'w(\d+)@\d+',source.get('record_id') or '')
                if match and source.get('dataset')=='OpenStreetMap':aliases.append('osm/way/'+match[1])
            flags={flag for rule in row.get('roadFlags') or [] for flag in rule.get('values',[])}
            tags={}
            if 'is_bridge' in flags:tags['bridge']='yes'
            if 'is_tunnel' in flags:tags['tunnel']='yes'
            if any(rule.get('value',0)!=0 for rule in row.get('levelRules') or []):tags['layer']='1'
            roads.append({'id':'overture/'+row['id'],'source':'overture','sourceURL':d['sourceURL'],
                'names':[row['name']] if row.get('name') else [],'geometry':[{'latitude':p[1],'longitude':p[0]} for p in line['coordinates']],
                'nodes':[],'tags':tags,'limit':value,'checkedAt':d['checkedAt'],'expiresAt':expires,
                'sourceUpdatedAt':release,'lineage':lineage,'aliases':aliases,'unavailableReason':reason})
    return roads


def load_roads(root,now=None):
    now=now or dt.datetime.now(UTC)
    roads=additional_roads(root,now);osm={};report=read(root/'Data/Review/speed-limit-fetch.json',{})
    for name in report.get('activeOSMShards',[]):
        d=read(root/f'Data/SpeedLimits/{name}.json',{})
        for e in d.get('elements',[]):
            if e.get('tags',{}).get('highway') not in ROAD_TYPES:continue
            old=osm.get(e['id'])
            if old and old[1]>=d['checkedAt']:continue
            osm[e['id']]=(e,d['checkedAt'])
    for e,at in osm.values():
        tags=e['tags'];limit,reason=tag_limit(tags)
        roads.append({'id':f'osm/way/{e["id"]}','source':'osm','sourceURL':f'https://www.openstreetmap.org/way/{e["id"]}',
            'geometry':[{'latitude':p['lat'],'longitude':p['lon']} for p in e['geometry']],
            'names':[tags[k] for k in ('name','alt_name','official_name','ref') if tags.get(k)],
            'nodes':e.get('nodes',[]),'tags':tags,'limit':limit,'unavailableReason':reason,
            'checkedAt':at,'sourceUpdatedAt':e.get('timestamp')})
    paths=list((root/'Data/SpeedLimits').glob('nyc-roads-*.json'))+list((root/'Data/SpeedLimits').glob('seattle-roads-*.json'))
    for path in sorted(paths):
        name='nyc-roads' if path.name.startswith('nyc') else 'seattle-roads';url=NYC if name=='nyc-roads' else SEATTLE
        d=read(path,{})
        for row in d.get('rows',d.get('features',[])):
            a=row.get('attributes',row)
            if name=='nyc-roads':
                paths=a.get('the_geom',{}).get('coordinates',[]);label=a['full_street_name'];raw=a.get('posted_speed');rid=a['physicalid']
            else:
                paths=row.get('geometry',{}).get('paths',[]);label=a['ONSTREET'];raw=a.get('SPEEDLIMIT');rid=a['OBJECTID']
            for n,path in enumerate(paths):
                value=numeric(raw,'mph')
                roads.append({'id':f'{name}/{rid}/{n}','source':name,'sourceURL':url,
                    'geometry':[{'latitude':p[1],'longitude':p[0]} for p in path],
                    'names':[label], 'nodes':[], 'tags':{},'limit':value,'checkedAt':d['checkedAt'],
                    'sourceUpdatedAt':a.get('modified_date'), 'unavailableReason':None if value else 'No road limit'})
    # A fresh direct OSM way replaces its older Overture mirror, not a second vote.
    live={r['id'] for r in roads if r['source']=='osm'}
    unique={}
    for r in roads:
        if r['source']=='overture' and live.intersection(r.get('aliases',[])):continue
        prior=unique.get(r['id'])
        if not prior or r['checkedAt']>prior['checkedAt']:unique[r['id']]=r
    return list(unique.values())


def road_candidates(camera,index,now):
    result=[];reasons=[];names=camera_names(camera);samples_matched=[]
    device_nodes={int(s.rsplit('/',1)[1]) for s in camera['sourceIDs'] if s.startswith('osm/node/')}
    explicit_ways={s for s in camera['sourceIDs'] if s.startswith('osm/way/')}
    for p in samples(camera['geometry'],30):
        choices=[]
        for road in index.nearby(p):
            d,b=closest(p,road['geometry'])
            if d>45:continue
            matched=bool(device_nodes & set(road['nodes']) or bool(({road['id']} | set(road.get('aliases',[]))) & explicit_ways))
            named=any(same_road(a,b) for a in names for b in road['names'])
            travel=camera.get('travelBearing')
            aligned=travel is None or min(angle(travel,b),angle(travel,(b+180)%360))<=35
            if travel is not None and road['tags'].get('oneway') in ('yes','1','-1'):
                along=(b+180)%360 if road['tags']['oneway']=='-1' else b
                aligned=angle(travel,along)<=45
            if not aligned:continue
            if names and not (matched or named):continue
            # Grade-separated roads cannot be inferred solely from 2D proximity.
            if not matched and (road['tags'].get('bridge')=='yes' or road['tags'].get('tunnel')=='yes' or road['tags'].get('layer','0')!='0'):continue
            choices.append((d,road,matched,named))
        choices.sort(key=lambda x:(not x[2],not x[3],x[0]))
        if not choices:reasons.append('No matching monitored road');continue
        strong=[x for x in choices if x[2]] or [x for x in choices if x[3]]
        uncertain_carriageway=False
        if strong:choices=strong
        else:
            nearest=choices[0]
            same=[x for x in choices if x is nearest or any(same_road(a,b) for a in nearest[1]['names'] for b in x[1]['names'])]
            others=[x for x in choices if x not in same]
            if nearest[0]>12 or any(x[0]-nearest[0]<15 for x in others):
                reasons.append('Ambiguous road or insufficient alignment');continue
            # Splitting one road into OSM ways, or mapping both carriageways,
            # must not create a false ambiguity. Require every plausible piece's
            # limit and use a lower bound, without claiming which lane is monitored.
            choices=same;uncertain_carriageway=len(same)>1
        # Include connected alternatives near a junction, rather than choosing the
        # highest limit. Missing/expired values on a plausible road block inference.
        # All qualified same-road alternatives within 45 m remain candidates;
        # do not discard the farther carriageway's lower or unknown limit.
        # A second provider with no attribute is not a contradictory value on
        # the same named, aligned centerline. Distinct nearby roads still block.
        known=[x for x in choices if x[1].get('limit')]
        def redundant_unknown(x):
            d,r,_,named=x
            return not r.get('limit') and r.get('unavailableReason') in ('No posted limit','No road limit') and named and any(
                r['source']!=other['source'] and other_named and abs(d-other_d)<=8
                and min(angle(closest(p,r['geometry'])[1],closest(p,other['geometry'])[1]),angle(closest(p,r['geometry'])[1],(closest(p,other['geometry'])[1]+180)%360))<10
                for other_d,other,_,other_named in known)
        choices=[x for x in choices if not redundant_unknown(x)]
        if any(not r.get('limit') or not fresh(r['checkedAt'],now) or (r.get('expiresAt') and r['expiresAt']<=stamp(now)) for _,r,_,_ in choices):
            if any(r.get('unavailableReason') not in (None,'No posted limit','No road limit') for _,r,_,_ in choices):
                reasons.append('Matched road has unresolved conditional/variable limit')
            else:reasons.append('Matched road has unknown or stale limit')
            continue
        sample=[]
        for d,r,linked,named in choices:
            lim=r['limit'];basis='conservative-lower-bound' if uncertain_carriageway or lim.get('basis')=='conservative-lower-bound' else 'road-matched'
            sample.append(evidence(lim,r['id'],r['sourceURL'],r['checkedAt'],basis,
                'Camera member of road' if linked else ('Same named monitored road and compatible alignment' if named else ('Conservative minimum across plausible segments/carriageways of the same named road' if uncertain_carriageway else 'Unique road within 12 m; alternatives at least 15 m farther away')),
                sourceUpdatedAt=r.get('sourceUpdatedAt'),matchDistanceMeters=round(d,2),
                expiresAt=r.get('expiresAt'),lineage=r.get('lineage'),unitBasis=r.get('unitBasis')))
        samples_matched.append(sample)
    if len(samples_matched)!=len(samples(camera['geometry'],30)):
        return [],sorted(set(reasons)) or ['Incomplete corridor coverage']
    for group in samples_matched:result.extend(group)
    return list({(x['sourceID'],x['value'],x['unit']):x for x in result}.values()),reasons


def enrich(root,records,documents,now):
    nodes={};rechecks={}
    for d in documents:
        for e in d['elements']:
            if e.get('tags'):
                sid=f'osm/{e["type"]}/{e["id"]}';nodes[sid]=e
                rechecks[sid]=d['osm3s']['timestamp_osm_base']
    registry={s['id']:s for s in read(root/'Data/source-registry.json',{'sources':[]})['sources']}
    caches={sid:read(root/f'Data/External/{sid}.json',{}) for sid in registry}
    city=read(root/'Data/SpeedLimits/abq-camera-limits.json',{})
    city_values={name_key(x['label']):x for x in city.get('limits',[])}
    school=read(root/'Data/SpeedLimits/seattle-school-policy.json',{})
    chicago=read(root/'Data/SpeedLimits/chicago-school-park-policy.json',{})
    philly=read(root/'Data/SpeedLimits/philadelphia-route13-limits.json',{})
    philly_table=read(root/'Data/SpeedLimits/philadelphia-report-limits.json',{})
    tacoma_school=read(root/'Data/SpeedLimits/tacoma-school-policy.json',{})
    roads=load_roads(root,now);index=RoadIndex(roads);ledger=[];sources={}
    for c in records:
        c.pop('speedLimitEvidenceIDs',None)
        c.pop('speedLimit',None)  # Recompute; removed/changed evidence must not survive as approval.
        if c['kind'] not in SPEED_KINDS:continue
        candidates=[];blocks=[]
        for sid in c['sourceIDs']:
            e=nodes.get(sid)
            if not e or e['type']=='way':continue
            value,reason=tag_limit(e['tags'])
            if value:candidates.append(evidence(value,sid,'https://www.openstreetmap.org/'+sid.removeprefix('osm/'),
                rechecks[sid],value['basis'],'Explicit maxspeed on the camera or its enforcement relation',rawTags=e['tags']))
            elif any(k.startswith('maxspeed') for k in e['tags']):blocks.append(reason)
        agency=c.get('agencyID','')
        agency_source=max((sid for sid in caches if agency.startswith('agency-'+sid+'-')),key=len,default=None)
        agency_record=next((x for x in caches.get(agency_source,{}).get('cameras',[]) if x['id']==agency),None)
        agency_present=bool(agency_record and distance(c.get('agencyGeometry',c['geometry'])[0],agency_record['geometry'][0])<=100)
        candidate=agency_record.get('speedLimitCandidate') if agency_present else None
        if candidate and agency_present:
            source=registry[agency_source];cache=caches[agency_source]
            # Device-specific posted values already present in official live feeds.
            if agency_source in ('sf','dc','tacoma','arlington'):
                basis='conservative-lower-bound' if candidate.get('conditional') else 'agency-posted'
                candidates.append(evidence(candidate,candidate['sourceID'],source.get('page',source['url']),
                    cache.get('checkedAt'),basis,'Agency camera-ID join; reduced school value retained as lower bound' if candidate.get('conditional') else 'Agency camera-ID join to posted speed-limit field'))
        if c['id'] in ABQ_JOIN:
            value=city_values.get(name_key(ABQ_JOIN[c['id']]))
            if value:candidates.append(evidence(value,'abq-limit/'+c['id'],ABQ,city.get('checkedAt'),
                'agency-posted','Reviewed named camera/approach join to city camera passing-data page'))
        if agency_present and agency_source=='seattle' and school.get('value'):
            at=min(school['checkedAt'],caches['seattle'].get('checkedAt',school['checkedAt']))
            candidates.append(evidence({'value':20,'unit':'mph','conditional':True},'seattle-school/'+agency,SCHOOL,at,
                'conservative-lower-bound','Official fixed school-zone program: use the reduced 20 MPH bound regardless of beacon state'))
        if agency_present and agency_source=='chicago-speed' and chicago.get('value'):
            at=min(chicago['checkedAt'],caches[agency_source].get('checkedAt',chicago['checkedAt']))
            candidates.append(evidence({'value':20,'unit':'mph','conditional':True},'chicago-school-park/'+agency,CHICAGO,at,
                'conservative-lower-bound','Official school/park camera program; conservative 20 MPH bound from city code, never the ordinary street limit'))
        if agency_present and agency_source=='philadelphia-addresses':
            location=c['label'].split(' · ')[0]
            # Address number must match too; same_road deliberately strips it.
            def address_key(x):return ' '.join(re.findall(r'[a-z0-9]+',x.lower())).replace('street','st').replace('avenue','ave')
            for data,prefix,url in [(philly,'philadelphia-route13',PHILLY13),(philly_table,'philadelphia-report',philly_table.get('reportURL',PHILLY_REPORT))]:
                values=data.get('limits',[{'label':x,'value':data['value'],'unit':'mph'} for x in data.get('locations',[])])
                for value in values:
                    if address_key(location)!=address_key(value['label']):continue
                    at=min(data['checkedAt'],caches[agency_source].get('checkedAt',data['checkedAt']))
                    candidates.append(evidence(value,prefix+'/'+agency,url,at,'agency-posted',
                        'Exact listed address join to PPA posted limit; not the 11 MPH ticket threshold'))
        if agency_present and agency_source=='tacoma' and not candidate and tacoma_school.get('value'):
            # WATCSZ IDs are the agency school-zone devices, WATCFS is separate.
            if agency.lower().startswith('agency-tacoma-watcsz'):
                at=min(tacoma_school['checkedAt'],caches['tacoma'].get('checkedAt',tacoma_school['checkedAt']))
                candidates.append(evidence({'value':20,'unit':'mph','conditional':True},'tacoma-school/'+agency,TACOMA_SCHOOL,at,
                    'conservative-lower-bound','Agency school-zone device and official reduced 20 MPH school limit; beacon state not inferred'))
        nearby,road_blocks=road_candidates(c,index,now)
        candidates+=nearby
        if 'Matched road has unresolved conditional/variable limit' in road_blocks:
            blocks.append('Matched road has unresolved conditional/variable limit')
        active=[x for x in candidates if fresh(x.get('checkedAt'),now)]
        reasons=sorted(set(blocks+road_blocks))
        # Unknown conditional/variable camera tags block even otherwise valid roads.
        eligible=active if not blocks else []
        # School camera metadata must never be replaced with a higher ordinary-road limit.
        known_school=agency_source in ('seattle','arlington','chicago-speed') or (agency_source=='tacoma' and not candidate) or (candidate or {}).get('conditional')
        if known_school and not any(x['basis']=='conservative-lower-bound' for x in active):eligible=[];reasons.append('School limit evidence unavailable')
        selected=None
        if eligible:
            selected=min(eligible,key=lambda x:(mps(x),x['sourceID'])).copy()
            different=len({round(mps(x),2) for x in eligible})>1
            if different:selected['basis']='conservative-lower-bound';selected['reason']+='; lower of credible alternatives'
            at=min(x['checkedAt'] for x in eligible)
            end=dt.datetime.fromisoformat(at.replace('Z','+00:00'))+dt.timedelta(days=30)
            expiry=min([stamp(end)]+[x['expiresAt'] for x in eligible if x.get('expiresAt')])
            c['speedLimit']={k:selected[k] for k in ('value','unit','sourceID','basis')}
            c['speedLimit'].update(verifiedAt=at,validUntil=expiry,conditional=False,
                semantics='conservative-suppression-bound' if selected['basis']=='conservative-lower-bound' else 'posted-limit',
                confidence={'agency-posted':'agency','osm-posted':'community'}.get(selected['basis'],'inferred'),
                sourceURL=selected['sourceURL'])
            c['speedLimitEvidenceIDs']=sorted({x['sourceID'] for x in eligible})
            for x in eligible:
                prior=sources.get(x['sourceURL'],{})
                sources[x['sourceURL']]={'id':x['sourceURL'],'name':'Speed-limit evidence','url':x['sourceURL'],
                    'license':'OSM/derived roads: ODbL-1.0; agency posted-limit facts: attribution at source URL.',
                    'checkedAt':min(x['checkedAt'],prior.get('checkedAt',x['checkedAt'])),
                    'status':'Posted limit or conservative lower bound; see speed-limit coverage report.'}
        ledger.append({'id':c['id'],'label':c['label'],'kind':c['kind'],
            'status':'eligible' if selected else ('candidate-only' if candidates else 'unknown'),
            'selected':selected,'candidates':candidates,'unavailableReasons':reasons})
    counts=collections.Counter(row['status'] for row in ledger)
    bases=collections.Counter(row['selected']['basis'] for row in ledger if row['selected'])
    report={'generatedAt':stamp(now),'totalCameras':len(records),'speedCameras':len(ledger),
        'eligible':counts['eligible'],'candidateOnly':counts['candidate-only'],'unknown':counts['unknown'],
        'byBasis':dict(bases),'coveragePercent':round(100*counts['eligible']/len(ledger),1) if ledger else 0,
        'albuquerqueCity':{'eligible':sum(bool(x['selected']) for x in ledger if x['id'].startswith('abq-')),
                           'speedCameras':sum(x['id'].startswith('abq-') for x in ledger)},
        'records':ledger}
    write(root/'Data/Review/speed-limit-coverage.json',report)
    return records,[sources[url] for url in sorted(sources)],report
