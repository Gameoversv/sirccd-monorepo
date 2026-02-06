"""
Script para detectar rostros y placas en dataset ya procesado (D-08).
Ejecuta solo la detección sin reprocesar las imágenes.
"""

from pathlib import Path
import json
from datetime import datetime
from tqdm import tqdm
import cv2
import argparse

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent
DATASET_DIR = SCRIPT_DIR / 'processed' / 'split'
IMAGES_DIR = DATASET_DIR / 'images'
METADATA_DIR = SCRIPT_DIR / 'metadata'


def detect_faces(img_path):
    """Detecta rostros en una imagen usando Haar Cascade."""
    try:
        # Cargar clasificador Haar Cascade
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Leer imagen
        img = cv2.imread(str(img_path))
        if img is None:
            return []
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar rostros
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces.tolist() if len(faces) > 0 else []
    except Exception as e:
        print(f"Error detectando rostros en {img_path.name}: {e}")
        return []


def analyze_split(split_name):
    """Analiza un split completo buscando rostros."""
    print(f"\n🔍 Analizando split: {split_name}")
    
    images_dir = IMAGES_DIR / split_name
    
    stats = {
        'total': 0,
        'with_faces': 0,
        'total_faces': 0,
        'images_with_faces': []
    }
    
    images = list(images_dir.glob('*'))
    
    for img_path in tqdm(images, desc=f"Escaneando {split_name}"):
        if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            continue
        
        stats['total'] += 1
        
        faces = detect_faces(img_path)
        
        if faces:
            stats['with_faces'] += 1
            stats['total_faces'] += len(faces)
            stats['images_with_faces'].append({
                'filename': img_path.name,
                'faces_count': len(faces),
                'faces': faces
            })
    
    return stats


def generate_report(all_stats):
    """Genera reporte de detección."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'face_detection',
        'classifier': 'haarcascade_frontalface_default',
        'splits': all_stats,
        'summary': {
            'total_images': sum(s['total'] for s in all_stats.values()),
            'images_with_faces': sum(s['with_faces'] for s in all_stats.values()),
            'total_faces_detected': sum(s['total_faces'] for s in all_stats.values()),
            'percentage_with_faces': 0
        }
    }
    
    total = report['summary']['total_images']
    with_faces = report['summary']['images_with_faces']
    
    if total > 0:
        report['summary']['percentage_with_faces'] = (with_faces / total) * 100
    
    # Guardar reporte
    report_path = METADATA_DIR / 'face_detection_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Reporte guardado: {report_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Detección de contenido sensible en dataset')
    parser.add_argument('--split', choices=['train', 'val', 'test'], 
                       help='Analizar solo un split específico')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 DETECCIÓN DE CONTENIDO SENSIBLE (D-08)")
    print("=" * 60)
    print(f"\nDetector: Haar Cascade (OpenCV)")
    print(f"Objetivo: Rostros humanos")
    
    # Verificar que el clasificador existe
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    if not Path(cascade_path).exists():
        print(f"\n❌ Error: No se encontró el clasificador en {cascade_path}")
        return
    
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Analizar splits
    all_stats = {}
    
    splits = [args.split] if args.split else ['train', 'val', 'test']
    
    for split in splits:
        stats = analyze_split(split)
        all_stats[split] = stats
        
        print(f"\n📊 Resultados {split}:")
        print(f"   Total de imágenes: {stats['total']}")
        print(f"   Imágenes con rostros: {stats['with_faces']}")
        print(f"   Total de rostros: {stats['total_faces']}")
        
        if stats['with_faces'] > 0:
            print(f"\n   ⚠️ Primeras 5 imágenes con rostros:")
            for img_info in stats['images_with_faces'][:5]:
                print(f"      - {img_info['filename']}: {img_info['faces_count']} rostro(s)")
    
    # Generar reporte
    report = generate_report(all_stats)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE DETECCIÓN")
    print("=" * 60)
    
    total = report['summary']['total_images']
    with_faces = report['summary']['images_with_faces']
    total_faces = report['summary']['total_faces_detected']
    percentage = report['summary']['percentage_with_faces']
    
    print(f"\nTotal de imágenes analizadas: {total}")
    print(f"Imágenes con rostros: {with_faces} ({percentage:.2f}%)")
    print(f"Total de rostros detectados: {total_faces}")
    
    if with_faces > 0:
        print(f"\n⚠️ ACCIÓN REQUERIDA:")
        print(f"   {with_faces} imágenes contienen potencialmente rostros.")
        print(f"   Ejecutar difuminado con:")
        print(f"   python scripts/blur_detected_faces.py")
    else:
        print(f"\n✅ No se detectaron rostros en el dataset.")
        print(f"   El dataset es seguro desde el punto de vista de privacidad facial.")


if __name__ == '__main__':
    main()
