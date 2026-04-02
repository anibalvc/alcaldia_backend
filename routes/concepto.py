from fastapi import APIRouter, HTTPException, Query
from config.db import conn
from models.concepto import conceptos_movimiento
from schemas.concepto import ConceptoCreate, ConceptoUpdate, ConceptoOut
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

concepto_router = APIRouter()

@concepto_router.get("/conceptos", tags=["Conceptos"], response_model=List[ConceptoOut])
def listar_conceptos(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ingreso/egreso/ambos)"),
    estado: Optional[bool] = Query(None, description="Filtrar por estado (true=activo, false=inactivo)")
):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(conceptos_movimiento)
    
    if tipo:
        query = query.where(conceptos_movimiento.c.tipo == tipo)
    
    if estado is not None:
        query = query.where(conceptos_movimiento.c.estado == estado)

    query = query.order_by(conceptos_movimiento.c.codigo)
    
    resultados = conn.execute(query).fetchall()
    
    return [ConceptoOut(**dict(row._mapping)) for row in resultados]

@concepto_router.post("/conceptos", tags=["Conceptos"], response_model=ConceptoOut, status_code=201)
def crear_concepto(concepto_data: ConceptoCreate):
    
    try:
        conn.rollback()
    except:
        pass

    query_check = select(conceptos_movimiento).where(conceptos_movimiento.c.codigo == concepto_data.codigo)
    if conn.execute(query_check).first():
        raise HTTPException(status_code=400, detail="El código de concepto ya existe")
    
    query = conceptos_movimiento.insert().values(
        codigo=concepto_data.codigo,
        descripcion=concepto_data.descripcion,
        tipo=concepto_data.tipo.value,
        estado=True,
        creado_por=concepto_data.creado_por,
        fecha_creacion=datetime.now()
    )
    
    resultado = conn.execute(query)
    conn.commit()

    concepto_id = resultado.lastrowid
    query_select = select(conceptos_movimiento).where(conceptos_movimiento.c.id == concepto_id)
    concepto_creado = conn.execute(query_select).first()
    
    return ConceptoOut(**dict(concepto_creado._mapping))

@concepto_router.get("/conceptos/{concepto_id}", tags=["Conceptos"], response_model=ConceptoOut)
def obtener_concepto(concepto_id: int):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(conceptos_movimiento).where(conceptos_movimiento.c.id == concepto_id)
    resultado = conn.execute(query).first()
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    
    return ConceptoOut(**dict(resultado._mapping))

@concepto_router.put("/conceptos/{concepto_id}", tags=["Conceptos"], response_model=ConceptoOut)
def actualizar_concepto(concepto_id: int, concepto_data: ConceptoUpdate):
    
    try:
        conn.rollback()
    except:
        pass

    query_check = select(conceptos_movimiento).where(conceptos_movimiento.c.id == concepto_id)
    if not conn.execute(query_check).first():
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    if concepto_data.codigo:
        query_code = select(conceptos_movimiento).where(
            (conceptos_movimiento.c.codigo == concepto_data.codigo) & 
            (conceptos_movimiento.c.id != concepto_id)
        )
        if conn.execute(query_code).first():
            raise HTTPException(status_code=400, detail="El código ya está en uso por otro concepto")
    
    update_data = {}
    if concepto_data.codigo: update_data['codigo'] = concepto_data.codigo
    if concepto_data.descripcion: update_data['descripcion'] = concepto_data.descripcion
    if concepto_data.tipo: update_data['tipo'] = concepto_data.tipo.value
    if concepto_data.estado is not None: update_data['estado'] = concepto_data.estado
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    query = conceptos_movimiento.update().where(conceptos_movimiento.c.id == concepto_id).values(**update_data)
    conn.execute(query)
    conn.commit()
    
    query_select = select(conceptos_movimiento).where(conceptos_movimiento.c.id == concepto_id)
    concepto_actualizado = conn.execute(query_select).first()
    
    return ConceptoOut(**dict(concepto_actualizado._mapping))

@concepto_router.delete("/conceptos/{concepto_id}", tags=["Conceptos"])
def eliminar_concepto(concepto_id: int):
    
    try:
        conn.rollback()
    except:
        pass

    query_check = select(conceptos_movimiento).where(conceptos_movimiento.c.id == concepto_id)
    if not conn.execute(query_check).first():
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    query = conceptos_movimiento.update().where(conceptos_movimiento.c.id == concepto_id).values(estado=False)
    conn.execute(query)
    conn.commit()
    
    return {"message": "Concepto desactivado correctamente"}
