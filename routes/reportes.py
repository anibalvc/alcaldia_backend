from fastapi import APIRouter, Query
from config.db import conn
from models.mueble import muebles, mueblesDeleted
from models.automovil import automoviles, automovilesDeleted
from schemas.reportes import BM1Response, BM1Item, BM1Totales
from sqlalchemy import func, extract, and_, or_, select
from datetime import datetime
from decimal import Decimal

reportes = APIRouter()

@reportes.get("/reportes/bm1", tags=["Reportes"], response_model=BM1Response)
def generar_reporte_bm1(
    departamento: str | None = None,
    fecha_corte: str | None = None
):

    try:
        
        conn.rollback()
    except:
        pass

    if fecha_corte is None:
        fecha_corte_obj = datetime.now()
        fecha_corte = f"{fecha_corte_obj.day}/{fecha_corte_obj.month}/{fecha_corte_obj.year}"
    else:
        
        partes = fecha_corte.split('/')
        fecha_corte_obj = datetime(int(partes[2]), int(partes[1]), int(partes[0]))

    año_actual = fecha_corte_obj.year

    query_muebles = muebles.select()

    if departamento:
        query_muebles = query_muebles.where(muebles.c.departamento.contains(departamento))

    query_muebles = query_muebles.order_by(muebles.c.num_catalogo, muebles.c.num_bien)

    resultados_muebles = conn.execute(query_muebles).fetchall()

    query_vehiculos = automoviles.select()

    if departamento:
        query_vehiculos = query_vehiculos.where(automoviles.c.departamento.contains(departamento))

    query_vehiculos = query_vehiculos.order_by(automoviles.c.num_bien)

    resultados_vehiculos = conn.execute(query_vehiculos).fetchall()

    items = []
    total_valor_inventario = Decimal('0.00')

    for row in resultados_muebles:
        item = BM1Item(
            numero_catalogo=row.num_catalogo or "",
            codigo_bien=row.num_bien,
            descripcion=row.descripcion or "",
            cantidad=1,
            orden_compra=str(row.orden_pago) if row.orden_pago and row.orden_pago != 0 else "",
            fecha_registro=row.fecha_ingreso or "",
            fecha_compra=row.fecha_compra or "",
            marca=row.marca or "",
            modelo=row.modelo or "",
            ubicacion=row.departamento or "",
            seriales=row.serial or "",
            responsable=row.responsable or "",
            valor=Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00'),
            estado=row.estado or ""
        )
        items.append(item)
        total_valor_inventario += item.valor

    for row in resultados_vehiculos:
        
        descripcion_parts = ["VEHÍCULO"]
        
        if row.año:
            descripcion_parts.append(f"Año: {row.año}")
        if row.color:
            descripcion_parts.append(f"Color: {row.color}")
        if row.placa:
            descripcion_parts.append(f"Placa: {row.placa}")
        if row.num_expediente:
            descripcion_parts.append(f"Expediente: {row.num_expediente}")
        if row.operatividad:
            descripcion_parts.append(f"Operatividad: {row.operatividad}")
        if row.num_factura and row.num_factura != 0:
            descripcion_parts.append(f"Factura: {row.num_factura}")
        if row.partida_compra and row.partida_compra != 0:
            descripcion_parts.append(f"Partida: {row.partida_compra}")
        
        descripcion = " - ".join(descripcion_parts)

        seriales_parts = []
        if row.num_serial_motor:
            seriales_parts.append(f"Motor: {row.num_serial_motor}")
        if row.num_serial_carroceria:
            seriales_parts.append(f"Carrocería: {row.num_serial_carroceria}")
        seriales = ", ".join(seriales_parts) if seriales_parts else ""
        
        item = BM1Item(
            numero_catalogo="",  
            codigo_bien=row.num_bien,
            descripcion=descripcion,
            cantidad=1,
            orden_compra=str(row.orden_pago) if row.orden_pago and row.orden_pago != 0 else "",
            fecha_registro=row.fecha_ingreso or "",
            fecha_compra="",  
            marca=row.marca or "",
            modelo=row.modelo or "",
            ubicacion=row.departamento or "",
            seriales=seriales,
            responsable=row.chofer or "",  
            valor=Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00'),
            estado=row.estatus or ""  
        )
        items.append(item)
        total_valor_inventario += item.valor

    items.sort(key=lambda x: x.codigo_bien)

    total_elementos = len(items)

    query_incorporados_muebles = muebles.select()
    if departamento:
        query_incorporados_muebles = query_incorporados_muebles.where(muebles.c.departamento.contains(departamento))

    incorporados_muebles = conn.execute(query_incorporados_muebles).fetchall()

    elementos_incorporados = 0
    monto_incorporaciones = Decimal('0.00')

    for row in incorporados_muebles:
        
        if row.fecha_ingreso:
            try:
                partes_fecha = row.fecha_ingreso.split('/')
                if len(partes_fecha) == 3:
                    año_ingreso = int(partes_fecha[2])
                    if año_ingreso == año_actual:
                        elementos_incorporados += 1
                        monto_incorporaciones += Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00')
            except:
                pass

    query_incorporados_vehiculos = automoviles.select()
    if departamento:
        query_incorporados_vehiculos = query_incorporados_vehiculos.where(automoviles.c.departamento.contains(departamento))

    incorporados_vehiculos = conn.execute(query_incorporados_vehiculos).fetchall()

    for row in incorporados_vehiculos:
        
        if row.fecha_ingreso:
            try:
                partes_fecha = row.fecha_ingreso.split('/')
                if len(partes_fecha) == 3:
                    año_ingreso = int(partes_fecha[2])
                    if año_ingreso == año_actual:
                        elementos_incorporados += 1
                        monto_incorporaciones += Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00')
            except:
                pass

    query_desincorporados_muebles = mueblesDeleted.select()
    if departamento:
        query_desincorporados_muebles = query_desincorporados_muebles.where(mueblesDeleted.c.departamento.contains(departamento))

    desincorporados_muebles = conn.execute(query_desincorporados_muebles).fetchall()

    elementos_desincorporados = 0
    monto_desincorporaciones = Decimal('0.00')

    for row in desincorporados_muebles:
        
        if row.fecha_ingreso:
            try:
                partes_fecha = row.fecha_ingreso.split('/')
                if len(partes_fecha) == 3:
                    año_eliminacion = int(partes_fecha[2])
                    if año_eliminacion == año_actual:
                        elementos_desincorporados += 1
                        monto_desincorporaciones += Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00')
            except:
                pass

    from sqlalchemy import select
    query_desincorporados_vehiculos = select(
        automovilesDeleted.c.fecha_ingreso,
        automovilesDeleted.c.valor_actual,
        automovilesDeleted.c.departamento
    )
    if departamento:
        query_desincorporados_vehiculos = query_desincorporados_vehiculos.where(automovilesDeleted.c.departamento.contains(departamento))

    desincorporados_vehiculos = conn.execute(query_desincorporados_vehiculos).fetchall()

    for row in desincorporados_vehiculos:
        
        if row.fecha_ingreso:
            try:
                partes_fecha = row.fecha_ingreso.split('/')
                if len(partes_fecha) == 3:
                    año_eliminacion = int(partes_fecha[2])
                    if año_eliminacion == año_actual:
                        elementos_desincorporados += 1
                        monto_desincorporaciones += Decimal(str(row.valor_actual)) if row.valor_actual else Decimal('0.00')
            except:
                pass

    inventario_inicial = total_elementos + elementos_desincorporados - elementos_incorporados

    inventario_inicial_monetario = total_valor_inventario + monto_desincorporaciones - monto_incorporaciones

    totales = BM1Totales(
        total_elementos=total_elementos,
        elementos_incorporados=elementos_incorporados,
        elementos_desincorporados=elementos_desincorporados,
        inventario_inicial=inventario_inicial,
        total_inventario_monetario=total_valor_inventario,
        monto_incorporaciones=monto_incorporaciones,
        monto_desincorporaciones=monto_desincorporaciones,
        inventario_inicial_monetario=inventario_inicial_monetario
    )

    return BM1Response(
        items=items,
        totales=totales,
        departamento=departamento,
        fecha_corte=fecha_corte
    )
