export interface GpsCoords {
  latitude: number;
  longitude: number;
}

export async function readExifGps(file: File): Promise<GpsCoords | null> {
  if (!file.type.includes('jpeg') && !file.name.toLowerCase().endsWith('.jpg')) {
    return null;
  }
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        resolve(extractGpsFromBuffer(e.target?.result as ArrayBuffer));
      } catch {
        resolve(null);
      }
    };
    reader.onerror = () => resolve(null);
    // First 128 KB is sufficient for EXIF headers
    reader.readAsArrayBuffer(file.slice(0, 131072));
  });
}

function readRational(view: DataView, offset: number, le: boolean): number {
  const num = view.getUint32(offset, le);
  const den = view.getUint32(offset + 4, le);
  return den === 0 ? 0 : num / den;
}

function dmsToDecimal(view: DataView, valOffset: number, le: boolean): number {
  const deg = readRational(view, valOffset, le);
  const min = readRational(view, valOffset + 8, le);
  const sec = readRational(view, valOffset + 16, le);
  return deg + min / 60 + sec / 3600;
}

function extractGpsFromBuffer(buf: ArrayBuffer): GpsCoords | null {
  const view = new DataView(buf);

  if (view.byteLength < 4 || view.getUint16(0) !== 0xffd8) return null;

  let pos = 2;
  while (pos < view.byteLength - 4) {
    const marker = view.getUint16(pos);
    pos += 2;

    if (marker === 0xffe1) {
      const segEnd = pos + view.getUint16(pos);
      pos += 2;

      // "Exif\0\0"
      if (pos + 6 > view.byteLength) return null;
      const header = String.fromCharCode(
        view.getUint8(pos),
        view.getUint8(pos + 1),
        view.getUint8(pos + 2),
        view.getUint8(pos + 3),
      );
      if (header !== 'Exif') return null;

      const tiff = pos + 6;
      const byteOrder = view.getUint16(tiff);
      const le = byteOrder === 0x4949;

      const ifd0Pos = tiff + view.getUint32(tiff + 4, le);
      const numEntries = view.getUint16(ifd0Pos, le);

      for (let i = 0; i < numEntries; i++) {
        const entry = ifd0Pos + 2 + i * 12;
        if (entry + 12 > segEnd) break;

        if (view.getUint16(entry, le) === 0x8825) {
          const gpsIfd = tiff + view.getUint32(entry + 8, le);
          return parseGpsIfd(view, gpsIfd, tiff, le);
        }
      }
      return null;
    } else if ((marker & 0xff00) === 0xff00 && marker !== 0xffda) {
      pos += view.getUint16(pos);
    } else {
      break;
    }
  }
  return null;
}

function parseGpsIfd(
  view: DataView,
  ifdStart: number,
  tiffBase: number,
  le: boolean,
): GpsCoords | null {
  if (ifdStart + 2 > view.byteLength) return null;
  const numEntries = view.getUint16(ifdStart, le);

  let latRef = 'N';
  let lngRef = 'E';
  let latVal: number | null = null;
  let lngVal: number | null = null;

  for (let i = 0; i < numEntries; i++) {
    const entry = ifdStart + 2 + i * 12;
    if (entry + 12 > view.byteLength) break;

    const tag = view.getUint16(entry, le);
    const valOrOffset = view.getUint32(entry + 8, le);

    switch (tag) {
      case 0x0001:
        latRef = String.fromCharCode(view.getUint8(entry + 8));
        break;
      case 0x0003:
        lngRef = String.fromCharCode(view.getUint8(entry + 8));
        break;
      case 0x0002: {
        const absOffset = tiffBase + valOrOffset;
        if (absOffset + 24 <= view.byteLength) {
          latVal = dmsToDecimal(view, absOffset, le);
        }
        break;
      }
      case 0x0004: {
        const absOffset = tiffBase + valOrOffset;
        if (absOffset + 24 <= view.byteLength) {
          lngVal = dmsToDecimal(view, absOffset, le);
        }
        break;
      }
    }
  }

  if (latVal === null || lngVal === null) return null;

  return {
    latitude: latRef === 'S' ? -latVal : latVal,
    longitude: lngRef === 'W' ? -lngVal : lngVal,
  };
}
