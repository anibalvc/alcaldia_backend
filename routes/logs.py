from typing import List, Optional
from fastapi import APIRouter, Query
from config.db import conn
from models.logs import logs
from schemas.logs import LogData, Log
from datetime import datetime

logs_router = APIRouter()

@logs_router.get("/logs", tags=["Logs"], response_model=LogData)
def get_logs(
    usuario: Optional[str] = Query(None, description="Filtrar por usuario"),
    accion: Optional[str] = Query(None, description="Filtrar por acción (CREATE, UPDATE, DELETE, DESINCORPORAR)"),
    modulo: Optional[str] = Query(None, description="Filtrar por módulo (MUEBLE, INMUEBLE, AUTOMOVIL, SOLICITUD)"),
    registro_id: Optional[int] = Query(None, description="Filtrar por ID del registro afectado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (formato: YYYY-MM-DD HH:MM:SS)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (formato: YYYY-MM-DD HH:MM:SS)"),
    limit: Optional[int] = Query(100, description="Límite de registros a devolver", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="Número de registros a saltar", ge=0)
):

    try:
        
        conn.rollback()
    except:
        pass

    conn.execution_options(stream_results=True)
    
    try:
        
        query = logs.select()

        if usuario:
            query = query.where(logs.c.usuario.ilike(f"%{usuario}%"))
            
        if accion:
            query = query.where(logs.c.accion == accion.upper())
            
        if modulo:
            query = query.where(logs.c.modulo == modulo.upper())
            
        if registro_id:
            query = query.where(logs.c.registro_id == registro_id)
            
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
                query = query.where(logs.c.fecha_hora >= fecha_desde_dt)
            except ValueError:
                
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.where(logs.c.fecha_hora >= fecha_desde_dt)
                
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
                query = query.where(logs.c.fecha_hora <= fecha_hasta_dt)
            except ValueError:
                
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                query = query.where(logs.c.fecha_hora <= fecha_hasta_dt)

        query = query.order_by(logs.c.fecha_hora.desc())

        query = query.offset(offset).limit(limit)

        result = conn.execution_options(stream_results=True).execute(query).fetchall()
        
        return {"data": result}
        
    except Exception as e:
        
        print(f"Error en consulta de logs: {str(e)}")
        try:
            basic_query = logs.select().order_by(logs.c.fecha_hora.desc()).limit(limit).offset(offset)
            result = conn.execution_options(stream_results=True).execute(basic_query).fetchall()
            return {"data": result}
        except Exception as fallback_error:
            print(f"Error en consulta básica de logs: {str(fallback_error)}")
            return {"data": []}

@logs_router.get("/logs/stats", tags=["Logs"])
def get_logs_stats():
    
    try:
        
        conn.rollback()
    except:
        pass

    conn.execution_options(stream_results=True)
    
    try:
        
        stats_accion = conn.execution_options(stream_results=True).execute().fetchall()

        stats_modulo = conn.execution_options(stream_results=True).execute().fetchall()

        stats_usuario = conn.execution_options(stream_results=True).execute().fetchall()

        logs_recientes = conn.execution_options(stream_results=True).execute().fetchall()

        total_logs = conn.execution_options(stream_results=True).execute("SELECT COUNT(*) as total FROM logs").fetchone()
        
        return {
            "total_logs": total_logs.total if total_logs else 0,
            "por_accion": [{"accion": row.accion, "total": row.total} for row in stats_accion],
            "por_modulo": [{"modulo": row.modulo, "total": row.total} for row in stats_modulo],
            "por_usuario": [{"usuario": row.usuario, "total": row.total} for row in stats_usuario],
            "ultimos_7_dias": [{"fecha": str(row.fecha), "total": row.total} for row in logs_recientes]
        }
        
    except Exception as e:
        return {
            "error": f"Error al obtener estadísticas: {str(e)}",
            "total_logs": 0,
            "por_accion": [],
            "por_modulo": [],
            "por_usuario": [],
            "ultimos_7_dias": []
        }

@logs_router.get("/logs/{log_id}", tags=["Logs"], response_model=Log)
def get_log_by_id(log_id: int):
    
    try:
        
        conn.rollback()
    except:
        pass

    conn.execution_options(stream_results=True)
    
    try:
        result = conn.execution_options(stream_results=True).execute(logs.select().where(logs.c.id == log_id)).first()
        
        if result is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Log no encontrado")
            
        return result
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error al obtener el log: {str(e)}")
