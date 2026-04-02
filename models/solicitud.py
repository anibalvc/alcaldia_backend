from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

solicitudes = Table("solicitudes", meta, Column(
    "id", Integer, primary_key=True,index=True),
    Column("num_bien", Integer),
    Column("descripcion", String(2000)),
    Column("serial", String(255)),
    Column("fecha", String(255)),
    Column("ingresado_por", String(255)))

