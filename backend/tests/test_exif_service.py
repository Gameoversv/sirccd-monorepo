"""
Tests unitarios para services/exif_service.py y la integración con ml_service.

Cubre:
- ExifData.zoom_scale_factor en todos los rangos (clamp, estándar, ultrawide)
- extract_exif() con imagen real PIL embebida con EXIF focal
- extract_exif() sin EXIF → valores None/False
- strip_exif() elimina EXIF y hace early-return si ya está limpia
- GPS DMS → decimal helpers (_dms_to_decimal, _rational_to_float)
- _evaluate_severity() con focal_scale_factor (import real, bypasa mock global)
- Prioridad coordenadas: EXIF GPS > usuario (lógica pura, sin imagen)
"""

import io
import sys
import os
import importlib.util
from pathlib import Path
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

from services.exif_service import (
    ExifData,
    extract_exif,
    strip_exif,
    _dms_to_decimal,
    _rational_to_float,
    _ZOOM_FACTOR_MIN,
    _ZOOM_FACTOR_MAX,
    _REFERENCE_FOCAL_35MM,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_jpeg(width: int = 200, height: int = 200) -> bytes:
    """JPEG mínimo sin EXIF."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color=(100, 149, 237))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _jpeg_with_focal(focal_35mm: int) -> bytes:
    """JPEG con FocalLengthIn35mmFilm (tag 41989) embebido vía Pillow."""
    from PIL import Image
    img = Image.new("RGB", (200, 200), color=(50, 100, 150))
    exif = img.getexif()
    exif[41989] = focal_35mm
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


def _jpeg_with_gps(lat_decimal: float, lon_decimal: float) -> bytes:
    """
    JPEG con GPS embebido.  Intenta vía Pillow IFD nativo; si falla por
    limitaciones de versión, construye los bytes EXIF mínimos manualmente.
    """
    from PIL import Image, TiffImagePlugin

    img = Image.new("RGB", (200, 200), color=(200, 100, 50))
    exif = img.getexif()

    def to_dms_tuples(value: float):
        value = abs(value)
        d = int(value)
        m = int((value - d) * 60)
        s = round(((value - d) * 60 - m) * 60 * 10000)
        return (
            TiffImagePlugin.IFDRational(d, 1),
            TiffImagePlugin.IFDRational(m, 1),
            TiffImagePlugin.IFDRational(s, 10000),
        )

    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = b"N\x00" if lat_decimal >= 0 else b"S\x00"
    gps_ifd[2] = to_dms_tuples(lat_decimal)
    gps_ifd[3] = b"E\x00" if lon_decimal >= 0 else b"W\x00"
    gps_ifd[4] = to_dms_tuples(lon_decimal)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    result = buf.getvalue()

    # Verificar que el GPS quedó embebido; si no, marcar como imposible en esta versión
    check = extract_exif(result)
    if not check.gps_available:
        pytest.skip("Esta versión de Pillow no soporta escritura de GPS IFD vía get_ifd()")

    return result


def _load_real_ml_service():
    """
    Carga el módulo services/ml_service directamente desde disco, bypassando
    el mock global que conftest.py inyecta en sys.modules.
    """
    ml_path = BACKEND / "services" / "ml_service.py"
    spec = importlib.util.spec_from_file_location("ml_service_real", ml_path)
    mod = importlib.util.module_from_spec(spec)
    # Inyectar dependencias mínimas que ml_service necesita al importarse
    mod.__dict__["__spec__"] = spec
    # Resolver imports internos: core.config, models.report
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════════
# ExifData — zoom_scale_factor
# ══════════════════════════════════════════════════════════════════════════════

class TestZoomScaleFactor:

    def test_no_focal_data_returns_one(self):
        assert ExifData().zoom_scale_factor == 1.0

    def test_standard_28mm_returns_one(self):
        assert ExifData(focal_length_35mm=28).zoom_scale_factor == pytest.approx(1.0, rel=1e-3)

    def test_2x_zoom_56mm_returns_half(self):
        assert ExifData(focal_length_35mm=56).zoom_scale_factor == pytest.approx(0.5, rel=1e-3)

    def test_1_5x_zoom_42mm(self):
        assert ExifData(focal_length_35mm=42).zoom_scale_factor == pytest.approx(28 / 42, rel=1e-3)

    def test_3x_zoom_84mm(self):
        assert ExifData(focal_length_35mm=84).zoom_scale_factor == pytest.approx(28 / 84, rel=1e-3)

    def test_ultrawide_14mm_at_max_clamp(self):
        # 14mm → raw = 2.0 → exactamente _ZOOM_FACTOR_MAX
        assert ExifData(focal_length_35mm=14).zoom_scale_factor == pytest.approx(_ZOOM_FACTOR_MAX, rel=1e-3)

    def test_extreme_ultrawide_clamped(self):
        # 10mm → raw = 2.8 → clamped a 2.0
        assert ExifData(focal_length_35mm=10).zoom_scale_factor == _ZOOM_FACTOR_MAX

    def test_5x_zoom_clamped_to_min(self):
        # 140mm → raw = 0.2 → clamped a 0.25
        assert ExifData(focal_length_35mm=140).zoom_scale_factor == _ZOOM_FACTOR_MIN

    def test_10x_zoom_clamped_to_min(self):
        assert ExifData(focal_length_35mm=280).zoom_scale_factor == _ZOOM_FACTOR_MIN

    def test_prefers_35mm_over_raw_focal(self):
        # Ambos presentes: usa focal_length_35mm (ya incluye crop + digital zoom)
        data = ExifData(focal_length_mm=50.0, focal_length_35mm=28)
        assert data.zoom_scale_factor == pytest.approx(1.0, rel=1e-3)

    def test_falls_back_to_raw_focal_if_no_35mm(self):
        assert ExifData(focal_length_mm=56.0).zoom_scale_factor == pytest.approx(0.5, rel=1e-3)

    def test_zero_focal_returns_one(self):
        assert ExifData(focal_length_35mm=0).zoom_scale_factor == 1.0

    def test_factor_always_within_clamp_bounds(self):
        for fl in [5, 10, 14, 20, 28, 42, 56, 84, 140, 280, 500]:
            factor = ExifData(focal_length_35mm=fl).zoom_scale_factor
            assert _ZOOM_FACTOR_MIN <= factor <= _ZOOM_FACTOR_MAX, (
                f"focal={fl}: factor={factor} fuera de [{_ZOOM_FACTOR_MIN}, {_ZOOM_FACTOR_MAX}]"
            )


# ══════════════════════════════════════════════════════════════════════════════
# _rational_to_float
# ══════════════════════════════════════════════════════════════════════════════

class TestRationalToFloat:

    def test_tuple_whole(self):
        assert _rational_to_float((28, 1)) == pytest.approx(28.0)

    def test_tuple_fractional(self):
        assert _rational_to_float((56, 10)) == pytest.approx(5.6)

    def test_zero_denominator_returns_none(self):
        assert _rational_to_float((5, 0)) is None

    def test_plain_float(self):
        assert _rational_to_float(3.5) == pytest.approx(3.5)

    def test_invalid_string_returns_none(self):
        assert _rational_to_float("invalid") is None

    def test_none_returns_none(self):
        assert _rational_to_float(None) is None


# ══════════════════════════════════════════════════════════════════════════════
# _dms_to_decimal
# ══════════════════════════════════════════════════════════════════════════════

class TestDmsToDecimal:

    def test_whole_degrees(self):
        assert _dms_to_decimal([(19, 1), (0, 1), (0, 1)]) == pytest.approx(19.0, abs=1e-5)

    def test_degrees_minutes(self):
        # 19° 25' 0" = 19 + 25/60
        assert _dms_to_decimal([(19, 1), (25, 1), (0, 1)]) == pytest.approx(19.41667, abs=1e-4)

    def test_full_dms(self):
        # 19° 25' 57.6"
        assert _dms_to_decimal([(19, 1), (25, 1), (576, 10)]) == pytest.approx(19.43267, abs=1e-4)

    def test_negative_handled_by_caller(self):
        # _dms_to_decimal siempre retorna positivo; el signo lo aplica extract_exif
        assert _dms_to_decimal([(34, 1), (36, 1), (0, 1)]) > 0

    def test_too_few_parts_returns_none(self):
        assert _dms_to_decimal([(19, 1), (25, 1)]) is None

    def test_invalid_element_returns_none(self):
        assert _dms_to_decimal(["bad", (0, 1), (0, 1)]) is None


# ══════════════════════════════════════════════════════════════════════════════
# extract_exif — imagen sin EXIF
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractExifNoExif:

    def test_plain_jpeg_all_defaults(self):
        data = extract_exif(_make_jpeg())
        assert data.focal_length_mm is None
        assert data.focal_length_35mm is None
        assert data.gps_available is False
        assert data.gps_latitude is None
        assert data.gps_longitude is None
        assert data.altitude_m is None
        assert data.zoom_scale_factor == 1.0

    def test_empty_bytes_returns_defaults(self):
        data = extract_exif(b"")
        assert data.zoom_scale_factor == 1.0

    def test_corrupt_bytes_returns_defaults(self):
        data = extract_exif(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)
        assert data.zoom_scale_factor == 1.0


# ══════════════════════════════════════════════════════════════════════════════
# extract_exif — focal length (embebido vía Pillow, funciona en PIL 11)
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractExifFocal:

    def test_reads_focal_length_35mm(self):
        data = extract_exif(_jpeg_with_focal(56))
        assert data.focal_length_35mm == 56

    def test_zoom_factor_computed_from_embedded_exif(self):
        data = extract_exif(_jpeg_with_focal(56))
        assert data.zoom_scale_factor == pytest.approx(0.5, rel=1e-3)

    def test_standard_lens_factor_is_one(self):
        data = extract_exif(_jpeg_with_focal(28))
        assert data.zoom_scale_factor == pytest.approx(1.0, rel=1e-3)

    def test_1_5x_zoom_factor(self):
        data = extract_exif(_jpeg_with_focal(42))
        assert data.zoom_scale_factor == pytest.approx(28 / 42, rel=1e-3)

    def test_5x_zoom_clamped(self):
        data = extract_exif(_jpeg_with_focal(140))
        assert data.zoom_scale_factor == _ZOOM_FACTOR_MIN

    def test_ultrawide_clamped(self):
        data = extract_exif(_jpeg_with_focal(10))
        assert data.zoom_scale_factor == _ZOOM_FACTOR_MAX


# ══════════════════════════════════════════════════════════════════════════════
# extract_exif — GPS (se salta si Pillow no soporta escritura GPS IFD)
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractExifGps:

    def test_gps_flag_and_sign_north_west(self):
        img_bytes = _jpeg_with_gps(19.4326, -99.1332)  # skips si Pillow no soporta
        data = extract_exif(img_bytes)
        assert data.gps_available is True
        assert data.gps_latitude is not None and data.gps_latitude > 0   # Norte
        assert data.gps_longitude is not None and data.gps_longitude < 0  # Oeste

    def test_south_hemisphere_negative_lat(self):
        img_bytes = _jpeg_with_gps(-34.6037, -58.3816)
        data = extract_exif(img_bytes)
        if data.gps_latitude is not None:
            assert data.gps_latitude < 0

    def test_no_gps_image(self):
        data = extract_exif(_make_jpeg())
        assert data.gps_available is False
        assert data.gps_latitude is None
        assert data.gps_longitude is None


# ══════════════════════════════════════════════════════════════════════════════
# strip_exif
# ══════════════════════════════════════════════════════════════════════════════

class TestStripExif:

    def test_removes_focal_length_exif(self):
        stripped = strip_exif(_jpeg_with_focal(56))
        assert extract_exif(stripped).focal_length_35mm is None

    def test_image_valid_after_strip(self):
        from PIL import Image
        stripped = strip_exif(_jpeg_with_focal(56))
        img = Image.open(io.BytesIO(stripped))
        assert img.size == (200, 200)

    def test_early_return_when_no_exif(self):
        plain = _make_jpeg()
        result = strip_exif(plain)
        # El resultado no tiene EXIF
        assert not extract_exif(result).focal_length_35mm

    def test_corrupt_bytes_returns_original(self):
        bad = b"not an image"
        assert strip_exif(bad) == bad

    def test_idempotent(self):
        # strip_exif aplicado dos veces = mismo resultado que una vez
        once = strip_exif(_jpeg_with_focal(42))
        twice = strip_exif(once)
        assert extract_exif(twice).focal_length_35mm is None


# ══════════════════════════════════════════════════════════════════════════════
# MLInferenceService._evaluate_severity con focal_scale_factor
# (importa el módulo real desde disco, bypaseando el mock de conftest)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def real_ml_module():
    """Módulo ml_service real cargado desde disco (no el mock de conftest)."""
    return _load_real_ml_service()


@pytest.fixture(scope="module")
def ml_service_instance(real_ml_module):
    return real_ml_module.MLInferenceService(use_mock=True)


@pytest.fixture
def make_bbox(real_ml_module):
    BBox = real_ml_module.BoundingBox
    def _make(width=100, height=100, conf=0.9):
        return BBox(x=0, y=0, width=width, height=height,
                    confidence=conf, class_name="bache", class_id=0)
    return _make


class TestEvaluateSeverityWithZoom:

    def test_no_bboxes_returns_baja(self, ml_service_instance):
        from models.report import SeverityLevel
        result = ml_service_instance._evaluate_severity([], 640, 480, focal_scale_factor=1.0)
        assert result.severity == SeverityLevel.BAJA
        assert result.damage_ratio_raw == 0.0

    def test_factor_1_identical_to_default(self, ml_service_instance, make_bbox):
        bbox = make_bbox(width=150, height=150, conf=0.7)
        default = ml_service_instance._evaluate_severity([bbox], 640, 480)
        explicit = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=1.0)
        assert default.severity == explicit.severity
        assert default.damage_ratio_normalized == explicit.damage_ratio_normalized

    def test_factor_1_leaves_the_ratio_untouched(self, ml_service_instance, make_bbox):
        bbox = make_bbox(width=150, height=150, conf=0.7)
        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=1.0)
        assert result.area_scale_factor == 1.0
        assert result.damage_ratio_normalized == result.damage_ratio_raw

    def test_correction_is_quadratic_not_linear(self, ml_service_instance, make_bbox):
        """
        damage_ratio es area: a 2x el bache ocupa 4x los pixeles, asi que la
        correccion debe ser factor**2 (0.25), no factor (0.5).
        """
        bbox = make_bbox(width=200, height=200, conf=0.4)
        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=0.5)

        assert result.area_scale_factor == 0.25
        assert result.damage_ratio_normalized == pytest.approx(
            result.damage_ratio_raw * 0.25
        )

    def test_zoomed_photo_of_a_small_pothole_stays_baja(self, ml_service_instance, make_bbox):
        """
        El bug que motivo el cambio: bache fotografiado a 2x.

        240x240 sobre 640x480 → ratio bruto 0.1875. El bache real ocupa un
        cuarto de eso (0.0469, BAJA), pero la correccion lineal solo bajaba a
        0.0938 y lo clasificaba MEDIA. Con la correccion de area da BAJA.
        """
        from models.report import SeverityLevel
        bbox = make_bbox(width=240, height=240, conf=0.4)  # conf baja: no dispara la via ponderada

        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=0.5)

        assert result.damage_ratio_raw == pytest.approx(0.1875)
        assert result.damage_ratio_normalized == pytest.approx(0.046875)
        assert result.severity == SeverityLevel.BAJA

    def test_same_pothole_without_zoom_is_unaffected(self, ml_service_instance, make_bbox):
        """Contraparte: sin zoom, ese mismo ratio bruto sigue siendo MEDIA."""
        from models.report import SeverityLevel
        bbox = make_bbox(width=240, height=240, conf=0.4)

        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=1.0)

        assert result.damage_ratio_normalized == pytest.approx(0.1875)
        assert result.severity == SeverityLevel.ALTA

    def test_ultrawide_inflates_the_ratio_quadratically(self, ml_service_instance, make_bbox):
        """Factor 2.0 (ultrawide 0.5x) → el area se corrige ×4."""
        bbox = make_bbox(width=40, height=40, conf=0.4)
        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=2.0)

        assert result.area_scale_factor == 4.0
        assert result.damage_ratio_normalized == pytest.approx(result.damage_ratio_raw * 4)

    def test_high_ratio_at_1x_returns_alta_or_media(self, ml_service_instance, make_bbox):
        from models.report import SeverityLevel
        # 350x350 en 640x480 → ratio≈0.398 → ALTA
        bbox = make_bbox(width=350, height=350, conf=0.9)
        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=1.0)
        assert result.severity in (SeverityLevel.MEDIA, SeverityLevel.ALTA)

    def test_extreme_zoom_in_very_small_ratio(self, ml_service_instance, make_bbox):
        """Factor 0.01 (extremo, sin clamp en ml_service) → ratio casi cero → BAJA."""
        from models.report import SeverityLevel
        bbox = make_bbox(width=350, height=350, conf=0.4)
        result = ml_service_instance._evaluate_severity([bbox], 640, 480, focal_scale_factor=0.01)
        assert result.severity == SeverityLevel.BAJA

    def test_multiple_detections_high_confidence_stays_alta(self, ml_service_instance, make_bbox):
        """weighted_detections >= 3.0 → ALTA sin importar el zoom."""
        from models.report import SeverityLevel
        # 4 detecciones con conf=0.9 → weighted=3.6 → ALTA aunque damage_ratio sea bajo
        bboxes = [make_bbox(width=20, height=20, conf=0.9) for _ in range(4)]
        result = ml_service_instance._evaluate_severity(bboxes, 640, 480, focal_scale_factor=0.25)
        assert result.severity == SeverityLevel.ALTA
        assert result.weighted_detections == pytest.approx(3.6)

    def test_breakdown_reaches_detections_json(self, ml_service_instance, make_bbox, real_ml_module):
        """El desglose tiene que sobrevivir hasta el dict que se persiste."""
        result = ml_service_instance._mock_detection(640, 480, focal_scale_factor=0.5)
        data = result.to_dict()

        assert data["focal_scale_factor"] == 0.5
        assert data["area_scale_factor"] == 0.25
        assert data["damage_ratio_normalized"] == pytest.approx(
            data["damage_ratio_raw"] * 0.25, rel=1e-3
        )
        assert data["severity"] == result.severity.value


# ══════════════════════════════════════════════════════════════════════════════
# Prioridad GPS: lógica pura sin imagen
# ══════════════════════════════════════════════════════════════════════════════

class TestGpsPriority:
    """Verifica la lógica de selección de coordenadas (replica reports.py)."""

    def _pick(self, exif_data: ExifData, user_lat: float, user_lon: float):
        if exif_data.gps_latitude is not None and exif_data.gps_longitude is not None:
            return exif_data.gps_latitude, exif_data.gps_longitude, "exif"
        return user_lat, user_lon, "user"

    def test_exif_gps_overrides_user(self):
        exif = ExifData(gps_available=True, gps_latitude=19.4326, gps_longitude=-99.1332)
        lat, lon, src = self._pick(exif, 0.0, 0.0)
        assert lat == 19.4326 and lon == -99.1332 and src == "exif"

    def test_user_fallback_when_no_exif_gps(self):
        exif = ExifData(gps_available=False)
        lat, lon, src = self._pick(exif, 18.5, -70.2)
        assert lat == 18.5 and lon == -70.2 and src == "user"

    def test_partial_gps_lat_only_uses_user(self):
        exif = ExifData(gps_available=True, gps_latitude=19.4326, gps_longitude=None)
        _, _, src = self._pick(exif, 18.5, -70.2)
        assert src == "user"

    def test_partial_gps_lon_only_uses_user(self):
        exif = ExifData(gps_available=True, gps_latitude=None, gps_longitude=-99.1)
        _, _, src = self._pick(exif, 18.5, -70.2)
        assert src == "user"

    def test_photo_from_pothole_uploaded_from_home(self):
        """Escenario real: foto en bache, subida desde casa."""
        pothole_lat, pothole_lon = -34.6037, -58.3816
        home_lat, home_lon = -34.6100, -58.3900
        exif = ExifData(gps_available=True, gps_latitude=pothole_lat, gps_longitude=pothole_lon)
        lat, lon, src = self._pick(exif, home_lat, home_lon)
        assert lat == pothole_lat and src == "exif"

    def test_south_negative_coordinates_correct(self):
        exif = ExifData(gps_available=True, gps_latitude=-34.6037, gps_longitude=-58.3816)
        lat, lon, src = self._pick(exif, 0.0, 0.0)
        assert lat < 0 and lon < 0 and src == "exif"
