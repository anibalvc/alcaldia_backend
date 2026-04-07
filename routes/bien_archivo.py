from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
import io

from config.db import conn
from models.bien_archivo import bien_archivos
from schemas.bien_archivo import (
    BienArchivoResponse, BienArchivosData, BienArchivoCreate, BienArchivoUpdate,
    BienArchivoDelete, UploadResponse, ErrorResponse, SuccessResponse, ArchivosStats
)
from utils.s3_file_handler import s3_file_handler
from utils.file_handler import FileHandler
from config.storage import StorageConfig
from config.s3_storage import s3_config
from utils.logger import AuditLogger
import logging

logger = logging.getLogger(__name__)

archivo_router = APIRouter()

USE_S3 = os.getenv('USE_S3_STORAGE', 'true').lower() == 'true'
file_handler_local = FileHandler() if not USE_S3 else None
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

        if USE_S3:
            s3_file_handler.validate_multiple_files(files)
        else:
            file_handler_local.validate_multiple_files(files)

        archivos_subidos = []

        for file in files:
            try:
                
                if USE_S3:
                    file_data = await s3_file_handler.save_file(file, bien_id, numero_bien, bien_tipo, subido_por)
                    storage_type = "s3"
                else:
                    file_data = file_handler_local.save_file(file, bien_id, numero_bien, bien_tipo, subido_por)
                    storage_type = "local"

                insert_data = {
                    'bien_id': bien_id,
                    'numero_bien': numero_bien,
                    'bien_tipo': bien_tipo,
                    'nombre_archivo': file_data['nombre_archivo'],
                    'nombre_original': file_data['nombre_original'],
                    'tipo_archivo': file_data['tipo_archivo'],
                    'extension': file_data['extension'],
                    'tamaño_bytes': file_data['tamaño_bytes'],
                    'ruta_archivo': file_data['ruta_archivo'],
                    'url_acceso': file_data['url_acceso'],
                    'thumbnail_path': file_data['thumbnail_path'],
                    'descripcion': descripcion,
                    'checksum_md5': file_data['checksum_md5'],
                    'subido_por': subido_por,
                    'fecha_subida': datetime.now(),
                    'storage_type': storage_type
                }

                if USE_S3:
                    insert_data.update({
                        's3_bucket': file_data.get('s3_bucket'),
                        's3_object_key': file_data.get('s3_object_key')
                    })

                insert_query = bien_archivos.insert().values(**insert_data)
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
                    descripcion=f"Archivo subido ({storage_type}): {file_data['nombre_original']} para {bien_tipo} {numero_bien}",
                    request=request
                )

                logger.info(f"✅ Archivo procesado ({storage_type}): {file_data['nombre_original']}")

            except Exception as e:
                
                if 'file_data' in locals():
                    if USE_S3 and 'ruta_archivo' in file_data:
                        await s3_file_handler.delete_file(file_data['ruta_archivo'])
                    elif not USE_S3 and 'ruta_archivo' in file_data:
                        file_handler_local.delete_file(file_data['ruta_archivo'])

                raise HTTPException(status_code=500, detail=f"Error procesando {file.filename}: {str(e)}")

        conn.commit()

        storage_info = "S3/MinIO" if USE_S3 else "local"
        return UploadResponse(
            success=True,
            message=f"{len(archivos_subidos)} archivo(s) subido(s) exitosamente a {storage_info}",
            archivos_subidos=archivos_subidos
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error interno del servidor: {e}")
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
        storage_type = archivo_dict.get('storage_type', 'local')

        if request:
            audit_logger.log_action(
                usuario="sistema",  
                accion="DOWNLOAD",
                modulo="ARCHIVO",
                registro_id=archivo_id,
                descripcion=f"Descarga de archivo ({storage_type}): {archivo_dict['nombre_original']}",
                request=request
            )

        if storage_type == 's3':
            object_key = archivo_dict.get('s3_object_key') or archivo_dict['ruta_archivo']
            file_content = await s3_file_handler.download_file(object_key)
            content_type = s3_config.get_content_type(archivo_dict['extension'])

            return StreamingResponse(
                io.BytesIO(file_content),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={archivo_dict['nombre_original']}",
                    "Cache-Control": "private, max-age=3600"
                }
            )
        else:
            file_path = archivo_dict['ruta_archivo']
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Archivo físico no encontrado")
            if not StorageConfig.is_safe_path(file_path):
                raise HTTPException(status_code=403, detail="Acceso denegado")

            content_type = StorageConfig.get_content_type(archivo_dict['extension'])
            with open(file_path, "rb") as f:
                file_content = f.read()

            return StreamingResponse(
                io.BytesIO(file_content),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={archivo_dict['nombre_original']}",
                    "Cache-Control": "private, max-age=3600"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error descargando archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error descargando archivo: {str(e)}")

@archivo_router.get("/archivos/{archivo_id}/url",
                   tags=["Archivos"])
def get_archivo_url(archivo_id: int, expiration: int = Query(3600, description="Tiempo de expiración en segundos")):
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
        storage_type = archivo_dict.get('storage_type', 'local')

        if storage_type == 's3':
            object_key = archivo_dict.get('s3_object_key') or archivo_dict['ruta_archivo']
            bucket = archivo_dict.get('s3_bucket') or s3_config.main_bucket

            if s3_config.is_development:
                url = s3_config.get_public_url(bucket, object_key)
            else:
                url = s3_config.get_presigned_url(bucket, object_key, expiration)
        else:
            url = archivo_dict['url_acceso']

        return {
            "success": True,
            "url": url,
            "expiration_seconds": expiration if storage_type == 's3' and not s3_config.is_development else None,
            "storage_type": storage_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo URL: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo URL: {str(e)}")

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

        return SuccessResponse(message="Descripción del archivo actualizada exitosamente")

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

        return SuccessResponse(message="Archivo eliminado exitosamente")

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
        from sqlalchemy import text
        query = conn.execute(text(f"SELECT COUNT(*), SUM(CASE WHEN tipo_archivo='imagen' THEN 1 ELSE 0 END), SUM(CASE WHEN tipo_archivo='documento' THEN 1 ELSE 0 END), SUM(tamaño_bytes)/1048576.0, MAX(fecha_subida) FROM bien_archivos WHERE bien_id={bien_id} AND bien_tipo='{bien_tipo}' AND activo=1"))
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
        query = conn.execute(text(f"SELECT COUNT(*) FROM bien_archivos WHERE bien_id={bien_id} AND bien_tipo='{bien_tipo}' AND activo=1"))
        result = query.fetchone()
        total = result[0] if result else 0
        return {"total": total}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo conteo: {str(e)}")

@archivo_router.post("/admin/migrate-to-s3",
                       tags=["Admin"],
                       response_model=SuccessResponse)
async def migrate_local_files_to_s3():
    if not USE_S3:
        raise HTTPException(status_code=400, detail="El almacenamiento S3 no está habilitado")

    try:
        query = bien_archivos.select().where(
            and_(
                bien_archivos.c.activo == True,
                or_(
                    bien_archivos.c.storage_type == 'local',
                    bien_archivos.c.storage_type.is_(None)
                )
            )
        )
        archivos_locales = conn.execute(query).fetchall()
        migrated_count = 0
        errors = []

        for archivo in archivos_locales:
            archivo_dict = dict(archivo._asdict())
            try:
                local_path = archivo_dict['ruta_archivo']
                if not os.path.exists(local_path):
                    errors.append(f"Archivo local no encontrado: {local_path}")
                    continue

                with open(local_path, 'rb') as f:
                    file_content = f.read()

                object_key = s3_config.get_object_key(
                    archivo_dict['bien_tipo'],
                    archivo_dict['bien_id'],
                    archivo_dict['nombre_archivo'],
                    "imagenes" if archivo_dict['tipo_archivo'] == 'imagen' else "documentos"
                )
                content_type = s3_config.get_content_type(archivo_dict['extension'])

                s3_config.minio_client.put_object(
                    bucket_name=s3_config.main_bucket,
                    object_name=object_key,
                    data=io.BytesIO(file_content),
                    length=len(file_content),
                    content_type=content_type,
                    metadata={
                        'migrated-from': 'local',
                        'migration-date': datetime.now().isoformat(),
                        'original-path': local_path
                    }
                )

                if s3_config.is_development:
                    new_url = s3_config.get_public_url(s3_config.main_bucket, object_key)
                else:
                    new_url = s3_config.get_presigned_url(s3_config.main_bucket, object_key, 86400)

                update_query = bien_archivos.update().where(
                    bien_archivos.c.id == archivo_dict['id']
                ).values(
                    storage_type='s3',
                    s3_bucket=s3_config.main_bucket,
                    s3_object_key=object_key,
                    url_acceso=new_url,
                    ruta_archivo=object_key,  
                    modificado_por='sistema_migracion',
                    fecha_modificacion=datetime.now()
                )

                conn.execute(update_query)
                migrated_count += 1
                logger.info(f"✅ Archivo migrado: {archivo_dict['nombre_original']} -> {object_key}")

            except Exception as e:
                error_msg = f"Error migrando {archivo_dict['nombre_original']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")

        conn.commit()
        return SuccessResponse(
            message=f"Migración completada. {migrated_count} archivos migrados",
            data={
                "migrated_count": migrated_count,
                "errors": errors,
                "total_processed": len(archivos_locales)
            }
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en migración: {e}")
        raise HTTPException(status_code=500, detail=f"Error en migración: {str(e)}")

@archivo_router.get("/admin/storage-info",
                      tags=["Admin"])
def get_storage_info():
    try:
        from sqlalchemy import text, func
        stats_query = conn.execute(text("SELECT storage_type, COUNT(*), SUM(CASE WHEN tipo_archivo='imagen' THEN 1 ELSE 0 END), SUM(CASE WHEN tipo_archivo='documento' THEN 1 ELSE 0 END), SUM(tamaño_bytes)/1048576.0 FROM bien_archivos GROUP BY storage_type"))

        storage_stats = {}
        for row in stats_query:
            storage_stats[row[0]] = {
                'total_archivos': row[1],
                'imagenes': row[2],
                'documentos': row[3],
                'tamaño_total_mb': float(row[4] or 0)
            }

        return {
            "success": True,
            "current_storage": "s3" if USE_S3 else "local",
            "s3_config": s3_config.get_debug_info() if USE_S3 else None,
            "storage_stats": storage_stats,
            "can_migrate": not USE_S3  
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo información: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo información: {str(e)}")
