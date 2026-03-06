"""
05_validate_dataset.py — Valida integridad del dataset de anonimización

Verifica:
  1. Cada imagen tiene su label correspondiente (y viceversa)
  2. Todas las labels usan clases válidas (0=face, 1=license_plate)
  3. Todas las coordenadas están en rango [0, 1]
  4. No hay archivos vacíos ni corruptos
  5. Distribución de clases por split
"""

import json
from collections import Counter
from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "datasets" / "processed"
VALID_CLASSES = {0, 1}
CLASS_NAMES = {0: "face", 1: "license_plate"}


def validate_split(split: str) -> dict:
    img_dir = DATA_DIR / "images" / split
    lbl_dir = DATA_DIR / "labels" / split

    if not img_dir.exists() or not lbl_dir.exists():
        return {"error": f"Directorio no encontrado: {img_dir} o {lbl_dir}"}

    img_files = {p.stem: p for p in img_dir.iterdir()
                 if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}}
    lbl_files = {p.stem: p for p in lbl_dir.iterdir() if p.suffix == ".txt"}

    issues = []
    class_counts = Counter()
    bbox_count = 0
    corrupt_images = 0

    # Imágenes sin label
    imgs_no_label = set(img_files.keys()) - set(lbl_files.keys())
    if imgs_no_label:
        issues.append(f"{len(imgs_no_label)} imágenes sin label")

    # Labels sin imagen
    lbls_no_img = set(lbl_files.keys()) - set(img_files.keys())
    if lbls_no_img:
        issues.append(f"{len(lbls_no_img)} labels sin imagen")

    # Validar cada par
    matched = set(img_files.keys()) & set(lbl_files.keys())
    for stem in sorted(matched):
        # Verificar imagen no corrupta
        try:
            with Image.open(img_files[stem]) as img:
                img.verify()
        except Exception:
            corrupt_images += 1
            issues.append(f"Imagen corrupta: {img_files[stem].name}")
            continue

        # Validar labels
        lbl_path = lbl_files[stem]
        with open(lbl_path) as f:
            lines = f.readlines()

        if not lines:
            issues.append(f"Label vacío: {lbl_path.name}")
            continue

        for i, line in enumerate(lines):
            parts = line.strip().split()
            if len(parts) != 5:
                issues.append(f"{lbl_path.name}:{i+1} — {len(parts)} campos (esperados 5)")
                continue

            cls = int(parts[0])
            if cls not in VALID_CLASSES:
                issues.append(f"{lbl_path.name}:{i+1} — clase inválida: {cls}")
                continue

            vals = [float(v) for v in parts[1:]]
            for j, v in enumerate(vals):
                if v < 0 or v > 1:
                    issues.append(f"{lbl_path.name}:{i+1} — valor fuera de rango: {v}")
                    break

            class_counts[cls] += 1
            bbox_count += 1

    return {
        "images": len(img_files),
        "labels": len(lbl_files),
        "matched_pairs": len(matched),
        "bboxes": bbox_count,
        "classes": {CLASS_NAMES.get(k, str(k)): v for k, v in sorted(class_counts.items())},
        "corrupt_images": corrupt_images,
        "issues": issues[:20],  # Primeros 20
        "total_issues": len(issues),
    }


def main():
    print("=" * 60)
    print("Dataset Validation — Anonymization Model")
    print("=" * 60)

    all_ok = True
    report = {}

    for split in ["train", "val", "test"]:
        print(f"\n[{split.upper()}]")
        result = validate_split(split)
        report[split] = result

        if "error" in result:
            print(f"  ❌ {result['error']}")
            all_ok = False
            continue

        print(f"  Imágenes: {result['images']}")
        print(f"  Labels:   {result['labels']}")
        print(f"  Pares:    {result['matched_pairs']}")
        print(f"  Bboxes:   {result['bboxes']}")
        print(f"  Clases:")
        for cls, cnt in result["classes"].items():
            print(f"    {cls}: {cnt}")

        if result["total_issues"] > 0:
            all_ok = False
            print(f"  ⚠️  {result['total_issues']} issues encontrados:")
            for issue in result["issues"]:
                print(f"    - {issue}")

    # Guardar reporte
    meta_dir = BASE / "datasets" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    report_path = meta_dir / "anonymization_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if all_ok:
        print("\n✅ Dataset válido — listo para entrenamiento")
    else:
        print("\n⚠️  Dataset tiene issues — revisar antes de entrenar")

    print(f"   Reporte: {report_path}")


if __name__ == "__main__":
    main()
