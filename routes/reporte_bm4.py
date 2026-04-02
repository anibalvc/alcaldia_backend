from fastapi import APIRouter, Query, HTTPException
from config.db import conn
from models.mueble import muebles, mueblesDeleted
from models.inmueble import inmuebles, inmueblesDeleted
from models.automovil import automoviles, automovilesDeleted
from schemas.reporte_bm4 import (
    ReporteBM4Response,
    DepartamentoBM4Item,
    GenerarReporteBM4Request
)
from sqlalchemy import and_, or_, func, select
from sqlalchemy.sql import case
from decimal import Decimal
from datetime import datetime
from typing import Dict, List
import calendar

reporte_bm4 = APIRouter()

MESES_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

def obtener_tabla_por_tipo(tipo_bien: str):
    
    if tipo_bien.lower() == "muebles":
        return muebles, mueblesDeleted
    elif tipo_bien.lower() == "inmuebles":
        return inmuebles, inmueblesDeleted
    elif tipo_bien.lower() == "automoviles":
        return automoviles, automovilesDeleted
    else:
        raise HTTPException(status_code=400, detail="Tipo de bien no válido")

def parsear_fecha(fecha_str: str) -> tuple:
    
    if not fecha_str or fecha_str.strip() == "":
        return (0, 0, 0)

    try:
        
        partes = fecha_str.strip().split("/")
        if len(partes) == 3:
            return (int(partes[0]), int(partes[1]), int(partes[2]))
    except:
        pass

    return (0, 0, 0)

def fecha_en_periodo(fecha_str: str, mes: int, anio: int) -> bool:
    
    dia, mes_fecha, anio_fecha = parsear_fecha(fecha_str)
    if mes_fecha == 0:
        return False
    return mes_fecha == mes and anio_fecha == anio

def fecha_antes_de_periodo(fecha_str: str, mes: int, anio: int) -> bool:
    
    dia, mes_fecha, anio_fecha = parsear_fecha(fecha_str)
    if mes_fecha == 0:
        return False

    if anio_fecha < anio:
        return True
    if anio_fecha > anio:
        return False

    return mes_fecha < mes

def safe_decimal_conversion(valor) -> Decimal:
    
    if valor is None or valor == "":
        return Decimal("0.00")
    
    try:
        
        return Decimal(str(valor))
    except:
        
        try:
            
            valor_str = str(valor).strip().replace(",", ".")
            
            valor_limpio = "".join(c for c in valor_str if c.isdigit() or c in ".-")
            if valor_limpio:
                return Decimal(valor_limpio)
        except:
            pass
    
    return Decimal("0.00")

@reporte_bm4.get(
    "/reportes/bm4",
    tags=["Reportes"],
    response_model=ReporteBM4Response,
    summary="Generar Reporte BM-4",
    description="Genera el reporte BM-4 (Resumen de la Cuenta de Bienes) para un mes y año específicos"
)
def generar_reporte_bm4(
    mes: int = Query(..., ge=1, le=12, description="Mes del reporte (1-12)"),
    anio: int = Query(..., ge=2020, le=2100, description="Año del reporte"),
    tipo_bien: str = Query("todos", description="Tipo de bien (muebles, inmuebles, automoviles, todos)")
):

    try:
        
        conn.commit()
    except:
        pass

    if tipo_bien.lower() == "todos":
        tipos_a_procesar = ["muebles", "automoviles"]
    else:
        tipos_a_procesar = [tipo_bien]

    departamentos_data = {}

    for tipo in tipos_a_procesar:
        
        tabla_activos, tabla_eliminados = obtener_tabla_por_tipo(tipo)

        query_departamentos = select(tabla_activos.c.departamento).distinct()
        departamentos_result = conn.execute(query_departamentos).fetchall()
        departamentos = [row[0] for row in departamentos_result if row[0]]

        query_departamentos_del = select(tabla_eliminados.c.departamento).distinct()
        departamentos_del_result = conn.execute(query_departamentos_del).fetchall()
        departamentos_del = [row[0] for row in departamentos_del_result if row[0]]

        todos_departamentos = list(set(departamentos + departamentos_del))

        for departamento in todos_departamentos:
            
            if departamento not in departamentos_data:
                departamentos_data[departamento] = {
                    "existencia_anterior": Decimal("0.00"),
                    "inc": Decimal("0.00"),
                    "desinc": Decimal("0.00")
                }

            query_bienes_activos = select(
                tabla_activos.c.fecha_ingreso,
                tabla_activos.c.valor_actual
            ).where(
                tabla_activos.c.departamento == departamento
            )

            bienes_activos = conn.execute(query_bienes_activos).fetchall()
            
            for bien in bienes_activos:
                fecha_ingreso = bien[0]
                monto = safe_decimal_conversion(bien[1])
                if fecha_antes_de_periodo(fecha_ingreso, mes, anio):
                    departamentos_data[departamento]["existencia_anterior"] += monto

            for bien in bienes_activos:
                fecha_ingreso = bien[0]
                monto = safe_decimal_conversion(bien[1])
                if fecha_en_periodo(fecha_ingreso, mes, anio):
                    departamentos_data[departamento]["inc"] += monto

            query_bienes_eliminados = select(
                tabla_eliminados.c.fecha_ingreso,
                tabla_eliminados.c.valor_actual
            ).where(
                tabla_eliminados.c.departamento == departamento
            )

            bienes_eliminados = conn.execute(query_bienes_eliminados).fetchall()
            
            for bien in bienes_eliminados:
                fecha_ingreso = bien[0]
                monto = safe_decimal_conversion(bien[1])
                if fecha_en_periodo(fecha_ingreso, mes, anio):
                    departamentos_data[departamento]["desinc"] += monto

    items_bm4: List[DepartamentoBM4Item] = []
    
    total_general_existencia_anterior = Decimal("0.00")
    total_general_inc = Decimal("0.00")
    total_general_desinc = Decimal("0.00")
    total_general_existencia_actual = Decimal("0.00")

    for departamento in sorted(departamentos_data.keys()):
        data = departamentos_data[departamento]
        
        existencia_anterior = data["existencia_anterior"]
        inc = data["inc"]
        desinc = data["desinc"]
        existencia_actual = existencia_anterior + inc - desinc

        if existencia_anterior > 0 or inc > 0 or desinc > 0 or existencia_actual > 0:
            items_bm4.append(DepartamentoBM4Item(
                ubicacion=departamento[:30],  
                descripcion=departamento,  
                existencia_anterior=existencia_anterior,
                inc=inc,
                desinc=desinc,
                existencia_actual=existencia_actual,
                observaciones="*"  
            ))

            total_general_existencia_anterior += existencia_anterior
            total_general_inc += inc
            total_general_desinc += desinc
            total_general_existencia_actual += existencia_actual

    mes_nombre = MESES_ES.get(mes, "").upper()
    periodo = f"{mes_nombre} {anio}"

    response = ReporteBM4Response(
        titulo="BM-4 RESUMEN DE LA CUENTA DE BIENES MUEBLES",
        periodo=periodo,
        mes=mes,
        anio=anio,
        departamentos=items_bm4,
        total_existencia_anterior=total_general_existencia_anterior,
        total_inc=total_general_inc,
        total_desinc=total_general_desinc,
        total_existencia_actual=total_general_existencia_actual,
        responsable_nombre="JESÚS BELTRÁN MARCANO RAMÍREZ",
        responsable_cargo="JEFE DE LA OFICINA DE BIENES REGIONALES",
        decreto_numero="N° 0020 de fecha 16/06/2025",
        gaceta_numero="N° E-6 383 de fecha 16/06/2025"
    )

    return response
