"""
Script para descargar y catalogar POIs (escuelas, hospitales, bomberos) de OpenStreetMap.
- Descarga usando Overpass API
- Filtra por tipo de POI
- Exporta a GeoJSON
"""
import requests
import json
from pathlib import Path

# Parámetros
CITY = "Santiago de los Caballeros, Dominican Republic"
POI_TYPES = {
    'school': 'amenity=school',
    'hospital': 'amenity=hospital',
    'fire_station': 'amenity=fire_station',
}
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
OUTPUT_DIR = SCRIPT_DIR / 'pois'
OUTPUT_DIR.mkdir(exist_ok=True)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_query(city, poi_tag):
    return f"""
[out:json][timeout:60];
area["name"="{city}"][admin_level=8];
(
  node[{poi_tag}](area);
  way[{poi_tag}](area);
  relation[{poi_tag}](area);
);
out center;
"""

def fetch_pois(city, poi_type, tag):
    print(f"Descargando {poi_type} de {city}...")
    query = build_query(city, tag)
    response = requests.post(OVERPASS_URL, data={'data': query})
    response.raise_for_status()
    data = response.json()
    return data

def osm_to_geojson(osm_data, poi_type):
    features = []
    for el in osm_data.get('elements', []):
        if 'lat' in el and 'lon' in el:
            coords = [el['lon'], el['lat']]
        elif 'center' in el:
            coords = [el['center']['lon'], el['center']['lat']]
        else:
            continue
        props = el.get('tags', {})
        props['osm_id'] = el['id']
        props['poi_type'] = poi_type
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': coords},
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
    for poi_type, tag in POI_TYPES.items():
        osm_data = fetch_pois(CITY, poi_type, tag)
        geojson = osm_to_geojson(osm_data, poi_type)
        save_geojson(geojson, f'{poi_type}.geojson')
    print("\n✅ POIs descargados y exportados a GeoJSON.")

if __name__ == '__main__':
    main()
