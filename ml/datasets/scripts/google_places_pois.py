"""
Script para descargar POIs (escuelas, hospitales, bomberos) de Google Places API
para Santiago de los Caballeros, RD y exportar a GeoJSON.
"""
import requests
import json
from pathlib import Path
import time

API_KEY = "AIzaSyDvHwIncXzSZnXrL4A1iH8KrEMl2Beg8FA"
LOCATION = "19.4503,-70.6831"  # Centro de Santiago de los Caballeros
RADIUS = 15000  # metros (15 km cubre toda la ciudad)
TYPES = {
    'school': 'school',
    'university': 'university',
    'hospital': 'hospital',
    'clinic': 'doctor',  # Google Places usa 'doctor' para clínicas
    'fire_station': 'fire_station',
    'police': 'police',
    'bridge': 'bridge',  # No existe tipo 'bridge' en Places, se buscará por nombre
}
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
OUTPUT_DIR = SCRIPT_DIR / 'pois_google'
OUTPUT_DIR.mkdir(exist_ok=True)

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def fetch_places(place_type):
    results = []
    next_page_token = None
    # Para 'bridge', usar Text Search porque no existe tipo en Places
    if place_type == 'bridge':
        text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'key': API_KEY,
            'query': 'puente',
            'location': LOCATION,
            'radius': RADIUS,
        }
        resp = requests.get(text_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get('results', []))
        return results
    while True:
        params = {
            'key': API_KEY,
            'location': LOCATION,
            'radius': RADIUS,
            'type': place_type,
        }
        if next_page_token:
            params['pagetoken'] = next_page_token
            time.sleep(2)
        resp = requests.get(PLACES_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get('results', []))
        next_page_token = data.get('next_page_token')
        if not next_page_token:
            break
    return results

def to_geojson(places, poi_type):
    features = []
    for p in places:
        loc = p.get('geometry', {}).get('location', {})
        if not loc:
            continue
        props = {
            'name': p.get('name'),
            'address': p.get('vicinity'),
            'place_id': p.get('place_id'),
            'types': p.get('types'),
            'poi_type': poi_type
        }
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [loc['lng'], loc['lat']]},
            'properties': props
        })
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def save_geojson(data, filename):
    with open(OUTPUT_DIR / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {filename}")

def main():
    for key, gtype in TYPES.items():
        print(f"Descargando {key}...")
        places = fetch_places(gtype)
        geojson = to_geojson(places, key)
        save_geojson(geojson, f'{key}.geojson')
    print("\n✅ POIs descargados y exportados a GeoJSON (Google Places).")

if __name__ == '__main__':
    main()
