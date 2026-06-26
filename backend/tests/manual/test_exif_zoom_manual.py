"""
Prueba manual de zoom_scale_factor leyendo EXIF de una imagen real.
Ejecutar desde backend/:

  # con imagen de fixture:
  python tests/manual/test_exif_zoom_manual.py tests/manual/fixtures/exif_no_zoom.jpg
  python tests/manual/test_exif_zoom_manual.py tests/manual/fixtures/exif_zoom_2x.jpg

  # con focal directo:
  python tests/manual/test_exif_zoom_manual.py 56

  # con tu propia foto:
  python tests/manual/test_exif_zoom_manual.py ruta/a/foto.jpg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from exif_service import extract_exif, ExifData

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

arg = sys.argv[1]

if Path(arg).suffix.lower() in {".jpg", ".jpeg", ".png"}:
    with open(arg, "rb") as f:
        data = extract_exif(f.read())
    print(f"Imagen:            {arg}")
    print(f"focal_length_mm:   {data.focal_length_mm}")
    print(f"focal_length_35mm: {data.focal_length_35mm}")
    print(f"zoom_scale_factor: {data.zoom_scale_factor:.3f}")
else:
    focal = int(arg)
    factor = ExifData(focal_length_35mm=focal).zoom_scale_factor
    print(f"{focal}mm -> factor: {factor:.3f}")
