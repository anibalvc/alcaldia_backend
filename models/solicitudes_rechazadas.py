from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

solicitudesRechazadas = Table("solicitudes_rechazadas", meta, Column(
    "id", Integer, primary_key=True, index=True),
    Column("fecha_solicitud", String(255)),
    Column("descripcion", String(2000)),
    Column("nombre", String(2000)),
    Column("num_bien", Integer),
    Column("tipo", String(255)),
    Column("id_solicitud", Integer),
    Column("departamento", String(255)),
    Column("rechazada_por", String(255)),
    Column("descripcion_rechazo", String(255)),
    Column("tipo_bien", String(255)),
    Column("solicitado_por", String(255)))