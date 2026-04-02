from fastapi import APIRouter, HTTPException
from config.db import conn
from models.reporte_historial import reportes_historial, reportes_detalles
from models.configuracion import configuraciones
from schemas.reporte_historial import ReporteGenerarRequest, ReporteHistorialOut, ReporteDetalleOut
from sqlalchemy import select, desc
from datetime import datetime
from typing import List

reporte_historial_router = APIRouter()

def obtener_siguiente_correlativo(tipo_reporte: str) -> str:
    
    clave_config = f"correlativo_{tipo_reporte.lower()}"
    anio_actual = datetime.now().year

    query = select(configuraciones).where(configuraciones.c.clave == clave_config)
    config = conn.execute(query).first()
    
    if config:
        
        try:
            ultimo_numero = int(config.valor)
        except:
            ultimo_numero = 0
        nuevo_numero = ultimo_numero + 1

        conn.execute(
            configuraciones.update()
            .where(configuraciones.c.clave == clave_config)
            .values(valor=str(nuevo_numero))
        )
    else:
        
        nuevo_numero = 1
        conn.execute(
            configuraciones.insert().values(
                clave=clave_config,
                valor="1",
                grupo="CORRELATIVOS",
                descripcion=f"Secuencia actual del reporte {tipo_reporte}"
            )
        )
    
    return f"{nuevo_numero:03d}-{anio_actual}"

@reporte_historial_router.post("/reportes/historial/generar", tags=["Reportes Historial"], response_model=ReporteHistorialOut)
def generar_reporte_historial(solicitud: ReporteGenerarRequest):
    
    try:
        conn.commit() 
    except:
        pass
        
    try:
        
        numero_reporte = obtener_siguiente_correlativo(solicitud.tipo_reporte.value)

        query_historial = reportes_historial.insert().values(
            numero_reporte=numero_reporte,
            tipo_reporte=solicitud.tipo_reporte.value,
            generado_por=solicitud.generado_por,
            observaciones=solicitud.observaciones,
            departamento=solicitud.departamento,
            fecha_generacion=datetime.now()
        )
        result_historial = conn.execute(query_historial)
        reporte_id = result_historial.lastrowid

        if solicitud.bienes:
            
            values_list = []
            for bien in solicitud.bienes:
                values_list.append({
                    "reporte_id": reporte_id,
                    "tipo_bien": bien.tipo_bien,
                    "bien_id": bien.bien_id,
                    "codigo_bien": bien.codigo_bien
                })
            
            conn.execute(reportes_detalles.insert(), values_list)
            
        conn.commit()

        query_get = select(reportes_historial).where(reportes_historial.c.id == reporte_id)
        reporte_creado = conn.execute(query_get).first()
        
        return ReporteHistorialOut(**dict(reporte_creado._mapping))
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error generando historial de reporte: {str(e)}")

@reporte_historial_router.get("/reportes/historial", tags=["Reportes Historial"], response_model=List[ReporteHistorialOut])
def listar_historial_reportes():
    
    query = select(reportes_historial).order_by(desc(reportes_historial.c.fecha_generacion))
    resultados = conn.execute(query).fetchall()
    return [ReporteHistorialOut(**dict(row._mapping)) for row in resultados]

@reporte_historial_router.get("/reportes/historial/{reporte_id}/detalles", tags=["Reportes Historial"], response_model=List[ReporteDetalleOut])
def obtener_detalles_reporte(reporte_id: int):
    
    query = select(reportes_detalles).where(reportes_detalles.c.reporte_id == reporte_id)
    resultados = conn.execute(query).fetchall()
    return [ReporteDetalleOut(**dict(row._mapping)) for row in resultados]
