from sqlalchemy import Table, Column, Enum
from sqlalchemy.sql.sqltypes import Integer, String, Boolean, DateTime
from config.db import meta
from datetime import datetime

conceptos_movimiento = Table(
    "conceptos_movimiento", meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("codigo", String(20), unique=True, nullable=False),
    Column("descripcion", String(255), nullable=False),
    Column("tipo", Enum('incorporacion', 'desincorporacion', 'ambos'), nullable=False, default='incorporacion'),
    Column("estado", Boolean, default=True),  
    Column("creado_por", String(100)),
    Column("fecha_creacion", DateTime, default=datetime.now)
)
