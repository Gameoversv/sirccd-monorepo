"""
Script para particionar dataset en train/val/test con seed fija.

D-03: Garantiza reproductibilidad mediante:
- Seed fija para random shuffling
- Particionado estratificado por clase
- Validación de proporciones finales
"""

from pathlib import Path
import random
import shutil
import json
from collections import defaultdict
from datetime import datetime


# Configuración
RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.20
TEST_RATIO = 0.10

SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
COMBINED_DIR = SCRIPT_DIR / 'processed' / 'combined'
OUTPUT_DIR = SCRIPT_DIR / 'processed' / 'split'


def get_image_class(label_file):
    """Extrae las clases presentes en un archivo de label.
    
    Para estratificación, usamos la clase dominante (más anotaciones).
    """
    if not label_file.exists():
        return None
    
    class_counts = defaultdict(int)
    with open(label_file) as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                cls = int(parts[0])
                class_counts[cls] += 1
    
    if not class_counts:
        return None
    
    # Retornar clase con más anotaciones
    return max(class_counts.items(), key=lambda x: x[1])[0]


def collect_all_samples():
    """Recolecta todas las imágenes y sus clases del dataset combinado."""
    print("📦 Recolectando muestras del dataset combinado...")
    
    samples_by_class = defaultdict(list)
    
    for split in ['train', 'val', 'test']:
        images_dir = COMBINED_DIR / 'images' / split
        labels_dir = COMBINED_DIR / 'labels' / split
        
        for img_file in images_dir.glob('*.*'):
            if img_file.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
                continue
            
            label_file = labels_dir / f"{img_file.stem}.txt"
            cls = get_image_class(label_file)
            
            if cls is not None:
                samples_by_class[cls].append({
                    'image': img_file,
                    'label': label_file,
                    'class': cls
                })
    
    total_samples = sum(len(samples) for samples in samples_by_class.values())
    print(f"   Total: {total_samples} muestras")
    
    for cls, samples in sorted(samples_by_class.items()):
        class_names = {0: 'bache', 2: 'grieta', 4: 'señal'}
        print(f"   Clase {cls} ({class_names.get(cls, 'unknown')}): {len(samples)} muestras")
    
    return samples_by_class


def stratified_split(samples_by_class, train_ratio, val_ratio, test_ratio, seed):
    """Particiona samples de manera estratificada manteniendo proporciones por clase."""
    random.seed(seed)
    
    splits = {'train': [], 'val': [], 'test': []}
    
    for cls, samples in samples_by_class.items():
        # Shuffle con seed fija
        shuffled = samples.copy()
        random.shuffle(shuffled)
        
        n_total = len(shuffled)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        splits['train'].extend(shuffled[:n_train])
        splits['val'].extend(shuffled[n_train:n_train + n_val])
        splits['test'].extend(shuffled[n_train + n_val:])
    
    # Shuffle final de cada split (manteniendo seed)
    for split_name in splits:
        random.shuffle(splits[split_name])
    
    return splits


def copy_split_files(splits):
    """Copia archivos a sus respectivos splits."""
    print("\n📋 Copiando archivos a nuevos splits...")
    
    # Limpiar directorio de salida
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    stats = {}
    
    for split_name, samples in splits.items():
        print(f"\n   {split_name.upper()}:")
        
        images_dst = OUTPUT_DIR / 'images' / split_name
        labels_dst = OUTPUT_DIR / 'labels' / split_name
        
        images_dst.mkdir(parents=True, exist_ok=True)
        labels_dst.mkdir(parents=True, exist_ok=True)
        
        class_counts = defaultdict(int)
        
        for i, sample in enumerate(samples):
            # Copiar imagen
            dst_img = images_dst / sample['image'].name
            shutil.copy2(sample['image'], dst_img)
            
            # Copiar label
            dst_label = labels_dst / sample['label'].name
            shutil.copy2(sample['label'], dst_label)
            
            class_counts[sample['class']] += 1
            
            if (i + 1) % 10000 == 0:
                print(f"      Procesadas: {i + 1}/{len(samples)}")
        
        stats[split_name] = {
            'total': len(samples),
            'class_distribution': dict(class_counts)
        }
        
        print(f"      Total: {len(samples)}")
        for cls, count in sorted(class_counts.items()):
            class_names = {0: 'bache', 2: 'grieta', 4: 'señal'}
            pct = count / len(samples) * 100
            print(f"      {class_names.get(cls, f'clase_{cls}')}: {count} ({pct:.1f}%)")
    
    return stats


def save_split_report(stats, seed, ratios):
    """Guarda reporte del particionado."""
    metadata_dir = SCRIPT_DIR / 'metadata'
    metadata_dir.mkdir(exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'seed': seed,
        'ratios': {
            'train': ratios[0],
            'val': ratios[1],
            'test': ratios[2]
        },
        'stats': stats,
        'total_samples': sum(s['total'] for s in stats.values())
    }
    
    report_file = metadata_dir / 'split_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Reporte guardado: {report_file}")


def create_data_yaml():
    """Crea archivo data.yaml para YOLOv8."""
    dataset_root = OUTPUT_DIR.absolute()
    
    yaml_content = f"""# SIRCCD Dataset Configuration
# Generado automáticamente por split_dataset.py
# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Rutas absolutas
path: {dataset_root.as_posix()}
train: images/train
val: images/val
test: images/test

# Clases (solo bache y grieta para SIRCCD)
nc: 2
names:
  0: bache
  1: grieta

# Nota: Las labels usan IDs 0 y 2 (mapeado de datasets originales)
# Durante entrenamiento, remapear 2 -> 1
"""
    
    yaml_file = OUTPUT_DIR / 'data.yaml'
    with open(yaml_file, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"✅ Configuración YOLO: {yaml_file}")


def main():
    """Ejecuta el particionado completo."""
    print("=" * 60)
    print("🔀 PARTICIONADO DE DATASET - D-03")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"   Seed: {RANDOM_SEED}")
    print(f"   Ratios: train={TRAIN_RATIO}, val={VAL_RATIO}, test={TEST_RATIO}")
    print(f"   Estrategia: Estratificado por clase dominante")
    
    # 1. Recolectar todas las muestras
    samples_by_class = collect_all_samples()
    
    # 2. Particionar de manera estratificada
    print(f"\n🔀 Particionando con seed={RANDOM_SEED}...")
    splits = stratified_split(
        samples_by_class,
        TRAIN_RATIO,
        VAL_RATIO,
        TEST_RATIO,
        RANDOM_SEED
    )
    
    total = sum(len(s) for s in splits.values())
    print(f"   Train: {len(splits['train'])} ({len(splits['train'])/total*100:.1f}%)")
    print(f"   Val: {len(splits['val'])} ({len(splits['val'])/total*100:.1f}%)")
    print(f"   Test: {len(splits['test'])} ({len(splits['test'])/total*100:.1f}%)")
    
    # 3. Copiar archivos
    stats = copy_split_files(splits)
    
    # 4. Guardar reporte
    save_split_report(stats, RANDOM_SEED, (TRAIN_RATIO, VAL_RATIO, TEST_RATIO))
    
    # 5. Crear data.yaml
    create_data_yaml()
    
    print("\n" + "=" * 60)
    print("✅ PARTICIONADO COMPLETADO")
    print("=" * 60)
    print(f"\nDataset final: {OUTPUT_DIR}")
    print(f"   Train: {stats['train']['total']} imágenes")
    print(f"   Val: {stats['val']['total']} imágenes")
    print(f"   Test: {stats['test']['total']} imágenes")
    print(f"\n🔁 Reproducible con seed={RANDOM_SEED}")


if __name__ == '__main__':
    main()
