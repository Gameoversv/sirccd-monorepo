#!/usr/bin/env python3
"""
Script para descargar dataset desde MinIO para entrenamiento en la nube.
Uso: python download_from_minio.py --output /path/to/download
"""

import os
import argparse
from pathlib import Path
from minio import Minio
from tqdm import tqdm
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def download_dataset(
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket_name: str,
    version: str,
    output_dir: str,
    use_ssl: bool = False
):
    """
    Descarga dataset completo desde MinIO.
    
    Args:
        endpoint: MinIO endpoint (host:port)
        access_key: MinIO access key
        secret_key: MinIO secret key
        bucket_name: Nombre del bucket
        version: Versión del dataset (ej: v1.0.0)
        output_dir: Directorio de salida
        use_ssl: Usar SSL/TLS
    """
    print(f"🔗 Conectando a MinIO: {endpoint}")
    
    # Conectar a MinIO
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=use_ssl
    )
    
    print(f"✅ Conectado a MinIO")
    
    # Crear directorios
    output_path = Path(output_dir)
    images_dir = output_path / "images"
    labels_dir = output_path / "labels"
    
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    # Descargar imágenes
    print(f"\n📥 Descargando imágenes desde {bucket_name}/{version}/images/...")
    image_objects = list(client.list_objects(
        bucket_name,
        prefix=f"{version}/images/",
        recursive=True
    ))
    
    for obj in tqdm(image_objects, desc="Imágenes"):
        if obj.object_name.endswith(('.jpg', '.jpeg', '.png')):
            filename = os.path.basename(obj.object_name)
            local_path = images_dir / filename
            client.fget_object(bucket_name, obj.object_name, str(local_path))
    
    print(f"✅ {len(image_objects)} imágenes descargadas")
    
    # Descargar labels YOLO
    print(f"\n📥 Descargando labels desde {bucket_name}/{version}/labels_yolo/...")
    label_objects = list(client.list_objects(
        bucket_name,
        prefix=f"{version}/labels_yolo/",
        recursive=True
    ))
    
    for obj in tqdm(label_objects, desc="Labels"):
        if obj.object_name.endswith('.txt'):
            filename = os.path.basename(obj.object_name)
            local_path = labels_dir / filename
            client.fget_object(bucket_name, obj.object_name, str(local_path))
    
    print(f"✅ {len(label_objects)} labels descargadas")
    
    # Crear data.yaml
    data_yaml_content = f"""# SIRCCD Dataset Configuration
path: {output_path.absolute()}
train: images
val: images

# Classes
names:
  0: residuo
  1: contenedor
  2: vehiculo

# Number of classes
nc: 3
"""
    
    data_yaml_path = output_path / "data.yaml"
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)
    
    print(f"\n✅ data.yaml creado: {data_yaml_path}")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE DESCARGA")
    print("="*60)
    print(f"Imágenes: {len(image_objects)}")
    print(f"Labels: {len(label_objects)}")
    print(f"Directorio: {output_path.absolute()}")
    print(f"data.yaml: {data_yaml_path}")
    print("="*60)
    print("\n🚀 Listo para entrenar!")
    print(f"   yolo train data={data_yaml_path} model=yolov8n.pt epochs=100")


def main():
    parser = argparse.ArgumentParser(
        description="Descargar dataset SIRCCD desde MinIO para entrenamiento"
    )
    
    parser.add_argument(
        "--endpoint",
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        help="MinIO endpoint (host:port)"
    )
    
    parser.add_argument(
        "--access-key",
        default=os.getenv("MINIO_ACCESS_KEY"),
        help="MinIO access key"
    )
    
    parser.add_argument(
        "--secret-key",
        default=os.getenv("MINIO_SECRET_KEY"),
        help="MinIO secret key"
    )
    
    parser.add_argument(
        "--bucket",
        default=os.getenv("MINIO_BUCKET_NAME", "sirccd-datasets"),
        help="Nombre del bucket"
    )
    
    parser.add_argument(
        "--version",
        default=os.getenv("DATASET_VERSION", "v1.0.0"),
        help="Versión del dataset"
    )
    
    parser.add_argument(
        "--output",
        default="./datasets/sirccd",
        help="Directorio de salida"
    )
    
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Usar SSL/TLS"
    )
    
    args = parser.parse_args()
    
    # Validar credenciales
    if not args.access_key or not args.secret_key:
        print("❌ Error: Credenciales de MinIO no proporcionadas")
        print("   Usa --access-key y --secret-key o configura .env")
        return 1
    
    try:
        download_dataset(
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            bucket_name=args.bucket,
            version=args.version,
            output_dir=args.output,
            use_ssl=args.ssl
        )
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
