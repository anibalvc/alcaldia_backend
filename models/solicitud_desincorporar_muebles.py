from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

solicitudesDesincorporarMuebles = Table("desincorporar_muebles", meta, Column(
    "id", Integer, primary_key=True, index=True),
    Column("fecha_solicitud", String(255)),
    Column("descripcion", String(2000)),
    Column("nombre", String(2000)),
    Column("num_bien", Integer),
    Column("tipo", String(255)),
    Column("departamento", String(255)),
    Column("solicitado_por", String(255)),
    Column("num_oficio", String(255)))
