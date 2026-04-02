from sqlalchemy import Table, Column, Numeric, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta

inmuebles = Table("inmuebles", meta, Column(
    "id", Integer, primary_key=True,index=True),
    Column("fecha_ingreso", String(255)),
    Column("orden_pago", Integer, nullable=True),
    Column("partida_compra", Integer, nullable=True),
    Column("num_factura", Integer, nullable=True),
    Column("nombre", String(255)),
    Column("descripcion", String(2000)),
    Column("valor_inicial", Numeric(40, 3)),
    Column("valor_actual", Numeric(40, 3)),
    Column("num_bien", Integer),
    Column("num_expediente", String(255)),
    Column("departamento", String(255)),
    Column("concepto_incorporacion", String(20), ForeignKey("conceptos_movimiento.codigo")),
    Column("ingresado_por", String(255)))

inmueblesDeleted = Table("deleted_inmuebles", meta, Column(
    "id", Integer, primary_key=True,index=True),
    Column("fecha_ingreso", String(255)),
    Column("orden_pago", Integer, nullable=True),
    Column("partida_compra", Integer, nullable=True),
    Column("num_factura", Integer, nullable=True),
    Column("nombre", String(255)),
    Column("descripcion", String(2000)),
    Column("valor_inicial", Numeric(40, 3)),
    Column("valor_actual", Numeric(40, 3)),
    Column("num_bien", Integer),
    Column("num_oficio", Integer),
    Column("num_expediente", String(255)),
    Column("departamento", String(255)),
    Column("eliminado_por", String(255)),
    Column("concepto_incorporacion", String(20)),
    Column("concepto_desincorporacion", String(20)),
    Column("ingresado_por", String(255)))