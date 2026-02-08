"""
Script de validación de integridad del dataset (D-09).

Valida:
- Imágenes válidas (formato, corrupción, dimensiones)
- Anotaciones completas (cada imagen tiene label)
- Clases correctas (0=bache, 1=grieta)
- Formato YOLO correcto (coordenadas en [0,1])
- Conteo y estadísticas del dataset

Genera reporte automático en JSON.
"""

from pathlib import Path
import json
from datetime import datetime
from PIL import Image
from collections import defaultdict
from tqdm import tqdm
import argparse

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent
DATASET_DIR = SCRIPT_DIR / 'processed' / 'split'
IMAGES_DIR = DATASET_DIR / 'images'
LABELS_DIR = DATASET_DIR / 'labels'
METADATA_DIR = SCRIPT_DIR / 'metadata'

# Configuración
VALID_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png'}
VALID_CLASSES = {0, 1}  # 0: bache, 1: grieta
CLASS_NAMES = {0: 'bache', 1: 'grieta'}


class ValidationError:
    """Representa un error de validación."""
    
    def __init__(self, severity, category, file_path, message):
        self.severity = severity  # 'critical', 'warning', 'info'
        self.category = category  # 'image', 'label', 'format', 'missing'
        self.file_path = str(file_path)
        self.message = message
    
    def to_dict(self):
        return {
            'severity': self.severity,
            'category': self.category,
            'file': self.file_path,
            'message': self.message
        }


def validate_image(img_path):
    """
    Valida que una imagen sea válida.
    
    Returns:
        tuple: (is_valid, error_list, metadata)
    """
    errors = []
    metadata = {
        'format': None,
        'size': None,
        'mode': None,
        'corrupted': False
    }
    
    # Verificar extensión
    if img_path.suffix.lower() not in VALID_IMAGE_FORMATS:
        errors.append(ValidationError(
            'critical', 'image', img_path,
            f"Formato inválido: {img_path.suffix}"
        ))
        return False, errors, metadata
    
    # Intentar abrir imagen
    try:
        with Image.open(img_path) as img:
            metadata['format'] = img.format
            metadata['size'] = img.size
            metadata['mode'] = img.mode
            
            # Verificar dimensiones mínimas
            if img.size[0] < 32 or img.size[1] < 32:
                errors.append(ValidationError(
                    'warning', 'image', img_path,
                    f"Dimensiones muy pequeñas: {img.size}"
                ))
            
            # Verificar modo de color
            if img.mode not in ['RGB', 'L']:
                errors.append(ValidationError(
                    'warning', 'image', img_path,
                    f"Modo de color inusual: {img.mode}"
                ))
            
            # Intentar cargar datos (detecta corrupción)
            img.load()
            
    except Exception as e:
        metadata['corrupted'] = True
        errors.append(ValidationError(
            'critical', 'image', img_path,
            f"Imagen corrupta o ilegible: {str(e)}"
        ))
        return False, errors, metadata
    
    return len(errors) == 0, errors, metadata


def validate_label(label_path, img_size):
    """
    Valida archivo de anotación YOLO.
    
    Args:
        label_path: Path al archivo .txt
        img_size: Tupla (width, height) de la imagen
    
    Returns:
        tuple: (is_valid, error_list, annotations)
    """
    errors = []
    annotations = []
    
    if not label_path.exists():
        errors.append(ValidationError(
            'critical', 'missing', label_path,
            "Archivo de label no existe"
        ))
        return False, errors, []
    
    try:
        with open(label_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Label vacío es válido (imagen sin objetos)
        if len(lines) == 0:
            return True, [], []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Saltar líneas vacías
            if not line:
                continue
            
            parts = line.split()
            
            # Validar formato básico (class x y w h)
            if len(parts) != 5:
                errors.append(ValidationError(
                    'critical', 'format', label_path,
                    f"Línea {line_num}: formato inválido (esperado: class x y w h), encontrado: {line}"
                ))
                continue
            
            try:
                # Parsear valores
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Validar clase
                if class_id not in VALID_CLASSES:
                    errors.append(ValidationError(
                        'critical', 'format', label_path,
                        f"Línea {line_num}: clase inválida {class_id} (válidas: {VALID_CLASSES})"
                    ))
                
                # Validar coordenadas normalizadas [0, 1]
                if not (0 <= x_center <= 1):
                    errors.append(ValidationError(
                        'critical', 'format', label_path,
                        f"Línea {line_num}: x_center fuera de rango [0,1]: {x_center}"
                    ))
                
                if not (0 <= y_center <= 1):
                    errors.append(ValidationError(
                        'critical', 'format', label_path,
                        f"Línea {line_num}: y_center fuera de rango [0,1]: {y_center}"
                    ))
                
                if not (0 < width <= 1):
                    errors.append(ValidationError(
                        'critical', 'format', label_path,
                        f"Línea {line_num}: width fuera de rango (0,1]: {width}"
                    ))
                
                if not (0 < height <= 1):
                    errors.append(ValidationError(
                        'critical', 'format', label_path,
                        f"Línea {line_num}: height fuera de rango (0,1]: {height}"
                    ))
                
                # Validar que el bbox esté dentro de la imagen
                x1 = x_center - width / 2
                x2 = x_center + width / 2
                y1 = y_center - height / 2
                y2 = y_center + height / 2
                
                if x1 < 0 or x2 > 1 or y1 < 0 or y2 > 1:
                    errors.append(ValidationError(
                        'warning', 'format', label_path,
                        f"Línea {line_num}: bbox se sale de la imagen"
                    ))
                
                # Validar tamaño mínimo del bbox (evitar anotaciones de 1 pixel)
                MIN_SIZE = 0.001  # 0.1% de la imagen
                if width < MIN_SIZE or height < MIN_SIZE:
                    errors.append(ValidationError(
                        'warning', 'format', label_path,
                        f"Línea {line_num}: bbox muy pequeño (w={width:.4f}, h={height:.4f})"
                    ))
                
                annotations.append({
                    'class_id': class_id,
                    'class_name': CLASS_NAMES[class_id],
                    'x_center': x_center,
                    'y_center': y_center,
                    'width': width,
                    'height': height
                })
                
            except ValueError as e:
                errors.append(ValidationError(
                    'critical', 'format', label_path,
                    f"Línea {line_num}: error parseando valores: {str(e)}"
                ))
                continue
    
    except Exception as e:
        errors.append(ValidationError(
            'critical', 'label', label_path,
            f"Error leyendo archivo: {str(e)}"
        ))
        return False, errors, []
    
    return len(errors) == 0, errors, annotations


def validate_split(split_name):
    """Valida un split completo (train/val/test)."""
    print(f"\n🔍 Validando split: {split_name}")
    
    images_split = IMAGES_DIR / split_name
    labels_split = LABELS_DIR / split_name
    
    stats = {
        'total_images': 0,
        'valid_images': 0,
        'invalid_images': 0,
        'corrupted_images': 0,
        'total_labels': 0,
        'valid_labels': 0,
        'invalid_labels': 0,
        'missing_labels': 0,
        'empty_labels': 0,
        'total_annotations': 0,
        'annotations_by_class': {0: 0, 1: 0},
        'images_by_class': {0: 0, 1: 0},
        'images_with_both_classes': 0,
        'image_formats': defaultdict(int),
        'image_sizes': defaultdict(int),
        'errors': {
            'critical': [],
            'warning': [],
            'info': []
        }
    }
    
    # Obtener lista de imágenes
    images = list(images_split.glob('*'))
    images = [img for img in images if img.suffix.lower() in VALID_IMAGE_FORMATS]
    
    stats['total_images'] = len(images)
    
    for img_path in tqdm(images, desc=f"Validando {split_name}"):
        # Validar imagen
        is_valid_img, img_errors, img_metadata = validate_image(img_path)
        
        if is_valid_img:
            stats['valid_images'] += 1
        else:
            stats['invalid_images'] += 1
        
        if img_metadata['corrupted']:
            stats['corrupted_images'] += 1
        
        if img_metadata['format']:
            stats['image_formats'][img_metadata['format']] += 1
        
        if img_metadata['size']:
            size_str = f"{img_metadata['size'][0]}x{img_metadata['size'][1]}"
            stats['image_sizes'][size_str] += 1
        
        # Agregar errores de imagen
        for error in img_errors:
            stats['errors'][error.severity].append(error.to_dict())
        
        # Validar label correspondiente
        label_path = labels_split / f"{img_path.stem}.txt"
        
        if not label_path.exists():
            stats['missing_labels'] += 1
            stats['errors']['critical'].append(ValidationError(
                'critical', 'missing', label_path,
                f"Label faltante para imagen {img_path.name}"
            ).to_dict())
            continue
        
        stats['total_labels'] += 1
        
        # Validar contenido del label
        is_valid_lbl, lbl_errors, annotations = validate_label(
            label_path, 
            img_metadata['size'] if img_metadata['size'] else (640, 640)
        )
        
        if is_valid_lbl:
            stats['valid_labels'] += 1
        else:
            stats['invalid_labels'] += 1
        
        # Agregar errores de label
        for error in lbl_errors:
            stats['errors'][error.severity].append(error.to_dict())
        
        # Estadísticas de anotaciones
        if len(annotations) == 0:
            stats['empty_labels'] += 1
        else:
            stats['total_annotations'] += len(annotations)
            
            # Contar por clase
            classes_in_image = set()
            for ann in annotations:
                class_id = ann['class_id']
                stats['annotations_by_class'][class_id] += 1
                classes_in_image.add(class_id)
            
            # Contar imágenes por clase
            for class_id in classes_in_image:
                stats['images_by_class'][class_id] += 1
            
            # Contar imágenes con ambas clases
            if len(classes_in_image) == 2:
                stats['images_with_both_classes'] += 1
    
    return stats


def generate_report(all_stats):
    """Genera reporte de validación."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'dataset_path': str(DATASET_DIR.absolute()),
        'splits': all_stats,
        'summary': {
            'total_images': sum(s['total_images'] for s in all_stats.values()),
            'valid_images': sum(s['valid_images'] for s in all_stats.values()),
            'invalid_images': sum(s['invalid_images'] for s in all_stats.values()),
            'corrupted_images': sum(s['corrupted_images'] for s in all_stats.values()),
            'missing_labels': sum(s['missing_labels'] for s in all_stats.values()),
            'empty_labels': sum(s['empty_labels'] for s in all_stats.values()),
            'total_annotations': sum(s['total_annotations'] for s in all_stats.values()),
            'annotations_by_class': {
                'bache': sum(s['annotations_by_class'][0] for s in all_stats.values()),
                'grieta': sum(s['annotations_by_class'][1] for s in all_stats.values())
            },
            'images_by_class': {
                'bache': sum(s['images_by_class'][0] for s in all_stats.values()),
                'grieta': sum(s['images_by_class'][1] for s in all_stats.values())
            },
            'total_errors': {
                'critical': sum(len(s['errors']['critical']) for s in all_stats.values()),
                'warning': sum(len(s['errors']['warning']) for s in all_stats.values()),
                'info': sum(len(s['errors']['info']) for s in all_stats.values())
            }
        },
        'validation_status': 'PASSED' if sum(len(s['errors']['critical']) for s in all_stats.values()) == 0 else 'FAILED'
    }
    
    # Guardar reporte
    report_path = METADATA_DIR / 'validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Reporte guardado: {report_path}")
    
    return report


def print_summary(report):
    """Imprime resumen de validación."""
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    summary = report['summary']
    
    print(f"\n📁 Dataset: {report['dataset_path']}")
    print(f"⏰ Timestamp: {report['timestamp']}")
    print(f"🎯 Estado: {report['validation_status']}")
    
    print(f"\n🖼️  Imágenes:")
    print(f"   Total: {summary['total_images']}")
    print(f"   Válidas: {summary['valid_images']} ({summary['valid_images']/summary['total_images']*100:.1f}%)")
    print(f"   Inválidas: {summary['invalid_images']}")
    print(f"   Corruptas: {summary['corrupted_images']}")
    
    print(f"\n🏷️  Labels:")
    print(f"   Faltantes: {summary['missing_labels']}")
    print(f"   Vacíos: {summary['empty_labels']}")
    
    print(f"\n📦 Anotaciones:")
    print(f"   Total: {summary['total_annotations']}")
    print(f"   Baches: {summary['annotations_by_class']['bache']} ({summary['annotations_by_class']['bache']/summary['total_annotations']*100:.1f}%)")
    print(f"   Grietas: {summary['annotations_by_class']['grieta']} ({summary['annotations_by_class']['grieta']/summary['total_annotations']*100:.1f}%)")
    
    print(f"\n🖼️  Imágenes con clases:")
    print(f"   Solo baches: {summary['images_by_class']['bache']}")
    print(f"   Solo grietas: {summary['images_by_class']['grieta']}")
    
    print(f"\n⚠️  Errores:")
    print(f"   Críticos: {summary['total_errors']['critical']}")
    print(f"   Advertencias: {summary['total_errors']['warning']}")
    print(f"   Info: {summary['total_errors']['info']}")
    
    # Mostrar por split
    print(f"\n📊 Desglose por split:")
    for split_name, stats in report['splits'].items():
        print(f"\n   {split_name.upper()}:")
        print(f"      Imágenes: {stats['total_images']}")
        print(f"      Anotaciones: {stats['total_annotations']}")
        print(f"      Errores críticos: {len(stats['errors']['critical'])}")


def main():
    parser = argparse.ArgumentParser(description='Validación de integridad del dataset (D-09)')
    parser.add_argument('--split', choices=['train', 'val', 'test'], 
                       help='Validar solo un split específico')
    parser.add_argument('--show-errors', action='store_true',
                       help='Mostrar todos los errores encontrados')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔍 VALIDACIÓN DE INTEGRIDAD DEL DATASET (D-09)")
    print("=" * 70)
    
    # Determinar splits a validar
    splits = [args.split] if args.split else ['train', 'val', 'test']
    
    # Validar cada split
    all_stats = {}
    for split in splits:
        stats = validate_split(split)
        all_stats[split] = stats
    
    # Generar reporte
    report = generate_report(all_stats)
    
    # Mostrar resumen
    print_summary(report)
    
    # Mostrar errores si se solicita
    if args.show_errors:
        print("\n" + "=" * 70)
        print("⚠️  ERRORES DETALLADOS")
        print("=" * 70)
        
        for split_name, stats in all_stats.items():
            if len(stats['errors']['critical']) > 0:
                print(f"\n🔴 Errores críticos en {split_name}:")
                for error in stats['errors']['critical'][:10]:  # Mostrar primeros 10
                    print(f"   {error['file']}: {error['message']}")
                
                if len(stats['errors']['critical']) > 10:
                    print(f"   ... y {len(stats['errors']['critical']) - 10} más")
            
            if len(stats['errors']['warning']) > 0:
                print(f"\n⚠️  Advertencias en {split_name}:")
                for error in stats['errors']['warning'][:10]:
                    print(f"   {error['file']}: {error['message']}")
                
                if len(stats['errors']['warning']) > 10:
                    print(f"   ... y {len(stats['errors']['warning']) - 10} más")
    
    # Retornar código de salida
    if report['validation_status'] == 'FAILED':
        print("\n❌ Validación FALLÓ - Hay errores críticos")
        return 1
    else:
        print("\n✅ Validación EXITOSA - Dataset íntegro")
        return 0


if __name__ == '__main__':
    exit(main())
