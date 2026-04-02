import numbers
from typing import List, Union, Optional
from fastapi import APIRouter, Response
from config.db import conn
from models.solicitud import solicitudes
from schemas.solicitud import Solicitud, SolicitudUpdate
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from sqlalchemy import and_

from cryptography.fernet import Fernet

solicitud = APIRouter()

@solicitud.get("/solicitud", tags=["Solicitud"], response_model=List[Solicitud] | Solicitud)
def get_solicitudes(
    numBien: int | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    
    if numBien and not fechaDesde and not fechaHasta:
        return conn.execute(solicitudes.select().where(solicitudes.c.num_bien == numBien)).first()

    query = solicitudes.select()
    filters = []
    
    if numBien:
        filters.append(solicitudes.c.num_bien == numBien)
    if fechaDesde:
        filters.append(solicitudes.c.fecha >= fechaDesde)
    if fechaHasta:
        filters.append(solicitudes.c.fecha <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return conn.execute(query).fetchall()

@solicitud.post("/solicitud", tags=["Solicitud"], response_model=Solicitud)
def create_solicitud(solicitud: Solicitud, ingresadoPor:str):

    new_solicitud = {"num_bien": solicitud.num_bien, "descripcion": solicitud.descripcion,
                   "serial": solicitud.serial, "fecha": solicitud.fecha, "ingresado_por": ingresadoPor}

    result = conn.execute(solicitudes.insert().values(new_solicitud))
    conn.commit()
    return conn.execute(solicitudes.select().where(solicitudes.c.id == result.lastrowid)).first()

@solicitud.put("/solicitud/{id}", tags=["Solicitud"], response_model=bool)
def update_solicitud(id: int, solicitud: SolicitudUpdate):

    solicitud_anterior = conn.execute(solicitudes.select().where(solicitudes.c.id == id)).first()
    if solicitud_anterior is None:
        return JSONResponse(status_code=404, content={"message": "Solicitud no encontrada"}, media_type="application/json")

    if solicitud.num_bien is not None and solicitud.num_bien != solicitud_anterior.num_bien:
        if conn.execute(solicitudes.select().where(solicitudes.c.num_bien == solicitud.num_bien)).rowcount > 0:
            return JSONResponse(status_code=400, content={"message": "Numero de bien duplicado"}, media_type="application/json")

    update_values = {}
    
    if solicitud.num_bien is not None:
        update_values['num_bien'] = solicitud.num_bien
    if solicitud.descripcion is not None:
        update_values['descripcion'] = solicitud.descripcion
    if solicitud.serial is not None:
        update_values['serial'] = solicitud.serial
    if solicitud.fecha is not None:
        update_values['fecha'] = solicitud.fecha
    if solicitud.ingresado_por is not None:
        update_values['ingresado_por'] = solicitud.ingresado_por

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")

    result = conn.execute(solicitudes.update().values(**update_values).where(solicitudes.c.id == id))
    if result.rowcount == 0:
        conn.commit()
        return Response(status_code=HTTP_404_NOT_FOUND, content="false".encode(), media_type="application/json")
    
    conn.commit()
    return Response(status_code=HTTP_200_OK, content="true".encode(), media_type="application/json")

@solicitud.delete("/solicitud/{id}", tags=["Solicitud"], response_model=bool)
def delete_solicitud(id: int):

    result = conn.execute(solicitudes.delete().where(solicitudes.c.id == id))

    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content="false".encode(), media_type="application/json")

    return Response(status_code=HTTP_200_OK, content="true".encode(), media_type="application/json")
