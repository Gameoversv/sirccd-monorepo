"""
Script para limpiar y balancear datasets (D-02).

Tareas:
1. Validar integridad de imágenes (corruptas, metadatos)
2. Detectar y eliminar duplicados
3. Normalizar formatos (JPEG/PNG)
4. Balancear clases
"""

from pathlib import Path
import hashlib
import json
from collections import defaultdict
from PIL import Image, ImageStat
import shutil
import argparse
from tqdm import tqdm
import random


BASE_DIR = Path(__file__).parent
PROCESSED_DIR = BASE_DIR / 'processed' / 'combined'
CLEANED_DIR = BASE_DIR / 'processed' / 'cleaned'
METADATA_DIR = BASE_DIR / 'metadata'


def validate_image(img_path: Path) -> dict:
    """
    Valida integridad de una imagen.
    
    Returns:
        dict con: valid (bool), error (str), width (int), height (int)
    """
    result = {
        'valid': False,
        'error': None,
        'width': 0,
        'height': 0,
        'format': None,
        'size_kb': 0
    }
    
    try:
        # Intentar abrir con PIL
        with Image.open(img_path) as img:
            result['width'] = img.width
            result['height'] = img.height
            result['format'] = img.format
            result['size_kb'] = img_path.stat().st_size / 1024
            
            # Verificar que no esté corrupta
            img.verify()
        
        # Verificar tamaño mínimo
        if result['width'] < 32 or result['height'] < 32:
            result['error'] = f'Too small: {result["width"]}x{result["height"]}'
            return result
        
        result['valid'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def compute_image_hash(img_path: Path) -> str:
    """Calcula hash perceptual de imagen para detectar duplicados."""
    try:
        with Image.open(img_path) as img:
            # Resize para comparación rápida
            img_resized = img.resize((8, 8)).convert('L')
            
            # Average hash
            pixels = list(img_resized.getdata())
            avg = sum(pixels) / len(pixels)
            
            hash_bits = ['1' if pixel > avg else '0' for pixel in pixels]
            hash_str = ''.join(hash_bits)
            
            return hash_str
    except:
        return None


def find_duplicates(images: list) -> dict:
    """
    Encuentra imágenes duplicadas usando hashing perceptual.
    
    Returns:
        dict con hash como key y lista de paths como value
    """
    print("\n🔍 Buscando duplicados...")
    hash_map = defaultdict(list)
    
    for img_path in tqdm(images, desc="Calculando hashes"):
        img_hash = compute_image_hash(img_path)
        if img_hash:
            hash_map[img_hash].append(img_path)
    
    # Filtrar solo duplicados
    duplicates = {k: v for k, v in hash_map.items() if len(v) > 1}
    
    return duplicates


def analyze_class_distribution(labels_dir: Path) -> dict:
    """Analiza distribución de clases en detalle."""
    class_counts = defaultdict(int)
    images_per_class = defaultdict(int)
    
    for label_file in labels_dir.glob('*.txt'):
        classes_in_image = set()
        
        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    class_counts[class_id] += 1
                    classes_in_image.add(class_id)
        
        # Contar imágenes por clase
        for cls in classes_in_image:
            images_per_class[cls] += 1
    
    return {
        'annotations_per_class': dict(class_counts),
        'images_per_class': dict(images_per_class)
    }


def clean_images(split: str):
    """Limpia y valida imágenes de un split."""
    print(f"\n🧹 Limpiando split: {split}")
    
    images_src = PROCESSED_DIR / 'images' / split
    labels_src = PROCESSED_DIR / 'labels' / split
    
    images_dst = CLEANED_DIR / 'images' / split
    labels_dst = CLEANED_DIR / 'labels' / split
    
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total': 0,
        'valid': 0,
        'corrupted': 0,
        'too_small': 0,
        'missing_label': 0,
        'errors': []
    }
    
    images = list(images_src.glob('*'))
    
    for img_path in tqdm(images, desc=f"Validando {split}"):
        stats['total'] += 1
        
        # Validar imagen
        validation = validate_image(img_path)
        
        if not validation['valid']:
            stats['corrupted'] += 1
            stats['errors'].append({
                'file': img_path.name,
                'error': validation['error']
            })
            continue
        
        # Verificar que tenga label correspondiente
        label_path = labels_src / f"{img_path.stem}.txt"
        if not label_path.exists():
            stats['missing_label'] += 1
            continue
        
        # Copiar imagen y label válidos
        shutil.copy2(img_path, images_dst / img_path.name)
        shutil.copy2(label_path, labels_dst / label_path.name)
        stats['valid'] += 1
    
    return stats


def balance_classes(strategy='undersample', target_ratio=None):
    """
    Balancea clases usando undersampling o oversampling.
    
    Args:
        strategy: 'undersample' o 'oversample'
        target_ratio: dict con ratios deseados por clase
    """
    print(f"\n⚖️ Balanceando clases con estrategia: {strategy}")
    
    # Analizar distribución actual
    class_images = defaultdict(list)
    
    for split in ['train']:  # Solo balancear train
        labels_dir = CLEANED_DIR / 'labels' / split
        images_dir = CLEANED_DIR / 'images' / split
        
        for label_file in labels_dir.glob('*.txt'):
            classes_in_image = set()
            
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        classes_in_image.add(class_id)
            
            # Asignar imagen a su clase principal
            if classes_in_image:
                primary_class = min(classes_in_image)
                img_path = images_dir / f"{label_file.stem}{get_image_extension(images_dir / label_file.stem)}"
                if img_path.exists():
                    class_images[primary_class].append({
                        'image': img_path,
                        'label': label_file
                    })
    
    # Mostrar distribución actual
    print("\n📊 Distribución actual (train):")
    class_names = {0: 'bache', 1: 'socavon', 2: 'grieta', 3: 'alcantarilla', 4: 'senal', 5: 'alumbrado'}
    for cls, images in sorted(class_images.items()):
        print(f"  Clase {cls} ({class_names.get(cls, 'unknown')}): {len(images)} imágenes")
    
    if strategy == 'undersample':
        # Encontrar clase minoritaria
        min_count = min(len(images) for images in class_images.values())
        print(f"\n🎯 Undersampling a {min_count} imágenes por clase")
        
        balanced_dir = CLEANED_DIR.parent / 'balanced'
        (balanced_dir / 'images' / 'train').mkdir(parents=True, exist_ok=True)
        (balanced_dir / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
        
        for cls, images in class_images.items():
            # Samplear aleatoriamente
            sampled = random.sample(images, min_count)
            
            for item in sampled:
                # Copiar imagen y label
                shutil.copy2(item['image'], balanced_dir / 'images' / 'train' / item['image'].name)
                shutil.copy2(item['label'], balanced_dir / 'labels' / 'train' / item['label'].name)
        
        print(f"✅ Balanceo completado: {min_count * len(class_images)} imágenes totales")
        
        # Copiar val y test sin modificar
        for split in ['val', 'test']:
            src_images = CLEANED_DIR / 'images' / split
            src_labels = CLEANED_DIR / 'labels' / split
            dst_images = balanced_dir / 'images' / split
            dst_labels = balanced_dir / 'labels' / split
            
            if src_images.exists():
                shutil.copytree(src_images, dst_images, dirs_exist_ok=True)
                shutil.copytree(src_labels, dst_labels, dirs_exist_ok=True)
        
        return balanced_dir
    
    elif strategy == 'oversample':
        # Encontrar clase mayoritaria
        max_count = max(len(images) for images in class_images.values())
        print(f"\n🎯 Oversampling a {max_count} imágenes por clase")
        
        balanced_dir = CLEANED_DIR.parent / 'balanced'
        (balanced_dir / 'images' / 'train').mkdir(parents=True, exist_ok=True)
        (balanced_dir / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
        
        for cls, images in class_images.items():
            # Oversamplear con reemplazo
            sampled = random.choices(images, k=max_count)
            
            for i, item in enumerate(sampled):
                suffix = f"_aug{i}" if i >= len(images) else ""
                img_ext = item['image'].suffix
                new_img_name = f"{item['image'].stem}{suffix}{img_ext}"
                new_label_name = f"{item['label'].stem}{suffix}.txt"
                
                shutil.copy2(item['image'], balanced_dir / 'images' / 'train' / new_img_name)
                shutil.copy2(item['label'], balanced_dir / 'labels' / 'train' / new_label_name)
        
        print(f"✅ Balanceo completado: {max_count * len(class_images)} imágenes totales")
        
        # Copiar val y test
        for split in ['val', 'test']:
            src_images = CLEANED_DIR / 'images' / split
            src_labels = CLEANED_DIR / 'labels' / split
            dst_images = balanced_dir / 'images' / split
            dst_labels = balanced_dir / 'labels' / split
            
            if src_images.exists():
                shutil.copytree(src_images, dst_labels, dirs_exist_ok=True)
                shutil.copytree(src_labels, dst_labels, dirs_exist_ok=True)
        
        return balanced_dir


def get_image_extension(path_stem: Path) -> str:
    """Encuentra la extensión de una imagen dado su stem."""
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        if Path(str(path_stem) + ext).exists():
            return ext
    return '.jpg'


def main():
    parser = argparse.ArgumentParser(description='Limpieza y balanceo de datasets (D-02)')
    parser.add_argument('--clean', action='store_true', help='Limpiar imágenes corruptas')
    parser.add_argument('--duplicates', action='store_true', help='Detectar duplicados')
    parser.add_argument('--balance', choices=['undersample', 'oversample', 'none'], 
                       default='none', help='Estrategia de balanceo')
    parser.add_argument('--analyze', action='store_true', help='Solo analizar distribución')
    
    args = parser.parse_args()
    
    # Crear directorios
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.clean:
        print("=" * 60)
        print("🧹 LIMPIEZA DE IMÁGENES")
        print("=" * 60)
        
        all_stats = {}
        for split in ['train', 'val', 'test']:
            stats = clean_images(split)
            all_stats[split] = stats
            
            print(f"\n📊 Resultados {split}:")
            print(f"  Total: {stats['total']}")
            print(f"  Válidas: {stats['valid']}")
            print(f"  Corruptas: {stats['corrupted']}")
            print(f"  Sin label: {stats['missing_label']}")
        
        # Guardar reporte
        report_path = METADATA_DIR / 'cleaning_report.json'
        with open(report_path, 'w') as f:
            json.dump(all_stats, f, indent=2)
        print(f"\n✅ Reporte guardado: {report_path}")
    
    if args.duplicates:
        print("\n" + "=" * 60)
        print("🔍 DETECCIÓN DE DUPLICADOS")
        print("=" * 60)
        
        all_images = []
        for split in ['train', 'val', 'test']:
            images_dir = CLEANED_DIR / 'images' / split
            if images_dir.exists():
                all_images.extend(images_dir.glob('*'))
        
        duplicates = find_duplicates(all_images)
        
        print(f"\n📊 Encontrados {len(duplicates)} grupos de duplicados")
        
        if duplicates:
            dup_report = []
            for hash_val, paths in duplicates.items():
                print(f"\nDuplicados ({len(paths)} imágenes):")
                for p in paths:
                    print(f"  - {p.relative_to(CLEANED_DIR)}")
                dup_report.append({
                    'count': len(paths),
                    'files': [str(p.relative_to(CLEANED_DIR)) for p in paths]
                })
            
            # Guardar reporte
            dup_path = METADATA_DIR / 'duplicates_report.json'
            with open(dup_path, 'w') as f:
                json.dump(dup_report, f, indent=2)
            print(f"\n✅ Reporte guardado: {dup_path}")
    
    if args.analyze:
        print("\n" + "=" * 60)
        print("📊 ANÁLISIS DE DISTRIBUCIÓN")
        print("=" * 60)
        
        class_names = {0: 'bache', 1: 'socavon', 2: 'grieta', 3: 'alcantarilla', 4: 'senal', 5: 'alumbrado'}
        
        for split in ['train', 'val', 'test']:
            labels_dir = CLEANED_DIR / 'labels' / split
            if labels_dir.exists():
                dist = analyze_class_distribution(labels_dir)
                
                print(f"\n{split.upper()}:")
                print("  Anotaciones por clase:")
                for cls, count in sorted(dist['annotations_per_class'].items()):
                    print(f"    {cls} ({class_names.get(cls, 'unknown')}): {count}")
                
                print("  Imágenes por clase:")
                for cls, count in sorted(dist['images_per_class'].items()):
                    print(f"    {cls} ({class_names.get(cls, 'unknown')}): {count}")
    
    if args.balance != 'none':
        print("\n" + "=" * 60)
        print(f"⚖️ BALANCEO DE CLASES ({args.balance})")
        print("=" * 60)
        
        balanced_dir = balance_classes(strategy=args.balance)
        
        # Generar nuevo data.yaml
        yaml_path = balanced_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            f.write(f"# SIRCCD Dataset (Balanced - {args.balance})\n")
            f.write(f"path: {balanced_dir.absolute()}\n")
            f.write("train: images/train\n")
            f.write("val: images/val\n")
            f.write("test: images/test\n")
            f.write("nc: 6\n")
            f.write("names:\n")
            f.write("  0: bache\n")
            f.write("  1: socavon\n")
            f.write("  2: grieta\n")
            f.write("  3: alcantarilla\n")
            f.write("  4: senal\n")
            f.write("  5: alumbrado\n")
        
        print(f"\n✅ data.yaml generado: {yaml_path}")


if __name__ == '__main__':
    main()
