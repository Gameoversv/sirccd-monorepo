"""
Servicio de almacenamiento de archivos usando MinIO (S3-compatible)
"""

import os
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from datetime import datetime
import mimetypes

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException, status

from core.config import settings


class StorageService:
    """
    Servicio para gestionar el almacenamiento de archivos en MinIO/S3
    
    Soporta:
    - Almacenamiento en MinIO (producción)
    - Almacenamiento local (desarrollo/fallback)
    """
    
    def __init__(self):
        """Inicializa el cliente de MinIO si está configurado"""
        self.use_minio = self._check_minio_available()
        
        if self.use_minio:
            try:
                self.client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                # Verificar/crear bucket de imágenes
                self._ensure_bucket(settings.MINIO_BUCKET_IMAGES)
            except Exception as e:
                print(f"  MinIO no disponible, usando almacenamiento local: {e}")
                self.use_minio = False
        
        # Configurar almacenamiento local como fallback
        if not self.use_minio:
            self.local_storage_path = Path("storage/images")
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def _check_minio_available(self) -> bool:
        """Verifica si MinIO está configurado y disponible"""
        try:
            # Intenta conectar al endpoint de MinIO
            import socket
            host, port = settings.MINIO_ENDPOINT.split(":")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _ensure_bucket(self, bucket_name: str) -> None:
        """Crea el bucket si no existe"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f" Bucket '{bucket_name}' creado")
        except S3Error as e:
            print(f"  Error al verificar/crear bucket: {e}")
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Genera un nombre de archivo único
        
        Formato: YYYY/MM/DD/uuid_originalname.ext
        """
        # Obtener extensión
        ext = Path(original_filename).suffix.lower()
        
        # Generar path con estructura de fechas
        now = datetime.utcnow()
        date_path = now.strftime("%Y/%m/%d")
        
        # Generar UUID para evitar colisiones
        unique_id = str(uuid.uuid4())[:8]
        
        # Sanitizar nombre original (solo tomar base, sin caracteres especiales)
        base_name = Path(original_filename).stem
        safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_")[:50]
        
        # Construir nombre final
        filename = f"{unique_id}_{safe_name}{ext}"
        
        return f"{date_path}/{filename}"
    
    def _validate_image(self, file: UploadFile) -> None:
        """
        Valida que el archivo sea una imagen válida
        
        Raises:
            HTTPException: Si el archivo no es válido
        """
        # Verificar content type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo debe ser una imagen. Tipo recibido: {file.content_type}"
            )
        
        # Verificar extensión permitida
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        ext = Path(file.filename or "").suffix.lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensión no permitida: {ext}. Permitidas: {', '.join(allowed_extensions)}"
            )
        
        # Verificar tamaño máximo (10 MB)
        max_size = 10 * 1024 * 1024  # 10 MB
        file.file.seek(0, 2)  # Ir al final del archivo
        size = file.file.tell()
        file.file.seek(0)  # Volver al inicio
        
        if size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande: {size / 1024 / 1024:.2f} MB. Máximo: 10 MB"
            )
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "reports",
        anonymize: bool = True
    ) -> Tuple:
        """
        Sube una imagen a MinIO o almacenamiento local

        IMPORTANTE: Anonimiza la imagen por defecto (B-05) y elimina EXIF (D-08)

        Args:
            file: Archivo subido por el usuario
            folder: Carpeta dentro del bucket (ej: 'reports', 'avatars')
            anonymize: Si True, anonimiza la imagen antes de guardar (default: True)

        Returns:
            Tuple[str, int, int, dict, ExifData]:
                (URL, ancho, alto, stats de anonimización, datos EXIF extraídos)
        
        Raises:
            HTTPException: Si hay errores de validación o carga
        """
        # Validar imagen
        self._validate_image(file)
        
        # Generar nombre único
        unique_filename = self._generate_unique_filename(file.filename or "image.jpg")
        object_name = f"{folder}/{unique_filename}"
        
        # Leer contenido del archivo
        content = await file.read()

        # D-08: Extraer EXIF técnico ANTES de cualquier transformación
        from .exif_service import extract_exif, strip_exif, ExifData
        exif_data: ExifData = extract_exif(content)
        if exif_data.focal_length_35mm or exif_data.focal_length_mm:
            print(
                f"ℹ  EXIF focal: {exif_data.focal_length_35mm or exif_data.focal_length_mm:.0f} mm "
                f"(zoom_factor={exif_data.zoom_scale_factor:.2f})"
            )

        # B-05: Anonimizar imagen ANTES de guardar (blur rostros/placas)
        anonymization_stats = {
            'faces_detected': 0,
            'plates_detected': 0,
            'regions_blurred': 0,
            'anonymized': False,
            'error': None
        }

        if anonymize:
            try:
                from .anonymizer import image_anonymizer

                # Anonimizar (detectar y difuminar rostros/placas)
                content, anonymization_stats = image_anonymizer.anonymize(
                    content,
                    detect_faces=True,
                    detect_plates=True
                )

                if anonymization_stats.get('error'):
                    print(f"  Error en anonimización: {anonymization_stats['error']}")
                elif anonymization_stats.get('anonymized'):
                    print(f" Imagen anonimizada: {anonymization_stats['regions_blurred']} regiones difuminadas "
                          f"({anonymization_stats['faces_detected']} rostros, {anonymization_stats['plates_detected']} placas)")
                else:
                    print("ℹ  No se detectaron regiones sensibles en la imagen")

            except Exception as e:
                print(f" Error crítico en anonimización: {e}")
                # POLÍTICA: En caso de error, NO guardar la imagen
                # Esto asegura que nunca se almacenen imágenes sin anonimizar
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error en proceso de anonimización: {str(e)}. Imagen no guardada por seguridad."
                )

        # D-08: Eliminar EXIF residual — siempre.
        # El anonymizer ya hace un re-save via PIL.fromarray cuando el modelo
        # está cargado, por lo que el EXIF ya fue eliminado en ese caso.
        # Cuando el modelo no está disponible o anonymize=False, los bytes
        # originales con EXIF estarían intactos; strip_exif los limpia.
        # Si ya no hay EXIF, la función retorna rápido sin degradación adicional.
        content = strip_exif(content)
        
        # Obtener dimensiones de la imagen (ya anonimizada)
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(content))
            width, height = img.size
        except Exception as e:
            print(f"  No se pudieron obtener dimensiones de la imagen: {e}")
            width, height = 0, 0
        
        # Subir según el modo configurado
        if self.use_minio:
            url = await self._upload_to_minio(object_name, content, file.content_type)
        else:
            url = await self._upload_to_local(object_name, content)
        
        return url, width, height, anonymization_stats, exif_data
    
    async def _upload_to_minio(
        self,
        object_name: str,
        content: bytes,
        content_type: Optional[str]
    ) -> str:
        """Sube archivo a MinIO con SSE-S3 si está habilitado (S-03)."""
        try:
            import io
            from minio.sse import SseS3

            sse = SseS3() if settings.MINIO_SSE_ENABLED else None

            self.client.put_object(
                bucket_name=settings.MINIO_BUCKET_IMAGES,
                object_name=object_name,
                data=io.BytesIO(content),
                length=len(content),
                content_type=content_type or "application/octet-stream",
                sse=sse,
            )
            
            # Construir URL pública
            if settings.MINIO_SECURE:
                protocol = "https"
            else:
                protocol = "http"
            
            url = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_IMAGES}/{object_name}"
            
            return url
        
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir archivo a MinIO: {str(e)}"
            )
    
    async def _upload_to_local(self, object_name: str, content: bytes) -> str:
        """Sube archivo a almacenamiento local"""
        try:
            # Crear ruta completa
            file_path = self.local_storage_path / object_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar archivo
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Retornar URL local (relativa)
            return f"/storage/images/{object_name}"
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar archivo localmente: {str(e)}"
            )
    
    async def delete_image(self, image_url: str) -> bool:
        """
        Elimina una imagen del storage
        
        Args:
            image_url: URL de la imagen a eliminar
        
        Returns:
            bool: True si se eliminó correctamente
        """
        if self.use_minio:
            return await self._delete_from_minio(image_url)
        else:
            return await self._delete_from_local(image_url)
    
    async def _delete_from_minio(self, image_url: str) -> bool:
        """Elimina imagen de MinIO"""
        try:
            # Extraer object_name de la URL
            # Formato: http://localhost:9000/sirccd-images/reports/2026/03/02/abc123_file.jpg
            parts = image_url.split(f"/{settings.MINIO_BUCKET_IMAGES}/")
            if len(parts) != 2:
                return False
            
            object_name = parts[1]
            
            self.client.remove_object(
                bucket_name=settings.MINIO_BUCKET_IMAGES,
                object_name=object_name
            )
            return True
        
        except S3Error:
            return False
    
    async def _delete_from_local(self, image_url: str) -> bool:
        """Elimina imagen del almacenamiento local"""
        try:
            # Extraer path del URL
            # Formato: /storage/images/reports/2026/03/02/abc123_file.jpg
            if image_url.startswith("/storage/images/"):
                relative_path = image_url.replace("/storage/images/", "")
                file_path = self.local_storage_path / relative_path
                
                if file_path.exists():
                    file_path.unlink()
                    return True
            
            return False
        
        except Exception:
            return False


# Instancia global del servicio
storage_service = StorageService()
