"""
D-08: Extracción y eliminación de metadatos EXIF

Extrae únicamente los campos técnicos necesarios:
  - focal length → normalizar severidad por zoom/distancia
  - coordenadas GPS → usar como ubicación del bache (más fiable que coords del usuario al subir)
  - altitud → contexto de sensor

Elimina TODO el EXIF de la imagen antes de persistir.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Focal length de referencia: cámara trasera principal estándar (~28 mm eq. 35 mm)
_REFERENCE_FOCAL_35MM = 28.0

# Clamp para el factor de zoom: evita correcciones extremas en telefotos muy largos
# o gran angulares muy abiertos que distorsionarían la severidad.
_ZOOM_FACTOR_MIN = 0.25   # equivale a teleobjetivo ~5x (>140 mm) — no reducir más
_ZOOM_FACTOR_MAX = 2.0    # equivale a ultrawide 0.5x (~14 mm) — no inflar más

# EXIF tag IDs
_TAG_FOCAL_LENGTH = 0x920A       # 37386 — FocalLength (IFDRational)
_TAG_FOCAL_LENGTH_35MM = 0xA405  # 41989 — FocalLengthIn35mmFilm (SHORT)
_TAG_GPS_INFO = 0x8825           # 34853 — GPSInfo (IFD pointer)

# GPS sub-tags dentro del IFD GPS
_GPS_LAT = 2
_GPS_LAT_REF = 1
_GPS_LON = 4
_GPS_LON_REF = 3
_GPS_ALT = 6
_GPS_ALT_REF = 5


@dataclass
class ExifData:
    """Metadatos EXIF extraídos — solo campos técnicos y de ubicación."""

    focal_length_mm: Optional[float] = None
    focal_length_35mm: Optional[int] = None
    gps_available: bool = False
    gps_latitude: Optional[float] = None   # decimal, positivo=Norte
    gps_longitude: Optional[float] = None  # decimal, positivo=Este
    altitude_m: Optional[float] = None

    @property
    def zoom_scale_factor(self) -> float:
        """
        Factor de normalización para compensar zoom/distancia al calcular severidad.

        Problema: damage_ratio = bbox_area / image_area
          - Zoom 2x (56 mm) → bache ocupa 4x más píxeles → ratio inflado → severidad ALTA falsa
          - Ultrawide 0.5x (14 mm) → bache ocupa menos píxeles → ratio deflado → severidad BAJA falsa

        Corrección: ratio_normalizado = ratio_raw × (focal_ref / focal_real)
          - 28 mm (estándar 1x): factor = 1.0 → sin cambio
          - 56 mm (2x zoom):     factor = 0.5 → ratio se reduce a la mitad
          - 14 mm (0.5x wide):   factor = 2.0 → ratio se duplica
          - 140 mm (5x zoom):    factor clamped a 0.25

        `FocalLengthIn35mmFilm` ya incluye crop factor del sensor y zoom digital,
        por eso se prefiere sobre `FocalLength` (que es solo la óptica física).
        """
        fl = (
            float(self.focal_length_35mm)
            if self.focal_length_35mm
            else self.focal_length_mm
        )
        if fl and fl > 0.0:
            raw = _REFERENCE_FOCAL_35MM / fl
            return max(_ZOOM_FACTOR_MIN, min(_ZOOM_FACTOR_MAX, raw))
        return 1.0


def _rational_to_float(value) -> Optional[float]:
    """Convierte IFDRational o tupla (num, den) a float."""
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            return float(value.numerator) / float(value.denominator) if value.denominator else None
        if isinstance(value, tuple) and len(value) == 2:
            num, den = value
            return float(num) / float(den) if den else None
        return float(value)
    except Exception:
        return None


def _dms_to_decimal(dms) -> Optional[float]:
    """
    Convierte grados-minutos-segundos EXIF a grados decimales.
    `dms` es una lista/tupla de 3 valores (cada uno IFDRational o tupla).
    """
    try:
        parts = list(dms)
        if len(parts) < 3:
            return None
        degrees = _rational_to_float(parts[0])
        minutes = _rational_to_float(parts[1])
        seconds = _rational_to_float(parts[2])
        if degrees is None or minutes is None or seconds is None:
            return None
        return degrees + minutes / 60.0 + seconds / 3600.0
    except Exception:
        return None


def extract_exif(image_bytes: bytes) -> ExifData:
    """
    Extrae metadatos EXIF técnicos de la imagen.

    GPS extraído aquí se usa como ubicación del bache (más fiable que las
    coordenadas reportadas por el usuario al momento de subir la foto, que
    podrían ser desde su casa si subió la foto después).
    """
    data = ExifData()
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        exif = img.getexif()
        if not exif:
            return data

        # Focal length (preferir el equivalente 35mm que ya incorpora zoom digital y crop)
        if _TAG_FOCAL_LENGTH in exif:
            data.focal_length_mm = _rational_to_float(exif[_TAG_FOCAL_LENGTH])

        if _TAG_FOCAL_LENGTH_35MM in exif:
            try:
                val = int(exif[_TAG_FOCAL_LENGTH_35MM])
                if val > 0:
                    data.focal_length_35mm = val
            except Exception:
                pass

        # GPS
        if _TAG_GPS_INFO in exif:
            data.gps_available = True
            try:
                gps = exif.get_ifd(_TAG_GPS_INFO)

                # Latitud
                lat_dms = gps.get(_GPS_LAT)
                lat_ref = gps.get(_GPS_LAT_REF, "N")
                if lat_dms is not None:
                    lat = _dms_to_decimal(lat_dms)
                    if lat is not None:
                        if isinstance(lat_ref, bytes):
                            lat_ref = lat_ref.decode("ascii", errors="ignore")
                        data.gps_latitude = -lat if lat_ref.strip("\x00").upper() == "S" else lat

                # Longitud
                lon_dms = gps.get(_GPS_LON)
                lon_ref = gps.get(_GPS_LON_REF, "E")
                if lon_dms is not None:
                    lon = _dms_to_decimal(lon_dms)
                    if lon is not None:
                        if isinstance(lon_ref, bytes):
                            lon_ref = lon_ref.decode("ascii", errors="ignore")
                        data.gps_longitude = -lon if lon_ref.strip("\x00").upper() == "W" else lon

                # Altitud
                alt_raw = gps.get(_GPS_ALT)
                if alt_raw is not None:
                    alt_f = _rational_to_float(alt_raw)
                    if alt_f is not None:
                        ref = gps.get(_GPS_ALT_REF, b"\x00")
                        below = ref == b"\x01" or ref == 1
                        data.altitude_m = -alt_f if below else alt_f

            except Exception as gps_exc:
                logger.debug("GPS extraction error: %s", gps_exc)

    except Exception as exc:
        logger.debug("EXIF extraction failed: %s", exc)

    return data


def strip_exif(image_bytes: bytes) -> bytes:
    """
    Retorna los bytes de la imagen SIN ningún metadato EXIF/XMP/IPTC.

    Pillow no copia EXIF en save() a menos que se pase explícitamente el
    parámetro exif=…, por lo que re-guardar sin ese parámetro es suficiente.
    Hace early-return si la imagen ya no tiene EXIF para evitar re-compresión innecesaria.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))

        # Early-exit: si ya no hay EXIF no hay que re-guardar
        if not img.getexif():
            return image_bytes

        fmt = (img.format or "JPEG").upper()
        if fmt == "JPG":
            fmt = "JPEG"

        output = io.BytesIO()
        save_kwargs: dict = {"format": fmt}
        if fmt == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["optimize"] = True

        img.save(output, **save_kwargs)
        stripped = output.getvalue()
        logger.debug("EXIF stripped: %d → %d bytes", len(image_bytes), len(stripped))
        return stripped

    except Exception as exc:
        logger.warning("EXIF strip failed, returning original bytes: %s", exc)
        return image_bytes
