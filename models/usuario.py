from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

usuarios = Table("usuarios", meta, Column(
    "id", Integer, primary_key=True,index=True),
    Column("nombre", String(255)),
    Column("ingresado_por", String(255)),
    Column("usuario", String(255)),
    Column("clave", String(255)),
    Column("rol", String(255)),
    Column("departamento", String(255)))

