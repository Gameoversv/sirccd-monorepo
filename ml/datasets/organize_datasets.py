"""
Script para organizar y convertir datasets a formato YOLO.

Uso:
    python organize_datasets.py --convert       # Convertir todos los datasets
    python organize_datasets.py --stats         # Generar estadísticas
    python organize_datasets.py --validate      # Validar integridad
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
import random


# Mapeo de clases de datasets originales a clases SIRCCD
CLASS_MAPPING = {
    'RDD2022': {
        'D00': 'grieta',      # Longitudinal crack
        'D10': 'grieta',      # Transverse crack
        'D20': 'bache',       # Alligator crack
        'D40': 'bache',       # Pothole
    },
    'N-RDD2024': {
        'crack': 'grieta',
        'pothole': 'bache',
        'patch': 'grieta',
    },
    'CRACK500': {
        'crack': 'grieta',
    },
    'CFD': {
        'crack': 'grieta',
    },
    'Pothole-600': {
        'pothole': 'bache',
    },
    'SUT-Crack': {
        'crack': 'grieta',
    }
}

# Clases finales de SIRCCD
SIRCCD_CLASSES = {
    'bache': 0,
    'socavon': 1,
    'grieta': 2,
    'alcantarilla': 3,
    'senal': 4,
    'alumbrado': 5,
}

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / 'raw'
PROCESSED_DIR = BASE_DIR / 'processed' / 'combined'
METADATA_DIR = BASE_DIR / 'metadata'


def convert_voc_to_yolo(xml_path: Path, img_width: int, img_height: int, dataset_name: str) -> List[str]:
    """
    Convierte anotaciones PASCAL VOC (XML) a formato YOLO.
    
    Args:
        xml_path: Ruta al archivo XML
        img_width: Ancho de la imagen
        img_height: Alto de la imagen
        dataset_name: Nombre del dataset para mapeo de clases
    
    Returns:
        Lista de anotaciones en formato YOLO (una línea por objeto)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    yolo_annotations = []
    
    for obj in root.findall('object'):
        class_name = obj.find('name').text
        
        # Mapear clase original a clase SIRCCD
        if class_name not in CLASS_MAPPING.get(dataset_name, {}):
            continue
        
        sirccd_class = CLASS_MAPPING[dataset_name][class_name]
        class_id = SIRCCD_CLASSES[sirccd_class]
        
        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        ymin = float(bbox.find('ymin').text)
        xmax = float(bbox.find('xmax').text)
        ymax = float(bbox.find('ymax').text)
        
        # Convertir a formato YOLO (normalizado)
        x_center = ((xmin + xmax) / 2) / img_width
        y_center = ((ymin + ymax) / 2) / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height
        
        yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    return yolo_annotations


def convert_coco_to_yolo(coco_json: Dict, dataset_name: str) -> Dict[str, List[str]]:
    """
    Convierte anotaciones COCO (JSON) a formato YOLO.
    
    Args:
        coco_json: Diccionario con anotaciones COCO
        dataset_name: Nombre del dataset
    
    Returns:
        Diccionario {image_id: [anotaciones_yolo]}
    """
    annotations_by_image = defaultdict(list)
    
    # Crear mapeo de image_id a dimensiones
    image_info = {img['id']: (img['width'], img['height'], img['file_name']) 
                  for img in coco_json['images']}
    
    # Crear mapeo de category_id a nombre
    category_names = {cat['id']: cat['name'] for cat in coco_json['categories']}
    
    for ann in coco_json['annotations']:
        img_id = ann['image_id']
        if img_id not in image_info:
            continue
        
        img_width, img_height, img_name = image_info[img_id]
        
        category_name = category_names[ann['category_id']]
        
        # Mapear a clase SIRCCD
        if category_name not in CLASS_MAPPING.get(dataset_name, {}):
            continue
        
        sirccd_class = CLASS_MAPPING[dataset_name][category_name]
        class_id = SIRCCD_CLASSES[sirccd_class]
        
        # COCO bbox: [x, y, width, height]
        x, y, w, h = ann['bbox']
        
        # Convertir a YOLO (normalizado, centro)
        x_center = (x + w / 2) / img_width
        y_center = (y + h / 2) / img_height
        width = w / img_width
        height = h / img_height
        
        yolo_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
        annotations_by_image[img_name].append(yolo_line)
    
    return dict(annotations_by_image)


def process_rdd2022():
    """Procesa el dataset RDD2022 (ya en formato YOLO, solo mapea clases)."""
    print("Procesando RDD2022...")
    dataset_dir = RAW_DIR / 'RDD2022'
    
    if not dataset_dir.exists():
        print(f"  ⚠️  Directorio {dataset_dir} no encontrado. Saltando...")
        return 0
    
    # RDD2022 mapeo de clases: D00, D10, D20, D40
    # D00 (Longitudinal crack) → grieta (2)
    # D10 (Transverse crack) → grieta (2)
    # D20 (Alligator crack) → bache (0)
    # D40 (Pothole) → bache (0)
    class_map_rdd = {
        0: 2,  # D00 → grieta
        1: 2,  # D10 → grieta
        2: 0,  # D20 → bache
        3: 0,  # D40 → bache
    }
    
    processed_count = 0
    
    for split in ['train', 'val', 'test']:
        images_src = dataset_dir / split / 'images'
        labels_src = dataset_dir / split / 'labels'
        
        if not images_src.exists() or not labels_src.exists():
            print(f"  ⚠️  Split {split} no encontrado")
            continue
        
        images_dst = PROCESSED_DIR / 'images' / split
        labels_dst = PROCESSED_DIR / 'labels' / split
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        # Copiar imágenes
        for img in images_src.glob('*'):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                shutil.copy2(img, images_dst / f"rdd2022_{img.name}")
                processed_count += 1
        
        # Convertir y copiar labels
        for label in labels_src.glob('*.txt'):
            new_label_path = labels_dst / f"rdd2022_{label.name}"
            with open(label, 'r') as f_in, open(new_label_path, 'w') as f_out:
                for line in f_in:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        orig_class = int(parts[0])
                        new_class = class_map_rdd.get(orig_class, orig_class)
                        f_out.write(f"{new_class} {' '.join(parts[1:])}\n")
    
    print(f"  ✅ RDD2022: {processed_count} imágenes procesadas")
    return processed_count


def process_n_rdd2024():
    """Procesa el dataset N-RDD2024 (ya en formato YOLO)."""
    print("Procesando N-RDD2024...")
    dataset_dir = RAW_DIR / 'N-RDD2024'
    
    if not dataset_dir.exists():
        print(f"  ⚠️  Directorio {dataset_dir} no encontrado. Saltando...")
        return 0
    
    # N-RDD2024 tiene clases: crack, pothole, patch
    # Mapeo a SIRCCD: crack→grieta(2), pothole→bache(0), patch→grieta(2)
    class_map_nrdd = {
        0: 2,  # crack → grieta
        1: 0,  # pothole → bache
        2: 2,  # patch → grieta
    }
    
    processed_count = 0
    split_mapping = {'train': 'train', 'valid': 'val', 'test': 'test'}
    
    for orig_split, target_split in split_mapping.items():
        images_src = dataset_dir / orig_split / 'images'
        labels_src = dataset_dir / orig_split / 'labels'
        
        if not images_src.exists():
            continue
        
        images_dst = PROCESSED_DIR / 'images' / target_split
        labels_dst = PROCESSED_DIR / 'labels' / target_split
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        # Copiar imágenes
        for img in images_src.glob('*'):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                shutil.copy2(img, images_dst / f"nrdd_{img.name}")
                processed_count += 1
        
        # Convertir labels si existen
        if labels_src.exists():
            for label in labels_src.glob('*.txt'):
                new_label_path = labels_dst / f"nrdd_{label.name}"
                with open(label, 'r') as f_in, open(new_label_path, 'w') as f_out:
                    for line in f_in:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            orig_class = int(parts[0])
                            new_class = class_map_nrdd.get(orig_class, orig_class)
                            f_out.write(f"{new_class} {' '.join(parts[1:])}\n")
    
    print(f"  ✅ N-RDD2024: {processed_count} imágenes procesadas")
    return processed_count


def process_rdd2020():
    """Procesa el dataset RDD2020 (similar a RDD2022)."""
    print("Procesando RDD2020...")
    dataset_dir = RAW_DIR / 'RDD2020'
    
    if not dataset_dir.exists():
        print(f"  ⚠️  Directorio {dataset_dir} no encontrado. Saltando...")
        return 0
    
    # Mismo mapeo que RDD2022
    class_map_rdd = {
        0: 2,  # D00 → grieta
        1: 2,  # D10 → grieta
        2: 0,  # D20 → bache
        3: 0,  # D40 → bache
    }
    
    processed_count = 0
    split_mapping = {'train': 'train', 'valid': 'val', 'test': 'test'}
    
    for orig_split, target_split in split_mapping.items():
        images_src = dataset_dir / orig_split / 'images'
        labels_src = dataset_dir / orig_split / 'labels'
        
        if not images_src.exists():
            continue
        
        images_dst = PROCESSED_DIR / 'images' / target_split
        labels_dst = PROCESSED_DIR / 'labels' / target_split
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        # Copiar imágenes
        for img in images_src.glob('*'):
            if img.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                shutil.copy2(img, images_dst / f"rdd2020_{img.name}")
                processed_count += 1
        
        # Convertir labels
        if labels_src.exists():
            for label in labels_src.glob('*.txt'):
                new_label_path = labels_dst / f"rdd2020_{label.name}"
                with open(label, 'r') as f_in, open(new_label_path, 'w') as f_out:
                    for line in f_in:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            orig_class = int(parts[0])
                            new_class = class_map_rdd.get(orig_class, orig_class)
                            f_out.write(f"{new_class} {' '.join(parts[1:])}\n")
    
    print(f"  ✅ RDD2020: {processed_count} imágenes procesadas")
    return processed_count


def process_pothole600():
    """Procesa el dataset Pothole-600 (máscaras PNG → YOLO bboxes)."""
    print("Procesando Pothole-600...")
    dataset_dir = RAW_DIR / 'Pothole-600' / 'pothole600'
    
    if not dataset_dir.exists():
        print(f"  ⚠️  Directorio {dataset_dir} no encontrado. Saltando...")
        return 0
    
    from PIL import Image
    import numpy as np
    
    processed_count = 0
    split_mapping = {'training': 'train', 'testing': 'test', 'validation': 'val'}
    
    for orig_split, target_split in split_mapping.items():
        rgb_dir = dataset_dir / orig_split / 'rgb'
        label_dir = dataset_dir / orig_split / 'label'
        
        if not rgb_dir.exists() or not label_dir.exists():
            continue
        
        images_dst = PROCESSED_DIR / 'images' / target_split
        labels_dst = PROCESSED_DIR / 'labels' / target_split
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        for img_file in rgb_dir.glob('*.png'):
            mask_file = label_dir / img_file.name
            
            if not mask_file.exists():
                continue
            
            # Leer imagen y máscara
            img = Image.open(img_file)
            mask = Image.open(mask_file).convert('L')
            
            img_width, img_height = img.size
            mask_array = np.array(mask)
            
            # Encontrar regiones de potholes (píxeles > 127)
            binary_mask = (mask_array > 127).astype(np.uint8)
            
            # Encontrar contornos usando connected components
            from skimage import measure
            labeled_mask = measure.label(binary_mask)
            regions = measure.regionprops(labeled_mask)
            
            # Copiar imagen
            dst_img = images_dst / f"pothole600_{img_file.name}"
            shutil.copy2(img_file, dst_img)
            
            # Generar anotaciones YOLO
            dst_label = labels_dst / f"pothole600_{img_file.stem}.txt"
            with open(dst_label, 'w') as f:
                for region in regions:
                    # Obtener bounding box
                    minr, minc, maxr, maxc = region.bbox
                    
                    # Filtrar bboxes muy pequeñas
                    width = maxc - minc
                    height = maxr - minr
                    if width < 10 or height < 10:
                        continue
                    
                    # Convertir a YOLO format (normalized)
                    x_center = (minc + maxc) / 2 / img_width
                    y_center = (minr + maxr) / 2 / img_height
                    width_norm = width / img_width
                    height_norm = height / img_height
                    
                    # Clase 0 = bache
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {width_norm:.6f} {height_norm:.6f}\n")
            
            processed_count += 1
    
    print(f"  ✅ Pothole-600: {processed_count} imágenes procesadas")
    return processed_count


def generate_data_yaml():
    """Genera el archivo data.yaml para entrenamiento YOLO."""
    data_yaml = {
        'path': str(PROCESSED_DIR.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': len(SIRCCD_CLASSES),
        'names': list(SIRCCD_CLASSES.keys())
    }
    
    yaml_path = PROCESSED_DIR / 'data.yaml'
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(f"# SIRCCD Dataset Configuration\n")
        f.write(f"# Generated: {Path(__file__).name}\n\n")
        for key, value in data_yaml.items():
            if isinstance(value, list):
                f.write(f"{key}:\n")
                for i, name in enumerate(value):
                    f.write(f"  {i}: {name}\n")
            else:
                f.write(f"{key}: {value}\n")
    
    print(f"✅ Generado {yaml_path}")


def generate_statistics():
    """Genera estadísticas de los datasets."""
    print("\nGenerando estadísticas...")
    
    stats = {
        'datasets': {},
        'total_images': 0,
        'total_annotations': 0,
        'class_distribution': defaultdict(int),
        'split_distribution': {
            'train': 0,
            'val': 0,
            'test': 0
        }
    }
    
    # Contar imágenes y anotaciones en processed/
    for split in ['train', 'val', 'test']:
        images_dir = PROCESSED_DIR / 'images' / split
        labels_dir = PROCESSED_DIR / 'labels' / split
        
        if not images_dir.exists():
            continue
        
        n_images = len(list(images_dir.glob('*.jpg'))) + len(list(images_dir.glob('*.png')))
        stats['split_distribution'][split] = n_images
        stats['total_images'] += n_images
        
        if labels_dir.exists():
            for label_file in labels_dir.glob('*.txt'):
                with open(label_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            class_id = int(line.split()[0])
                            class_name = list(SIRCCD_CLASSES.keys())[class_id]
                            stats['class_distribution'][class_name] += 1
                            stats['total_annotations'] += 1
    
    # Guardar estadísticas
    stats_path = METADATA_DIR / 'dataset_stats.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Estadísticas guardadas en {stats_path}")
    print(f"\nResumen:")
    print(f"  Total de imágenes: {stats['total_images']}")
    print(f"  Total de anotaciones: {stats['total_annotations']}")
    print(f"  Distribución por split:")
    for split, count in stats['split_distribution'].items():
        print(f"    {split}: {count}")
    print(f"  Distribución por clase:")
    for class_name, count in stats['class_distribution'].items():
        print(f"    {class_name}: {count}")


def validate_datasets():
    """Valida la integridad de los datasets."""
    print("\nValidando datasets...")
    
    issues = []
    
    # Verificar que cada imagen tenga su label correspondiente
    for split in ['train', 'val', 'test']:
        images_dir = PROCESSED_DIR / 'images' / split
        labels_dir = PROCESSED_DIR / 'labels' / split
        
        if not images_dir.exists():
            continue
        
        for img_path in images_dir.glob('*'):
            if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                continue
            
            label_path = labels_dir / f"{img_path.stem}.txt"
            if not label_path.exists():
                issues.append(f"Falta label para {img_path.name} en {split}")
    
    if issues:
        print(f"⚠️  Se encontraron {len(issues)} problemas:")
        for issue in issues[:10]:  # Mostrar solo los primeros 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... y {len(issues) - 10} más")
    else:
        print("✅ Todos los datasets son válidos")


def save_class_mapping():
    """Guarda el mapeo de clases en metadata."""
    mapping_data = {
        'sirccd_classes': SIRCCD_CLASSES,
        'dataset_mappings': CLASS_MAPPING,
        'description': 'Mapeo de clases de datasets originales a clases SIRCCD'
    }
    
    mapping_path = METADATA_DIR / 'class_mapping.json'
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Mapeo de clases guardado en {mapping_path}")


def main():
    parser = argparse.ArgumentParser(description='Organizar y convertir datasets a formato YOLO')
    parser.add_argument('--convert', action='store_true', help='Convertir datasets a YOLO')
    parser.add_argument('--stats', action='store_true', help='Generar estadísticas')
    parser.add_argument('--validate', action='store_true', help='Validar integridad')
    
    args = parser.parse_args()
    
    if args.convert:
        print("🔄 Convirtiendo datasets a formato YOLO...\n")
        
        # Crear directorios si no existen
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Procesar cada dataset
        total_processed = 0
        total_processed += process_rdd2022()
        total_processed += process_rdd2020()
        total_processed += process_n_rdd2024()
        total_processed += process_pothole600()
        # CFD y CRACK500 requieren conversión más compleja (máscaras → bboxes)
        
        print(f"\n✅ Procesadas {total_processed} imágenes en total")
        
        # Generar archivos de configuración
        generate_data_yaml()
        save_class_mapping()
    
    if args.stats:
        generate_statistics()
    
    if args.validate:
        validate_datasets()
    
    if not any([args.convert, args.stats, args.validate]):
        print("ℹ️  Usa --convert, --stats o --validate para ejecutar acciones")
        print("\nEstructura de directorios:")
        print(f"  📁 raw/: {len(list(RAW_DIR.glob('*')))} datasets")
        print(f"  📁 processed/: {PROCESSED_DIR.exists()}")
        print(f"  📁 metadata/: {METADATA_DIR.exists()}")


if __name__ == '__main__':
    main()
