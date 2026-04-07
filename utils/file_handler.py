import os
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import UploadFile, HTTPException
from PIL import Image
from pathlib import Path

from config.storage import StorageConfig, ThumbnailConfig

class FileHandler:
    """Manejador para operaciones de archivos físicos"""

    def __init__(self):
        self.storage_config = StorageConfig
        self.thumbnail_config = ThumbnailConfig

    def validate_file(self, file: UploadFile) -> Dict[str, any]:
        """Valida tipo, tamaño y contenido del archivo"""

        # Verificar que el archivo tenga nombre
        if not file.filename:
            raise HTTPException(status_code=400, detail="El archivo debe tener un nombre")

        # Obtener extensión
        extension = os.path.splitext(file.filename)[1].lower()

        # Determinar tipo de archivo
        tipo_archivo = self._determine_file_type(extension)
        if not tipo_archivo:
            raise HTTPException(
                status_code=400,
                detail=f"Extensión {extension} no permitida. Formatos válidos: JPG, PNG, GIF, WebP, PDF"
            )

        # Obtener tamaño del archivo
        file.file.seek(0, 2)  # Ir al final del archivo
        file_size = file.file.tell()
        file.file.seek(0)  # Volver al inicio

        # Validar tamaño
        if file_size > self.storage_config.MAX_FILE_SIZE:
            size_mb = file_size / 1024 / 1024
            max_mb = self.storage_config.MAX_FILE_SIZE / 1024 / 1024
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande: {size_mb:.1f}MB. Máximo permitido: {max_mb}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")

        return {
            'tipo_archivo': tipo_archivo,
            'extension': extension,
            'tamaño_bytes': file_size,
            'nombre_original': file.filename
        }

    def save_file(self, file: UploadFile, bien_id: int, numero_bien: str,
                  bien_tipo: str, subido_por: str) -> Dict[str, str]:
        """Guarda archivo físicamente y retorna metadatos para BD"""

        # Validar archivo
        file_info = self.validate_file(file)

        # Generar ruta de destino
        base_path = self.storage_config.get_bien_path(bien_tipo, bien_id)
        subfolder = "imagenes" if file_info['tipo_archivo'] == 'imagen' else "documentos"
        full_path = os.path.join(base_path, subfolder)

        # Crear directorios si no existen
        self.storage_config.ensure_directory_exists(full_path)

        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sequence = self._get_next_sequence(full_path, file_info['tipo_archivo'])

        nombre_archivo = self.storage_config.NAMING_PATTERN.format(
            tipo=file_info['tipo_archivo'][:3].upper(),
            secuencia=sequence,
            timestamp=timestamp,
            extension=file_info['extension']
        )

        archivo_path = os.path.join(full_path, nombre_archivo)

        # Guardar archivo físicamente
        try:
            with open(archivo_path, "wb") as buffer:
                file.file.seek(0)  # Asegurar que estamos al inicio
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")

        # Generar URL de acceso
        relative_path = os.path.relpath(archivo_path, self.storage_config.UPLOAD_BASE_DIR)
        url_acceso = f"{self.storage_config.STATIC_URL_PREFIX}/{relative_path.replace(os.sep, '/')}"

        # Generar thumbnail para imágenes
        thumbnail_path = None
        if file_info['tipo_archivo'] == 'imagen':
            thumbnail_path = self.generate_thumbnail(archivo_path)

        # Generar checksum
        checksum_md5 = self.get_file_checksum(archivo_path)

        return {
            'nombre_archivo': nombre_archivo,
            'ruta_archivo': archivo_path,  # Ruta física completa
            'url_acceso': url_acceso,      # URL para acceso web
            'thumbnail_path': thumbnail_path,
            'checksum_md5': checksum_md5,
            **file_info  # tipo_archivo, extension, tamaño_bytes, nombre_original
        }

    def delete_file(self, ruta_archivo: str) -> bool:
        """Elimina archivo físico del sistema"""
        try:
            # Verificar que la ruta sea segura
            if not self.storage_config.is_safe_path(ruta_archivo):
                return False

            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

                # Eliminar thumbnail si existe
                thumbnail_path = self.thumbnail_config.get_thumbnail_path(ruta_archivo)
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)

                return True
            return False
        except Exception:
            return False

    def generate_thumbnail(self, image_path: str) -> Optional[str]:
        """Genera thumbnail para imágenes"""
        try:
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Generar thumbnail manteniendo aspecto
                img.thumbnail(self.thumbnail_config.DEFAULT_SIZE, Image.Resampling.LANCZOS)

                # Generar path para thumbnail
                thumbnail_path = self.thumbnail_config.get_thumbnail_path(image_path)

                # Guardar thumbnail
                img.save(
                    thumbnail_path,
                    self.thumbnail_config.FORMAT,
                    quality=self.thumbnail_config.QUALITY
                )
                return thumbnail_path

        except Exception as e:
            print(f"Error generando thumbnail: {str(e)}")
            return None

    def get_file_checksum(self, file_path: str) -> str:
        """Genera checksum MD5 del archivo para verificar integridad"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _determine_file_type(self, extension: str) -> Optional[str]:
        """Determina el tipo de archivo basado en extensión"""
        for tipo, extensions in self.storage_config.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return tipo
        return None

    def _get_next_sequence(self, directory: str, file_type: str) -> int:
        """Obtiene el siguiente número de secuencia para el archivo"""
        if not os.path.exists(directory):
            return 1

        try:
            existing_files = [f for f in os.listdir(directory)
                             if f.startswith(file_type[:3].upper())]
            return len(existing_files) + 1
        except Exception:
            return 1

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

    def get_file_info(self, file_path: str) -> Optional[Dict[str, any]]:
        """Obtiene información de un archivo existente"""
        try:
            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'exists': True
            }
        except Exception:
            return None