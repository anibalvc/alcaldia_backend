from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Response, Request, UploadFile, File, Form
from config.db import conn
from models.automovil import automoviles, automovilesDeleted
from schemas.automovil import Automovil, AutomovilData, AutomovilDelete, AutomovilDeleteData, AutomovilPOSTResponse, AutomovilUpdate
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from cryptography.fernet import Fernet
from utils.logger import AuditLogger
from utils.file_handler import FileHandler
from models.bien_archivo import bien_archivos

automovil = APIRouter()

@automovil.get("/automovil", tags=["Automovil"], response_model=AutomovilData)
def get_automoviles(
    numBien: int | None = None, 
    ordenPago: int | None = None, 
    departamento: str | None = None, 
    marca: str | None = None,
    descripcion: str | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    try:
        
        conn.rollback()
    except:
        pass

    conn.execution_options(stream_results=True)

    query = automoviles.select()
    filters = []
    
    if numBien:
        filters.append(automoviles.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(automoviles.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(automoviles.c.departamento.contains(departamento))
    if marca:
        filters.append(automoviles.c.marca.contains(marca))
    if descripcion:
        filters.append(or_(
            automoviles.c.marca.contains(descripcion),
            automoviles.c.modelo.contains(descripcion),
            automoviles.c.placa.contains(descripcion)
        ))
    if fechaDesde:
        filters.append(automoviles.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(automoviles.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@automovil.get("/automovildeleted", tags=["Automovil"], response_model=AutomovilDeleteData)
def get_automovilesdeleted(
    numBien: int | None = None, 
    ordenPago: int | None = None, 
    departamento: str | None = None, 
    numOficio: int | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):
    
    conn.commit()

    conn.execution_options(stream_results=True)

    query = automovilesDeleted.select()
    filters = []
    
    if numBien:
        filters.append(automovilesDeleted.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(automovilesDeleted.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(automovilesDeleted.c.departamento.contains(departamento))
    if numOficio:
        filters.append(automovilesDeleted.c.num_oficio.contains(numOficio))
    if fechaDesde:
        filters.append(automovilesDeleted.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(automovilesDeleted.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@automovil.post("/automovil", tags=["Automovil"], response_model=Automovil)
def create_Automovil(automovil: Automovil, request: Request):

    conn.commit()

    conn.execution_options(stream_results=True)
    
    try:
        now = str(datetime.now().day) + "/" + str(datetime.now().month) + "/" + str(datetime.now().year)
        new_automovil = {
            "ingresado_por": automovil.ingresado_por,
            "fecha_ingreso": now,
            "orden_pago": automovil.orden_pago,
            "partida_compra": automovil.partida_compra,
            "num_factura": automovil.num_factura,
            "modelo": automovil.modelo,
            "marca": automovil.marca,
            "año": automovil.año,
            "color": automovil.color,
            "placa": automovil.placa,   
            "estatus": automovil.estatus,
            "operatividad": automovil.operatividad, 
            "estatus": automovil.estatus,
            "operatividad": automovil.operatividad, 
            "valor_inicial": automovil.valor_inicial,
            "valor_actual": automovil.valor_actual,
            "num_bien": automovil.num_bien,
            "num_serial_motor": automovil.num_bien,
            "num_serial_carroceria": automovil.num_bien,
            "num_expediente": automovil.num_expediente,
            "chofer": automovil.chofer,
            "concepto_incorporacion": automovil.concepto_incorporacion,
            "departamento": automovil.departamento
        }

        result = conn.execute(automoviles.insert().values(new_automovil))
        conn.commit()

        nuevo_id = result.lastrowid
        AuditLogger.log_create(
            usuario=automovil.ingresado_por,
            modulo="AUTOMOVIL",
            registro_id=nuevo_id,
            datos=new_automovil,
            descripcion=f"Se creó el automóvil {automovil.marca} {automovil.modelo} con placa {automovil.placa} y número de bien {automovil.num_bien}",
            request=request
        )
        
        inserted_automovil = conn.execute(automoviles.select().where(automoviles.c.id == result.lastrowid)).first()
        
        if inserted_automovil is None:
            return JSONResponse(status_code=404, content={"message": "Automóvil no encontrado después de la inserción"}, media_type="application/json")

        return inserted_automovil
    except SQLAlchemyError as e:
        error_str = str(e.__dict__['orig'])
        return JSONResponse(status_code=400, content={"message": f"Error al insertar el automóvil: {error_str}"}, media_type="application/json")
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)}, media_type="application/json")

@automovil.put("/automovil/{id}", tags=["Automovil"], response_model=AutomovilPOSTResponse)
def update_Automovil(id: int, automovil: AutomovilUpdate, request: Request, usuario: str):

    conn.commit()

    conn.execution_options(stream_results=True)

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    automovil_anterior = conn.execute(automoviles.select().where(automoviles.c.id == id)).first()
    if automovil_anterior is None:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
    
    datos_anteriores = dict(automovil_anterior._mapping)

    update_values = {}
    
    if automovil.fecha_ingreso is not None:
        update_values['fecha_ingreso'] = automovil.fecha_ingreso
    if automovil.orden_pago is not None:
        update_values['orden_pago'] = automovil.orden_pago
    if automovil.partida_compra is not None:
        update_values['partida_compra'] = automovil.partida_compra
    if automovil.num_factura is not None:
        update_values['num_factura'] = automovil.num_factura
    if automovil.modelo is not None:
        update_values['modelo'] = automovil.modelo
    if automovil.marca is not None:
        update_values['marca'] = automovil.marca
    if automovil.año is not None:
        update_values['año'] = automovil.año
    if automovil.color is not None:
        update_values['color'] = automovil.color
    if automovil.placa is not None:
        update_values['placa'] = automovil.placa
    if automovil.estatus is not None:
        update_values['estatus'] = automovil.estatus
    if automovil.operatividad is not None:
        update_values['operatividad'] = automovil.operatividad
    if automovil.num_serial_motor is not None:
        update_values['num_serial_motor'] = automovil.num_serial_motor
    if automovil.num_serial_carroceria is not None:
        update_values['num_serial_carroceria'] = automovil.num_serial_carroceria
    if automovil.valor_inicial is not None:
        update_values['valor_inicial'] = automovil.valor_inicial
    if automovil.valor_actual is not None:
        update_values['valor_actual'] = automovil.valor_actual
    if automovil.num_bien is not None:
        update_values['num_bien'] = automovil.num_bien
    if automovil.chofer is not None:
        update_values['chofer'] = automovil.chofer
    if automovil.num_expediente is not None:
        update_values['num_expediente'] = automovil.num_expediente
    if automovil.departamento is not None:
        update_values['departamento'] = automovil.departamento

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")
    
    result = conn.execute(automoviles.update().values(**update_values).where(automoviles.c.id == id))
    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

    datos_nuevos = {}
    for key, value in update_values.items():
        datos_nuevos[key] = str(value) if value is not None else value

    campos_cambiados = ", ".join(update_values.keys())
    num_bien_desc = update_values.get('num_bien', datos_anteriores.get('num_bien', 'N/A'))
    
    AuditLogger.log_update(
        usuario=usuario,
        modulo="AUTOMOVIL",
        registro_id=id,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        descripcion=f"Se actualizó el automóvil con ID {id} y número de bien {num_bien_desc}. Campos modificados: {campos_cambiados}",
        request=request
    )
    
    conn.commit()
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@automovil.delete("/automovil/{id}", tags=["Automovil"], response_model=AutomovilPOSTResponse)
def delete_Automovil(id: int, eliminado_por: str, num_oficio: int, concepto_desincorporacion: str, request: Request):

    conn.commit()

    conn.execution_options(stream_results=True)

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    automovil = conn.execute(automoviles.select().where(
        automoviles.c.id == id)).first()

    if automovil == None:
        return JSONResponse(status_code=400, content={"message": "No se encontro el Automovil"}, media_type="application/json")

    delete_Automovil = {"num_bien": automovil.num_bien, "modelo": automovil.descripcion,
                        "partida_compra": automovil.partida_compra,
                        "fecha_ingreso": automovil.fecha_ingreso,
                        "ingresado_por": automovil.ingresado_por,
                        "num_oficio": num_oficio,
                        "num_serial_motor": automovil.num_serial_motor,
                        "num_serial_carroceria": automovil.num_serial_carroceria,
                        "orden_pago": automovil.orden_pago,
                        "num_factura": automovil.num_factura,
                        "num_expediente": automovil.num_expediente,
                        "marca": automovil.marca,
                        "año": automovil.año,
                        "color": automovil.color,
                        "placa": automovil.placa,
                        "estatus": automovil.estatus,
                        "operatividad": automovil.operatividad,
                        "estatus": automovil.estatus,
                        "operatividad": automovil.operatividad,
                        "valor_inicial": automovil.valor_inicial,
                        "valor_actual": automovil.valor_actual,
                        "departamento": automovil.departamento,
                        "chofer": automovil.chofer,
                        "concepto_incorporacion": automovil.concepto_incorporacion,
                        "concepto_desincorporacion": concepto_desincorporacion,
                        "eliminado_por": eliminado_por}

    try:
        resultDelete = conn.execute(automovilesDeleted.insert().values(delete_Automovil))
    except IntegrityError as e:
        conn.rollback()
        return JSONResponse(status_code=400, content={"message": f"Error de integridad: {e.orig}"}, media_type="application/json")

    if resultDelete.rowcount > 0:
        result = conn.execute(
            automoviles.delete().where(automoviles.c.id == id))

        if result.rowcount == 0:
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

        datos_automovil = dict(automovil._mapping)
        AuditLogger.log_desincorporar(
            usuario=eliminado_por,
            modulo="AUTOMOVIL",
            registro_id=id,
            datos=datos_automovil,
            num_oficio=num_oficio,
            descripcion=f"Se desincorporó el automóvil {automovil.marca} con placa {automovil.placa} y número de bien {automovil.num_bien} mediante oficio 
            request=request
        )
        
        conn.commit()
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro el Automovil"}, media_type="application/json")

file_handler = FileHandler()

@automovil.post("/automovil/traspaso", tags=["Automovil"])
def traspaso_automovil(
    id_bien: int = Form(...),
    nuevo_departamento: str = Form(...),
    eliminado_por: str = Form(...),
    num_oficio: int = Form(...),
    archivo: UploadFile = File(...),
    request: Request = None
):

    conn.commit()
    
    try:
        
        automovil_original = conn.execute(automoviles.select().where(automoviles.c.id == id_bien)).first()
        
        if not automovil_original:
            return JSONResponse(status_code=404, content={"message": "Automóvil no encontrado"}, media_type="application/json")
            
        automovil_dict = dict(automovil_original._mapping)

        delete_data = automovil_dict.copy()
        if 'id' in delete_data: delete_data.pop('id') 
        delete_data['num_oficio'] = num_oficio
        delete_data['concepto_desincorporacion'] = '51' 
        delete_data['eliminado_por'] = eliminado_por
        
        conn.execute(automovilesDeleted.insert().values(delete_data))

        conn.execute(automoviles.delete().where(automoviles.c.id == id_bien))

        new_automovil_data = automovil_dict.copy()
        if 'id' in new_automovil_data: new_automovil_data.pop('id') 
        new_automovil_data['departamento'] = nuevo_departamento
        new_automovil_data['concepto_incorporacion'] = '02'
        new_automovil_data['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y") 
        
        result_insert = conn.execute(automoviles.insert().values(new_automovil_data))
        nuevo_id_bien = result_insert.lastrowid

        try:
            
            file_info = file_handler.save_file(
                file=archivo,
                bien_id=nuevo_id_bien,
                numero_bien=str(new_automovil_data['num_bien']),
                bien_tipo='automovil',
                subido_por=eliminado_por 
            )

            conn.execute(bien_archivos.insert().values(
                bien_id=nuevo_id_bien,
                numero_bien=str(new_automovil_data['num_bien']),
                bien_tipo='automovil',
                nombre_archivo=file_info['nombre_archivo'],
                nombre_original=file_info['nombre_original'],
                tipo_archivo=file_info['tipo_archivo'],
                extension=file_info['extension'],
                tamaño_bytes=file_info['tamaño_bytes'],
                ruta_archivo=file_info['ruta_archivo'],
                url_acceso=file_info['url_acceso'],
                thumbnail_path=file_info['thumbnail_path'],
                descripcion=f"Justificante de Traspaso (De {automovil_dict['departamento']} a {nuevo_departamento})",
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
            modulo="AUTOMOVIL",
            registro_id=nuevo_id_bien,
            datos=new_automovil_data,
            descripcion=f"Traspaso de Automóvil: {automovil_dict['departamento']} -> {nuevo_departamento}. (Anterior ID: {id_bien})",
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

@automovil.post("/automovil/reincorporar", tags=["Automovil"])
def reincorporar_automovil(
    id_historial: int = Form(...),
    concepto_incorporacion: str = Form(...),
    nuevo_departamento: str = Form(None),
    usuario_accion: str = Form(...),
    request: Request = None
):
    
    conn.commit()
    
    try:
        
        automovil_deleted = conn.execute(
            automovilesDeleted.select().where(automovilesDeleted.c.id == id_historial)
        ).first()
        
        if not automovil_deleted:
            return JSONResponse(status_code=404, content={"message": "Registro histórico no encontrado"}, media_type="application/json")

        datos_deleted = dict(automovil_deleted._mapping)

        nuevo_automovil = datos_deleted.copy()

        campos_a_eliminar = ['id', 'fecha_eliminacion', 'eliminado_por', 'concepto_desincorporacion', 'num_oficio_eliminacion']
        for campo in campos_a_eliminar:
            if campo in nuevo_automovil:
                del nuevo_automovil[campo]

        nuevo_automovil['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y")
        nuevo_automovil['concepto_incorporacion'] = concepto_incorporacion
        nuevo_automovil['ingresado_por'] = usuario_accion

        if nuevo_departamento:
            nuevo_automovil['departamento'] = nuevo_departamento

        try:
            result = conn.execute(automoviles.insert().values(nuevo_automovil))
            nuevo_id = result.lastrowid

            AuditLogger.log_create(
                usuario=usuario_accion,
                modulo="AUTOMOVIL",
                registro_id=nuevo_id,
                datos=nuevo_automovil,
                descripcion=f"Reincorporación de automóvil desde historial ID {id_historial}. Concepto: {concepto_incorporacion}",
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
