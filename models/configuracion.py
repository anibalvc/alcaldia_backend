from sqlalchemy import Table, Column, Text
from sqlalchemy.sql.sqltypes import String
from config.db import meta

configuraciones = Table(
    "configuraciones", meta,
    Column("clave", String(50), primary_key=True),
    Column("valor", Text),
    Column("grupo", String(50)),
    Column("descripcion", String(255))
)
