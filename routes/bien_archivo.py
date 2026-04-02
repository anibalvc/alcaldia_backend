from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os

from config.db import conn
from models.bien_archivo import bien_archivos
from schemas.bien_archivo import (
    BienArchivoResponse, BienArchivosData, BienArchivoCreate, BienArchivoUpdate,
    BienArchivoDelete, UploadResponse, ErrorResponse, SuccessResponse, ArchivosStats
)
from utils.file_handler import FileHandler
from config.storage import StorageConfig
from utils.logger import AuditLogger

archivo_router = APIRouter()
file_handler = FileHandler()
audit_logger = AuditLogger()

@archivo_router.post("/bienes/{bien_id}/archivos/{bien_tipo}/upload",
                    tags=["Archivos"],
                    response_model=UploadResponse)
async def upload_archivos(
    bien_id: int,
    bien_tipo: str,
    files: List[UploadFile] = File(...),
    numero_bien: str = Form(...),
    descripcion: Optional[str] = Form(None),
    subido_por: str = Form(...),
    request: Request = None
):

    try:
        
        if bien_tipo not in ['mueble', 'inmueble', 'automovil']:
            raise HTTPException(status_code=400, detail="bien_tipo debe ser: mueble, inmueble o automovil")

        file_handler.validate_multiple_files(files)

        archivos_subidos = []

        for file in files:
            try:
                
                file_data = file_handler.save_file(file, bien_id, numero_bien, bien_tipo, subido_por)

                insert_query = bien_archivos.insert().values(
                    bien_id=bien_id,
                    numero_bien=numero_bien,
                    bien_tipo=bien_tipo,
                    nombre_archivo=file_data['nombre_archivo'],
                    nombre_original=file_data['nombre_original'],
                    tipo_archivo=file_data['tipo_archivo'],
                    extension=file_data['extension'],
                    tamaño_bytes=file_data['tamaño_bytes'],
                    ruta_archivo=file_data['ruta_archivo'],
                    url_acceso=file_data['url_acceso'],
                    thumbnail_path=file_data['thumbnail_path'],
                    descripcion=descripcion,
                    checksum_md5=file_data['checksum_md5'],
                    subido_por=subido_por,
                    fecha_subida=datetime.now()
                )

                result = conn.execute(insert_query)
                archivo_id = result.lastrowid

                select_query = bien_archivos.select().where(bien_archivos.c.id == archivo_id)
                archivo_record = conn.execute(select_query).fetchone()

                if archivo_record:
                    archivo_dict = dict(archivo_record._asdict())
                    archivos_subidos.append(BienArchivoResponse(**archivo_dict))

                audit_logger.log_create(
                    usuario=subido_por,
                    modulo="ARCHIVO",
                    registro_id=archivo_id,
                    datos=archivo_dict,
                    descripcion=f"Archivo subido: {file_data['nombre_original']} para {bien_tipo} {numero_bien}",
                    request=request
                )

            except Exception as e:
                
                if 'file_data' in locals():
                    file_handler.delete_file(file_data['ruta_archivo'])
                raise HTTPException(status_code=500, detail=f"Error procesando {file.filename}: {str(e)}")

        conn.commit()

        return UploadResponse(
            success=True,
            message=f"{len(archivos_subidos)} archivo(s) subido(s) exitosamente",
            archivos_subidos=archivos_subidos
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@archivo_router.get("/bienes/{bien_id}/archivos/{bien_tipo}",
                   tags=["Archivos"],
                   response_model=BienArchivosData)
def get_archivos_bien_por_id(
    bien_id: int,
    bien_tipo: str,
    tipo_archivo: Optional[str] = Query(None, description="imagen o documento"),
    activo: bool = Query(True, description="Filtrar por archivos activos")
):

    try:
        conn.rollback()  

        query = bien_archivos.select().where(
            and_(
                bien_archivos.c.bien_id == bien_id,
                bien_archivos.c.bien_tipo == bien_tipo,
                bien_archivos.c.activo == activo
            )
        )

        if tipo_archivo:
            if tipo_archivo not in ['imagen', 'documento']:
                raise HTTPException(status_code=400, detail="tipo_archivo debe ser: imagen o documento")
            query = query.where(bien_archivos.c.tipo_archivo == tipo_archivo)

        query = query.order_by(bien_archivos.c.tipo_archivo.asc(), bien_archivos.c.fecha_subida.desc())

        result = conn.execute(query)
        archivos = result.fetchall()

        archivos_list = []
        for archivo in archivos:
            archivo_dict = dict(archivo._asdict())
            archivos_list.append(BienArchivoResponse(**archivo_dict))

        return BienArchivosData(data=archivos_list, total=len(archivos_list))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando archivos: {str(e)}")

@archivo_router.get("/bienes/numero/{numero_bien}/archivos/{bien_tipo}",
                   tags=["Archivos"],
                   response_model=BienArchivosData)
def get_archivos_bien_por_numero(
    numero_bien: str,
    bien_tipo: str,
    tipo_archivo: Optional[str] = Query(None, description="imagen o documento"),
    activo: bool = Query(True, description="Filtrar por archivos activos")
):

    try:
        conn.rollback()

        query = bien_archivos.select().where(
            and_(
                bien_archivos.c.numero_bien == numero_bien,
                bien_archivos.c.bien_tipo == bien_tipo,
                bien_archivos.c.activo == activo
            )
        )

        if tipo_archivo:
            if tipo_archivo not in ['imagen', 'documento']:
                raise HTTPException(status_code=400, detail="tipo_archivo debe ser: imagen o documento")
            query = query.where(bien_archivos.c.tipo_archivo == tipo_archivo)

        query = query.order_by(bien_archivos.c.tipo_archivo.asc(), bien_archivos.c.fecha_subida.desc())

        result = conn.execute(query)
        archivos = result.fetchall()

        archivos_list = []
        for archivo in archivos:
            archivo_dict = dict(archivo._asdict())
            archivos_list.append(BienArchivoResponse(**archivo_dict))

        return BienArchivosData(data=archivos_list, total=len(archivos_list))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando archivos: {str(e)}")

@archivo_router.get("/archivos/{archivo_id}/download",
                   tags=["Archivos"])
async def download_archivo(archivo_id: int, request: Request = None):

    try:
        
        query = bien_archivos.select().where(
            and_(
                bien_archivos.c.id == archivo_id,
                bien_archivos.c.activo == True
            )
        )

        result = conn.execute(query)
        archivo = result.fetchone()

        if not archivo:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        archivo_dict = dict(archivo._asdict())

        if not os.path.exists(archivo_dict['ruta_archivo']):
            raise HTTPException(status_code=404, detail="Archivo físico no encontrado")

        if not StorageConfig.is_safe_path(archivo_dict['ruta_archivo']):
            raise HTTPException(status_code=403, detail="Acceso denegado")

        if request:
            audit_logger.log_action(
                usuario="sistema",  
                accion="DOWNLOAD",
                modulo="ARCHIVO",
                registro_id=archivo_id,
                descripcion=f"Descarga de archivo: {archivo_dict['nombre_original']}",
                request=request
            )

        content_type = StorageConfig.get_content_type(archivo_dict['extension'])

        return FileResponse(
            path=archivo_dict['ruta_archivo'],
            filename=archivo_dict['nombre_original'],
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={archivo_dict['nombre_original']}",
                "Cache-Control": "private, max-age=3600"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@archivo_router.put("/archivos/{archivo_id}",
                   tags=["Archivos"],
                   response_model=SuccessResponse)
def update_archivo_descripcion(
    archivo_id: int,
    update_data: BienArchivoUpdate,
    request: Request = None
):

    try:
        
        select_query = bien_archivos.select().where(
            and_(
                bien_archivos.c.id == archivo_id,
                bien_archivos.c.activo == True
            )
        )

        result = conn.execute(select_query)
        archivo = result.fetchone()

        if not archivo:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        update_query = bien_archivos.update().where(
            bien_archivos.c.id == archivo_id
        ).values(
            descripcion=update_data.descripcion,
            modificado_por=update_data.modificado_por,
            fecha_modificacion=datetime.now()
        )

        conn.execute(update_query)
        conn.commit()

        audit_logger.log_update(
            usuario=update_data.modificado_por,
            modulo="ARCHIVO",
            registro_id=archivo_id,
            datos_anteriores=dict(archivo._asdict()),
            datos_nuevos={"descripcion": update_data.descripcion},
            descripcion=f"Descripción actualizada para archivo ID: {archivo_id}",
            request=request
        )

        return SuccessResponse(
            message="Descripción del archivo actualizada exitosamente"
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando archivo: {str(e)}")

@archivo_router.delete("/archivos/{archivo_id}",
                      tags=["Archivos"],
                      response_model=SuccessResponse)
def delete_archivo(
    archivo_id: int,
    delete_data: BienArchivoDelete,
    request: Request = None
):

    try:
        
        select_query = bien_archivos.select().where(
            and_(
                bien_archivos.c.id == archivo_id,
                bien_archivos.c.activo == True
            )
        )

        result = conn.execute(select_query)
        archivo = result.fetchone()

        if not archivo:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        archivo_dict = dict(archivo._asdict())

        update_query = bien_archivos.update().where(
            bien_archivos.c.id == archivo_id
        ).values(
            activo=False,
            modificado_por=delete_data.eliminado_por,
            fecha_modificacion=datetime.now()
        )

        conn.execute(update_query)
        conn.commit()

        audit_logger.log_delete(
            usuario=delete_data.eliminado_por,
            modulo="ARCHIVO",
            registro_id=archivo_id,
            datos=archivo_dict,
            descripcion=f"Archivo eliminado: {archivo_dict['nombre_original']} (ID: {archivo_id})",
            request=request
        )

        return SuccessResponse(
            message="Archivo eliminado exitosamente"
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando archivo: {str(e)}")

@archivo_router.get("/bienes/{bien_id}/archivos/{bien_tipo}/stats",
                   tags=["Archivos"],
                   response_model=ArchivosStats)
def get_archivos_stats(bien_id: int, bien_tipo: str):

    try:
        conn.rollback()

        from sqlalchemy import func, case

        from sqlalchemy import text
        query = conn.execute(text(f))

        result = query.fetchone()

        if result:
            return ArchivosStats(
                total_archivos=result[0] or 0,
                total_imagenes=result[1] or 0,
                total_documentos=result[2] or 0,
                tamaño_total_mb=float(result[3] or 0),
                ultimo_archivo=result[4]
            )
        else:
            return ArchivosStats(
                total_archivos=0,
                total_imagenes=0,
                total_documentos=0,
                tamaño_total_mb=0.0
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@archivo_router.get("/bienes/{bien_id}/archivos/{bien_tipo}/count",
                   tags=["Archivos"])
def get_archivos_count(bien_id: int, bien_tipo: str):

    try:
        conn.rollback()

        from sqlalchemy import text
        query = conn.execute(text(f))

        result = query.fetchone()
        total = result[0] if result else 0

        return {"total": total}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo conteo: {str(e)}")
