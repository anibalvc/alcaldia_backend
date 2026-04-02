from fastapi import APIRouter, HTTPException, Query
from config.db import conn, engine
from models.comodato import comodatos
from models.mueble import muebles
from models.inmueble import inmuebles
from models.automovil import automoviles
from schemas.comodato import (
    ComodatoCreate,
    ComodatoUpdate,
    ComodatoDevolucion,
    ComodatoCancelar,
    ComodatoOut,
    ComodatoListItem
)
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import date, datetime

comodato = APIRouter()

def generar_numero_comodato(tipo_bien: str, año: int) -> str:
    
    prefijo_tipo = {
        'mueble': 'MUE',
        'inmueble': 'INM',
        'automovil': 'AUT'
    }

    query = select(comodatos.c.numero_comodato).where(
        and_(
            comodatos.c.tipo_bien == tipo_bien,
            comodatos.c.numero_comodato.like(f"COM-{prefijo_tipo[tipo_bien]}-{año}-%")
        )
    ).order_by(comodatos.c.numero_comodato.desc())
    
    resultado = conn.execute(query).first()
    
    if resultado:
        
        ultimo_numero = resultado[0]
        secuencia = int(ultimo_numero.split('-')[-1]) + 1
    else:
        secuencia = 1
    
    return f"COM-{prefijo_tipo[tipo_bien]}-{año}-{secuencia:03d}"

def obtener_info_bien(tipo_bien: str, bien_id: int):
    
    if tipo_bien == 'mueble':
        tabla = muebles
        query = select(tabla.c.num_bien, tabla.c.descripcion).where(tabla.c.id == bien_id)
    elif tipo_bien == 'inmueble':
        tabla = inmuebles
        query = select(tabla.c.num_bien, tabla.c.descripcion).where(tabla.c.id == bien_id)
    elif tipo_bien == 'automovil':
        tabla = automoviles
        query = select(tabla.c.num_bien, tabla.c.marca, tabla.c.modelo).where(tabla.c.id == bien_id)
    else:
        raise HTTPException(status_code=400, detail="Tipo de bien no válido")
    
    resultado = conn.execute(query).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail=f"Bien no encontrado: {tipo_bien} con ID {bien_id}")
    
    if tipo_bien == 'automovil':
        return resultado[0], f"{resultado[1]} {resultado[2]}"  
    else:
        return resultado[0], resultado[1]  

def verificar_comodato_activo(tipo_bien: str, bien_id: int) -> bool:
    
    query = select(comodatos).where(
        and_(
            comodatos.c.tipo_bien == tipo_bien,
            comodatos.c.bien_id == bien_id,
            comodatos.c.estado.in_(['activo', 'vencido'])
        )
    )
    resultado = conn.execute(query).first()
    return resultado is not None

@comodato.post("/comodatos", tags=["Comodatos"], response_model=ComodatoOut, status_code=201)
def crear_comodato(comodato_data: ComodatoCreate):
    
    try:
        conn.rollback()
    except:
        pass

    codigo_bien, descripcion_bien = obtener_info_bien(
        comodato_data.tipo_bien.value,
        comodato_data.bien_id
    )

    if verificar_comodato_activo(comodato_data.tipo_bien.value, comodato_data.bien_id):
        raise HTTPException(
            status_code=400,
            detail=f"El bien ya tiene un comodato activo"
        )

    año_actual = datetime.now().year
    numero_comodato = generar_numero_comodato(comodato_data.tipo_bien.value, año_actual)

    query = comodatos.insert().values(
        numero_comodato=numero_comodato,
        tipo_bien=comodato_data.tipo_bien.value,
        bien_id=comodato_data.bien_id,
        codigo_bien=codigo_bien,
        descripcion_bien=descripcion_bien,
        comodatario_nombre=comodato_data.comodatario_nombre,
        comodatario_cedula=comodato_data.comodatario_cedula,
        comodatario_telefono=comodato_data.comodatario_telefono,
        comodatario_email=comodato_data.comodatario_email,
        comodatario_direccion=comodato_data.comodatario_direccion,
        comodante_nombre=comodato_data.comodante_nombre,
        comodante_representante=comodato_data.comodante_representante,
        fecha_inicio=comodato_data.fecha_inicio,
        fecha_fin=comodato_data.fecha_fin,
        condiciones=comodato_data.condiciones,
        observaciones=comodato_data.observaciones,
        estado='activo',
        creado_por=comodato_data.creado_por,
        fecha_creacion=datetime.now()
    )
    
    resultado = conn.execute(query)
    conn.commit()

    comodato_id = resultado.lastrowid
    query_select = select(comodatos).where(comodatos.c.id == comodato_id)
    comodato_creado = conn.execute(query_select).first()
    
    return ComodatoOut(**dict(comodato_creado._mapping))

@comodato.get("/comodatos", tags=["Comodatos"], response_model=List[ComodatoListItem])
def listar_comodatos(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    tipo_bien: Optional[str] = Query(None, description="Filtrar por tipo de bien"),
    comodatario_cedula: Optional[str] = Query(None, description="Filtrar por cédula del comodatario"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(comodatos)

    if estado:
        query = query.where(comodatos.c.estado == estado)
    if tipo_bien:
        query = query.where(comodatos.c.tipo_bien == tipo_bien)
    if comodatario_cedula:
        query = query.where(comodatos.c.comodatario_cedula == comodatario_cedula)

    query = query.order_by(comodatos.c.fecha_creacion.desc())
    query = query.offset(skip).limit(limit)
    
    resultados = conn.execute(query).fetchall()
    
    return [ComodatoListItem(**dict(row._mapping)) for row in resultados]

@comodato.get("/comodatos/{comodato_id}", tags=["Comodatos"], response_model=ComodatoOut)
def obtener_comodato(comodato_id: int):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(comodatos).where(comodatos.c.id == comodato_id)
    resultado = conn.execute(query).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Comodato no encontrado")
    
    return ComodatoOut(**dict(resultado._mapping))

@comodato.put("/comodatos/{comodato_id}", tags=["Comodatos"], response_model=ComodatoOut)
def actualizar_comodato(comodato_id: int, comodato_data: ComodatoUpdate):
    
    try:
        conn.rollback()
    except:
        pass

    query_select = select(comodatos).where(comodatos.c.id == comodato_id)
    comodato_existente = conn.execute(query_select).first()
    
    if not comodato_existente:
        raise HTTPException(status_code=404, detail="Comodato no encontrado")

    if comodato_existente.estado in ['devuelto', 'cancelado']:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede actualizar un comodato {comodato_existente.estado}"
        )

    update_data = {}
    if comodato_data.comodatario_telefono is not None:
        update_data['comodatario_telefono'] = comodato_data.comodatario_telefono
    if comodato_data.comodatario_email is not None:
        update_data['comodatario_email'] = comodato_data.comodatario_email
    if comodato_data.comodatario_direccion is not None:
        update_data['comodatario_direccion'] = comodato_data.comodatario_direccion
    if comodato_data.fecha_fin is not None:
        update_data['fecha_fin'] = comodato_data.fecha_fin
    if comodato_data.condiciones is not None:
        update_data['condiciones'] = comodato_data.condiciones
    if comodato_data.observaciones is not None:
        update_data['observaciones'] = comodato_data.observaciones
    
    update_data['actualizado_por'] = comodato_data.actualizado_por
    update_data['fecha_actualizacion'] = datetime.now()
    
    query_update = comodatos.update().where(
        comodatos.c.id == comodato_id
    ).values(**update_data)
    
    conn.execute(query_update)
    conn.commit()

    comodato_actualizado = conn.execute(query_select).first()
    return ComodatoOut(**dict(comodato_actualizado._mapping))

@comodato.post("/comodatos/{comodato_id}/devolver", tags=["Comodatos"], response_model=ComodatoOut)
def registrar_devolucion(comodato_id: int, devolucion_data: ComodatoDevolucion):
    
    try:
        conn.rollback()
    except:
        pass

    query_select = select(comodatos).where(comodatos.c.id == comodato_id)
    comodato_existente = conn.execute(query_select).first()
    
    if not comodato_existente:
        raise HTTPException(status_code=404, detail="Comodato no encontrado")

    if comodato_existente.estado not in ['activo', 'vencido']:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede registrar devolución de un comodato {comodato_existente.estado}"
        )

    if devolucion_data.fecha_devolucion < comodato_existente.fecha_inicio:
        raise HTTPException(
            status_code=400,
            detail="La fecha de devolución no puede ser anterior a la fecha de inicio del comodato"
        )

    observaciones_actualizadas = comodato_existente.observaciones or ""
    if devolucion_data.observaciones:
        observaciones_actualizadas += f"\n[DEVOLUCIÓN] {devolucion_data.observaciones}"
    
    query_update = comodatos.update().where(
        comodatos.c.id == comodato_id
    ).values(
        fecha_devolucion=devolucion_data.fecha_devolucion,
        estado='devuelto',
        observaciones=observaciones_actualizadas,
        actualizado_por=devolucion_data.actualizado_por,
        fecha_actualizacion=datetime.now()
    )
    
    conn.execute(query_update)
    conn.commit()

    comodato_actualizado = conn.execute(query_select).first()
    return ComodatoOut(**dict(comodato_actualizado._mapping))

@comodato.delete("/comodatos/{comodato_id}", tags=["Comodatos"], response_model=ComodatoOut)
def cancelar_comodato(comodato_id: int, cancelacion_data: ComodatoCancelar):
    
    try:
        conn.rollback()
    except:
        pass

    query_select = select(comodatos).where(comodatos.c.id == comodato_id)
    comodato_existente = conn.execute(query_select).first()
    
    if not comodato_existente:
        raise HTTPException(status_code=404, detail="Comodato no encontrado")

    if comodato_existente.estado == 'devuelto':
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar un comodato ya devuelto"
        )

    observaciones_actualizadas = comodato_existente.observaciones or ""
    if cancelacion_data.motivo:
        observaciones_actualizadas += f"\n[CANCELACIÓN] {cancelacion_data.motivo}"
    
    query_update = comodatos.update().where(
        comodatos.c.id == comodato_id
    ).values(
        estado='cancelado',
        observaciones=observaciones_actualizadas,
        actualizado_por=cancelacion_data.actualizado_por,
        fecha_actualizacion=datetime.now()
    )
    
    conn.execute(query_update)
    conn.commit()

    comodato_actualizado = conn.execute(query_select).first()
    return ComodatoOut(**dict(comodato_actualizado._mapping))

@comodato.get("/comodatos/vencidos/list", tags=["Comodatos"], response_model=List[ComodatoListItem])
def listar_comodatos_vencidos():
    
    try:
        conn.rollback()
    except:
        pass
    
    hoy = date.today()
    
    query = select(comodatos).where(
        and_(
            comodatos.c.estado == 'activo',
            comodatos.c.fecha_fin < hoy
        )
    ).order_by(comodatos.c.fecha_fin.asc())
    
    resultados = conn.execute(query).fetchall()
    
    return [ComodatoListItem(**dict(row._mapping)) for row in resultados]

@comodato.get("/comodatos/bien/{tipo_bien}/{bien_id}", tags=["Comodatos"], response_model=List[ComodatoListItem])
def obtener_historial_bien(tipo_bien: str, bien_id: int):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(comodatos).where(
        and_(
            comodatos.c.tipo_bien == tipo_bien,
            comodatos.c.bien_id == bien_id
        )
    ).order_by(comodatos.c.fecha_creacion.desc())
    
    resultados = conn.execute(query).fetchall()
    
    return [ComodatoListItem(**dict(row._mapping)) for row in resultados]
