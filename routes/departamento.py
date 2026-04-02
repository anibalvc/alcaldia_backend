from typing import Optional
from fastapi import APIRouter, Response, Query, Depends
from sqlalchemy.engine import Connection
from config.db import get_db_connection
from models.departamento import departamentos
from schemas.departamento import (
    DepartamentoCreate,
    DepartamentoUpdate,
    DepartamentoOut,
    DepartamentoSimple,
    DepartamentoData
)
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from fastapi.responses import JSONResponse
from utils.logger import AuditLogger

departamento_router = APIRouter()

@departamento_router.get("/departamentos", tags=["Departamentos"], response_model=DepartamentoData)
def get_departamentos(
    codigo: Optional[int] = Query(None, description="Filtrar por código numérico"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado"),
    solo_activos: bool = Query(True, description="Mostrar solo departamentos activos"),
    conn: Connection = Depends(get_db_connection)
):
    
    try:
        query = departamentos.select()

        if codigo:
            query = query.where(departamentos.c.codigo == codigo)

        if nombre:
            query = query.where(departamentos.c.nombre.contains(nombre))

        if activo is not None:
            query = query.where(departamentos.c.activo == activo)
        elif solo_activos:
            query = query.where(departamentos.c.activo == True)

        query = query.order_by(departamentos.c.nombre)

        result = conn.execute(query).fetchall()
        return {"data": result}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener departamentos: {str(e)}"}
        )

@departamento_router.get("/departamentos/{id}", tags=["Departamentos"], response_model=DepartamentoOut)
def get_departamento_by_id(id: int, conn: Connection = Depends(get_db_connection)):
    
    try:
        result = conn.execute(
            departamentos.select().where(departamentos.c.id == id)
        ).first()

        if not result:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Departamento no encontrado"}
            )

        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener departamento: {str(e)}"}
        )

@departamento_router.get("/departamentos/codigo/{codigo}", tags=["Departamentos"], response_model=DepartamentoOut)
def get_departamento_by_codigo(codigo: int, conn: Connection = Depends(get_db_connection)):
    
    try:
        result = conn.execute(
            departamentos.select().where(departamentos.c.codigo == codigo)
        ).first()

        if not result:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Departamento no encontrado"}
            )

        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener departamento: {str(e)}"}
        )

@departamento_router.post("/departamentos", tags=["Departamentos"], response_model=DepartamentoOut)
def create_departamento(departamento: DepartamentoCreate, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing_codigo = conn.execute(
            departamentos.select().where(departamentos.c.codigo == departamento.codigo)
        ).first()

        if existing_codigo:
            return JSONResponse(
                status_code=400,
                content={"message": f"Ya existe un departamento con el código '{departamento.codigo}'"}
            )

        existing_nombre = conn.execute(
            departamentos.select().where(departamentos.c.nombre == departamento.nombre)
        ).first()

        if existing_nombre:
            return JSONResponse(
                status_code=400,
                content={"message": f"Ya existe un departamento con el nombre '{departamento.nombre}'"}
            )

        new_departamento = {
            "codigo": departamento.codigo,
            "nombre": departamento.nombre,
            "descripcion": departamento.descripcion,
            "responsable": departamento.responsable,
            "director": departamento.director,
            "ubicacion": departamento.ubicacion,
            "telefono": departamento.telefono,
            "email": departamento.email,
            "activo": departamento.activo,
            "creado_por": departamento.creado_por,
        }

        result = conn.execute(departamentos.insert().values(new_departamento))

        created = conn.execute(
            departamentos.select().where(departamentos.c.id == result.lastrowid)
        ).first()

        AuditLogger.log_action(
            usuario=departamento.creado_por,
            accion="Creación de Departamento",
            modulo="DEPARTAMENTO",
            registro_id=result.lastrowid,
            descripcion=f"Se creó el departamento '{departamento.nombre}' ({departamento.codigo})"
        )

        return created

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al crear departamento: {str(e)}"}
        )

@departamento_router.put("/departamentos/{id}", tags=["Departamentos"], response_model=bool)
def update_departamento(id: int, departamento: DepartamentoUpdate, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing = conn.execute(
            departamentos.select().where(departamentos.c.id == id)
        ).first()

        if not existing:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Departamento no encontrado"}
            )

        update_values = {}

        if departamento.codigo is not None:
            
            if departamento.codigo != existing.codigo:
                existing_codigo = conn.execute(
                    departamentos.select().where(departamentos.c.codigo == departamento.codigo)
                ).first()
                if existing_codigo:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"El código '{departamento.codigo}' ya está en uso"}
                    )
            update_values['codigo'] = departamento.codigo

        if departamento.nombre is not None:
            
            if departamento.nombre != existing.nombre:
                existing_nombre = conn.execute(
                    departamentos.select().where(departamentos.c.nombre == departamento.nombre)
                ).first()
                if existing_nombre:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"El nombre '{departamento.nombre}' ya está en uso"}
                    )
            update_values['nombre'] = departamento.nombre

        if departamento.descripcion is not None:
            update_values['descripcion'] = departamento.descripcion
        if departamento.responsable is not None:
            update_values['responsable'] = departamento.responsable
        if departamento.director is not None:
            update_values['director'] = departamento.director
        if departamento.ubicacion is not None:
            update_values['ubicacion'] = departamento.ubicacion
        if departamento.telefono is not None:
            update_values['telefono'] = departamento.telefono
        if departamento.email is not None:
            update_values['email'] = departamento.email
        if departamento.activo is not None:
            update_values['activo'] = departamento.activo
        if departamento.actualizado_por is not None:
            update_values['actualizado_por'] = departamento.actualizado_por

        if not update_values:
            return JSONResponse(
                status_code=400,
                content={"message": "No se enviaron campos para actualizar"}
            )

        result = conn.execute(
            departamentos.update().values(**update_values).where(departamentos.c.id == id)
        )

        if result.rowcount == 0:
            return Response(
                status_code=HTTP_404_NOT_FOUND,
                content="false".encode(),
                media_type="application/json"
            )

        AuditLogger.log_action(
            usuario=departamento.actualizado_por or "Sistema",
            accion="Actualización de Departamento",
            modulo="DEPARTAMENTO",
            registro_id=id,
            descripcion=f"Se actualizó el departamento ID {id}"
        )

        return Response(
            status_code=HTTP_200_OK,
            content="true".encode(),
            media_type="application/json"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al actualizar departamento: {str(e)}"}
        )

@departamento_router.delete("/departamentos/{id}", tags=["Departamentos"], response_model=bool)
def delete_departamento(id: int, eliminado_por: str = "Sistema", conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing = conn.execute(
            departamentos.select().where(departamentos.c.id == id)
        ).first()

        if not existing:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Departamento no encontrado"}
            )

        result = conn.execute(
            departamentos.delete().where(departamentos.c.id == id)
        )

        if result.rowcount == 0:
            return Response(
                status_code=HTTP_404_NOT_FOUND,
                content="false".encode(),
                media_type="application/json"
            )

        AuditLogger.log_action(
            usuario=eliminado_por,
            accion="Eliminación de Departamento",
            modulo="DEPARTAMENTO",
            registro_id=id,
            descripcion=f"Se eliminó permanentemente el departamento '{existing.nombre}'"
        )

        return Response(
            status_code=HTTP_200_OK,
            content="true".encode(),
            media_type="application/json"
        )

    except Exception as e:
        
        if "foreign key constraint" in str(e).lower():
            return JSONResponse(
                status_code=400,
                content={"message": "No se puede eliminar el departamento porque tiene usuarios asociados"}
            )
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al eliminar departamento: {str(e)}"}
        )
