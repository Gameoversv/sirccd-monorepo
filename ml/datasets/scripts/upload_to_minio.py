"""
Script para ingestar dataset a MinIO con metadatos organizados.
D-07: Sube imágenes y anotaciones del dataset YOLO a bucket MinIO.
"""
from pathlib import Path
import json
from datetime import datetime
from minio import Minio
from minio.error import S3Error
import hashlib

# Configuración MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "sirccd_admin"
MINIO_SECRET_KEY = "sirccd_password_2026"
BUCKET_NAME = "sirccd-datasets"

# Rutas del dataset
SCRIPT_DIR = Path(__file__).parent.parent  # ml/datasets/
DATASET_DIR = SCRIPT_DIR / "processed" / "split"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

# Metadatos del dataset
DATASET_VERSION = "v1.0.0"
DATASET_INFO = {
    "name": "SIRCCD Road Damage Dataset",
    "version": DATASET_VERSION,
    "created_at": datetime.now().isoformat(),
    "classes": ["bache", "grieta"],
    "splits": ["train", "val", "test"],
    "source_datasets": ["RDD2022", "RDD2020", "N-RDD2024", "Pothole-600"],
    "seed": 42,
    "total_images": 58209,
}


def get_file_hash(file_path):
    """Calcula SHA256 hash de un archivo."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_minio_client():
    """Crea y retorna cliente MinIO."""
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False  # True si usas HTTPS
    )
    return client


def create_bucket_if_not_exists(client):
    """Crea bucket si no existe."""
    try:
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            print(f"✅ Bucket '{BUCKET_NAME}' creado")
        else:
            print(f"ℹ️  Bucket '{BUCKET_NAME}' ya existe")
    except S3Error as e:
        print(f"❌ Error creando bucket: {e}")
        raise


def upload_file_with_metadata(client, local_path, object_name, metadata):
    """Sube archivo a MinIO con metadatos."""
    try:
        client.fput_object(
            BUCKET_NAME,
            object_name,
            local_path,
            metadata=metadata
        )
        return True
    except S3Error as e:
        print(f"❌ Error subiendo {object_name}: {e}")
        return False


def upload_dataset_split(client, split_name):
    """Sube imágenes y labels de un split."""
    images_split = IMAGES_DIR / split_name
    labels_split = LABELS_DIR / split_name
    
    if not images_split.exists():
        print(f"⚠️  Split '{split_name}' no existe")
        return 0, 0
    
    uploaded_images = 0
    uploaded_labels = 0
    
    print(f"\n📤 Subiendo split: {split_name}")
    
    # Subir imágenes
    for img_file in images_split.glob("*.*"):
        if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            continue
        
        object_name = f"{DATASET_VERSION}/{split_name}/images/{img_file.name}"
        metadata = {
            "dataset-version": DATASET_VERSION,
            "split": split_name,
            "type": "image",
            "file-hash": get_file_hash(img_file),
            "uploaded-at": datetime.now().isoformat()
        }
        
        if upload_file_with_metadata(client, str(img_file), object_name, metadata):
            uploaded_images += 1
            if uploaded_images % 1000 == 0:
                print(f"  Imágenes: {uploaded_images}")
    
    # Subir labels
    for label_file in labels_split.glob("*.txt"):
        object_name = f"{DATASET_VERSION}/{split_name}/labels/{label_file.name}"
        metadata = {
            "dataset-version": DATASET_VERSION,
            "split": split_name,
            "type": "label",
            "file-hash": get_file_hash(label_file),
            "uploaded-at": datetime.now().isoformat()
        }
        
        if upload_file_with_metadata(client, str(label_file), object_name, metadata):
            uploaded_labels += 1
    
    print(f"  ✅ {split_name}: {uploaded_images} imágenes, {uploaded_labels} labels")
    return uploaded_images, uploaded_labels


def upload_dataset_metadata(client):
    """Sube archivo de metadatos del dataset."""
    metadata_file = Path("dataset_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(DATASET_INFO, f, indent=2)
    
    object_name = f"{DATASET_VERSION}/metadata.json"
    metadata = {
        "dataset-version": DATASET_VERSION,
        "type": "metadata",
        "uploaded-at": datetime.now().isoformat()
    }
    
    if upload_file_with_metadata(client, str(metadata_file), object_name, metadata):
        print(f"✅ Metadatos subidos: {object_name}")
        metadata_file.unlink()  # Eliminar archivo temporal


def main():
    """Ejecuta el proceso completo de ingesta."""
    print("=" * 60)
    print("📦 INGESTA DE DATASET A MinIO (D-07)")
    print("=" * 60)
    
    # Crear cliente MinIO
    print("\n🔌 Conectando a MinIO...")
    client = create_minio_client()
    
    # Crear bucket
    create_bucket_if_not_exists(client)
    
    # Subir metadatos
    print("\n📄 Subiendo metadatos del dataset...")
    upload_dataset_metadata(client)
    
    # Subir splits
    total_images = 0
    total_labels = 0
    
    for split in ["train", "val", "test"]:
        img_count, lbl_count = upload_dataset_split(client, split)
        total_images += img_count
        total_labels += lbl_count
    
    # Resumen
    print("\n" + "=" * 60)
    print("✅ INGESTA COMPLETADA")
    print("=" * 60)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Versión: {DATASET_VERSION}")
    print(f"Total imágenes: {total_images}")
    print(f"Total labels: {total_labels}")
    print(f"\n🌐 Consola MinIO: http://localhost:9001")
    print(f"Usuario: {MINIO_ACCESS_KEY}")
    print(f"Contraseña: {MINIO_SECRET_KEY}")


if __name__ == "__main__":
    main()
