from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, Text, Boolean, DateTime
from config.db import meta

usuarios_extended = Table(
    "usuarios_extended",
    meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("authy_user_id", String(100), unique=True, nullable=False),
    Column("email", String(255), nullable=False, index=True),
    Column("departamento_id", Integer, ForeignKey("departamentos.id"), nullable=False),
    Column("cargo", String(255), nullable=True),
    Column("telefono", String(50), nullable=True),
    Column("extension", String(20), nullable=True),
    Column("preferencias", Text, nullable=True),
    Column("activo", Boolean, default=True),
    Column("notas", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=True),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("creado_por", String(255), nullable=True),
    Column("actualizado_por", String(255), nullable=True),
)
