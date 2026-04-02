from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

solicitudesMuebles = Table("solicitudes_muebles", meta, Column(
    "id", Integer, primary_key=True, index=True),
    Column("fecha_solicitud", String(255)),
    Column("descripcion", String(2000)),
    Column("marca", String(2000)),
    Column("modelo", String(2000)),
    Column("serial", String(2000)),
    Column("responsable", String(2000)),
    Column("num_bien", Integer),
    Column("tipo", String(255)),
    Column("departamento", String(255)),
    Column("solicitado_por", String(255)))

