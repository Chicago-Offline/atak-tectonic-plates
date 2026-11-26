#!/usr/bin/env python3
"""Build an ATAK-friendly KMZ of PB2002 tectonic plates (Bird 2003)."""
import json, collections, zipfile, os, html, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, 'src', 'tectonic')
BASE = 'https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON'
FILES = ['PB2002_boundaries.json', 'PB2002_plates.json',
         'PB2002_orogens.json', 'PB2002_steps.json']

os.makedirs(SRC, exist_ok=True)
for fn in FILES:
    p = os.path.join(SRC, fn)
    if not os.path.exists(p):
        print('fetch', fn)
        urllib.request.urlretrieve(f'{BASE}/{fn}', p)

# KML color = aabbggrr
CLASS = {
    'SUB': ('Subduction zone',            'ff2222cc', 4.0),
    'OCB': ('Oceanic convergent',         'ff4466ee', 3.0),
    'CCB': ('Continental convergent',     'ff3399ff', 3.0),
    'OSR': ('Oceanic spreading ridge',    'ff14ff39', 3.0),
    'CRB': ('Continental rift',           'ff44dd88', 3.0),
    'OTF': ('Oceanic transform fault',    'ff00e5ff', 2.5),
    'CTF': ('Continental transform fault','ff00b3ff', 3.0),
    'UNK': ('Unclassified boundary',      'ffdddddd', 2.5),
}

bounds = json.load(open(f'{SRC}/PB2002_boundaries.json'))['features']
plates = json.load(open(f'{SRC}/PB2002_plates.json'))['features']
orog   = json.load(open(f'{SRC}/PB2002_orogens.json'))['features']
steps  = json.load(open(f'{SRC}/PB2002_steps.json'))['features']

# dominant step class per boundary name
tally = collections.defaultdict(collections.Counter)
for s in steps:
    p = s['properties']
    tally[p['PLATEBOUND']][p.get('STEPCLASS') or 'UNK'] += 1
dom = {k: v.most_common(1)[0][0] for k, v in tally.items()}

PNAME = {p['properties']['Code']: p['properties']['PlateName'] for p in plates}

def esc(s): return html.escape(str(s), quote=True)

def coords(ring):
    return ' '.join(f'{x:.4f},{y:.4f},0' for x, y in ring)


def split_dateline(pts):
    """Split a coordinate run wherever a segment jumps >180 deg of longitude.

    A single segment that steps from -180 to +180 is drawn by ATAK as a line
    sweeping the long way round the globe.  On a world-scale feature that sweep
    is rendered as a huge soft white smear, and one runaway segment can throw
    several apparent "blobs" across the map.  PB2002 already places vertices on
    the antimeridian, so cutting there loses no geometry.
    """
    runs, cur = [], [pts[0]]
    for a, b in zip(pts, pts[1:]):
        if abs(b[0] - a[0]) > 180:
            runs.append(cur)
            cur = [b]
        else:
            cur.append(b)
    runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def linestrings(ring):
    """Emit one <LineString>, or a <MultiGeometry> if the ring crosses +/-180."""
    runs = split_dateline(list(ring))
    body = ''.join('<LineString><tessellate>1</tessellate><coordinates>'
                   f'{coords(r)}</coordinates></LineString>' for r in runs)
    return body if len(runs) == 1 else f'<MultiGeometry>{body}</MultiGeometry>'

out = []
out.append('<?xml version="1.0" encoding="UTF-8"?>')
out.append('<kml xmlns="http://www.opengis.net/kml/2.2"><Document>')
out.append('<name>Tectonic Plates (PB2002)</name>')
out.append('<description>Peter Bird (2003) PB2002 model. 52 plates, 241 boundary '
           'segments, 13 orogens. Source: github.com/fraxen/tectonicplates</description>')

for k, (label, color, w) in CLASS.items():
    out.append(f'<Style id="b_{k}"><LineStyle><color>{color}</color>'
               f'<width>{w}</width></LineStyle></Style>')
out.append('<Style id="plate">'
           '<LineStyle><color>80ffffff</color><width>1.2</width></LineStyle>'
           '<PolyStyle><fill>0</fill></PolyStyle></Style>')
out.append('<Style id="orogen">'
           '<LineStyle><color>a000b3ff</color><width>1.0</width></LineStyle>'
           '<PolyStyle><color>3000b3ff</color></PolyStyle></Style>')

# ---- boundaries, grouped into one folder per class
out.append('<Folder><name>Plate boundaries</name><open>1</open>')
bycls = collections.defaultdict(list)
for f in bounds:
    p = f['properties']
    nm = p['Name']
    k = 'SUB' if p.get('Type') == 'subduction' else dom.get(nm, 'UNK')
    if k not in CLASS: k = 'UNK'
    bycls[k].append((f, nm, p))
for k, (label, color, w) in CLASS.items():
    items = bycls.get(k)
    if not items: continue
    out.append(f'<Folder><name>{esc(label)} ({len(items)})</name>')
    for f, nm, p in items:
        a, b = p.get('PlateA', ''), p.get('PlateB', '')
        desc = (f'{esc(PNAME.get(a, a))} / {esc(PNAME.get(b, b))}<br/>'
                f'Class: {esc(label)}<br/>Source: {esc(p.get("Source", ""))}')
        g = f['geometry']
        parts = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for ln in parts:
            out.append(f'<Placemark><name>{esc(nm)}</name><styleUrl>#b_{k}</styleUrl>'
                       f'<description><![CDATA[{desc}]]></description>'
                       f'{linestrings(ln)}</Placemark>')
    out.append('</Folder>')
out.append('</Folder>')

# ---- plate outlines
out.append('<Folder><name>Plate outlines</name><open>0</open>')
for f in plates:
    p = f['properties']
    nm = f'{p["PlateName"]} ({p["Code"]})'
    g = f['geometry']
    polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    # Emitted as LineString, NOT Polygon: the style is fill-less anyway, and a
    # filled ring enclosing a pole triangulates badly in ATAK.
    #
    # 2026-11-20: LineString alone was NOT enough.  North America and Antarctica
    # each contained one segment stepping -180 -> +180, which ATAK swept the long
    # way round the globe as giant white smears (verified on tablet R52W60EHMJB:
    # removing the #plate folder cleared every blob, and splitting these two
    # features at the antimeridian cleared them with all 312 placemarks present).
    # linestrings() cuts those segments.
    for poly in polys:
        out.append(f'<Placemark><name>{esc(nm)}</name><styleUrl>#plate</styleUrl>'
                   f'{linestrings(poly[0])}</Placemark>')
out.append('</Folder>')

# ---- orogens
out.append('<Folder><name>Orogens (diffuse deformation)</name><open>0</open>')
for f in orog:
    p = f['properties']
    g = f['geometry']
    polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    for poly in polys:
        out.append(f'<Placemark><name>{esc(p["Name"])}</name><styleUrl>#orogen</styleUrl>'
                   f'<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>'
                   f'<coordinates>{coords(poly[0])}</coordinates>'
                   f'</LinearRing></outerBoundaryIs></Polygon></Placemark>')
out.append('</Folder>')
out.append('</Document></kml>')

kml = '\n'.join(out)
with zipfile.ZipFile(f'{D}/tectonic-plates.kmz', 'w', zipfile.ZIP_DEFLATED) as z:
    # Pinned timestamp -> byte-reproducible KMZ (sha256 stable across rebuilds)
    zi = zipfile.ZipInfo('doc.kml', date_time=(2026, 11, 20, 14, 32, 42))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o600 << 16
    z.writestr(zi, kml)
print('classes:', {k: len(v) for k, v in bycls.items()})
print('kml bytes', len(kml), 'kmz bytes', os.path.getsize(f'{D}/tectonic-plates.kmz'))
