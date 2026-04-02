from array import array
from typing import List
from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

menus = Table("menu", meta, Column(
    "id", Integer, primary_key=True, index=True),
    Column(
    "idPadre", Integer),
    Column(
    "tieneItems", Integer),
    Column("vista", String(255)),
    Column("ruta", String(255)),)

roles = Table("roles_menu", meta, Column(
    "id", Integer, primary_key=True, index=True),
    Column(
    "idMenuPadre", Integer),
    Column(
    "idMenuHijo", Integer),
    Column("rol", String(255)),)

especial = Table("seguro", meta, Column(
    "variable", Integer),
)
