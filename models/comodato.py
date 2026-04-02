from sqlalchemy import Table, Column, Enum, Text
from sqlalchemy.sql.sqltypes import Integer, String, Date, DateTime
from config.db import meta
from datetime import datetime

comodatos = Table(
    "comodatos", meta,
    Column("id", Integer, primary_key=True, index=True),
    Column("numero_comodato", String(50), unique=True, nullable=False),
    Column("tipo_bien", Enum('mueble', 'inmueble', 'automovil'), nullable=False),
    Column("bien_id", Integer, nullable=False),
    Column("codigo_bien", Integer),
    Column("descripcion_bien", Text),
    Column("comodatario_nombre", String(255), nullable=False),
    Column("comodatario_cedula", String(20), nullable=False),
    Column("comodatario_telefono", String(50)),
    Column("comodatario_email", String(100)),
    Column("comodatario_direccion", Text),
    Column("comodante_nombre", String(255)),
    Column("comodante_representante", String(255)),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date),
    Column("fecha_devolucion", Date),
    Column("documento_comodato", String(500)),
    Column("observaciones", Text),
    Column("condiciones", Text),
    Column("estado", Enum('activo', 'vencido', 'devuelto', 'cancelado'), default='activo'),
    Column("creado_por", String(100)),
    Column("fecha_creacion", DateTime, default=datetime.now),
    Column("actualizado_por", String(100)),
    Column("fecha_actualizacion", DateTime, default=datetime.now, onupdate=datetime.now)
)
