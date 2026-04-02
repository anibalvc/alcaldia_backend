from json import JSONEncoder
from typing import List, Optional
from fastapi import APIRouter, Response, Request, UploadFile, File, Form
from config.db import conn
from models.solicitudes_muebles import solicitudesMuebles
from models.mueble import muebles, mueblesTecnologia
from models.solicitudes_rechazadas import solicitudesRechazadas
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from datetime import datetime
import locale
from sqlalchemy import and_
import csv
import io

from cryptography.fernet import Fernet
from utils.logger import AuditLogger
from schemas.mueble import Mueble

from schemas.solicitudes_muebles import RechazarSolicitudesMuebles, SolicitudesMuebles, SolicitudesMueblesData, SolicitudesMueblesPOSTResponse, SolicitudesMueblesUpdate, ImportResultado
from schemas.solicitudes_rechazadas import SolicitudesRechazadasMuebles, SolicitudesRechazadasMueblesData
from schemas.mueble import MuebleData

solicitudes_muebles = APIRouter()

@solicitudes_muebles.get("/solicitudes-muebles", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesData)
def get_solicitudes_muebles(
    numBien: str | None = None, 
    departamento: str | None = None, 
    marca: str | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    
    query = solicitudesMuebles.select()
    filters = []
    
    if numBien:
        filters.append(solicitudesMuebles.c.num_bien.contains(numBien))
    if departamento:
        filters.append(solicitudesMuebles.c.departamento.contains(departamento))
    if marca:
        filters.append(solicitudesMuebles.c.marca.contains(marca))
    if fechaDesde:
        filters.append(solicitudesMuebles.c.fecha_solicitud >= fechaDesde)
    if fechaHasta:
        filters.append(solicitudesMuebles.c.fecha_solicitud <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@solicitudes_muebles.get("/solicitudes-muebles-tecnologia", tags=["Solicitudes Muebles"], response_model=MuebleData)
def get_solicitudes_muebles_tecnologia(numBien: str | None = None, departamento: str | None = None, marca: str | None = None):

    if numBien:
        return {"data": conn.execute(mueblesTecnologia.select().filter(mueblesTecnologia.c.num_bien.contains(numBien))).fetchall()}
    if departamento:
        return {"data": conn.execute(mueblesTecnologia.select().filter(mueblesTecnologia.c.departamento.contains(departamento))).fetchall()}
    if marca:
        return {"data": conn.execute(mueblesTecnologia.select().filter(mueblesTecnologia.c.marca.contains(marca))).fetchall()}

    return {"data": conn.execute(mueblesTecnologia.select()).fetchall()}

@solicitudes_muebles.delete("/rechazar-solicitud-mueble-es-tecnologia", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def rechazar_solicitud_mueble_es_tecnologia(muebleTecnologia: RechazarSolicitudesMuebles):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitudMuebleVerificacion = conn.execute(
        mueblesTecnologia.select().where(mueblesTecnologia.c.id == muebleTecnologia.id)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    solicitud_rechazada = {
        "num_bien": muebleTecnologia.num_bien,
        "id_solicitud": muebleTecnologia.id,
        "descripcion": muebleTecnologia.descripcion,
        "solicitado_por": muebleTecnologia.solicitado_por,
        "fecha_solicitud": muebleTecnologia.fecha_solicitud,
        "nombre": muebleTecnologia.nombre,
        "tipo": muebleTecnologia.tipo,
        "rechazada_por": muebleTecnologia.rechazada_por,
        "descripcion_rechazo": muebleTecnologia.descripcion_rechazo,
        "tipo_bien": "Mueble",
        "departamento": muebleTecnologia.departamento}
    resultRechazo = conn.execute(
        solicitudesRechazadas.insert().values(solicitud_rechazada))

    if resultRechazo.rowcount > 0:
        result = conn.execute(mueblesTecnologia.delete().where(
            mueblesTecnologia.c.id == muebleTecnologia.id))

        if result.rowcount == 0:
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
        conn.commit()
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro la solicitud"}, media_type="application/json")

@solicitudes_muebles.post("/aprobar-solicitud-mueble-es-tecnologia", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def aprobar_solicitud_mueble(mueble: Mueble, idSolicitud: int):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)

    solicitudMuebleVerificacion = conn.execute(
        mueblesTecnologia.select().where(mueblesTecnologia.c.id == idSolicitud)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    solicitud_aprobada = {
        "fecha_ingreso": now,
        "fecha_compra": mueble.fecha_compra,
        "orden_pago": mueble.orden_pago,
        "partida_compra": mueble.partida_compra,
        "num_factura": mueble.num_factura,
        "num_catalogo": mueble.num_catalogo,
        "modelo": mueble.modelo,
        "esTecnologia": mueble.esTecnologia,
        "marca": mueble.marca,
        "serial": mueble.serial,
        "responsable": mueble.responsable,
        "estado": mueble.estado,
        "descripcion": mueble.descripcion,
        "monto": mueble.monto,
        "num_bien": mueble.num_bien,
        "ingresado_por": mueble.ingresado_por,
        "departamento": mueble.departamento}
    
    resultAprobacion = conn.execute(
        muebles.insert().values(solicitud_aprobada))

    if resultAprobacion.rowcount > 0:
        result = conn.execute(mueblesTecnologia.delete().where(
            mueblesTecnologia.c.id == idSolicitud))

        if result.rowcount == 0:
            conn.commit()
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro la solicitud"}, media_type="application/json")

@solicitudes_muebles.get("/solicitudes-rechazadas-muebles", tags=["Solicitudes Muebles"], response_model=SolicitudesRechazadasMueblesData)
def get_solicitudes_rechazadas_muebles(departamento: str | None = None, marca: str | None = None):
    if departamento:
        return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble").filter(solicitudesMuebles.c.departamento.contains(departamento))).fetchall()}
    if marca:
        return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble").filter(solicitudesMuebles.c.marca.contains(marca))).fetchall()}

    return {"data": conn.execute(solicitudesRechazadas.select().where(solicitudesRechazadas.c.tipo_bien == "Mueble")).fetchall()}

@solicitudes_muebles.post("/aprobar-solicitud-mueble", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def aprobar_solicitud_mueble(mueble: Mueble, idSolicitud: int, request: Request, usuario: str):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)

    solicitudMuebleVerificacion = conn.execute(
        solicitudesMuebles.select().where(solicitudesMuebles.c.id == idSolicitud)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    solicitud_aprobada = {
        "fecha_ingreso": now,
        "fecha_compra": mueble.fecha_compra,
        "orden_pago": mueble.orden_pago,
        "partida_compra": mueble.partida_compra,
        "num_factura": mueble.num_factura,
        "num_catalogo": mueble.num_catalogo,
        "modelo": mueble.modelo,
        "esTecnologia": mueble.esTecnologia,
        "marca": mueble.marca,
        "serial": mueble.serial,
        "responsable": mueble.responsable,
        "estado": mueble.estado,
        "descripcion": mueble.descripcion,
        "monto": mueble.monto,
        "num_bien": mueble.num_bien,
        "ingresado_por": mueble.ingresado_por,
        "departamento": mueble.departamento}
    
    if mueble.esTecnologia == 1:
        resultAprobacion = conn.execute(
            mueblesTecnologia.insert().values(solicitud_aprobada))
    else:
        resultAprobacion = conn.execute(
            muebles.insert().values(solicitud_aprobada))

    if resultAprobacion.rowcount > 0:
        result = conn.execute(solicitudesMuebles.delete().where(
            solicitudesMuebles.c.id == idSolicitud))

        if result.rowcount == 0:
            conn.commit()
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

        datos_solicitud = dict(solicitudMuebleVerificacion._mapping)
        nuevo_mueble_id = resultAprobacion.lastrowid
        tabla_destino = "mueblesTecnologia" if mueble.esTecnologia == 1 else "muebles"
        
        AuditLogger.log_action(
            usuario=usuario,
            accion="APROBAR",
            modulo="SOLICITUD",
            registro_id=idSolicitud,
            datos_anteriores=datos_solicitud,
            datos_nuevos=solicitud_aprobada,
            descripcion=f"Se aprobó la solicitud de mueble ID {idSolicitud} y se creó el mueble ID {nuevo_mueble_id} en {tabla_destino}",
            request=request
        )
        
        conn.commit()
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro la solicitud"}, media_type="application/json")

@solicitudes_muebles.post("/solicitudes-muebles/create", tags=["Solicitudes Muebles"], response_model=SolicitudesMuebles)
def create_solicitud_mueble(solicitudMueble: SolicitudesMuebles, request: Request):
    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)
    new_mueble = {"num_bien": solicitudMueble.num_bien,
                  "descripcion": solicitudMueble.descripcion,
                  "marca": solicitudMueble.marca,
                  "modelo": solicitudMueble.modelo,
                  "serial": solicitudMueble.serial,
                  "responsable": solicitudMueble.responsable,
                  "fecha_solicitud": now,
                  "tipo": solicitudMueble.tipo,
                  "solicitado_por": solicitudMueble.solicitado_por,
                  "departamento": solicitudMueble.departamento}
    result = conn.execute(solicitudesMuebles.insert().values(new_mueble))
    conn.commit()

    nuevo_id = result.lastrowid
    AuditLogger.log_create(
        usuario=solicitudMueble.solicitado_por,
        modulo="SOLICITUD",
        registro_id=nuevo_id,
        datos=new_mueble,
        descripcion=f"Se creó una nueva solicitud de mueble: {solicitudMueble.descripcion} por {solicitudMueble.solicitado_por}",
        request=request
    )
    
    return conn.execute(solicitudesMuebles.select().where(solicitudesMuebles.c.id == result.lastrowid)).first()

@solicitudes_muebles.put("/solicitudes-muebles/{id}", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def update_solicitud_mueble(id: int, solicitudMueble: SolicitudesMueblesUpdate, usuario: str):
    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitud_anterior = conn.execute(solicitudesMuebles.select().where(solicitudesMuebles.c.id == id)).first()
    if solicitud_anterior is None:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

    update_values = {}
    
    if solicitudMueble.fecha_solicitud is not None:
        update_values['fecha_solicitud'] = solicitudMueble.fecha_solicitud
    if solicitudMueble.marca is not None:
        update_values['marca'] = solicitudMueble.marca
    if solicitudMueble.modelo is not None:
        update_values['modelo'] = solicitudMueble.modelo
    if solicitudMueble.serial is not None:
        update_values['serial'] = solicitudMueble.serial
    if solicitudMueble.responsable is not None:
        update_values['responsable'] = solicitudMueble.responsable
    if solicitudMueble.nombre is not None:
        update_values['nombre'] = solicitudMueble.nombre
    if solicitudMueble.descripcion is not None:
        update_values['descripcion'] = solicitudMueble.descripcion
    if solicitudMueble.num_bien is not None:
        update_values['num_bien'] = solicitudMueble.num_bien
    if solicitudMueble.departamento is not None:
        update_values['departamento'] = solicitudMueble.departamento
    if solicitudMueble.solicitado_por is not None:
        update_values['solicitado_por'] = solicitudMueble.solicitado_por
    if solicitudMueble.tipo is not None:
        update_values['tipo'] = solicitudMueble.tipo

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")
    
    result = conn.execute(solicitudesMuebles.update().values(**update_values).where(solicitudesMuebles.c.id == id))
    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
    
    conn.commit()
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@solicitudes_muebles.delete("/rechazar-solicitud-mueble", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def rechazar_solicitud_mueble(solicitudMueble: RechazarSolicitudesMuebles, request: Request, usuario: str):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitudMuebleVerificacion = conn.execute(
        solicitudesMuebles.select().where(solicitudesMuebles.c.id == solicitudMueble.id)).first()

    if solicitudMuebleVerificacion == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    solicitud_rechazada = {
        "num_bien": solicitudMueble.num_bien,
        "id_solicitud": solicitudMueble.id,
        "descripcion": solicitudMueble.descripcion,
        "solicitado_por": solicitudMueble.solicitado_por,
        "fecha_solicitud": solicitudMueble.fecha_solicitud,
        "nombre": solicitudMueble.nombre,
        "tipo": solicitudMueble.tipo,
        "rechazada_por": solicitudMueble.rechazada_por,
        "descripcion_rechazo": solicitudMueble.descripcion_rechazo,
        "tipo_bien": "Mueble",
        "departamento": solicitudMueble.departamento}
    resultRechazo = conn.execute(
        solicitudesRechazadas.insert().values(solicitud_rechazada))

    if resultRechazo.rowcount > 0:
        result = conn.execute(solicitudesMuebles.delete().where(
            solicitudesMuebles.c.id == solicitudMueble.id))

        if result.rowcount == 0:
            conn.commit()
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

        datos_solicitud = dict(solicitudMuebleVerificacion._mapping)
        
        AuditLogger.log_action(
            usuario=usuario,
            accion="RECHAZAR",
            modulo="SOLICITUD",
            registro_id=solicitudMueble.id,
            datos_anteriores=datos_solicitud,
            datos_nuevos=solicitud_rechazada,
            descripcion=f"Se rechazó la solicitud de mueble ID {solicitudMueble.id}: {solicitudMueble.descripcion_rechazo}",
            request=request
        )
        
        conn.commit()
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro la solicitud"}, media_type="application/json")

@solicitudes_muebles.delete("/solicitudes-muebles/{id}", tags=["Solicitudes Muebles"], response_model=SolicitudesMueblesPOSTResponse)
def delete_solicitud_mueble(id: int, request: Request, usuario: str):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    solicitudMueble = conn.execute(
        solicitudesMuebles.select().where(solicitudesMuebles.c.id == id)).first()

    if solicitudMueble == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro la Solicitud"}, media_type="application/json")

    result = conn.execute(solicitudesMuebles.delete().where(
        solicitudesMuebles.c.id == id))

    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

    datos_solicitud = dict(solicitudMueble._mapping)
    
    AuditLogger.log_delete(
        usuario=usuario,
        modulo="SOLICITUD",
        registro_id=id,
        datos=datos_solicitud,
        descripcion=f"Se eliminó la solicitud de mueble ID {id}",
        request=request
    )

    conn.commit()
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@solicitudes_muebles.post("/solicitudes-muebles/import-csv", tags=["Solicitudes Muebles"], response_model=ImportResultado)
async def importar_solicitudes_desde_csv(
    file: UploadFile = File(...),
    solicitado_por: str = Form(...),
    tipo: str = Form(default="Mueble"),
    request: Request = None
):

    tipos_permitidos = ["Mueble", "Inmueble", "Automovil"]
    if tipo not in tipos_permitidos:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"Tipo inválido: '{tipo}'. Valores permitidos: {', '.join(tipos_permitidos)}"
            }
        )

    if not file.filename.endswith('.csv'):
        return JSONResponse(status_code=400, content={"message": "El archivo debe ser un CSV"})

    contents = await file.read()

    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded = contents.decode('latin-1')
        except UnicodeDecodeError:
            decoded = contents.decode('cp1252')

    csv_reader = csv.reader(io.StringIO(decoded), delimiter=';')

    total_procesados = 0
    errores = []
    solicitudes_a_crear = []

    now = f"{datetime.now().day}/{datetime.now().month}/{datetime.now().year}"

    next(csv_reader, None)  
    next(csv_reader, None)  
    next(csv_reader, None)  

    for row_num, row in enumerate(csv_reader, start=4):  
        total_procesados += 1

        try:
            
            if len(row) < 12:
                errores.append({
                    "fila": row_num,
                    "codigo": row[1] if len(row) > 1 else "N/A",
                    "error": f"Fila incompleta: tiene {len(row)} columnas, se esperan al menos 12"
                })
                continue

            codigo = row[1].strip() if row[1] else None
            descripcion = row[2].strip() if row[2] else None
            marca = row[7].strip() if row[7] else ""  
            modelo = row[8].strip() if row[8] else ""
            ubicacion = row[9].strip() if row[9] else "Sin especificar"
            serial = row[10].strip() if row[10] else ""
            responsable = row[11].strip() if row[11] else ""

            if not codigo:
                errores.append({
                    "fila": row_num,
                    "codigo": "N/A",
                    "error": "Código del bien es obligatorio"
                })
                continue

            if not descripcion:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": "Descripción es obligatoria"
                })
                continue

            try:
                num_bien = int(codigo)
            except ValueError:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": f"El código '{codigo}' no es un número válido"
                })
                continue

            solicitudes_a_crear.append({
                "fila": row_num,
                "num_bien": num_bien,
                "descripcion": descripcion,
                "marca": marca,
                "modelo": modelo,
                "serial": serial,
                "responsable": responsable,
                "fecha_solicitud": now,
                "tipo": tipo,
                "solicitado_por": solicitado_por,
                "departamento": ubicacion
            })

        except Exception as e:
            errores.append({
                "fila": row_num,
                "codigo": row[1] if len(row) > 1 else "N/A",
                "error": str(e)
            })
            continue

    if len(errores) > 0:
        return ImportResultado(
            total_procesados=total_procesados,
            exitosos=0,
            fallidos=len(errores),
            errores=errores,
            solicitudes_creadas=[]
        )

    solicitudes_creadas = []

    try:
        for solicitud_data in solicitudes_a_crear:
            fila = solicitud_data.pop("fila")  

            result = conn.execute(solicitudesMuebles.insert().values(solicitud_data))
            nuevo_id = result.lastrowid
            solicitudes_creadas.append(nuevo_id)

            AuditLogger.log_create(
                usuario=solicitado_por,
                modulo="SOLICITUD",
                registro_id=nuevo_id,
                datos=solicitud_data,
                descripcion=f"Solicitud importada desde CSV (fila {fila}): {solicitud_data['descripcion'][:50]}",
                request=request
            )

        conn.commit()

        return ImportResultado(
            total_procesados=total_procesados,
            exitosos=len(solicitudes_creadas),
            fallidos=0,
            errores=[],
            solicitudes_creadas=solicitudes_creadas
        )

    except Exception as e:
        
        conn.rollback()
        return JSONResponse(
            status_code=500,
            content={
                "message": "Error durante la importación masiva",
                "error": str(e),
                "detalle": "Se canceló toda la operación. No se creó ninguna solicitud."
            }
        )
