from sqlalchemy import Table, Column, ForeignKey, Enum
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Text
from config.db import meta
from datetime import datetime

reportes_historial = Table(
    "reportes_historial", meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("numero_reporte", String(50), nullable=False),
    Column("tipo_reporte", String(20), nullable=False),
    Column("fecha_generacion", DateTime, default=datetime.now),
    Column("generado_por", String(100)),
    Column("observaciones", Text),
    Column("departamento", String(100))
)

reportes_detalles = Table(
    "reportes_detalles", meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("reporte_id", Integer, ForeignKey("reportes_historial.id"), nullable=False),
    Column("tipo_bien", Enum('mueble', 'inmueble', 'automovil'), nullable=False),
    Column("bien_id", Integer, nullable=False),
    Column("codigo_bien", Integer)
)
