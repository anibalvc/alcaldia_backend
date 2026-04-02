from json import JSONEncoder
from typing import List, Optional
from fastapi import APIRouter, Response, Request, UploadFile, File, Form
from config.db import conn, engine
from models.mueble import muebles, mueblesDeleted, mueblesTecnologia
from schemas.mueble import ErrorResponse, Mueble, MuebleData, MuebleDelete, MuebleDeleteData, MueblePOSTResponse, MuebleUpdate, ImportMuebleResultado
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from datetime import datetime
import locale
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from sqlalchemy import and_
import csv
import io
from decimal import Decimal

from cryptography.fernet import Fernet
from utils.logger import AuditLogger
from utils.file_handler import FileHandler
from models.bien_archivo import bien_archivos

mueble = APIRouter()

@mueble.get("/mueble", tags=["Mueble"], response_model=MuebleData)
def get_muebles(
    numBien: str | None = None, 
    ordenPago: str | None = None, 
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

    query = muebles.select()
    filters = []
    
    if numBien:
        filters.append(muebles.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(muebles.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(muebles.c.departamento.contains(departamento))
    if marca:
        filters.append(muebles.c.marca.contains(marca))
    if descripcion:
        filters.append(muebles.c.descripcion.contains(descripcion))
    if fechaDesde:
        filters.append(muebles.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(muebles.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execution_options(stream_results=True).execute(query).fetchall()}

@mueble.get("/muebledeleted", tags=["Mueble"], response_model=MuebleDeleteData)
def get_mueblesdeleted(
    numBien: int | None = None, 
    ordenPago: int | None = None, 
    departamento: str | None = None, 
    marca: str | None = None, 
    num_oficio: int | None = None,
    fechaDesde: str | None = None,
    fechaHasta: str | None = None
):

    conn.commit()

    conn.execution_options(stream_results=True)

    query = mueblesDeleted.select()
    filters = []
    
    if numBien:
        filters.append(mueblesDeleted.c.num_bien.contains(numBien))
    if ordenPago:
        filters.append(mueblesDeleted.c.orden_pago.contains(ordenPago))
    if departamento:
        filters.append(mueblesDeleted.c.departamento.contains(departamento))
    if marca:
        filters.append(mueblesDeleted.c.marca.contains(marca))
    if num_oficio:
        filters.append(mueblesDeleted.c.num_oficio.contains(num_oficio))
    if fechaDesde:
        filters.append(mueblesDeleted.c.fecha_ingreso >= fechaDesde)
    if fechaHasta:
        filters.append(mueblesDeleted.c.fecha_ingreso <= fechaHasta)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return {"data": conn.execute(query).fetchall()}

@mueble.post("/mueble/create", tags=["Mueble"], response_model=Mueble)
def create_mueble(mueble: Mueble, request: Request):

    conn.commit()

    conn.execution_options(stream_results=True)
    try:
        now = str(datetime.now().day)+"/"+str(datetime.now().month) + \
            "/"+str(datetime.now().year)
        new_mueble = {"num_bien": mueble.num_bien, "descripcion": mueble.descripcion,
                      "marca": mueble.marca,
                      "partida_compra": mueble.partida_compra,
                      "fecha_ingreso": now,
                      "fecha_compra": mueble.fecha_compra,
                      "ingresado_por": mueble.ingresado_por,
                      "orden_pago": mueble.orden_pago,
                      "esTecnologia": mueble.esTecnologia,
                      "num_factura": mueble.num_factura,
                      "num_catalogo": mueble.num_catalogo,
                      "modelo": mueble.modelo,
                      "serial": mueble.serial,
                      "responsable": mueble.responsable,
                      "estado": mueble.estado,
                      "responsable": mueble.responsable,
                      "estado": mueble.estado,
                      "valor_inicial": mueble.valor_inicial,
                      "valor_actual": mueble.valor_actual,
                      "concepto_incorporacion": mueble.concepto_incorporacion,
                      "departamento": mueble.departamento}

        if mueble.esTecnologia == 1:
            result = conn.execute(
                mueblesTecnologia.insert().values(new_mueble))
            tabla_nombre = "mueblesTecnologia"
            tabla_obj = mueblesTecnologia
        else:
            result = conn.execute(muebles.insert().values(new_mueble))
            tabla_nombre = "muebles"
            tabla_obj = muebles
        
        conn.commit()

        nuevo_id = result.inserted_primary_key[0]
        AuditLogger.log_create(
            usuario=mueble.ingresado_por,
            modulo="MUEBLE",
            registro_id=nuevo_id,
            datos=new_mueble,
            descripcion=f"Se creó el mueble '{mueble.descripcion}' con número de bien {mueble.num_bien} en {tabla_nombre}",
            request=request
        )

        inserted_mueble = conn.execute(tabla_obj.select().where(tabla_obj.c.id == nuevo_id)).first()
        return inserted_mueble
    except SQLAlchemyError as e:
        error_str = str(e.__dict__['orig'])
        return JSONResponse(status_code=400, content={"message": "Error al insertar el mueble: " + error_str}, media_type="application/json")

@mueble.put("/mueble/{id}", tags=["Mueble"], response_model=MueblePOSTResponse)
def update_mueble(id: int, mueble: MuebleUpdate, request: Request, usuario: str):

    conn.commit()

    conn.execution_options(stream_results=True)
    responseTrue = {"data": True}
    responseFalse = {"data": False}

    mueble_anterior = conn.execute(muebles.select().where(muebles.c.id == id)).first()
    if mueble_anterior is None:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")
    
    datos_anteriores = dict(mueble_anterior._mapping)

    update_values = {}
    
    if mueble.orden_pago is not None:
        update_values['orden_pago'] = mueble.orden_pago
    if mueble.partida_compra is not None:
        update_values['partida_compra'] = mueble.partida_compra
    if mueble.num_factura is not None:
        update_values['num_factura'] = mueble.num_factura
    if mueble.num_catalogo is not None:
        update_values['num_catalogo'] = mueble.num_catalogo
    if mueble.modelo is not None:
        update_values['modelo'] = mueble.modelo
    if mueble.serial is not None:
        update_values['serial'] = mueble.serial
    if mueble.responsable is not None:
        update_values['responsable'] = mueble.responsable
    if mueble.estado is not None:
        update_values['estado'] = mueble.estado
    if mueble.marca is not None:
        update_values['marca'] = mueble.marca
    if mueble.esTecnologia is not None:
        update_values['esTecnologia'] = mueble.esTecnologia
    if mueble.descripcion is not None:
        update_values['descripcion'] = mueble.descripcion
    if mueble.valor_inicial is not None:
        update_values['valor_inicial'] = mueble.valor_inicial
    if mueble.valor_actual is not None:
        update_values['valor_actual'] = mueble.valor_actual
    if mueble.num_bien is not None:
        update_values['num_bien'] = mueble.num_bien
    if mueble.departamento is not None:
        update_values['departamento'] = mueble.departamento

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")
    
    result = conn.execute(muebles.update().values(**update_values).where(muebles.c.id == id))
    conn.commit()
    if result.rowcount == 0:
        return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

    datos_nuevos = {}
    for key, value in update_values.items():
        datos_nuevos[key] = str(value) if value is not None else value

    campos_cambiados = ", ".join(update_values.keys())
    num_bien_desc = update_values.get('num_bien', datos_anteriores.get('num_bien', 'N/A'))
    
    AuditLogger.log_update(
        usuario=usuario,
        modulo="MUEBLE",
        registro_id=id,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        descripcion=f"Se actualizó el mueble con ID {id} y número de bien {num_bien_desc}. Campos modificados: {campos_cambiados}",
        request=request
    )
    
    return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")

@mueble.get("/mueble/subirData", tags=["Mueble"], response_model=ErrorResponse)
def cargar_datos_excel():
    
    conn.commit()

    conn.execution_options(stream_results=True)
    
    try:
        
        ruta_excel = "C:/carga/muebles.xlsx"
        data = pd.read_excel(ruta_excel)
        tabla_destino = "muebles"

        if tabla_destino == "muebles":
            tabla = muebles
        elif tabla_destino == "mueblesDeleted":
            tabla = mueblesDeleted
        elif tabla_destino == "mueblesTecnologia":
            tabla = mueblesTecnologia

        columnas_tabla = [col.name for col in tabla.columns]
        print(data.columns)

        if 'id' not in data.columns:
            data['id'] = None  
        if 'partida_compra' not in data.columns:
            data['partida_compra'] = None  
        if 'num_factura' not in data.columns:
            data['num_factura'] = None  
        if 'esTecnologia' not in data.columns:
            data['esTecnologia'] = 0  
        if 'ingresado_por' not in data.columns:
            data['ingresado_por'] = "usuario_fijo"  

        if 'fecha_compra' in data.columns:
            data['fecha_compra'] = data['fecha_compra'].str.replace('-', '_', regex=False)
            
        data = data[columnas_tabla]  

        data.to_sql(tabla.name, con=conn, if_exists="append", index=False)
        return {"success": True, "message": f"Datos cargados exitosamente en la tabla {tabla_destino}."}

    except FileNotFoundError as e:
        return {"success": False, "message": "El archivo Excel no fue encontrado. {e}"}
    except KeyError as e:
        return {"success": False, "message": f"Error en las columnas: {e}"}
    except SQLAlchemyError as e:
        return {"success": False, "message": f"Error al insertar en la base de datos: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error inesperado: {str(e)}"}

@mueble.delete("/mueble/{id}", tags=["Mueble"], response_model=MueblePOSTResponse)
def delete_mueble(id: int, eliminado_por: str, num_oficio: int, concepto_desincorporacion: str, request: Request):

    conn.commit()

    conn.execution_options(stream_results=True)

    responseTrue = {"data": True}
    responseFalse = {"data": False}

    mueble = conn.execute(
        muebles.select().where(muebles.c.id == id)).first()

    if mueble is None:
        return JSONResponse(status_code=400, content={"message": "No se encontro el Mueble"}, media_type="application/json")

    delete_mueble = {"num_bien": mueble.num_bien, "descripcion": mueble.descripcion,
                     "partida_compra": mueble.partida_compra,
                     "fecha_ingreso": mueble.fecha_ingreso,
                     "fecha_compra": mueble.fecha_compra,
                     "marca": mueble.marca,
                     "num_catalogo": mueble.num_catalogo,
                     "modelo": mueble.modelo,
                     "serial": mueble.serial,
                     "responsable": mueble.responsable,
                     "estado": mueble.estado,
                     "ingresado_por": mueble.ingresado_por,
                     "orden_pago": mueble.orden_pago,
                     "esTecnologia": mueble.esTecnologia,
                     "num_factura": mueble.num_factura,
                     "valor_inicial": mueble.valor_inicial,
                     "valor_actual": mueble.valor_actual,
                     "departamento": mueble.departamento,
                     "num_oficio": num_oficio,
                     "concepto_incorporacion": mueble.concepto_incorporacion,
                     "concepto_desincorporacion": concepto_desincorporacion,
                     "eliminado_por": eliminado_por}
    
    try:
        resultDelete = conn.execute(mueblesDeleted.insert().values(delete_mueble))
    except IntegrityError as e:
        conn.rollback()
        return JSONResponse(status_code=400, content={"message": "Error de integridad: {e.orig}"}, media_type="application/json")

    if resultDelete.rowcount > 0:
        result = conn.execute(muebles.delete().where(muebles.c.id == id))

        if result.rowcount == 0:
            conn.commit()
            return Response(status_code=HTTP_404_NOT_FOUND, content=JSONEncoder(sort_keys=True).encode(responseFalse), media_type="application/json")

        datos_mueble = dict(mueble._mapping)
        AuditLogger.log_desincorporar(
            usuario=eliminado_por,
            modulo="MUEBLE",
            registro_id=id,
            datos=datos_mueble,
            num_oficio=num_oficio,
            descripcion=f"Se desincorporó el mueble '{mueble.descripcion}' con número de bien {mueble.num_bien} mediante oficio 
            request=request
        )
        
        conn.commit()
        return Response(status_code=HTTP_200_OK, content=JSONEncoder(sort_keys=True).encode(responseTrue), media_type="application/json")
    else:
        return JSONResponse(status_code=400, content={"message": "No se encontro el mueble"}, media_type="application/json")

@mueble.post("/mueble/import-csv", tags=["Mueble"], response_model=ImportMuebleResultado)
async def importar_muebles_desde_csv(
    file: UploadFile = File(...),
    ingresado_por: str = Form(...),
    esTecnologia: int = Form(default=0),
    request: Request = None
):

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
    muebles_a_crear = []
    num_bienes_en_csv = set()  

    now = f"{datetime.now().day}/{datetime.now().month}/{datetime.now().year}"

    next(csv_reader, None)

    for row_num, row in enumerate(csv_reader, start=2):  
        total_procesados += 1

        try:
            
            if len(row) < 14:
                errores.append({
                    "fila": row_num,
                    "codigo": row[1] if len(row) > 1 else "N/A",
                    "error": f"Fila incompleta: tiene {len(row)} columnas, se esperan al menos 14"
                })
                continue

            num_catalogo = row[0].strip() if row[0] else ""
            codigo = row[1].strip() if row[1] else None
            descripcion = row[2].strip() if row[2] else None
            orden_compra = row[4].strip() if row[4] else "0"
            fecha_compra = row[5].strip() if row[5] else ""
            
            marca = row[7].strip() if row[7] else ""
            modelo = row[8].strip() if row[8] else ""
            ubicacion = row[9].strip() if row[9] else None
            serial = row[10].strip() if row[10] else ""
            responsable = row[11].strip() if row[11] else ""
            valor = row[12].strip() if row[12] else None
            estado = row[13].strip() if row[13] else ""

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

            if not ubicacion:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": "Ubicación/Departamento es obligatorio"
                })
                continue

            if not valor:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": "Valor/Monto es obligatorio"
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

            try:
                orden_pago = int(orden_compra) if orden_compra and orden_compra != "0" else 0
            except ValueError:
                orden_pago = 0

            try:
                
                valor_limpio = valor.replace('"', '').strip()
                
                if '.' in valor_limpio and ',' in valor_limpio:
                    valor_limpio = valor_limpio.replace('.', '').replace(',', '.')
                
                elif ',' in valor_limpio:
                    valor_limpio = valor_limpio.replace(',', '.')
                monto = Decimal(valor_limpio) if valor_limpio else Decimal('0.00')
            except:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": f"El valor '{valor}' no es un número válido"
                })
                continue

            with engine.connect() as check_conn:
                existe_en_bd = check_conn.execute(
                    muebles.select().where(muebles.c.num_bien == num_bien)
                ).first()

            if existe_en_bd:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": f"El código de bien {num_bien} ya existe en la base de datos (ID: {existe_en_bd.id})"
                })
                continue

            if num_bien in num_bienes_en_csv:
                errores.append({
                    "fila": row_num,
                    "codigo": codigo,
                    "error": f"El código de bien {num_bien} está duplicado dentro del CSV"
                })
                continue

            num_bienes_en_csv.add(num_bien)

            muebles_a_crear.append({
                "fila": row_num,
                "num_catalogo": num_catalogo,
                "num_bien": num_bien,
                "descripcion": descripcion,
                "orden_pago": orden_pago,
                "partida_compra": 0,  
                "num_factura": 0,     
                "fecha_compra": fecha_compra if fecha_compra else "",
                "fecha_ingreso": now,  
                "marca": marca,
                "modelo": modelo,
                "serial": serial,
                "responsable": responsable,
                "departamento": ubicacion,
                "valor_inicial": monto,
                "valor_actual": monto,
                "estado": estado if estado else "D",  
                "esTecnologia": esTecnologia,
                "ingresado_por": ingresado_por
            })

        except Exception as e:
            errores.append({
                "fila": row_num,
                "codigo": row[1] if len(row) > 1 else "N/A",
                "error": str(e)
            })
            continue

    if len(errores) > 0:
        return ImportMuebleResultado(
            total_procesados=total_procesados,
            exitosos=0,
            fallidos=len(errores),
            errores=errores,
            muebles_creados=[]
        )

    muebles_creados = []

    with engine.connect() as connection:
        
        trans = connection.begin()

        try:
            for mueble_data in muebles_a_crear:
                fila = mueble_data.pop("fila")  

                result = connection.execute(muebles.insert().values(mueble_data))
                nuevo_id = result.lastrowid
                muebles_creados.append(nuevo_id)

                AuditLogger.log_create(
                    usuario=ingresado_por,
                    modulo="MUEBLE",
                    registro_id=nuevo_id,
                    datos=mueble_data,
                    descripcion=f"Mueble importado desde CSV (fila {fila}): {mueble_data['descripcion'][:50]}",
                    request=request
                )

            trans.commit()

            return ImportMuebleResultado(
                total_procesados=total_procesados,
                exitosos=len(muebles_creados),
                fallidos=0,
                errores=[],
                muebles_creados=muebles_creados
            )

        except Exception as e:
            
            trans.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Error durante la importación masiva",
                    "error": str(e),
                    "detalle": "Se canceló toda la operación. No se creó ningún mueble."
                }
            )

file_handler = FileHandler()

@mueble.post("/mueble/traspaso", tags=["Mueble"])
def traspaso_mueble(
    id_bien: int = Form(...),
    nuevo_departamento: str = Form(...),
    eliminado_por: str = Form(...),
    num_oficio: int = Form(...),
    archivo: UploadFile = File(...),
    request: Request = None
):

    conn.commit()
    
    try:
        
        mueble_original = conn.execute(muebles.select().where(muebles.c.id == id_bien)).first()
        
        if not mueble_original:
            return JSONResponse(status_code=404, content={"message": "Mueble no encontrado"}, media_type="application/json")
            
        mueble_dict = dict(mueble_original._mapping)

        delete_data = mueble_dict.copy()
        if 'id' in delete_data: delete_data.pop('id') 
        delete_data['num_oficio'] = num_oficio
        delete_data['concepto_desincorporacion'] = '51' 
        delete_data['eliminado_por'] = eliminado_por
        
        conn.execute(mueblesDeleted.insert().values(delete_data))

        conn.execute(muebles.delete().where(muebles.c.id == id_bien))

        new_mueble_data = mueble_dict.copy()
        if 'id' in new_mueble_data: new_mueble_data.pop('id') 
        new_mueble_data['departamento'] = nuevo_departamento
        new_mueble_data['concepto_incorporacion'] = '02'
        new_mueble_data['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y") 
        
        result_insert = conn.execute(muebles.insert().values(new_mueble_data))
        nuevo_id_bien = result_insert.lastrowid

        try:
            
            file_info = file_handler.save_file(
                file=archivo,
                bien_id=nuevo_id_bien,
                numero_bien=str(new_mueble_data['num_bien']),
                bien_tipo='mueble',
                subido_por=eliminado_por 
            )

            conn.execute(bien_archivos.insert().values(
                bien_id=nuevo_id_bien,
                numero_bien=str(new_mueble_data['num_bien']),
                bien_tipo='mueble',
                nombre_archivo=file_info['nombre_archivo'],
                nombre_original=file_info['nombre_original'],
                tipo_archivo=file_info['tipo_archivo'],
                extension=file_info['extension'],
                tamaño_bytes=file_info['tamaño_bytes'],
                ruta_archivo=file_info['ruta_archivo'],
                url_acceso=file_info['url_acceso'],
                thumbnail_path=file_info['thumbnail_path'],
                descripcion=f"Justificante de Traspaso (De {mueble_dict['departamento']} a {nuevo_departamento})",
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
            modulo="MUEBLE",
            registro_id=nuevo_id_bien,
            datos=new_mueble_data,
            descripcion=f"Traspaso de Mueble: {mueble_dict['departamento']} -> {nuevo_departamento}. (Anterior ID: {id_bien})",
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

@mueble.post("/mueble/reincorporar", tags=["Mueble"])
def reincorporar_mueble(
    id_historial: int = Form(...),
    concepto_incorporacion: str = Form(...),
    nuevo_departamento: str = Form(None),
    usuario_accion: str = Form(...),
    request: Request = None
):
    
    conn.commit()
    
    try:
        
        mueble_deleted = conn.execute(
            mueblesDeleted.select().where(mueblesDeleted.c.id == id_historial)
        ).first()
        
        if not mueble_deleted:
            return JSONResponse(status_code=404, content={"message": "Registro histórico no encontrado"}, media_type="application/json")

        datos_deleted = dict(mueble_deleted._mapping)

        nuevo_mueble = datos_deleted.copy()

        campos_a_eliminar = ['id', 'fecha_eliminacion', 'eliminado_por', 'concepto_desincorporacion', 'num_oficio_eliminacion']
        for campo in campos_a_eliminar:
            if campo in nuevo_mueble:
                del nuevo_mueble[campo]

        nuevo_mueble['fecha_ingreso'] = datetime.now().strftime("%d/%m/%Y")
        nuevo_mueble['concepto_incorporacion'] = concepto_incorporacion
        nuevo_mueble['ingresado_por'] = usuario_accion

        if nuevo_departamento:
            nuevo_mueble['departamento'] = nuevo_departamento

        try:
            result = conn.execute(muebles.insert().values(nuevo_mueble))
            nuevo_id = result.lastrowid

            AuditLogger.log_create(
                usuario=usuario_accion,
                modulo="MUEBLE",
                registro_id=nuevo_id,
                datos=nuevo_mueble,
                descripcion=f"Reincorporación de mueble desde historial ID {id_historial}. Concepto: {concepto_incorporacion}",
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
