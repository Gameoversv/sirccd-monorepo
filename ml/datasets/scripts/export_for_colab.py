"""
Script para exportar dataset desde MinIO a formato ZIP para Google Colab.

Este script descarga el dataset desde MinIO local y lo empaqueta en un ZIP
optimizado para subirlo a Google Drive y usar en Colab.
"""

from pathlib import Path
import zipfile
import json
from datetime import datetime
from minio import Minio
from tqdm import tqdm
import sys

# Configuración MinIO (local)
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "sirccd_admin"
MINIO_SECRET_KEY = "sirccd_password_2026"
MINIO_SECURE = False

BUCKET_NAME = "sirccd-datasets"
DATASET_VERSION = "v1.0.0"

# Directorios
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
OUTPUT_DIR = SCRIPT_DIR / 'exports'
OUTPUT_ZIP = OUTPUT_DIR / f'sirccd_dataset_{DATASET_VERSION}.zip'


def connect_minio():
    """Conecta a MinIO local."""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        # Verificar conexión
        buckets = client.list_buckets()
        print(f"✅ Conectado a MinIO ({len(buckets)} buckets)")
        
        return client
    except Exception as e:
        print(f"❌ Error conectando a MinIO: {e}")
        print("   Asegúrate de que MinIO esté ejecutándose:")
        print("   docker-compose -f docker-compose.minio.yml up -d")
        sys.exit(1)


def create_zip_for_colab(minio_client):
    """Crea ZIP con estructura lista para Colab."""
    print("\n📦 Creando ZIP para Google Colab...")
    
    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Eliminar ZIP anterior si existe
    if OUTPUT_ZIP.exists():
        print(f"🗑️  Eliminando ZIP anterior: {OUTPUT_ZIP}")
        OUTPUT_ZIP.unlink()
    
    # Listar objetos en MinIO
    print(f"\n📊 Escaneando bucket '{BUCKET_NAME}/{DATASET_VERSION}'...")
    
    all_objects = list(minio_client.list_objects(
        BUCKET_NAME,
        prefix=f"{DATASET_VERSION}/",
        recursive=True
    ))
    
    print(f"   Total de archivos: {len(all_objects):,}")
    
    # Crear ZIP
    stats = {
        'total_files': 0,
        'total_size': 0,
        'images': {'train': 0, 'val': 0, 'test': 0},
        'labels': {'train': 0, 'val': 0, 'test': 0}
    }
    
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        # Crear data.yaml
        data_yaml_content = f"""# SIRCCD Dataset - Road Damage Detection
# Version: {DATASET_VERSION}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

path: /content/sirccd_dataset
train: images/train
val: images/val
test: images/test

names:
  0: bache
  1: grieta

nc: 2

# Dataset Statistics
# Total: 57,976 images
# Train: 40,543 (70%)
# Val: 11,614 (20%)
# Test: 5,819 (10%)
"""
        zf.writestr('sirccd_dataset/data.yaml', data_yaml_content)
        
        # Procesar cada archivo
        for obj in tqdm(all_objects, desc="Empaquetando"):
            # Saltar metadata.json
            if obj.object_name.endswith('metadata.json'):
                continue
            
            # Extraer información del path
            # Formato real: v1.0.0/train/images/xxx.jpg o v1.0.0/train/labels/xxx.txt
            parts = obj.object_name.split('/')
            
            if len(parts) < 4:
                continue
            
            version, split, tipo, filename = parts[0], parts[1], parts[2], parts[3]
            
            # Validar split
            if split not in ['train', 'val', 'test']:
                continue
            
            # Determinar ruta en ZIP
            if tipo == 'images':
                zip_path = f'sirccd_dataset/images/{split}/{filename}'
                stats['images'][split] += 1
            elif tipo == 'labels':
                zip_path = f'sirccd_dataset/labels/{split}/{filename}'
                stats['labels'][split] += 1
            else:
                continue
            
            # Descargar de MinIO
            try:
                response = minio_client.get_object(BUCKET_NAME, obj.object_name)
                data = response.read()
                response.close()
                response.release_conn()
                
                # Agregar a ZIP
                zf.writestr(zip_path, data)
                
                stats['total_files'] += 1
                stats['total_size'] += len(data)
                
            except Exception as e:
                print(f"\n⚠️  Error procesando {obj.object_name}: {e}")
                continue
    
    # Mostrar estadísticas
    print(f"\n✅ ZIP creado exitosamente")
    print(f"\n📊 Estadísticas:")
    print(f"   Archivo: {OUTPUT_ZIP}")
    print(f"   Tamaño: {stats['total_size'] / (1024**3):.2f} GB")
    print(f"   Total de archivos: {stats['total_files']:,}")
    print(f"\n   Imágenes:")
    print(f"      Train: {stats['images']['train']:,}")
    print(f"      Val: {stats['images']['val']:,}")
    print(f"      Test: {stats['images']['test']:,}")
    print(f"\n   Labels:")
    print(f"      Train: {stats['labels']['train']:,}")
    print(f"      Val: {stats['labels']['val']:,}")
    print(f"      Test: {stats['labels']['test']:,}")
    
    # Guardar metadata
    metadata = {
        'version': DATASET_VERSION,
        'created': datetime.now().isoformat(),
        'stats': stats,
        'file': str(OUTPUT_ZIP),
        'size_gb': round(stats['total_size'] / (1024**3), 2)
    }
    
    metadata_file = OUTPUT_DIR / f'export_metadata_{DATASET_VERSION}.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Metadata guardada: {metadata_file}")
    
    return OUTPUT_ZIP


def print_instructions(zip_path):
    """Imprime instrucciones para usar en Colab."""
    print("\n" + "=" * 60)
    print("📤 SIGUIENTE PASO: SUBIR A GOOGLE DRIVE")
    print("=" * 60)
    print(f"\n1. Sube este archivo a Google Drive:")
    print(f"   {zip_path}")
    print(f"   Tamaño: ~{zip_path.stat().st_size / (1024**3):.2f} GB")
    print(f"\n2. Crea carpeta en Drive:")
    print(f"   MyDrive/SIRCCD_Dataset/")
    print(f"\n3. Mueve el archivo a:")
    print(f"   MyDrive/SIRCCD_Dataset/sirccd_dataset_{DATASET_VERSION}.zip")
    print(f"\n4. Abre el notebook de Colab:")
    print(f"   ml/notebooks/SIRCCD_Training_Colab.ipynb")
    print(f"\n5. Sube el notebook a Google Colab")
    print(f"\n6. Ejecuta las celdas secuencialmente")
    print("\n" + "=" * 60)
    print("⏱️  Tiempo estimado de subida a Drive: 30-60 minutos")
    print("⏱️  Tiempo de entrenamiento en Colab: 6-8 horas")
    print("=" * 60)


def main():
    print("=" * 60)
    print("📦 EXPORTAR DATASET PARA GOOGLE COLAB")
    print("=" * 60)
    
    # Conectar a MinIO
    minio_client = connect_minio()
    
    # Crear ZIP
    zip_path = create_zip_for_colab(minio_client)
    
    # Mostrar instrucciones
    print_instructions(zip_path)


if __name__ == '__main__':
    main()
