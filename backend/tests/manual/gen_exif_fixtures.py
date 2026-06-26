"""
Genera fixtures JPEG con y sin EXIF de zoom para pruebas manuales.
Ejecutar desde backend/:
  python tests/manual/gen_exif_fixtures.py

Genera en tests/manual/fixtures/:
  exif_no_zoom.jpg   -> sin EXIF (factor esperado: 1.0)
  exif_zoom_2x.jpg   -> FocalLengthIn35mmFilm=56mm (factor esperado: 0.5)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))
from exif_service import _TAG_FOCAL_LENGTH, _TAG_FOCAL_LENGTH_35MM

FIXTURES = Path(__file__).parent / "fixtures"


def make_base() -> Image.Image:
    return Image.new("RGB", (640, 480), color=(100, 149, 237))


def gen_no_zoom():
    img = make_base()
    out = FIXTURES / "exif_no_zoom.jpg"
    img.save(out, format="JPEG", quality=95)
    print(f"Generada: {out} (sin EXIF, factor=1.0)")


def gen_zoom_2x():
    img = make_base()
    exif = img.getexif()
    exif[_TAG_FOCAL_LENGTH] = (56, 1)
    exif[_TAG_FOCAL_LENGTH_35MM] = 56
    out = FIXTURES / "exif_zoom_2x.jpg"
    img.save(out, format="JPEG", quality=95, exif=exif.tobytes())
    print(f"Generada: {out} (focal 56mm, factor=0.5)")


if __name__ == "__main__":
    gen_no_zoom()
    gen_zoom_2x()
