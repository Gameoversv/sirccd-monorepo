"""
Genera zonas de riesgo teóricas (buffers) alrededor de POIs sensibles (escuelas, hospitales, puentes, etc.)
para Santiago de los Caballeros usando los POIs descargados de Google Places.
"""
import json
from pathlib import Path
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
import geojson

# Parámetros
POI_FILES = [
    'school.geojson',
    'university.geojson',
    'hospital.geojson',
    'clinic.geojson',
    'bridge.geojson',
]
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
POIS_DIR = SCRIPT_DIR / 'pois_google'
OUTPUT_FILE = SCRIPT_DIR / 'risk_zones_theoretical.geojson'
BUFFER_METERS = 200  # radio del buffer en metros

# Utilidad para transformar coordenadas (WGS84 a metros aproximados)
def lonlat_to_meters(lon, lat):
    # Aproximación válida para distancias pequeñas cerca del ecuador
    from math import cos, pi
    R = 6378137  # radio de la Tierra en metros
    x = lon * (pi/180) * R
    y = lat * (pi/180) * R
    return x, y

def meters_to_lonlat(x, y):
    from math import pi
    R = 6378137
    lon = x / (R * (pi/180))
    lat = y / (R * (pi/180))
    return lon, lat

def buffer_point(lon, lat, radius_m):
    x, y = lonlat_to_meters(lon, lat)
    pt = Point(x, y)
    buf = pt.buffer(radius_m)
    # Convertir el polígono de vuelta a lon/lat
    coords = [meters_to_lonlat(x, y) for x, y in buf.exterior.coords]
    return {
        "type": "Polygon",
        "coordinates": [coords]
    }

def main():
    buffers = []
    for fname in POI_FILES:
        fpath = POIS_DIR / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            data = json.load(f)
        for feat in data['features']:
            lon, lat = feat['geometry']['coordinates']
            poly = buffer_point(lon, lat, BUFFER_METERS)
            buffers.append({
                "type": "Feature",
                "geometry": poly,
                "properties": {
                    "poi_type": feat['properties'].get('poi_type', fname.replace('.geojson','')),
                    "name": feat['properties'].get('name'),
                    "source": fname
                }
            })
    # Unir buffers superpuestos (opcional)
    # unioned = unary_union([shape(f['geometry']) for f in buffers])
    # ...
    out = {
        "type": "FeatureCollection",
        "features": buffers
    }
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        geojson.dump(out, f, indent=2)
    print(f"✅ Zonas de riesgo teóricas generadas: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
