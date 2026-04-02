import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)

class S3StorageConfig:

    def __init__(self):
        
        self.host = os.getenv('MINIO_HOST', 'localhost')
        self.port = int(os.getenv('MINIO_PORT', '9000'))
        self.endpoint = f"{self.host}:{self.port}"
        self.access_key = os.getenv('MINIO_ROOT_USER', 'admin')
        self.secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'password123')
        self.use_ssl = os.getenv('MINIO_USE_SSL', 'false').lower() == 'true'
        self.region = os.getenv('S3_REGION', 'us-east-1')

        self.main_bucket = os.getenv('MINIO_DEFAULT_BUCKETS', 'bienes-storage')
        self.thumbnails_bucket = 'bienes-thumbnails'

        self.is_development = os.getenv('ENVIRONMENT', 'development') == 'development'

        self.MAX_FILE_SIZE = 50 * 1024 * 1024  
        self.ALLOWED_EXTENSIONS = {
            'imagen': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
            'documento': {'.pdf'}
        }

        if self.is_development:
            self.public_url_prefix = f"http{'s' if self.use_ssl else ''}://localhost:{self.port}"
        else:
            self.public_url_prefix = f"http{'s' if self.use_ssl else ''}://{self.endpoint}"

        self._minio_client = None
        self._boto3_client = None

    @property
    def minio_client(self) -> Minio:
        
        if self._minio_client is None:
            try:
                from minio import Minio
                from urllib3 import disable_warnings
                from urllib3.exceptions import InsecureRequestWarning

                if not self.use_ssl:
                    disable_warnings(InsecureRequestWarning)

                if self.use_ssl and self.port == 443:
                    endpoint = self.host
                else:
                    endpoint = f"{self.host}:{self.port}"

                self._minio_client = Minio(
                    endpoint=endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.use_ssl,
                    region=self.region
                )

                logger.info(f"✅ Cliente MinIO inicializado: {self.host}:{self.port}")
                return self._minio_client

            except Exception as e:
                logger.error(f"❌ Error configurando cliente MinIO: {e}")
                self._minio_client = None
                raise e
        return self._minio_client

    @property
    def boto3_client(self):
        
        if self._boto3_client is None:
            config = Config(
                region_name=self.region,
                retries={'max_attempts': 3},
                s3={'addressing_style': 'path'}
            )

            if self.use_ssl and self.port == 443:
                endpoint_url = f"https://{self.host}"
            elif self.use_ssl:
                endpoint_url = f"https://{self.host}:{self.port}"
            else:
                endpoint_url = f"http://{self.host}:{self.port}"

            self._boto3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=config
            )

        return self._boto3_client

    def get_object_key(self, bien_tipo: str, bien_id: int, filename: str,
                      subfolder: str = None) -> str:
        
        parts = [bien_tipo, str(bien_id)]

        if subfolder:
            parts.append(subfolder)

        parts.append(filename)
        return '/'.join(parts)

    def get_public_url(self, bucket: str, object_key: str) -> str:
        
        return f"{self.public_url_prefix}/{bucket}/{object_key}"

    def get_presigned_url(self, bucket: str, object_key: str,
                         expiration: int = 3600, method: str = 'GET') -> str:
        
        try:
            if method == 'GET':
                url = self.boto3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            elif method == 'PUT':
                url = self.boto3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': bucket, 'Key': object_key},
                    ExpiresIn=expiration
                )
            else:
                raise ValueError(f"Método no soportado: {method}")

            return url
        except ClientError as e:
            logger.error(f"Error generando URL pre-firmada: {e}")
            return ""

    def init_buckets(self) -> Dict[str, bool]:
        
        results = {}
        buckets = [self.main_bucket, self.thumbnails_bucket]

        for bucket_name in buckets:
            try:
                
                if not self.minio_client.bucket_exists(bucket_name):
                    
                    self.minio_client.make_bucket(bucket_name)
                    logger.info(f"✅ Bucket '{bucket_name}' creado")
                else:
                    logger.info(f"✅ Bucket '{bucket_name}' ya existe")

                if self.is_development:
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                            }
                        ]
                    }

                    import json
                    self.minio_client.set_bucket_policy(bucket_name, json.dumps(policy))
                    logger.info(f"✅ Política pública configurada para '{bucket_name}'")

                results[bucket_name] = True

            except S3Error as e:
                logger.error(f"❌ Error configurando bucket '{bucket_name}': {e}")
                results[bucket_name] = False
            except Exception as e:
                logger.error(f"❌ Error inesperado configurando bucket '{bucket_name}': {e}")
                results[bucket_name] = False

        return results

    def get_content_type(self, extension: str) -> str:
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf'
        }
        return content_types.get(extension.lower(), 'application/octet-stream')

    def generate_unique_filename(self, original_filename: str, bien_id: int,
                               tipo_archivo: str) -> str:
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = Path(original_filename).suffix.lower()

        filename = f"{tipo_archivo[:3].upper()}_{bien_id}_{timestamp}{extension}"
        return filename

    def is_valid_file_type(self, filename: str) -> tuple[bool, str]:
        
        extension = Path(filename).suffix.lower()

        for tipo, extensions in self.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return True, tipo

        return False, ""

    def get_debug_info(self) -> Dict[str, Any]:
        
        return {
            'endpoint': self.endpoint,
            'main_bucket': self.main_bucket,
            'thumbnails_bucket': self.thumbnails_bucket,
            'use_ssl': self.use_ssl,
            'is_development': self.is_development,
            'public_url_prefix': self.public_url_prefix,
            'max_file_size_mb': self.MAX_FILE_SIZE / 1024 / 1024,
            'allowed_extensions': self.ALLOWED_EXTENSIONS
        }

s3_config = S3StorageConfig()

logger.info("⚙️ Configuración S3 cargada. Buckets se inicializan bajo demanda.")
