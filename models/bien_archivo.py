from sqlalchemy import Table, Column, Text, Boolean, func
from sqlalchemy.sql.sqltypes import Integer, String, DateTime
from config.db import meta

bien_archivos = Table(
    "bien_archivos", meta,

    Column("id", Integer, primary_key=True, index=True),

    Column("bien_id", Integer, nullable=False, index=True),
    Column("numero_bien", String(50), nullable=False, index=True),
    Column("bien_tipo", String(20), nullable=False, index=True),

    Column("nombre_archivo", String(255), nullable=False),
    Column("nombre_original", String(255), nullable=False),
    Column("tipo_archivo", String(10), nullable=False),
    Column("extension", String(10), nullable=False),
    Column("tamaño_bytes", Integer, nullable=False),

    Column("ruta_archivo", String(500), nullable=False, unique=True),  
    Column("url_acceso", String(500), nullable=False),
    Column("thumbnail_path", String(500)),

    Column("s3_bucket", String(100)),  
    Column("s3_object_key", String(500)),  
    Column("storage_type", String(20), default="local"),  

    Column("descripcion", Text),
    Column("checksum_md5", String(32)),

    Column("subido_por", String(100), nullable=False),
    Column("fecha_subida", DateTime, server_default=func.now()),
    Column("modificado_por", String(100)),
    Column("fecha_modificacion", DateTime),

    Column("activo", Boolean, default=True, nullable=False)
)
