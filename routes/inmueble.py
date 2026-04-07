from datetime import datetime
from json import JSONEncoder
from typing import List, Optional
from fastapi import APIRouter, Response, Request, UploadFile, File, Form
from config.db import conn
from models.inmueble import inmuebles, inmueblesDeleted
from schemas.inmueble import Inmueble, InmuebleData, InmuebleDelete, InmuebleDeleteData, InmueblePOSTResponse, InmuebleUpdate
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from cryptography.fernet import Fernet
from utils.logger import AuditLogger
from utils.file_handler import FileHandler
from models.bien_archivo import bien_archivos

inmueble = APIRouter()

@inmueble.get("/inmueble", tags=["Inmueble"], response_model=InmuebleData)
def get_inmuebles(
    numBien: int | None = None, 
    ordenPago: int | None = None, 
    departamento: str | None = None, 
    nombre: str | None = None,
    descripcion: str | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    
    query = inmuebles.select()
    filters = []
    
    if numBien:
        filters.append(inmuebles.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(inmuebles.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(inmuebles.c.departamento.contains(departamento))
    if nombre:
        filters.append(inmuebles.c.nombre.contains(nombre))
    if descripcion:
        filters.append(inmuebles.c.descripcion.contains(descripcion))
    if fechaDesde:
        filters.append(inmuebles.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(inmuebles.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@inmueble.get("/inmuebledeleted", tags=["Inmueble"], response_model=InmuebleDeleteData)
def get_inmueblesdeleted(
    numBien: int | None = None, 
    ordenPago: int | None = None, 
    departamento: str | None = None, 
    nombre: str | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    
    query = inmueblesDeleted.select()
    filters = []
    
    if numBien:
        filters.append(inmueblesDeleted.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(inmueblesDeleted.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(inmueblesDeleted.c.departamento.contains(departamento))
    if nombre:
        filters.append(inmueblesDeleted.c.nombre.contains(nombre))
    if fechaDesde:
        filters.append(inmueblesDeleted.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(inmueblesDeleted.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@inmueble.post("/inmueble", tags=["Inmueble"], response_model=Inmueble)
def create_Inmueble(inmueble: Inmueble, request: Request):
    now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
        "/"+str(datetime.now().year)
    new_inmueble = {"num_bien": inmueble.num_bien, "descripcion": inmueble.descripcion,
                    "partida_compra": inmueble.partida_compra,
                    "fecha_ingreso": now,
                    "nombre": inmueble.nombre,
                    "ingresado_por": inmueble.ingresado_por,
                    "orden_pago": inmueble.orden_pago,
                    "num_expediente": inmueble.num_expediente,
                    "num_factura": inmueble.num_factura,
                    "num_expediente": inmueble.num_expediente,
                    "num_factura": inmueble.num_factura,
                    "valor_inicial": inmueble.valor_inicial,
                    "valor_actual": inmueble.valor_actual,
                    "concepto_incorporacion": inmueble.concepto_incorporacion,
                    "departamento": inmueble.departamento}

    result = conn.execute(inmuebles.insert().values(new_inmueble))
    conn.commit()

    nuevo_id = result.lastrowid
    AuditLogger.log_create(
        usuario=inmueble.ingresado_por,
        modulo="INMUEBLE",
        registro_id=nuevo_id,
        datos=new_inmueble,
        descripcion=f"Se creó el inmueble '{inmueble.nombre}' con número de bien {inmueble.num_bien}",
        request=request
    )
    
    return conn.execute(inmuebles.select().where(inmuebles.c.id == result.lastrowid)).first()

@inmueble.put("/inmueble/{id}", tags=["Inmueble"], response_model=InmueblePOSTResponse)
def update_Inmueble(id: int, inmueble: InmuebleUpdate, request: Request, usuario: str):

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    inmueble_anterior = conn.execute(inmuebles.select().where(inmuebles.c.id == id)).first()
    if inmueble_anterior is None:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
    
    datos_anteriores = dict(inmueble_anterior._mapping)

    update_values = {}
    
    if inmueble.nombre is not None:
        update_values['nombre'] = inmueble.nombre
    if inmueble.orden_pago is not None:
        update_values['orden_pago'] = inmueble.orden_pago
    if inmueble.partida_compra is not None:
        update_values['partida_compra'] = inmueble.partida_compra
    if inmueble.num_factura is not None:
        update_values['num_factura'] = inmueble.num_factura
    if inmueble.descripcion is not None:
        update_values['descripcion'] = inmueble.descripcion
    if inmueble.valor_inicial is not None:
        update_values['valor_inicial'] = inmueble.valor_inicial
    if inmueble.valor_actual is not None:
        update_values['valor_actual'] = inmueble.valor_actual
    if inmueble.num_bien is not None:
        update_values['num_bien'] = inmueble.num_bien
    if inmueble.num_expediente is not None:
        update_values['num_expediente'] = inmueble.num_expediente
    if inmueble.departamento is not None:
        update_values['departamento'] = inmueble.departamento

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")
    
    result = conn.execute(inmuebles.update().values(**update_values).where(inmuebles.c.id == id))
    if result.rowcount == 0:
        conn.commit()
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

    datos_nuevos = {}
    for key, value in update_values.items():
        datos_nuevos[key] = str(value) if value is not None else value

    campos_cambiados = ", ".join(update_values.keys())
    num_bien_desc = update_values.get('num_bien', datos_anteriores.get('num_bien', 'N/A'))
    
    AuditLogger.log_update(
        usuario=usuario,
        modulo="INMUEBLE",
        registro_id=id,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        descripcion=f"Se actualizó el inmueble con ID {id} y número de bien {num_bien_desc}. Campos modificados: {campos_cambiados}",
        request=request
    )
    
    conn.commit()
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@inmueble.delete("/inmueble/{id}", tags=["Inmueble"], response_model=bool)
def delete_Inmueble(id: int, eliminado_por: str, num_oficio: int, concepto_desincorporacion: str, request: Request):

    inmueble = conn.execute(
        inmuebles.select().where(inmuebles.c.id == id)).first()

    if inmueble is None:
        return JSONResponse(status_code=400, content={"message": "No se encontro el Inmueble"}, media_type="application/json")

    delete_Inmueble = {"num_bien": inmueble.num_bien, "descripcion": inmueble.descripcion,
                       "partida_compra": inmueble.partida_compra,
                       "fecha_ingreso": inmueble.fecha_ingreso,
                       "ingresado_por": inmueble.ingresado_por,
                       "orden_pago": inmueble.orden_pago,
                       "num_oficio": num_oficio,
                       "num_factura": inmueble.num_factura,
                       "num_expediente": inmueble.num_expediente,
                       "nombre": inmueble.nombre,
                       "nombre": inmueble.nombre,
                       "valor_inicial": inmueble.valor_inicial,
                       "valor_actual": inmueble.valor_actual,
                       "departamento": inmueble.departamento,
                       "concepto_incorporacion": inmueble.concepto_incorporacion,
                       "concepto_desincorporacion": concepto_desincorporacion,
                       "eliminado_por": eliminado_por}

    try:
        resultDelete = conn.execute(inmueblesDeleted.insert().values(delete_Inmueble))
    except IntegrityError as e:
        conn.rollback()
        return JSONResponse(status_code=400, content={"message": f"Error de integridad: {e.orig}"}, media_type="application/json")

    if resultDelete.rowcount > 0:
        result = conn.execute(inmuebles.delete().where(inmuebles.c.id == id))

        if result.rowcount == 0:
            return Response(status_code=HTTP_404_NOT_FOUND, content="false".encode(), media_type="application/json")

        datos_inmueble = dict(inmueble._mapping)
        AuditLogger.log_desincorporar(
            usuario=eliminado_por,
            modulo="INMUEBLE",
            registro_id=id,
            datos=datos_inmueble,
            num_oficio=num_oficio,
            descripcion=f"Se desincorporó el inmueble '{inmueble.nombre}' con número de bien {inmueble.num_bien} mediante oficio #{num_oficio}",
            request=request
        )
        
        conn.commit()
        return Response(status_code=HTTP_200_OK, content="true".encode(), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro el Inmueble"}, media_type="application/json")

file_handler = FileHandler()

@inmueble.post("/inmueble/traspaso", tags=["Inmueble"])
def traspaso_inmueble(
    id_bien: int = Form(...),
    nuevo_departamento: str = Form(...),
    eliminado_por: str = Form(...),
    num_oficio: int = Form(...),
    archivo: UploadFile = File(...),
    request: Request = None
):

    conn.commit()
    
    try:
        
        inmueble_original = conn.execute(inmuebles.select().where(inmuebles.c.id == id_bien)).first()
        
        if not inmueble_original:
            return JSONResponse(status_code=404, content={"message": "Inmueble no encontrado"}, media_type="application/json")
            
        inmueble_dict = dict(inmueble_original._mapping)

        delete_data = inmueble_dict.copy()
        if 'id' in delete_data: delete_data.pop('id') 
        delete_data['num_oficio'] = num_oficio
        delete_data['concepto_desincorporacion'] = '51' 
        delete_data['eliminado_por'] = eliminado_por
        
        conn.execute(inmueblesDeleted.insert().values(delete_data))

        conn.execute(inmuebles.delete().where(inmuebles.c.id == id_bien))

        new_inmueble_data = inmueble_dict.copy()
        if 'id' in new_inmueble_data: new_inmueble_data.pop('id') 
        new_inmueble_data['departamento'] = nuevo_departamento
        new_inmueble_data['concepto_incorporacion'] = '02'
        new_inmueble_data['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y") 
        
        result_insert = conn.execute(inmuebles.insert().values(new_inmueble_data))
        nuevo_id_bien = result_insert.lastrowid

        try:
            
            file_info = file_handler.save_file(
                file=archivo,
                bien_id=nuevo_id_bien,
                numero_bien=str(new_inmueble_data['num_bien']),
                bien_tipo='inmueble',
                subido_por=eliminado_por 
            )

            conn.execute(bien_archivos.insert().values(
                bien_id=nuevo_id_bien,
                numero_bien=str(new_inmueble_data['num_bien']),
                bien_tipo='inmueble',
                nombre_archivo=file_info['nombre_archivo'],
                nombre_original=file_info['nombre_original'],
                tipo_archivo=file_info['tipo_archivo'],
                extension=file_info['extension'],
                tamaño_bytes=file_info['tamaño_bytes'],
                ruta_archivo=file_info['ruta_archivo'],
                url_acceso=file_info['url_acceso'],
                thumbnail_path=file_info['thumbnail_path'],
                descripcion=f"Justificante de Traspaso (De {inmueble_dict['departamento']} a {nuevo_departamento})",
                checksum_md5=file_info['checksum_md5'],
                subido_por=eliminado_por,
                fecha_subida=datetime.now()
            ))
            
        except Exception as e:
            if 'file_info' in locals():
                file_handler.delete_file(file_info['ruta_archivo'])
            raise e 

        AuditLogger.log_create(
            usuario=eliminado_por,
            modulo="INMUEBLE",
            registro_id=nuevo_id_bien,
            datos=new_inmueble_data,
            descripcion=f"Traspaso de Inmueble: {inmueble_dict['departamento']} -> {nuevo_departamento}. (Anterior ID: {id_bien})",
            request=request
        )
        
        conn.commit()
        
        return JSONResponse(
            status_code=200, 
            content={
                "data": True, 
                "message": "Traspaso realizado con éxito", 
                "nuevo_id": nuevo_id_bien
            }
        )

    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"message": f"Error en traspaso: {str(e)}"}, media_type="application/json")

@inmueble.post("/inmueble/reincorporar", tags=["Inmueble"])
def reincorporar_inmueble(
    id_historial: int = Form(...),
    concepto_incorporacion: str = Form(...),
    nuevo_departamento: str = Form(None),
    usuario_accion: str = Form(...),
    request: Request = None
):
    
    conn.commit()
    
    try:
        
        inmueble_deleted = conn.execute(
            inmueblesDeleted.select().where(inmueblesDeleted.c.id == id_historial)
        ).first()
        
        if not inmueble_deleted:
            return JSONResponse(status_code=404, content={"message": "Registro histórico no encontrado"}, media_type="application/json")

        datos_deleted = dict(inmueble_deleted._mapping)

        nuevo_inmueble = datos_deleted.copy()

        campos_a_eliminar = ['id', 'fecha_eliminacion', 'eliminado_por', 'concepto_desincorporacion', 'num_oficio_eliminacion']
        for campo in campos_a_eliminar:
            if campo in nuevo_inmueble:
                del nuevo_inmueble[campo]

        nuevo_inmueble['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y")
        nuevo_inmueble['concepto_incorporacion'] = concepto_incorporacion
        nuevo_inmueble['ingresado_por'] = usuario_accion

        if nuevo_departamento:
            nuevo_inmueble['departamento'] = nuevo_departamento

        try:
            result = conn.execute(inmuebles.insert().values(nuevo_inmueble))
            nuevo_id = result.lastrowid

            AuditLogger.log_create(
                usuario=usuario_accion,
                modulo="INMUEBLE",
                registro_id=nuevo_id,
                datos=nuevo_inmueble,
                descripcion=f"Reincorporación de inmueble desde historial ID {id_historial}. Concepto: {concepto_incorporacion}",
                request=request
            )
            
            conn.commit()
            
            return JSONResponse(
                status_code=200, 
                content={
                    "data": True, 
                    "message": "Bien reincorporado exitosamente", 
                    "nuevo_id": nuevo_id
                }
            )
            
        except IntegrityError as e:
            conn.rollback()
            return JSONResponse(status_code=400, content={"message": f"Error de integridad al reincorporar (posible duplicado de número de bien): {e.orig}"})

    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"message": f"Error interno: {str(e)}"})
