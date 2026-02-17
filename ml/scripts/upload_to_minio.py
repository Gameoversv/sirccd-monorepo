#!/usr/bin/env python3
"""
Script para subir modelos entrenados a MinIO.
Uso: python upload_to_minio.py --model runs/detect/train/weights/best.pt --name baseline-v1
"""

import os
import argparse
from pathlib import Path
from minio import Minio
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def upload_model(
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket_name: str,
    model_path: str,
    model_name: str,
    upload_artifacts: bool = True,
    use_ssl: bool = False
):
    """
    Sube modelo entrenado y artefactos a MinIO.
    
    Args:
        endpoint: MinIO endpoint
        access_key: MinIO access key
        secret_key: MinIO secret key
        bucket_name: Nombre del bucket
        model_path: Path al modelo (.pt)
        model_name: Nombre descriptivo del modelo
        upload_artifacts: Subir también métricas, gráficos, etc.
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
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Path del modelo
    model_file = Path(model_path)
    if not model_file.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
    
    # Subir modelo principal
    object_name = f"models/{model_name}_{timestamp}/best.pt"
    print(f"\n📤 Subiendo modelo: {object_name}")
    
    client.fput_object(
        bucket_name,
        object_name,
        str(model_file)
    )
    
    print(f"✅ Modelo subido: {object_name}")
    
    uploaded_files = [object_name]
    
    # Subir artefactos adicionales
    if upload_artifacts:
        # Directorio del entrenamiento (normalmente el padre de weights/)
        train_dir = model_file.parent.parent
        
        artifacts = {
            'results.csv': 'results.csv',
            'results.png': 'results.png',
            'confusion_matrix.png': 'confusion_matrix.png',
            'confusion_matrix_normalized.png': 'confusion_matrix_normalized.png',
            'PR_curve.png': 'PR_curve.png',
            'F1_curve.png': 'F1_curve.png',
            'P_curve.png': 'P_curve.png',
            'R_curve.png': 'R_curve.png',
            'weights/last.pt': 'last.pt',
            'args.yaml': 'args.yaml'
        }
        
        print(f"\n📤 Subiendo artefactos...")
        for src, dst in artifacts.items():
            src_path = train_dir / src
            if src_path.exists():
                artifact_object = f"models/{model_name}_{timestamp}/{dst}"
                try:
                    client.fput_object(
                        bucket_name,
                        artifact_object,
                        str(src_path)
                    )
                    uploaded_files.append(artifact_object)
                    print(f"   ✅ {dst}")
                except Exception as e:
                    print(f"   ⚠️  {dst}: {e}")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE SUBIDA")
    print("="*60)
    print(f"Bucket: {bucket_name}")
    print(f"Modelo: {model_name}_{timestamp}")
    print(f"Archivos subidos: {len(uploaded_files)}")
    print("\n📁 Archivos:")
    for f in uploaded_files:
        print(f"   - {f}")
    print("="*60)
    print("\n✅ Modelo disponible en MinIO")
    
    return uploaded_files


def main():
    parser = argparse.ArgumentParser(
        description="Subir modelo entrenado a MinIO"
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
        "--model",
        required=True,
        help="Path al modelo (.pt)"
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="Nombre descriptivo del modelo (ej: baseline-v1, yolov8s-finetuned)"
    )
    
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Solo subir modelo, no artefactos adicionales"
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
        upload_model(
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            bucket_name=args.bucket,
            model_path=args.model,
            model_name=args.name,
            upload_artifacts=not args.no_artifacts,
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
