from enum import auto
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import multiprocessing
from sqlalchemy.orm import sessionmaker

from routes.usuario import usuario
from routes.solicitud import solicitud
from routes.inmueble import inmueble
from routes.automovil import automovil
from routes.menu import menu
from routes.mueble import mueble
from routes.solicitudes_muebles import solicitudes_muebles
from routes.solicitudes_desincorporar_muebles import solicitudes_desincorporar_muebles
from routes.logs import logs_router
from routes.bien_archivo import archivo_router
from routes.static_files import static_router, configure_static_files
from routes.reporte_bm4 import reporte_bm4
from routes.reportes import reportes
from routes.departamento import departamento_router
from routes.usuario_extended import usuario_extended_router
from routes.comodato import comodato
from routes.concepto import concepto_router
from routes.configuracion import configuracion_router
from routes.reporte_historial import reporte_historial_router
from routes.reporte_bm7 import reporte_bm7_router
from doc.tags import tags_metadata
from starlette.responses import RedirectResponse

ui = {
    "docExpansion": 'none',
}

app = FastAPI(openapi_tags=tags_metadata, swagger_ui_parameters=ui)

@app.get("/", include_in_schema=False,)
def main():
    return RedirectResponse(url="/docs/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(usuario,)
app.include_router(solicitud)
app.include_router(mueble)
app.include_router(inmueble)
app.include_router(automovil)
app.include_router(menu)
app.include_router(solicitudes_muebles)
app.include_router(solicitudes_desincorporar_muebles)
app.include_router(logs_router)
app.include_router(archivo_router, prefix="/api/v1")
app.include_router(static_router, prefix="/api/v1")
app.include_router(reporte_bm4, prefix="/api/v1")
app.include_router(reportes, prefix="/api/v1")
app.include_router(departamento_router, prefix="/api/v1")
app.include_router(usuario_extended_router, prefix="/api/v1")
app.include_router(comodato, prefix="/api/v1")
app.include_router(concepto_router, prefix="/api/v1")
app.include_router(configuracion_router, prefix="/api/v1")
app.include_router(reporte_historial_router, prefix="/api/v1")
app.include_router(reporte_bm7_router, prefix="/api/v1")

configure_static_files(app)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=8000)
