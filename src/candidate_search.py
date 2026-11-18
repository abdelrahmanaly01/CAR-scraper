"""Collect candidate properties and check the point against their CAR boundaries."""
import io
import json
import math
import struct
import urllib.parse
import urllib.request
import zipfile
from .car_api import BASE_URL, normalize_registration
from .network import create_ssl_context


def check_boundary(data, longitude, latitude):
    with zipfile.ZipFile(io.BytesIO(data)) as outer:
        path = next(n for n in outer.namelist() if n.lower().endswith('area_do_imovel.zip'))
        with zipfile.ZipFile(io.BytesIO(outer.read(path))) as inner:
            prj = next(n for n in inner.namelist() if n.lower().endswith('.prj'))
            if 'SIRGAS' not in inner.read(prj).decode('utf-8', 'replace').upper():
                raise ValueError('Unsupported boundary coordinate system')
            shp = inner.read(next(n for n in inner.namelist() if n.lower().endswith('.shp')))
    pos = 100
    inside_any = False
    distance = float('inf')
    found = False
    scale_x = 111320 * math.cos(math.radians(latitude))
    while pos + 8 <= len(shp):
        _, length = struct.unpack_from('>ii', shp, pos)
        pos += 8
        block = shp[pos:pos + length * 2]
        pos += length * 2
        kind = struct.unpack_from('<i', block)[0]
        if kind == 0:
            continue
        if kind not in (5, 15, 25):
            raise ValueError('Unsupported boundary geometry')
        count, points = struct.unpack_from('<ii', block, 36)
        starts = list(struct.unpack_from('<' + 'i' * count, block, 44)) + [points]
        coords = [struct.unpack_from('<dd', block, 44 + 4 * count + 16 * i) for i in range(points)]
        inside = False
        found = True
        for start, end in zip(starts, starts[1:]):
            ring = coords[start:end]
            for (x1,y1),(x2,y2) in zip(ring, ring[1:] + ring[:1]):
                if (y1 > latitude) != (y2 > latitude) and longitude < (x2-x1)*(latitude-y1)/(y2-y1)+x1:
                    inside = not inside
                dx,dy=(x2-x1)*scale_x,(y2-y1)*111320
                px,py=(longitude-x1)*scale_x,(latitude-y1)*111320
                t=max(0,min(1,(px*dx+py*dy)/(dx*dx+dy*dy))) if dx or dy else 0
                distance=min(distance,math.hypot(px-t*dx,py-t*dy))
        inside_any |= inside
    if not found:
        raise ValueError('No property boundary found')
    return inside_any, round(distance)


def search_candidates(latitude, longitude, progress=lambda *a: None, attempts=10):
    candidates = {}
    failures = []
    params = urllib.parse.urlencode({'lat':latitude,'lng':longitude})
    ssl_context = create_ssl_context()
    for i in range(attempts):
        progress(i + 1, attempts)
        try:
            with urllib.request.urlopen(
                BASE_URL + '/api/totalizer/getDetailsByCoordinates?' + params,
                timeout=30,
                context=ssl_context,
            ) as r:
                p = json.load(r)
            code = normalize_registration(p.get('codeProperty'))
            origin = p.get('idOrigin')
            if type(origin) is not int or origin <= 0:
                raise ValueError('Invalid download identifier')
            candidates[code] = {'registration':code,'id_origin':origin,'area':p.get('haRegisteredArea'),
                                'city':p.get('nameCity'), 'state':p.get('idState')}
        except Exception as e:
            failures.append(str(e))
    for item in candidates.values():
        try:
            with urllib.request.urlopen(
                BASE_URL + '/api/downloadBase/getShapeByIdOrigin/' + str(item['id_origin']),
                timeout=60,
                context=ssl_context,
            ) as r:
                data=r.read(30 * 1024 * 1024 + 1)
            if len(data)>30*1024*1024:
                raise ValueError('Boundary archive too large')
            item['inside'],item['distance_m']=check_boundary(data,longitude,latitude)
        except Exception as e:
            item['inside']=None
            item['boundary_error']=str(e)
    return {'candidates':list(candidates.values()),'failures':failures,'attempts':attempts}
