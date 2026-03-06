"""
04_merge_and_split.py — Unifica datasets de rostros y placas en un solo dataset YOLO

Lee:
  processed/wider_face_yolo/{images,labels}/{train,val}/
  processed/plates_yolo/{images,labels}/{train,val}/

Genera:
  processed/images/{train,val,test}/
  processed/labels/{train,val,test}/

Estrategia:
  - Combina train de ambas fuentes → shuffle → 85% train / 10% val / 5% test
  - Combina val de ambas fuentes   → agrega al pool antes de split
  - Genera reporte de distribución de clases
"""

import json
import random
import shutil
from collections import Counter
from pathlib import Path

SEED = 42

BASE = Path(__file__).resolve().parent.parent
FACES_DIR = BASE / "datasets" / "processed" / "wider_face_yolo"
PLATES_DIR = BASE / "datasets" / "processed" / "plates_yolo"
OUT_DIR = BASE / "datasets" / "processed"
META_DIR = BASE / "datasets" / "metadata"

TRAIN_RATIO = 0.85
VAL_RATIO = 0.10
TEST_RATIO = 0.05

CLASS_NAMES = {0: "face", 1: "license_plate"}


def collect_pairs(src_dir: Path) -> list[tuple[Path, Path]]:
    """Recolecta pares (imagen, label) de un directorio YOLO."""
    pairs = []
    for split in ["train", "val"]:
        img_dir = src_dir / "images" / split
        lbl_dir = src_dir / "labels" / split
        if not img_dir.exists():
            continue
        for img_path in sorted(img_dir.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                continue
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            if lbl_path.exists():
                pairs.append((img_path, lbl_path))
    return pairs


def count_classes(lbl_path: Path) -> Counter:
    """Cuenta instancias de cada clase en un archivo de labels."""
    c = Counter()
    with open(lbl_path) as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                c[int(parts[0])] += 1
    return c


def main():
    print("=" * 60)
    print("Merge & Split — Anonymization Dataset")
    print("=" * 60)

    # Recolectar pares de ambos datasets
    print("\nRecolectando pares de imágenes...")
    face_pairs = collect_pairs(FACES_DIR)
    plate_pairs = collect_pairs(PLATES_DIR)

    print(f"  Rostros: {len(face_pairs)} pares")
    print(f"  Placas:  {len(plate_pairs)} pares")

    all_pairs = face_pairs + plate_pairs
    print(f"  Total:   {len(all_pairs)} pares")

    if not all_pairs:
        print("\n❌ No se encontraron datos. Ejecuta primero los scripts de conversión.")
        return

    # Shuffle determinístico
    random.seed(SEED)
    random.shuffle(all_pairs)

    # Split
    n = len(all_pairs)
    n_train = int(n * TRAIN_RATIO)
    n_val = int(n * VAL_RATIO)
    # test = resto

    train_pairs = all_pairs[:n_train]
    val_pairs = all_pairs[n_train:n_train + n_val]
    test_pairs = all_pairs[n_train + n_val:]

    print(f"\n  Train: {len(train_pairs)}")
    print(f"  Val:   {len(val_pairs)}")
    print(f"  Test:  {len(test_pairs)}")

    # Copiar archivos a la estructura final
    splits = {"train": train_pairs, "val": val_pairs, "test": test_pairs}
    class_counts = {"train": Counter(), "val": Counter(), "test": Counter()}

    for split, pairs in splits.items():
        img_out = OUT_DIR / "images" / split
        lbl_out = OUT_DIR / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img_src, lbl_src in pairs:
            # Nombre único basado en el stem original
            dst_name = img_src.stem
            shutil.copy2(img_src, img_out / f"{dst_name}{img_src.suffix}")
            shutil.copy2(lbl_src, lbl_out / f"{dst_name}.txt")

            # Contar clases
            class_counts[split] += count_classes(lbl_src)

    # Generar reporte
    META_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "total_images": n,
        "splits": {
            split: {
                "images": len(pairs),
                "classes": {CLASS_NAMES.get(k, str(k)): v for k, v in class_counts[split].items()}
            }
            for split, pairs in splits.items()
        },
        "class_names": CLASS_NAMES,
        "seed": SEED,
    }

    report_path = META_DIR / "anonymization_dataset_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Distribución de clases:")
    for split in ["train", "val", "test"]:
        print(f"  {split}:")
        for cls_id, count in sorted(class_counts[split].items()):
            print(f"    {CLASS_NAMES.get(cls_id, cls_id)}: {count}")

    print(f"\n✅ Dataset unificado generado en: {OUT_DIR}")
    print(f"   Reporte: {report_path}")


if __name__ == "__main__":
    main()
