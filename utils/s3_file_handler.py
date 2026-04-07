import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional, List, BinaryIO
from io import BytesIO
from fastapi import UploadFile, HTTPException
from PIL import Image
from pathlib import Path

from config.s3_storage import s3_config
from minio.error import S3Error
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3FileHandler:
    """Manejador para operaciones de archivos en S3/MinIO"""

    def __init__(self):
        self.s3_config = s3_config
        # Configuración de thumbnails (mantener compatibilidad)
        self.thumbnail_size = (200, 200)
        self.thumbnail_quality = 85

    def validate_file(self, file: UploadFile) -> Dict[str, any]:
        """Valida tipo, tamaño y contenido del archivo"""

        # Verificar que el archivo tenga nombre
        if not file.filename:
            raise HTTPException(status_code=400, detail="El archivo debe tener un nombre")

        # Validar tipo de archivo
        is_valid, tipo_archivo = self.s3_config.is_valid_file_type(file.filename)
        if not is_valid:
            extension = Path(file.filename).suffix.lower()
            raise HTTPException(
                status_code=400,
                detail=f"Extensión {extension} no permitida. Formatos válidos: JPG, PNG, GIF, WebP, PDF"
            )

        # Obtener tamaño del archivo
        file.file.seek(0, 2)  # Ir al final del archivo
        file_size = file.file.tell()
        file.file.seek(0)  # Volver al inicio

        # Validar tamaño
        if file_size > self.s3_config.MAX_FILE_SIZE:
            size_mb = file_size / 1024 / 1024
            max_mb = self.s3_config.MAX_FILE_SIZE / 1024 / 1024
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande: {size_mb:.1f}MB. Máximo permitido: {max_mb}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")

        extension = Path(file.filename).suffix.lower()

        return {
            'tipo_archivo': tipo_archivo,
            'extension': extension,
            'tamaño_bytes': file_size,
            'nombre_original': file.filename
        }

    async def save_file(self, file: UploadFile, bien_id: int, numero_bien: str,
                       bien_tipo: str, subido_por: str) -> Dict[str, str]:
        """Guarda archivo en S3/MinIO y retorna metadatos para BD"""

        # Validar archivo
        file_info = self.validate_file(file)

        # Generar nombre único
        unique_filename = self.s3_config.generate_unique_filename(
            file.filename, bien_id, file_info['tipo_archivo']
        )

        # Determinar subfolder
        subfolder = "imagenes" if file_info['tipo_archivo'] == 'imagen' else "documentos"

        # Generar object key en S3
        object_key = self.s3_config.get_object_key(
            bien_tipo, bien_id, unique_filename, subfolder
        )

        try:
            # Leer contenido del archivo
            file.file.seek(0)
            file_content = await file.read()

            # Generar checksum
            checksum_md5 = hashlib.md5(file_content).hexdigest()

            # Configurar metadatos
            metadata = {
                'original-filename': file.filename,
                'bien-id': str(bien_id),
                'numero-bien': numero_bien,
                'bien-tipo': bien_tipo,
                'subido-por': subido_por,
                'upload-timestamp': datetime.now().isoformat(),
                'checksum-md5': checksum_md5
            }

            # Subir archivo principal a S3/MinIO
            content_type = self.s3_config.get_content_type(file_info['extension'])

            self.s3_config.minio_client.put_object(
                bucket_name=self.s3_config.main_bucket,
                object_name=object_key,
                data=BytesIO(file_content),
                length=len(file_content),
                content_type=content_type,
                metadata=metadata
            )

            # Generar thumbnail para imágenes
            thumbnail_url = None
            if file_info['tipo_archivo'] == 'imagen':
                thumbnail_url = await self._generate_and_upload_thumbnail(
                    file_content, object_key, bien_tipo, bien_id, unique_filename
                )

            # Generar URLs
            public_url = self.s3_config.get_public_url(self.s3_config.main_bucket, object_key)

            # Para desarrollo, usar URL directa. Para producción, usar presigned URL
            if self.s3_config.is_development:
                url_acceso = public_url
            else:
                # URL pre-firmada de 24 horas
                url_acceso = self.s3_config.get_presigned_url(
                    self.s3_config.main_bucket, object_key, expiration=86400
                )

            logger.info(f"✅ Archivo subido a S3: {object_key}")

            return {
                'nombre_archivo': unique_filename,
                'ruta_archivo': object_key,  # En S3 usamos object_key como "ruta"
                'url_acceso': url_acceso,
                'thumbnail_path': thumbnail_url,
                'checksum_md5': checksum_md5,
                's3_bucket': self.s3_config.main_bucket,
                's3_object_key': object_key,
                **file_info  # tipo_archivo, extension, tamaño_bytes, nombre_original
            }

        except S3Error as e:
            logger.error(f"❌ Error S3 subiendo archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error al guardar archivo en S3: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error inesperado subiendo archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")

    async def _generate_and_upload_thumbnail(self, image_data: bytes, original_object_key: str,
                                           bien_tipo: str, bien_id: int, filename: str) -> Optional[str]:
        """Genera y sube thumbnail a S3"""
        try:
            # Abrir imagen con PIL
            with Image.open(BytesIO(image_data)) as img:
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Generar thumbnail manteniendo aspecto
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

                # Guardar thumbnail en memoria
                thumbnail_buffer = BytesIO()
                img.save(thumbnail_buffer, 'JPEG', quality=self.thumbnail_quality)
                thumbnail_data = thumbnail_buffer.getvalue()

                # Generar object key para thumbnail
                thumbnail_filename = f"thumb_{filename.replace(Path(filename).suffix, '.jpg')}"
                thumbnail_object_key = self.s3_config.get_object_key(
                    bien_tipo, bien_id, thumbnail_filename, "thumbnails"
                )

                # Subir thumbnail
                self.s3_config.minio_client.put_object(
                    bucket_name=self.s3_config.thumbnails_bucket,
                    object_name=thumbnail_object_key,
                    data=BytesIO(thumbnail_data),
                    length=len(thumbnail_data),
                    content_type='image/jpeg',
                    metadata={
                        'original-object-key': original_object_key,
                        'thumbnail-size': f"{self.thumbnail_size[0]}x{self.thumbnail_size[1]}",
                        'generated-at': datetime.now().isoformat()
                    }
                )

                # Retornar URL del thumbnail
                if self.s3_config.is_development:
                    return self.s3_config.get_public_url(self.s3_config.thumbnails_bucket, thumbnail_object_key)
                else:
                    return self.s3_config.get_presigned_url(
                        self.s3_config.thumbnails_bucket, thumbnail_object_key, expiration=86400
                    )

        except Exception as e:
            logger.warning(f"⚠️ Error generando thumbnail: {e}")
            return None

    async def download_file(self, object_key: str, bucket: str = None) -> bytes:
        """Descarga archivo desde S3/MinIO"""
        if bucket is None:
            bucket = self.s3_config.main_bucket

        try:
            response = self.s3_config.minio_client.get_object(bucket, object_key)
            file_data = response.read()
            response.close()
            response.release_conn()

            logger.info(f"✅ Archivo descargado desde S3: {object_key}")
            return file_data

        except S3Error as e:
            logger.error(f"❌ Error S3 descargando archivo: {e}")
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {object_key}")
        except Exception as e:
            logger.error(f"❌ Error inesperado descargando archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

    async def delete_file(self, object_key: str, bucket: str = None) -> bool:
        """Elimina archivo de S3/MinIO"""
        if bucket is None:
            bucket = self.s3_config.main_bucket

        try:
            self.s3_config.minio_client.remove_object(bucket, object_key)
            logger.info(f"✅ Archivo eliminado de S3: {object_key}")
            return True

        except S3Error as e:
            logger.error(f"❌ Error S3 eliminando archivo: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado eliminando archivo: {e}")
            return False

    def get_file_url(self, object_key: str, bucket: str = None, expiration: int = 3600) -> str:
        """Obtiene URL de acceso para un archivo"""
        if bucket is None:
            bucket = self.s3_config.main_bucket

        if self.s3_config.is_development:
            # En desarrollo, usar URL pública directa
            return self.s3_config.get_public_url(bucket, object_key)
        else:
            # En producción, usar URL pre-firmada
            return self.s3_config.get_presigned_url(bucket, object_key, expiration)

    def get_thumbnail_url(self, thumbnail_object_key: str, expiration: int = 3600) -> str:
        """Obtiene URL de acceso para un thumbnail"""
        return self.get_file_url(thumbnail_object_key, self.s3_config.thumbnails_bucket, expiration)

    def validate_multiple_files(self, files: List[UploadFile]) -> List[Dict[str, any]]:
        """Valida múltiples archivos"""
        if not files:
            raise HTTPException(status_code=400, detail="No se proporcionaron archivos")

        if len(files) > 10:  # Límite de archivos por upload
            raise HTTPException(status_code=400, detail="Máximo 10 archivos por subida")

        validated_files = []
        for file in files:
            try:
                file_info = self.validate_file(file)
                validated_files.append(file_info)
            except HTTPException as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error en archivo '{file.filename}': {e.detail}"
                )

        return validated_files

    async def get_file_info(self, object_key: str, bucket: str = None) -> Optional[Dict[str, any]]:
        """Obtiene información de un archivo en S3"""
        if bucket is None:
            bucket = self.s3_config.main_bucket

        try:
            stat = self.s3_config.minio_client.stat_object(bucket, object_key)

            return {
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata,
                'exists': True
            }

        except S3Error:
            return None
        except Exception:
            return None

# Instancia global del file handler
s3_file_handler = S3FileHandler()