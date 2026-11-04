"""A durable review queue produced by GitHub Actions, with no Codex dependency."""
from camera_data import ROOT, read, write, stamp, UTC
import datetime as dt


def generate(root=ROOT):
    now=dt.datetime.now(UTC)
    watches=read(root/'Data/Review/source-watch.json',{})
    identity=read(root/'Data/Review/agency-reconciliation.json',{})
    moved=read(root/'Data/Review/metro-source-changes.json',{})
    limits=read(root/'Data/Review/speed-limit-coverage.json',{})
    limit_fetch=read(root/'Data/Review/speed-limit-fetch.json',{})
    overture=read(root/'Data/Review/overture-fetch.json',{})
    items=[]
    zones=read(root/'Data/Review/road-zone-coverage.json',{})
    acquisition=limit_fetch.get('directionalCoverage',{})
    if acquisition.get('complete',0)<acquisition.get('candidates',0):
        items.append({'source':'road-acquisition','reason':f"{acquisition['complete']} / {acquisition['candidates']} directional cameras have complete road-query coverage; see speed-limit-fetch.json"})
    if zones.get('sourceChecksDue'):
        items.append({'source':'road-zones','reason':f"{zones['sourceChecksDue']} road zones need source rechecks; validated geometry remains active"})
    if zones.get('retained'):
        items.append({'source':'road-zones','reason':f"{zones['retained']} prior zones retained pending complete approach geometry; see road-zone-coverage.json"})
    if overture.get('error'):items.append({'source':'overture','reason':overture['error'],'lastGoodAt':overture.get('lastGoodAt')})
    for c in watches.get('checks',[]):
        if c.get('reviewRequired'):
            items.append({'source':c['id'],'url':c['url'],'reason':c.get('error','Source page changed'),
                          'added':c.get('added',[]),'removed':c.get('removed',[]),'lastGoodAt':c.get('lastGoodAt')})
    items += identity.get('review',[]) + moved.get('review',[])
    items += [{'source':x['id'],'reason':x['error'],'lastGoodAt':x.get('lastGoodAt')} for x in limit_fetch.get('checks',[]) if x.get('error')]
    report={'generatedAt':stamp(now),'reviewCount':len(items),'items':items}
    write(root/'Data/Review/maintenance.json',report)
    lines=['# Weekly camera maintenance','',f"Generated {stamp(now)}",'',
           f"{len(watches.get('checks',[]))} registered sources checked; {len(identity.get('automaticMatches',[]))} evidence-based identity matches; {len(items)} unresolved findings.",'',
           'New unambiguous agency records and validated coordinate estimates are staged automatically. Ambiguous identities, source removals, changed page layouts, and failed checks retain previous coverage and remain in this queue until reviewed.','',
           '| Source or record | Finding |','|---|---|']
    for item in items:
        key=item.get('id',item.get('sourceRecord',item.get('source','Source')))
        reason=item.get('reason','Review required')
        lines.append(f"| {str(key).replace('|','/')} | {str(reason).replace('|','/')} |")
    lines += ['', 'Full added/removed facts, nearby candidates, and evidence are in maintenance.json and the source-specific reports.', '']
    if limits:
        lines += ['## Speed-limit coverage','',f"{limits['eligible']} / {limits['speedCameras']} speed-camera approaches can suppress ({limits['coveragePercent']}%). Red-light and combined cameras are excluded from this denominator.",
                  '',f"Evidence: {limits['byBasis']}. {limits['candidateOnly']} candidate-only; {limits['unknown']} unknown.",
                  '', 'Per-camera values, sources, timestamps, inferred lower bounds and missing-data reasons: speed-limit-coverage.json.', '']
    metro=read(root/'Data/Review/metro-coverage.json',{})
    coverage_lines=['# Speed-limit coverage','',f"Snapshot {limits.get('version','staged')}",'',f"{limits.get('eligible',0)} / {limits.get('speedCameras',0)} speed-camera approaches have an approved posted limit or conservative suppression bound.",'',
        '| Census metro | Speed approaches | With limit/bound |','|---|---:|---:|']
    for m in metro.get('metros',[]):
        coverage_lines.append(f"| {m['name']} | {m.get('speedCameraApproaches',0)} | {m.get('withSuppressionLimit',0)} |")
    coverage_lines+=['','Values are not field-verified sign readings. Agency camera values, OSM tags, matched-road estimates and conservative school/conflict bounds are distinct evidence categories in speed-limit-coverage.json. Red-light/combined cameras are excluded. Unknown, expired or unresolved variable limits continue warning.','']
    (root/'Data/Review/speed-limit-coverage.md').write_text('\n'.join(coverage_lines))
    (root/'Data/Review/maintenance.md').write_text('\n'.join(lines))
    print(f'{len(items)} unresolved maintenance findings.')
    return report

if __name__=='__main__':generate()
