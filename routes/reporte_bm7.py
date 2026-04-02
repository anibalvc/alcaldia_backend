from fastapi import APIRouter, HTTPException, Body
from config.db import conn
from models.mueble import muebles
from models.automovil import automoviles
from models.concepto import conceptos_movimiento
from models.departamento import departamentos
from typing import List
from schemas.reporte_bm7 import ReporteBM7Response, BienBM7Item, BienDisponibleBM7
from schemas.reporte_historial import ReporteGenerarRequest, ReporteTipoEnum, DetalleBien
from routes.reporte_historial import generar_reporte_historial
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal

reporte_bm7_router = APIRouter()

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def get_motivo_descripcion(codigo: str) -> str:
    if not codigo:
        return "COMPRA"
    
    query = select(conceptos_movimiento.c.descripcion).where(conceptos_movimiento.c.codigo == codigo)
    try:
        desc = conn.execute(query).scalar()
        return desc.upper() if desc else "COMPRA"
    except Exception:
        return "COMPRA"

@reporte_bm7_router.post("/reportes/bm7", tags=["Reportes"], response_model=ReporteBM7Response)
def generar_acta_incorporacion(
    request: ReporteGenerarRequest
):

    if request.tipo_reporte != ReporteTipoEnum.BM7:
        raise HTTPException(status_code=400, detail="El tipo de reporte debe ser BM7")

    historial = generar_reporte_historial(request)

    items_bm7 = []
    total_monto = Decimal("0.00")
    
    for bien_req in request.bienes:
        bien_data = None
        tipo_bien = bien_req.tipo_bien.lower()
        bien_id = bien_req.bien_id
        
        try:
            if tipo_bien == "mueble":
                query = select(muebles).where(muebles.c.id == bien_id)
                bien_data = conn.execute(query).first()
                if bien_data:
                    
                    item = BienBM7Item(
                        numero_catalogo=bien_data.num_catalogo or "S/C",
                        cantidad=1,
                        motivo=get_motivo_descripcion(bien_data.concepto_incorporacion),
                        codigo_bien=str(bien_data.num_bien),
                        nombre_descripcion=f"{bien_data.descripcion} - {bien_data.marca or ''} {bien_data.modelo or ''}".strip(),
                        orden_compra=str(bien_data.orden_pago) if bien_data.orden_pago else "S/N",
                        fecha_registro=bien_data.fecha_ingreso or "",
                        seriales=bien_data.serial or "S/N",
                        valor_unitario=bien_data.monto or Decimal("0.01"),
                        estado=bien_data.estado or "BUENO"
                    )
                    items_bm7.append(item)
                    total_monto += item.valor_unitario
                    
            elif tipo_bien == "automovil":
                query = select(automoviles).where(automoviles.c.id == bien_id)
                bien_data = conn.execute(query).first()
                if bien_data:
                     
                    descripcion = f"{bien_data.marca} {bien_data.modelo} {bien_data.color or ''} {bien_data.placa or ''}".strip()
                    seriales = f"Motor: {bien_data.num_serial_motor or ''} Carroceria: {bien_data.num_serial_carroceria or ''}"
                    
                    item = BienBM7Item(
                        numero_catalogo="VEHÍCULO", 
                        cantidad=1,
                        motivo=get_motivo_descripcion(bien_data.concepto_incorporacion),
                        codigo_bien=str(bien_data.num_bien),
                        nombre_descripcion=descripcion,
                        orden_compra=str(bien_data.orden_pago) if bien_data.orden_pago else "S/N",
                        fecha_registro=bien_data.fecha_ingreso or "",
                        seriales=seriales,
                        valor_unitario=bien_data.valor_inicial or Decimal("0.01"),
                        estado=bien_data.estatus or "OPERATIVO"
                    )
                    items_bm7.append(item)
                    total_monto += item.valor_unitario

        except Exception as e:
            print(f"Error procesando bien {tipo_bien} {bien_id}: {str(e)}")
            continue

    fecha_hoy = datetime.now()
    fecha_formato = f"{fecha_hoy.day} DE {MESES[fecha_hoy.month-1].upper()} DEL {fecha_hoy.year}"

    query_dept = select(departamentos.c.ubicacion, departamentos.c.director).where(departamentos.c.nombre == request.departamento)
    try:
        dept_info = conn.execute(query_dept).first()
        if dept_info:
            ubicacion = dept_info.ubicacion if dept_info.ubicacion else "EDIFICIO SEDE ADMINISTRATIVA"
            director = dept_info.director if dept_info.director else "ESP. JOSÉ JESÚS VÁSQUEZ V."
        else:
            ubicacion = "EDIFICIO SEDE ADMINISTRATIVA"
            director = "ESP. JOSÉ JESÚS VÁSQUEZ V."
    except Exception:
        ubicacion = "EDIFICIO SEDE ADMINISTRATIVA"
        director = "ESP. JOSÉ JESÚS VÁSQUEZ V."
    
    return ReporteBM7Response(
        numero_acta=historial.numero_reporte,
        fecha_actual=fecha_formato,
        suscrito_nombre=director.upper(),
        suscrito_cargo="JEFE (A) DE LA UNIDAD DE TRABAJO",

        unidad_trabajo_nombre="DIRECCIÓN DE ADMINISTRACIÓN",
        departamento=request.departamento,
        unidad_trabajo_ubicacion=ubicacion,
        testigo1_nombre="TESTIGO 1",
        testigo2_nombre="TESTIGO 2",
        bienes=items_bm7,
        total_cantidad=len(items_bm7),
        total_monto=total_monto
    )

@reporte_bm7_router.get("/reportes/bm7/bienes-disponibles", tags=["Reportes"], response_model=List[BienDisponibleBM7])
def listar_bienes_disponibles_bm7():
    
    try:
        conn.rollback()
    except:
        pass
        
    try:

        from models.reporte_historial import reportes_historial, reportes_detalles
        from schemas.reporte_bm7 import BienDisponibleBM7
        
        query_usados = select(
            reportes_detalles.c.tipo_bien,
            reportes_detalles.c.bien_id
        ).select_from(
            reportes_detalles.join(
                reportes_historial,
                reportes_detalles.c.reporte_id == reportes_historial.c.id
            )
        ).where(
            reportes_historial.c.tipo_reporte == ReporteTipoEnum.BM7.value
        )
        
        resultados_usados = conn.execute(query_usados).fetchall()

        usados_set = {(row.tipo_bien, row.bien_id) for row in resultados_usados}
        
        bienes_disponibles = []

        query_muebles = select(muebles) 
        res_muebles = conn.execute(query_muebles).fetchall()
        
        for m in res_muebles:
            if ("mueble", m.id) not in usados_set:
                bienes_disponibles.append(BienDisponibleBM7(
                    id=m.id,
                    tipo_bien="mueble",
                    codigo_bien=str(m.num_bien),
                    descripcion=m.descripcion or "",
                    fecha_ingreso=m.fecha_ingreso or "",
                    marca=m.marca,
                    modelo=m.modelo
                ))

        query_autos = select(automoviles)
        res_autos = conn.execute(query_autos).fetchall()
        
        for a in res_autos:
            if ("automovil", a.id) not in usados_set:
                desc = f"Vehículo {a.marca} {a.modelo} Placa: {a.placa or 'S/P'}"
                bienes_disponibles.append(BienDisponibleBM7(
                    id=a.id,
                    tipo_bien="automovil",
                    codigo_bien=str(a.num_bien),
                    descripcion=desc,
                    fecha_ingreso=a.fecha_ingreso or "",
                    marca=a.marca,
                    modelo=a.modelo
                ))
        
        return bienes_disponibles
        
    except Exception as e:
        print(f"Error obteniendo bienes disponibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@reporte_bm7_router.get("/reportes/bm7/buscar/{numero_acta}", tags=["Reportes"], response_model=ReporteBM7Response)
def buscar_reporte_bm7(numero_acta: str):
    
    try:
        
        from models.reporte_historial import reportes_historial, reportes_detalles
        
        query_hist = select(reportes_historial).where(
            (reportes_historial.c.numero_reporte == numero_acta) &
            (reportes_historial.c.tipo_reporte == ReporteTipoEnum.BM7.value)
        )
        historial = conn.execute(query_hist).first()
        
        if not historial:
             raise HTTPException(status_code=404, detail="Reporte no encontrado")

        query_detalles = select(reportes_detalles).where(
            reportes_detalles.c.reporte_id == historial.id
        )
        detalles = conn.execute(query_detalles).fetchall()

        items_bm7 = []
        total_monto = Decimal("0.00")
        
        for det in detalles:
            bien_data = None
            tipo_bien = det.tipo_bien
            bien_id = det.bien_id

            if tipo_bien == "mueble":
                query_m = select(muebles).where(muebles.c.id == bien_id)
                bien_data = conn.execute(query_m).first()
                if bien_data:
                    item = BienBM7Item(
                        numero_catalogo=bien_data.num_catalogo or "S/C",
                        cantidad=1,
                        motivo=get_motivo_descripcion(bien_data.concepto_incorporacion),
                        codigo_bien=str(bien_data.num_bien),
                        nombre_descripcion=f"{bien_data.descripcion} - {bien_data.marca or ''} {bien_data.modelo or ''}".strip(),
                        orden_compra=str(bien_data.orden_pago) if bien_data.orden_pago else "S/N",
                        fecha_registro=bien_data.fecha_ingreso or "",
                        seriales=bien_data.serial or "S/N",
                        valor_unitario=bien_data.valor_inicial or Decimal("0.01"),
                        estado=bien_data.estado or "BUENO"
                    )
                    items_bm7.append(item)
                    total_monto += item.valor_unitario
                    
            elif tipo_bien == "automovil":
                query_a = select(automoviles).where(automoviles.c.id == bien_id)
                bien_data = conn.execute(query_a).first()
                if bien_data:
                    descripcion = f"{bien_data.marca} {bien_data.modelo} {bien_data.color or ''} {bien_data.placa or ''}".strip()
                    seriales = f"Motor: {bien_data.num_serial_motor or ''} Carroceria: {bien_data.num_serial_carroceria or ''}"
                    item = BienBM7Item(
                        numero_catalogo="VEHÍCULO",
                        cantidad=1,
                        motivo=get_motivo_descripcion(bien_data.concepto_incorporacion),
                        codigo_bien=str(bien_data.num_bien),
                        nombre_descripcion=descripcion,
                        orden_compra=str(bien_data.orden_pago) if bien_data.orden_pago else "S/N",
                        fecha_registro=bien_data.fecha_ingreso or "",
                        seriales=seriales,
                        valor_unitario=bien_data.valor_inicial or Decimal("0.01"),
                        estado=bien_data.estatus or "OPERATIVO"
                    )
                    items_bm7.append(item)
                    total_monto += item.valor_unitario

        fecha_gen = historial.fecha_generacion
        fecha_formato = f"{fecha_gen.day} DE {MESES[fecha_gen.month-1].upper()} DEL {fecha_gen.year}"

        query_dept = select(departamentos.c.ubicacion, departamentos.c.director).where(departamentos.c.nombre == historial.departamento)
        try:
            dept_info = conn.execute(query_dept).first()
            if dept_info:
                ubicacion = dept_info.ubicacion if dept_info.ubicacion else "EDIFICIO SEDE ADMINISTRATIVA"
                director = dept_info.director if dept_info.director else "ESP. JOSÉ JESÚS VÁSQUEZ V."
            else:
                ubicacion = "EDIFICIO SEDE ADMINISTRATIVA"
                director = "ESP. JOSÉ JESÚS VÁSQUEZ V."
        except Exception:
            ubicacion = "EDIFICIO SEDE ADMINISTRATIVA"
            director = "ESP. JOSÉ JESÚS VÁSQUEZ V."
            
        return ReporteBM7Response(
            numero_acta=historial.numero_reporte,
            
            fecha_actual=fecha_formato,
            suscrito_nombre=director.upper(), 
            suscrito_cargo="JEFE (A) DE LA UNIDAD DE TRABAJO",

            unidad_trabajo_nombre="DIRECCIÓN DE ADMINISTRACIÓN", 
            departamento=historial.departamento,
            unidad_trabajo_ubicacion=ubicacion,
            testigo1_nombre="TESTIGO 1",
            testigo2_nombre="TESTIGO 2",
            bienes=items_bm7,
            total_cantidad=len(items_bm7),
            total_monto=total_monto
        )
    except Exception as e:
        print(f"Error buscando reporte BM7: {e}")
        raise HTTPException(status_code=500, detail=str(e))
