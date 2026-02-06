"""
Script para difuminar rostros detectados en el dataset anonimizado (D-08).

Lee el reporte de detección (face_detection_report.json) y aplica
Gaussian Blur sobre las regiones de rostros encontrados en las
imágenes del dataset anonimizado.

Uso:
    # Difuminar todos los rostros detectados
    python scripts/blur_detected_faces.py

    # Solo un split
    python scripts/blur_detected_faces.py --split test

    # Previsualizar sin modificar
    python scripts/blur_detected_faces.py --dry-run
"""

from pathlib import Path
import json
import shutil
from datetime import datetime
from tqdm import tqdm
import cv2
import argparse

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
ANONYMIZED_DIR = SCRIPT_DIR / 'processed' / 'anonymized'
METADATA_DIR = SCRIPT_DIR / 'metadata'
REPORT_PATH = METADATA_DIR / 'face_detection_report.json'


def load_detection_report():
    """Carga el reporte de detección de rostros."""
    if not REPORT_PATH.exists():
        print(f"❌ No se encontró el reporte de detección: {REPORT_PATH}")
        print(f"   Ejecutar primero: python scripts/detect_sensitive_content.py")
        return None

    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


def blur_faces_in_image(img_path, faces, kernel_size=(51, 51), sigma=30):
    """
    Aplica Gaussian Blur sobre las regiones de rostros en una imagen.

    Args:
        img_path: Ruta a la imagen
        faces: Lista de [x, y, w, h] con las coordenadas de los rostros
        kernel_size: Tamaño del kernel Gaussian
        sigma: Desviación estándar del blur

    Returns:
        True si se difuminó correctamente, False en caso de error
    """
    try:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  ⚠️ No se pudo leer: {img_path.name}")
            return False

        for (x, y, w, h) in faces:
            # Asegurar que las coordenadas estén dentro de la imagen
            h_img, w_img = img.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)

            if w <= 0 or h <= 0:
                continue

            # Extraer ROI y aplicar blur
            roi = img[y:y+h, x:x+w]
            blurred = cv2.GaussianBlur(roi, kernel_size, sigma)
            img[y:y+h, x:x+w] = blurred

        # Sobrescribir imagen anonimizada
        cv2.imwrite(str(img_path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True

    except Exception as e:
        print(f"  ❌ Error difuminando {img_path.name}: {e}")
        return False


def process_split(split_name, split_data, dry_run=False):
    """Procesa un split difuminando los rostros detectados."""
    images_with_faces = split_data.get('images_with_faces', [])

    if not images_with_faces:
        print(f"\n  ✅ {split_name}: Sin rostros detectados")
        return {'processed': 0, 'blurred': 0, 'errors': 0}

    print(f"\n  🔧 {split_name}: {len(images_with_faces)} imágenes con rostros")

    stats = {'processed': 0, 'blurred': 0, 'errors': 0, 'total_faces': 0}

    for img_info in tqdm(images_with_faces, desc=f"  Difuminando {split_name}"):
        filename = img_info['filename']
        faces = img_info['faces']
        img_path = ANONYMIZED_DIR / 'images' / split_name / filename

        if not img_path.exists():
            stats['errors'] += 1
            continue

        stats['processed'] += 1
        stats['total_faces'] += len(faces)

        if dry_run:
            continue

        if blur_faces_in_image(img_path, faces):
            stats['blurred'] += 1
        else:
            stats['errors'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Difuminar rostros detectados en dataset anonimizado (D-08)'
    )
    parser.add_argument('--split', choices=['train', 'val', 'test'],
                       help='Procesar solo un split específico')
    parser.add_argument('--dry-run', action='store_true',
                       help='Previsualizar sin modificar imágenes')
    parser.add_argument('--kernel', type=int, default=51,
                       help='Tamaño del kernel Gaussian (default: 51)')
    parser.add_argument('--sigma', type=int, default=30,
                       help='Sigma del Gaussian Blur (default: 30)')

    args = parser.parse_args()

    print("=" * 60)
    print("🔒 DIFUMINADO DE ROSTROS DETECTADOS (D-08)")
    print("=" * 60)

    if args.dry_run:
        print("⚠️  MODO DRY-RUN: No se modificarán imágenes")

    # Cargar reporte de detección
    report = load_detection_report()
    if report is None:
        return

    summary = report.get('summary', {})
    print(f"\nReporte: {report['timestamp']}")
    print(f"Clasificador: {report.get('classifier', 'desconocido')}")
    print(f"Total imágenes con rostros: {summary.get('images_with_faces', 0)}")
    print(f"Total rostros detectados: {summary.get('total_faces_detected', 0)}")

    # Procesar splits
    splits = [args.split] if args.split else ['train', 'val', 'test']
    all_stats = {}

    for split in splits:
        if split not in report.get('splits', {}):
            print(f"\n  ⚠️ {split}: No hay datos de detección")
            continue

        stats = process_split(split, report['splits'][split], args.dry_run)
        all_stats[split] = stats

    # Resumen
    total_processed = sum(s['processed'] for s in all_stats.values())
    total_blurred = sum(s['blurred'] for s in all_stats.values())
    total_errors = sum(s['errors'] for s in all_stats.values())
    total_faces = sum(s['total_faces'] for s in all_stats.values())

    print("\n" + "=" * 60)
    if args.dry_run:
        print("📊 RESUMEN (DRY-RUN)")
    else:
        print("✅ DIFUMINADO COMPLETADO")
    print("=" * 60)
    print(f"\nImágenes procesadas: {total_processed}")
    print(f"Rostros difuminados: {total_faces}")
    if not args.dry_run:
        print(f"Imágenes modificadas: {total_blurred}")
    print(f"Errores: {total_errors}")

    # Actualizar reporte de anonimización
    if not args.dry_run and total_blurred > 0:
        anon_report_path = METADATA_DIR / 'anonymization_report.json'
        if anon_report_path.exists():
            with open(anon_report_path, 'r') as f:
                anon_report = json.load(f)

            anon_report['face_blur'] = {
                'timestamp': datetime.now().isoformat(),
                'classifier': report.get('classifier', 'haarcascade_frontalface_default'),
                'kernel_size': args.kernel,
                'sigma': args.sigma,
                'total_images_blurred': total_blurred,
                'total_faces_blurred': total_faces,
                'splits': {
                    split: {
                        'images_blurred': stats['blurred'],
                        'faces_blurred': stats['total_faces']
                    }
                    for split, stats in all_stats.items()
                }
            }
            anon_report['summary']['images_blurred'] = total_blurred
            anon_report['summary']['faces_detected'] = total_faces

            with open(anon_report_path, 'w') as f:
                json.dump(anon_report, f, indent=2)

            print(f"\n📝 Reporte actualizado: {anon_report_path}")

    if not args.dry_run:
        print(f"\n🔒 Dataset completamente anonimizado con rostros difuminados")


if __name__ == '__main__':
    main()
