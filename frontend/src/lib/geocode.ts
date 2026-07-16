export interface ResolvedAddress {
  address?: string;
  city?: string;
  province?: string;
}

interface NominatimResponse {
  address?: {
    road?: string;
    house_number?: string;
    suburb?: string;
    city?: string;
    town?: string;
    village?: string;
    municipality?: string;
    county?: string;
    state?: string;
    state_district?: string;
  };
}

export async function reverseGeocode(
  lat: number,
  lng: number,
  lang = 'es',
): Promise<ResolvedAddress> {
  const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&accept-language=${lang}`;
  const res = await fetch(url, {
    headers: { 'Accept-Language': lang },
  });

  if (!res.ok) throw new Error(`Geocode failed: ${res.status}`);

  const data: NominatimResponse = await res.json();
  const a = data.address ?? {};

  const street = [a.road, a.house_number].filter(Boolean).join(' ') || a.suburb;
  const city = a.city ?? a.town ?? a.village ?? a.municipality;
  const province = a.state ?? a.state_district ?? a.county;

  return {
    address: street,
    city,
    province,
  };
}
