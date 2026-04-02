import os
from pathlib import Path
from typing import Optional

class StorageConfig:

    UPLOAD_BASE_DIR = os.path.join(os.getcwd(), "uploads", "bienes")

    STATIC_URL_PREFIX = "/api/v1/files"

    MAX_FILE_SIZE = 50 * 1024 * 1024  
    ALLOWED_EXTENSIONS = {
        'imagen': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
        'documento': {'.pdf'}
    }

    NAMING_PATTERN = "{tipo}_{secuencia:03d}_{timestamp}{extension}"

    @classmethod
    def get_bien_path(cls, bien_tipo: str, bien_id: int) -> str:
        
        return os.path.join(cls.UPLOAD_BASE_DIR, bien_tipo, str(bien_id))

    @classmethod
    def get_bien_path_by_numero(cls, bien_tipo: str, numero_bien: str) -> str:

        safe_numero = numero_bien.replace('/', '_').replace('\\', '_')
        return os.path.join(cls.UPLOAD_BASE_DIR, bien_tipo, f"num_{safe_numero}")

    @classmethod
    def ensure_directory_exists(cls, path: str) -> None:
        
        Path(path).mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_safe_path(cls, file_path: str) -> bool:
        
        try:
            
            abs_file_path = os.path.abspath(file_path)
            abs_base_path = os.path.abspath(cls.UPLOAD_BASE_DIR)

            return abs_file_path.startswith(abs_base_path)
        except:
            return False

    @classmethod
    def get_content_type(cls, extension: str) -> str:
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf'
        }
        return content_types.get(extension.lower(), 'application/octet-stream')

    @classmethod
    def init_storage(cls) -> None:
        
        base_dir = cls.UPLOAD_BASE_DIR

        for bien_tipo in ['muebles', 'inmuebles', 'automoviles']:
            tipo_dir = os.path.join(base_dir, bien_tipo)
            cls.ensure_directory_exists(tipo_dir)

            for subdir in ['imagenes', 'documentos']:
                ejemplo_dir = os.path.join(tipo_dir, 'ejemplo', subdir)
                cls.ensure_directory_exists(ejemplo_dir)

        print(f"✅ Estructura de almacenamiento inicializada en: {base_dir}")

class ThumbnailConfig:

    DEFAULT_SIZE = (200, 200)
    QUALITY = 85
    FORMAT = 'JPEG'
    SUFFIX = '_thumb'

    @classmethod
    def get_thumbnail_path(cls, original_path: str) -> str:
        
        base_name = os.path.splitext(original_path)[0]
        return f"{base_name}{cls.SUFFIX}.jpg"
