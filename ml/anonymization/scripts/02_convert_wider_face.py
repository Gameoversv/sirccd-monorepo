"""
02_convert_wider_face.py — Convierte WIDER FACE a formato YOLO

Espera la siguiente estructura en raw/:
  wider_face/
    WIDER_train/images/0--Parade/*.jpg, 1--Handshaking/*.jpg, ...
    WIDER_val/images/0--Parade/*.jpg, ...
    wider_face_split/
      wider_face_train_bbx_gt.txt
      wider_face_val_bbx_gt.txt

Genera labels YOLO (clase 0 = face) en:
  processed/wider_face_yolo/images/{train,val}/
  processed/wider_face_yolo/labels/{train,val}/

Formato YOLO por línea: class cx cy w h (normalizado 0-1)
"""

import os
import shutil
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "datasets" / "raw" / "wider_face"
OUT_DIR = Path(__file__).resolve().parent.parent / "datasets" / "processed" / "wider_face_yolo"

FACE_CLASS = 0


def parse_wider_annotations(ann_path: Path, images_root: Path, split: str):
    """Lee el archivo de anotaciones de WIDER FACE y genera labels YOLO."""
    out_images = OUT_DIR / "images" / split
    out_labels = OUT_DIR / "labels" / split
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels.mkdir(parents=True, exist_ok=True)

    with open(ann_path, "r") as f:
        lines = f.readlines()

    idx = 0
    total = 0
    skipped = 0

    while idx < len(lines):
        # Línea con la ruta relativa de la imagen
        img_rel = lines[idx].strip()
        idx += 1

        img_path = images_root / img_rel
        if not img_path.exists():
            # Saltar imagen no encontrada
            num_faces = int(lines[idx].strip())
            idx += 1
            idx += max(num_faces, 1)
            skipped += 1
            continue

        num_faces = int(lines[idx].strip())
        idx += 1

        # Caso especial: 0 caras marcadas con una línea dummy
        if num_faces == 0:
            idx += 1
            continue

        # Leer imagen para obtener dimensiones
        from PIL import Image
        with Image.open(img_path) as img:
            img_w, img_h = img.size

        yolo_lines = []
        for _ in range(num_faces):
            parts = lines[idx].strip().split()
            idx += 1

            # Formato WIDER FACE: x1 y1 w h blur expression illumination invalid occlusion pose
            x1, y1, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])

            # Filtrar cajas inválidas (w<=0 o h<=0) o marcadas como invalid
            if w <= 0 or h <= 0:
                continue
            if len(parts) >= 8 and int(parts[7]) == 1:
                # invalid flag
                continue

            # Convertir a YOLO: center_x, center_y, width, height (normalizado)
            cx = (x1 + w / 2) / img_w
            cy = (y1 + h / 2) / img_h
            nw = w / img_w
            nh = h / img_h

            # Clamp to [0, 1]
            cx = max(0.0, min(1.0, cx))
            cy = max(0.0, min(1.0, cy))
            nw = max(0.001, min(1.0, nw))
            nh = max(0.001, min(1.0, nh))

            yolo_lines.append(f"{FACE_CLASS} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        if not yolo_lines:
            continue

        # Copiar imagen
        safe_name = img_rel.replace("/", "_").replace("\\", "_")
        stem = Path(safe_name).stem
        suffix = img_path.suffix

        dst_img = out_images / f"{stem}{suffix}"
        dst_lbl = out_labels / f"{stem}.txt"

        shutil.copy2(img_path, dst_img)
        with open(dst_lbl, "w") as lf:
            lf.write("\n".join(yolo_lines) + "\n")

        total += 1

    return total, skipped


def main():
    print("=" * 60)
    print("WIDER FACE → YOLO Format Converter")
    print("=" * 60)

    ann_dir = RAW_DIR / "wider_face_split"

    # Train
    train_ann = ann_dir / "wider_face_train_bbx_gt.txt"
    train_imgs = RAW_DIR / "WIDER_train" / "images"
    if train_ann.exists() and train_imgs.exists():
        print(f"\n[Train] Procesando: {train_ann}")
        total, skipped = parse_wider_annotations(train_ann, train_imgs, "train")
        print(f"  → {total} imágenes convertidas, {skipped} omitidas")
    else:
        print(f"  [Train] No encontrado: {train_ann} o {train_imgs}")

    # Val
    val_ann = ann_dir / "wider_face_val_bbx_gt.txt"
    val_imgs = RAW_DIR / "WIDER_val" / "images"
    if val_ann.exists() and val_imgs.exists():
        print(f"\n[Val] Procesando: {val_ann}")
        total, skipped = parse_wider_annotations(val_ann, val_imgs, "val")
        print(f"  → {total} imágenes convertidas, {skipped} omitidas")
    else:
        print(f"  [Val] No encontrado: {val_ann} o {val_imgs}")

    print("\n✅ Conversión WIDER FACE completada")
    print(f"   Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
