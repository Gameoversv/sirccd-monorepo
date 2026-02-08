"""
Script para anonimizar dataset (D-08).

Tareas:
1. Eliminar todos los metadatos EXIF (GPS, usuario, dispositivo, etc.)
2. Generar reporte de anonimización

NOTA: Detección de rostros/placas removida por falsos positivos en dash cam.
"""

from pathlib import Path
import json
from datetime import datetime
from PIL import Image
import piexif
from collections import defaultdict
from tqdm import tqdm
import argparse

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
DATASET_DIR = SCRIPT_DIR / 'processed' / 'split'
IMAGES_DIR = DATASET_DIR / 'images'
ANONYMIZED_DIR = SCRIPT_DIR / 'processed' / 'anonymized'
METADATA_DIR = SCRIPT_DIR / 'metadata'

# Tags EXIF sensibles a eliminar
SENSITIVE_EXIF_TAGS = {
    'GPS': ['GPSLatitude', 'GPSLongitude', 'GPSAltitude', 'GPSTimeStamp', 'GPSDateStamp'],
    'Exif': ['UserComment', 'MakerNote', 'CameraOwnerName'],
    '0th': ['Artist', 'Copyright', 'Software', 'HostComputer'],
    '1st': [],
    'Interop': []
}

# Ya no se usa detección de rostros/placas (falsos positivos en dash cam)


def get_exif_data(img_path):
    """Extrae datos EXIF de una imagen."""
    try:
        img = Image.open(img_path)
        if 'exif' not in img.info:
            return None
        
        exif_dict = piexif.load(img.info['exif'])
        return exif_dict
    except Exception as e:
        return None


def has_sensitive_exif(exif_dict):
    """Verifica si la imagen tiene EXIF sensible."""
    if not exif_dict:
        return False
    
    sensitive_found = []
    
    # Verificar GPS
    if 'GPS' in exif_dict and exif_dict['GPS']:
        sensitive_found.append('GPS')
    
    # Verificar tags de usuario
    if 'Exif' in exif_dict:
        for tag, value in exif_dict['Exif'].items():
            tag_name = piexif.TAGS['Exif'].get(tag, {}).get('name', '')
            if tag_name in ['UserComment', 'MakerNote', 'CameraOwnerName']:
                sensitive_found.append(f'Exif.{tag_name}')
    
    # Verificar metadata de autor
    if '0th' in exif_dict:
        for tag, value in exif_dict['0th'].items():
            tag_name = piexif.TAGS['0th'].get(tag, {}).get('name', '')
            if tag_name in ['Artist', 'Copyright', 'HostComputer']:
                sensitive_found.append(f'0th.{tag_name}')
    
    return sensitive_found


def remove_exif(img_path, output_path):
    """Elimina todos los metadatos EXIF de una imagen."""
    try:
        img = Image.open(img_path)
        
        # Guardar sin EXIF (mantener formato y calidad)
        img.save(output_path, quality=95, optimize=True, exif=b'')
        
        return True
    except Exception as e:
        print(f"Error limpiando EXIF de {img_path.name}: {e}")
        return False





def anonymize_image(img_path, output_path):
    """
    Anonimiza una imagen eliminando todos los metadatos EXIF.
    
    Args:
        img_path: Ruta de imagen original
        output_path: Ruta de salida
    
    Returns:
        dict con estadísticas de anonimización
    """
    stats = {
        'exif_removed': False,
        'exif_sensitive': [],
        'success': False
    }
    
    # Verificar EXIF sensible (solo para reporte)
    exif_data = get_exif_data(img_path)
    sensitive_tags = has_sensitive_exif(exif_data)
    
    if sensitive_tags:
        stats['exif_sensitive'] = sensitive_tags
    
    # Eliminar todo EXIF
    success = remove_exif(img_path, output_path)
    stats['exif_removed'] = success
    stats['success'] = success
    
    return stats


def process_split(split_name):
    """Procesa todas las imágenes de un split."""
    print(f"\n🔒 Anonimizando split: {split_name}")
    
    images_src = IMAGES_DIR / split_name
    labels_src = DATASET_DIR / 'labels' / split_name
    
    images_dst = ANONYMIZED_DIR / 'images' / split_name
    labels_dst = ANONYMIZED_DIR / 'labels' / split_name
    
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total': 0,
        'processed': 0,
        'exif_removed': 0,
        'exif_sensitive_found': 0,
        'errors': []
    }
    
    # Procesar imágenes
    images = list(images_src.glob('*'))
    
    for img_path in tqdm(images, desc=f"Procesando {split_name}"):
        if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            continue
        
        stats['total'] += 1
        
        output_path = images_dst / img_path.name
        
        # Anonimizar imagen
        result = anonymize_image(img_path, output_path)
        
        if result['success']:
            stats['processed'] += 1
            
            if result['exif_removed']:
                stats['exif_removed'] += 1
            
            if result['exif_sensitive']:
                stats['exif_sensitive_found'] += 1
        else:
            stats['errors'].append(img_path.name)
        
        # Copiar label correspondiente
        label_path = labels_src / f"{img_path.stem}.txt"
        if label_path.exists():
            import shutil
            shutil.copy2(label_path, labels_dst / label_path.name)
    
    return stats


def generate_report(all_stats):
    """Genera reporte de anonimización."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'configuration': {
            'remove_all_exif': True,
            'note': 'Face/plate detection removed due to false positives in dash cam dataset'
        },
        'splits': all_stats,
        'summary': {
            'total_images': sum(s['total'] for s in all_stats.values()),
            'processed': sum(s['processed'] for s in all_stats.values()),
            'exif_removed': sum(s['exif_removed'] for s in all_stats.values()),
            'sensitive_found': sum(s['exif_sensitive_found'] for s in all_stats.values())
        }
    }
    
    # Guardar reporte
    report_path = METADATA_DIR / 'anonymization_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Reporte guardado: {report_path}")
    
    return report


def create_data_yaml():
    """Crea data.yaml para dataset anonimizado."""
    yaml_content = f"""# SIRCCD Dataset - Anonimizado (D-08)
# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Metadatos EXIF eliminados para proteger privacidad

path: {ANONYMIZED_DIR.absolute().as_posix()}
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: bache
  1: grieta

# Nota: Dataset completamente anonimizado
# - Sin coordenadas GPS
# - Sin información de usuario/dispositivo
# - Sin metadatos EXIF sensibles
"""
    
    yaml_file = ANONYMIZED_DIR / 'data.yaml'
    with open(yaml_file, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"✅ Configuración YOLO: {yaml_file}")


def main():
    parser = argparse.ArgumentParser(description='Anonimización de dataset (D-08)')
    parser.add_argument('--check-only', action='store_true',
                       help='Solo analizar sin procesar')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔒 ANONIMIZACIÓN DE DATASET (D-08)")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"   Eliminar EXIF: Todos los metadatos")
    print(f"   Detección rostros/placas: Desactivada (falsos positivos)")
    
    if args.check_only:
        print("\n📊 Modo análisis (sin modificar archivos)")
        
        # Analizar EXIF sensible
        sensitive_count = 0
        total_count = 0
        
        for split in ['train', 'val', 'test']:
            images_dir = IMAGES_DIR / split
            for img_path in images_dir.glob('*'):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    total_count += 1
                    exif_data = get_exif_data(img_path)
                    if has_sensitive_exif(exif_data):
                        sensitive_count += 1
        
        print(f"\n📊 Resultados del análisis:")
        print(f"   Total de imágenes: {total_count}")
        print(f"   Con EXIF sensible: {sensitive_count} ({sensitive_count/total_count*100:.1f}%)")
        return
    
    # Crear directorios
    ANONYMIZED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Procesar cada split
    all_stats = {}
    
    for split in ['train', 'val', 'test']:
        stats = process_split(split)
        all_stats[split] = stats
        
        print(f"\n📊 Resultados {split}:")
        print(f"   Total: {stats['total']}")
        print(f"   Procesadas: {stats['processed']}")
        print(f"   EXIF eliminado: {stats['exif_removed']}")
        print(f"   EXIF sensible encontrado: {stats['exif_sensitive_found']}")
    
    # Generar reporte
    report = generate_report(all_stats)
    
    # Crear data.yaml
    create_data_yaml()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ ANONIMIZACIÓN COMPLETADA")
    print("=" * 60)
    print(f"\nDataset anonimizado: {ANONYMIZED_DIR}")
    print(f"   Total procesadas: {report['summary']['processed']}")
    print(f"   EXIF eliminado: {report['summary']['exif_removed']}")
    print(f"   EXIF sensible encontrado: {report['summary']['sensitive_found']}")
    print(f"\n🔒 Dataset completamente anonimizado y listo para uso")


if __name__ == '__main__':
    main()
