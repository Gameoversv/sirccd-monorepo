"""
03_convert_plates.py — Convierte datasets de placas a formato YOLO

Soporta:
  1. CCPD  — coordenadas codificadas en el nombre de archivo
  2. RodoSol-ALPR — archivos .txt por imagen

Genera labels YOLO (clase 1 = license_plate) en:
  processed/plates_yolo/images/{train,val}/
  processed/plates_yolo/labels/{train,val}/
"""

import os
import random
import shutil
from pathlib import Path
from PIL import Image

SEED = 42
PLATE_CLASS = 1

BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / "datasets" / "raw"
OUT_DIR = BASE / "datasets" / "processed" / "plates_yolo"

# Submuestreo para balanceo con rostros
CCPD_MAX = 15_000
RODOSOL_MAX = 5_000


# ──────────────────────────────────────────────
#  CCPD — Chinese City Parking Dataset
# ──────────────────────────────────────────────
def convert_ccpd(split_ratio: float = 0.85):
    """
    CCPD codifica las coordenadas de la placa en el nombre del archivo.
    Formato del nombre:
      025-95_113-154&383-386&473-...jpg
    Los campos separados por '-':
      [0] tilt degrees
      [1] bounding box tilt
      [2] top-left vertex (x&y)
      [3] bottom-right vertex (x&y)
      [4] LP vertices (4 puntos)
      [5] LP number
      [6] brightness/blurriness
    """
    ccpd_dir = RAW_DIR / "ccpd" / "ccpd_base"
    if not ccpd_dir.exists():
        print(f"  CCPD no encontrado en {ccpd_dir}")
        return 0

    images = list(ccpd_dir.glob("*.jpg")) + list(ccpd_dir.glob("*.png"))
    print(f"  CCPD: {len(images)} imágenes encontradas")

    # Submuestrear
    random.seed(SEED)
    if len(images) > CCPD_MAX:
        images = random.sample(images, CCPD_MAX)
        print(f"  Submuestreado a {CCPD_MAX}")

    random.shuffle(images)
    split_idx = int(len(images) * split_ratio)
    splits = {"train": images[:split_idx], "val": images[split_idx:]}

    total = 0
    for split, img_list in splits.items():
        out_img_dir = OUT_DIR / "images" / split
        out_lbl_dir = OUT_DIR / "labels" / split
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in img_list:
            try:
                stem = img_path.stem
                parts = stem.split("-")
                if len(parts) < 5:
                    continue

                # Extraer bounding box: parts[2] = tl, parts[3] = br
                tl = parts[2].split("&")
                br = parts[3].split("&")
                x1, y1 = int(tl[0]), int(tl[1])
                x2, y2 = int(br[0]), int(br[1])

                with Image.open(img_path) as img:
                    img_w, img_h = img.size

                w = x2 - x1
                h = y2 - y1
                if w <= 0 or h <= 0:
                    continue

                cx = (x1 + w / 2) / img_w
                cy = (y1 + h / 2) / img_h
                nw = w / img_w
                nh = h / img_h

                cx = max(0.0, min(1.0, cx))
                cy = max(0.0, min(1.0, cy))
                nw = max(0.001, min(1.0, nw))
                nh = max(0.001, min(1.0, nh))

                dst_name = f"ccpd_{stem}"
                shutil.copy2(img_path, out_img_dir / f"{dst_name}{img_path.suffix}")
                with open(out_lbl_dir / f"{dst_name}.txt", "w") as f:
                    f.write(f"{PLATE_CLASS} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

                total += 1
            except Exception:
                continue

    return total


# ──────────────────────────────────────────────
#  RodoSol-ALPR
# ──────────────────────────────────────────────
def convert_rodosol(split_ratio: float = 0.85):
    """
    RodoSol-ALPR estructura similar a UFPR.
    Anotaciones en .txt con position_plate: x y w h
    """
    rodosol_dir = RAW_DIR / "rodosol_alpr"
    if not rodosol_dir.exists():
        print(f"  RodoSol-ALPR no encontrado en {rodosol_dir}")
        return 0

    images = sorted(rodosol_dir.rglob("*.png")) + sorted(rodosol_dir.rglob("*.jpg"))
    print(f"  RodoSol-ALPR: {len(images)} imágenes encontradas")

    random.seed(SEED)
    if len(images) > RODOSOL_MAX:
        images = random.sample(images, RODOSOL_MAX)
        print(f"  Submuestreado a {RODOSOL_MAX}")

    random.shuffle(images)
    split_idx = int(len(images) * split_ratio)
    splits = {"train": images[:split_idx], "val": images[split_idx:]}

    total = 0
    for split, img_list in splits.items():
        out_img_dir = OUT_DIR / "images" / split
        out_lbl_dir = OUT_DIR / "labels" / split
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in img_list:
            ann_path = img_path.with_suffix(".txt")
            if not ann_path.exists():
                continue

            try:
                with Image.open(img_path) as img:
                    img_w, img_h = img.size

                plate_box = None
                with open(ann_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("position_plate:"):
                            coords = line.split(":")[1].strip().split()
                            if len(coords) == 4:
                                plate_box = [int(c) for c in coords]
                            break

                if plate_box is None:
                    continue

                x, y, w, h = plate_box
                if w <= 0 or h <= 0:
                    continue

                cx = (x + w / 2) / img_w
                cy = (y + h / 2) / img_h
                nw = w / img_w
                nh = h / img_h

                cx = max(0.0, min(1.0, cx))
                cy = max(0.0, min(1.0, cy))
                nw = max(0.001, min(1.0, nw))
                nh = max(0.001, min(1.0, nh))

                dst_name = f"rodosol_{img_path.stem}"
                shutil.copy2(img_path, out_img_dir / f"{dst_name}{img_path.suffix}")
                with open(out_lbl_dir / f"{dst_name}.txt", "w") as f:
                    f.write(f"{PLATE_CLASS} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

                total += 1
            except Exception:
                continue

    return total


def main():
    print("=" * 60)
    print("License Plate Datasets → YOLO Format Converter")
    print("=" * 60)

    total_all = 0

    print("\n[1/2] Convirtiendo CCPD...")
    n = convert_ccpd()
    print(f"  → {n} imágenes convertidas")
    total_all += n

    print("\n[2/2] Convirtiendo RodoSol-ALPR...")
    n = convert_rodosol()
    print(f"  → {n} imágenes convertidas")
    total_all += n

    print(f"\n✅ Total placas convertidas: {total_all}")
    print(f"   Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
