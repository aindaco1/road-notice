"""Shared camera-pipeline I/O and coordinate primitives (standard library only)."""
import datetime as dt
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
# Public global OSM mirror with current replication, listed in OSM's instance directory.
OVERPASS_URL = 'https://maps.mail.ru/osm/tools/overpass/api/interpreter'

def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()

def write(path, value, *, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() if compact else encode(value)
    temp.write_bytes(raw); temp.replace(path)

def stamp(now):
    return now.astimezone(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def valid_point(lat, lon):
    return (isinstance(lat, (int, float)) and isinstance(lon, (int, float))
        and math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180)

def distance(a, b):
    lat1, lat2 = map(math.radians, (a['latitude'], b['latitude']))
    dlat = lat2 - lat1; dlon = math.radians(b['longitude'] - a['longitude'])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


def projection(point, line):
    """Return distance, distance along line, and directed bearing."""
    scale=111195;cos=math.cos(math.radians(point['latitude']));best=(float('inf'),0,0);along=0
    for a,b in zip(line,line[1:]):
        ax=(a['longitude']-point['longitude'])*scale*cos;ay=(a['latitude']-point['latitude'])*scale
        dx=(b['longitude']-a['longitude'])*scale*cos;dy=(b['latitude']-a['latitude'])*scale
        den=dx*dx+dy*dy;length=distance(a,b)
        if den:
            t=max(0,min(1,-(ax*dx+ay*dy)/den));d=math.hypot(ax+t*dx,ay+t*dy)
            if d<best[0]:best=(d,along+t*length,math.degrees(math.atan2(dx,dy))%360)
        along+=length
    return best
