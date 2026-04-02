from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from config.storage import StorageConfig
from utils.logger import AuditLogger

static_router = APIRouter()
audit_logger = AuditLogger()

@static_router.get("/files/{bien_tipo}/{bien_id}/{subfolder}/{filename}")
async def serve_file(
    bien_tipo: str,
    bien_id: str,
    subfolder: str,
    filename: str,
    request: Request
):

    try:
        
        if bien_tipo not in ['muebles', 'inmuebles', 'automoviles']:
            raise HTTPException(status_code=400, detail="Tipo de bien no válido")

        if subfolder not in ['imagenes', 'documentos']:
            raise HTTPException(status_code=400, detail="Subfolder no válido")

        safe_path = os.path.join(
            StorageConfig.UPLOAD_BASE_DIR,
            bien_tipo, bien_id, subfolder, filename
        )

        if not os.path.exists(safe_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        if not StorageConfig.is_safe_path(safe_path):
            raise HTTPException(status_code=403, detail="Acceso denegado")

        extension = os.path.splitext(filename)[1].lower()
        content_type = StorageConfig.get_content_type(extension)

        audit_logger.log_action(
            usuario="sistema",  
            accion="ACCESS",
            modulo="ARCHIVO",
            registro_id=0,  
            descripcion=f"Acceso a archivo: {bien_tipo}/{bien_id}/{subfolder}/{filename}",
            request=request
        )

        return FileResponse(
            safe_path,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Cache-Control": "private, max-age=3600"  
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sirviendo archivo: {str(e)}")

def configure_static_files(app):

    upload_dir = StorageConfig.UPLOAD_BASE_DIR
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    StorageConfig.init_storage()

    print(f"✅ Servicio de archivos estáticos configurado en: {upload_dir}")
    return upload_dir
