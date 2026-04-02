from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Text, Boolean, DateTime
from config.db import meta

departamentos = Table(
    "departamentos",
    meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("codigo", Integer, unique=True, nullable=False),
    Column("nombre", String(255), unique=True, nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("responsable", String(255), nullable=True),
    Column("director", String(255), nullable=True),
    Column("ubicacion", String(255), nullable=True),
    Column("telefono", String(50), nullable=True),
    Column("email", String(255), nullable=True),
    Column("activo", Boolean, default=True),
    Column("fecha_creacion", DateTime, nullable=True),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("creado_por", String(255), nullable=True),
    Column("actualizado_por", String(255), nullable=True),
)
