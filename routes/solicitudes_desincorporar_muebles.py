from json import JSONEncoder
from typing import List
from fastapi import APIRouter, Response
from config.db import conn
from models.solicitud_desincorporar_muebles import solicitudesDesincorporarMuebles
from models.solicitudes_muebles import solicitudesMuebles
from models.solicitudes_rechazadas import solicitudesRechazadas
from models.mueble import muebles, mueblesDeleted
from schemas.solicitudes_desincorporar_muebles import SolicitudesDesincorporarMuebles, SolicitudesDesincorporarMueblesData
from schemas.solicitudes_rechazadas import SolicitudesRechazadasMueblesData
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from datetime import datetime
import locale

from cryptography.fernet import Fernet
from schemas.mueble import Mueble
from schemas.solicitudes_muebles import RechazarSolicitudesMuebles, SolicitudesMueblesPOSTResponse

solicitudes_desincorporar_muebles = APIRouter()

@solicitudes_desincorporar_muebles.get("/solicitudes-desincorporar-muebles", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesDesincorporarMueblesData)
def get_solicitudes_desincorporar_muebles(numBien: str | None = None, departamento: str | None = None, marca: str | None = None):

    if numBien:
        return {"data": conn.execute(solicitudesDesincorporarMuebles.select().filter(solicitudesDesincorporarMuebles.c.num_bien.contains(numBien))).fetchall()}
    if departamento:
        return {"data": conn.execute(solicitudesDesincorporarMuebles.select().filter(solicitudesDesincorporarMuebles.c.departamento.contains(departamento))).fetchall()}
    if marca:
        return {"data": conn.execute(solicitudesDesincorporarMuebles.select().filter(solicitudesDesincorporarMuebles.c.marca.contains(marca))).fetchall()}

    return {"data": conn.execute(solicitudesDesincorporarMuebles.select()).fetchall()}

@solicitudes_desincorporar_muebles.get("/desincorporaciones-rechazadas-muebles", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesRechazadasMueblesData)
def get_desincorporaciones_rechazadas_muebles(departamento: str | None = None, marca: str | None = None):
    if departamento:
        return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble", solicitudesRechazadas.c.tipo == "Desincorporar").filter(solicitudesMuebles.c.departamento.contains(departamento))).fetchall()}
    if marca:
        return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble", solicitudesRechazadas.c.tipo == "Desincorporar").filter(solicitudesMuebles.c.marca.contains(marca))).fetchall()}

    return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble", solicitudesRechazadas.c.tipo == "Desincorporar")).fetchall()}

@solicitudes_desincorporar_muebles.post("/aprobar-solicitud-desincorporar-mueble", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def aprobar_solicitud_desincorporar_mueble(idSolicitud: int, eliminadoPor:str):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)

    solicitudMuebleVerificacion = conn.execute(
       solicitudesDesincorporarMuebles.select().where(solicitudesDesincorporarMuebles.c.id == idSolicitud)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    mueble = conn.execute(
        muebles.select().where(muebles.c.num_bien == solicitudMuebleVerificacion.num_bien)).first()

    mueble_desincorporado = {
        "fecha_ingreso": mueble.fecha_ingreso,
        "fecha_compra": mueble.fecha_compra,
        "orden_pago": mueble.orden_pago,
        "partida_compra": mueble.partida_compra,
        "num_factura": mueble.num_factura,
        "num_catalogo": mueble.num_catalogo,
        "esTecnologia": mueble.esTecnologia,
        "marca": mueble.marca,
        "modelo": mueble.modelo,
        "serial": mueble.serial,
        "responsable": mueble.responsable,
        "estado": mueble.estado,
        "descripcion": mueble.descripcion,
        "monto": mueble.monto,
        "num_bien": mueble.num_bien,
        "ingresado_por": mueble.ingresado_por,
        "num_oficio": solicitudMuebleVerificacion.num_oficio,
        "eliminado_por": eliminadoPor,
        "departamento": mueble.departamento}
    resultDesincorporacion = conn.execute(
        mueblesDeleted.insert().values(mueble_desincorporado))

    if resultDesincorporacion.rowcount > 0:
        result = conn.execute(solicitudesDesincorporarMuebles.delete().where(
            solicitudesDesincorporarMuebles.c.id == idSolicitud))
        if result.rowcount == 0:
            conn.commit()
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
        else:
            result2 = conn.execute(muebles.delete().where(
                muebles.c.num_bien == solicitudMuebleVerificacion.num_bien))
            if result2.rowcount == 0:
                conn.commit()
                return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
            return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@solicitudes_desincorporar_muebles.post("/solicitudes-desincorporar-muebles/create", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesDesincorporarMuebles)
def create_solicitud_desincorporar_mueble(solicitudDesincorporarMueble: SolicitudesDesincorporarMuebles):
    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)
    new_mueble = {"num_bien": solicitudDesincorporarMueble.num_bien,
                  "descripcion": solicitudDesincorporarMueble.descripcion,
                  "marca": solicitudDesincorporarMueble.marca,
                  "modelo": solicitudDesincorporarMueble.modelo,
                  "serial": solicitudDesincorporarMueble.serial,
                  "responsable": solicitudDesincorporarMueble.responsable,
                  "fecha_solicitud": now,
                  "tipo": solicitudDesincorporarMueble.tipo,
                  "solicitado_por": solicitudDesincorporarMueble.solicitado_por,
                  "departamento": solicitudDesincorporarMueble.departamento,
                  "num_oficio": solicitudDesincorporarMueble.num_oficio}
    result = conn.execute(
        solicitudesDesincorporarMuebles.insert().values(new_mueble))
    return conn.execute(solicitudesDesincorporarMuebles.select().where(solicitudesDesincorporarMuebles.c.id == result.lastrowid)).first()

@solicitudes_desincorporar_muebles.delete("/rechazar-solicitud-desincorporar-mueble", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def rechazar_solicitud_mueble(solicitudMueble: RechazarSolicitudesMuebles):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitudMuebleVerificacion = conn.execute(
        solicitudesDesincorporarMuebles.select().where(solicitudesDesincorporarMuebles.c.id == solicitudMueble.id)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    solicitud_rechazada = {
        "num_bien": solicitudMueble.num_bien,
        "id_solicitud": solicitudMueble.id,
        "descripcion": solicitudMueble.descripcion,
        "solicitado_por": solicitudMueble.solicitado_por,
        "fecha_solicitud": solicitudMueble.fecha_solicitud,
        "nombre": solicitudMueble.nombre,
        "tipo": "Desincorporar",
        "rechazada_por": solicitudMueble.rechazada_por,
        "descripcion_rechazo": solicitudMueble.descripcion_rechazo,
        "tipo_bien": "Mueble",
        "departamento": solicitudMueble.departamento}
    resultRechazo = conn.execute(
        solicitudesRechazadas.insert().values(solicitud_rechazada))

    if resultRechazo.rowcount > 0:
        result = conn.execute(solicitudesDesincorporarMuebles.delete().where(
            solicitudesDesincorporarMuebles.c.id == solicitudMueble.id))

        if result.rowcount == 0:
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro la solicitud"}, media_type="application/json")

@solicitudes_desincorporar_muebles.delete("/delete-solicitudes-muebles-desincorporar/{id}", tags=["Solicitudes Desincorporar Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def delete_solicitud_mueble_desincorporar(id: int):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitudDesincorporarMuebles = conn.execute(
        solicitudesDesincorporarMuebles.select().where(solicitudesDesincorporarMuebles.c.id == id)).first()

    if solicitudDesincorporarMuebles == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    result = conn.execute(solicitudesDesincorporarMuebles.delete().where(
        solicitudesDesincorporarMuebles.c.id == id))

    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
