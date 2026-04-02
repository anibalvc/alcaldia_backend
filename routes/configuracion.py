from fastapi import APIRouter, HTTPException, Query
from config.db import conn
from models.configuracion import configuraciones
from schemas.configuracion import ConfiguracionCreate, ConfiguracionUpdate, ConfiguracionOut
from sqlalchemy import select
from typing import List, Optional

configuracion_router = APIRouter()

@configuracion_router.get("/configuraciones", tags=["Configuración"], response_model=List[ConfiguracionOut])
def listar_configuraciones(grupo: Optional[str] = None):
    
    try:
        conn.rollback()
    except:
        pass
    
    query = select(configuraciones)
    if grupo:
        query = query.where(configuraciones.c.grupo == grupo)
    
    resultados = conn.execute(query).fetchall()
    return [ConfiguracionOut(**dict(row._mapping)) for row in resultados]

@configuracion_router.post("/configuraciones", tags=["Configuración"], response_model=ConfiguracionOut)
def crear_configuracion(config: ConfiguracionCreate):
    
    try:
        conn.rollback()
    except:
        pass

    query_check = select(configuraciones).where(configuraciones.c.clave == config.clave)
    if conn.execute(query_check).first():
        raise HTTPException(status_code=400, detail="La clave de configuración ya existe")
    
    query = configuraciones.insert().values(
        clave=config.clave,
        valor=config.valor,
        grupo=config.grupo,
        descripcion=config.descripcion
    )
    conn.execute(query)
    conn.commit()
    
    return config

@configuracion_router.put("/configuraciones/{clave}", tags=["Configuración"], response_model=ConfiguracionOut)
def actualizar_configuracion(clave: str, config: ConfiguracionUpdate):
    
    try:
        conn.rollback()
    except:
        pass

    query_check = select(configuraciones).where(configuraciones.c.clave == clave)
    actual = conn.execute(query_check).first()
    
    if not actual:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    update_data = {}
    if config.valor is not None: update_data['valor'] = config.valor
    if config.grupo is not None: update_data['grupo'] = config.grupo
    if config.descripcion is not None: update_data['descripcion'] = config.descripcion
    
    if update_data:
        query = configuraciones.update().where(configuraciones.c.clave == clave).values(**update_data)
        conn.execute(query)
        conn.commit()

    updated = conn.execute(query_check).first()
    return ConfiguracionOut(**dict(updated._mapping))

@configuracion_router.delete("/configuraciones/{clave}", tags=["Configuración"])
def eliminar_configuracion(clave: str):
    
    try:
        conn.rollback()
    except:
        pass
        
    query = configuraciones.delete().where(configuraciones.c.clave == clave)
    result = conn.execute(query)
    conn.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
    return {"message": "Configuración eliminada"}
