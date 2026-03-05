'use client';

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon paths (same as MapView.tsx)
// @ts-ignore
delete Icon.Default.prototype._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface Props {
  lat: number;
  lng: number;
  label?: string;
  height?: string;
  zoom?: number;
}

export function MiniMap({ lat, lng, label, height = '220px', zoom = 15 }: Props) {
  return (
    <MapContainer
      center={[lat, lng]}
      zoom={zoom}
      style={{ height, width: '100%' }}
      className="rounded-b-xl"
      zoomControl
      scrollWheelZoom={false}
      dragging={false}
      doubleClickZoom={false}
      keyboard={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright" rel="noopener noreferrer">OpenStreetMap</a>'
        maxZoom={19}
      />
      <Marker position={[lat, lng]}>
        {label && <Popup>{label}</Popup>}
      </Marker>
    </MapContainer>
  );
}

export default MiniMap;

