"""
Script para etiquetar severidad de baches y grietas a partir de bounding boxes YOLO.
- Severidad bache: por área relativa
- Severidad grieta: por longitud relativa
- Criterios en severity_criteria.md
"""

from pathlib import Path
import shutil
import os

# Umbrales (ajustables)
BACHE_THRESHOLDS = [(0.01, 'baja'), (0.03, 'media'), (1.0, 'alta')]
GRIETA_THRESHOLDS = [(0.2, 'baja'), (0.4, 'media'), (1.0, 'alta')]

# Clases
CLASE_BACHE = 0
CLASE_GRIETA = 2

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
LABELS_DIR = SCRIPT_DIR / 'processed' / 'split' / 'labels'
IMAGES_DIR = SCRIPT_DIR / 'processed' / 'split' / 'images'
OUTPUT_DIR = SCRIPT_DIR / 'processed' / 'split' / 'labels_severity'


def get_image_size(image_path):
    from PIL import Image
    with Image.open(image_path) as img:
        return img.size  # (width, height)


def get_severity_bache(area_rel):
    for th, label in BACHE_THRESHOLDS:
        if area_rel < th:
            return label
    return 'alta'


def get_severity_grieta(long_rel):
    for th, label in GRIETA_THRESHOLDS:
        if long_rel < th:
            return label
    return 'alta'


def process_split(split):
    labels_split = LABELS_DIR / split
    images_split = IMAGES_DIR / split
    output_split = OUTPUT_DIR / split
    output_split.mkdir(parents=True, exist_ok=True)

    for label_file in labels_split.glob('*.txt'):
        image_file = images_split / (label_file.stem + '.jpg')
        if not image_file.exists():
            image_file = images_split / (label_file.stem + '.png')
        if not image_file.exists():
            continue
        width, height = get_image_size(image_file)
        with open(label_file) as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            cls = int(parts[0])
            x_c, y_c, w_rel, h_rel = map(float, parts[1:5])
            # Convertir a píxeles
            w = w_rel * width
            h = h_rel * height
            area_rel = (w * h) / (width * height)
            long_rel = max(w / width, h / height)
            if cls == CLASE_BACHE:
                sev = get_severity_bache(area_rel)
            elif cls == CLASE_GRIETA:
                sev = get_severity_grieta(long_rel)
            else:
                sev = 'NA'
            new_lines.append(line.strip() + f' {sev}\n')
        with open(output_split / label_file.name, 'w') as f:
            f.writelines(new_lines)


def main():
    for split in ['train', 'val', 'test']:
        print(f'Procesando {split}...')
        process_split(split)
    print('✅ Etiquetado de severidad completado.')

if __name__ == '__main__':
    main()
