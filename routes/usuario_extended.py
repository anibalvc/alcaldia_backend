from typing import Optional
import json
from fastapi import APIRouter, Response, Query, Depends
from sqlalchemy.engine import Connection
from config.db import get_db_connection
from models.usuario_extended import usuarios_extended
from models.departamento import departamentos
from schemas.usuario_extended import (
    UsuarioExtendedCreate,
    UsuarioExtendedUpdate,
    UsuarioExtendedOut,
    UsuarioExtendedWithDepartamento,
    UsuarioExtendedData,
    EnrichSessionRequest,
    SessionExtendedData,
    RegistroRapidoRequest
)
from schemas.departamento import DepartamentoSimple
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from fastapi.responses import JSONResponse
from sqlalchemy import select, join

usuario_extended_router = APIRouter()

@usuario_extended_router.get("/usuarios-extended", tags=["Usuarios Extended"], response_model=UsuarioExtendedData)
def get_usuarios_extended(
    authy_user_id: Optional[str] = Query(None, description="Filtrar por ID de Authy"),
    email: Optional[str] = Query(None, description="Filtrar por email"),
    departamento_id: Optional[int] = Query(None, description="Filtrar por departamento"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado"),
    solo_activos: bool = Query(True, description="Mostrar solo usuarios activos"),
    conn: Connection = Depends(get_db_connection)
):
    
    try:
        query = usuarios_extended.select()

        if authy_user_id:
            query = query.where(usuarios_extended.c.authy_user_id == authy_user_id)

        if email:
            query = query.where(usuarios_extended.c.email.contains(email))

        if departamento_id:
            query = query.where(usuarios_extended.c.departamento_id == departamento_id)

        if activo is not None:
            query = query.where(usuarios_extended.c.activo == activo)
        elif solo_activos:
            query = query.where(usuarios_extended.c.activo == True)

        query = query.order_by(usuarios_extended.c.email)

        result = conn.execute(query).fetchall()
        return {"data": result}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener usuarios extendidos: {str(e)}"}
        )

@usuario_extended_router.get(
    "/usuarios-extended/{id}",
    tags=["Usuarios Extended"],
    response_model=UsuarioExtendedWithDepartamento
)
def get_usuario_extended_by_id(id: int, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        query = select(
            usuarios_extended.c.id,
            usuarios_extended.c.authy_user_id,
            usuarios_extended.c.email,
            usuarios_extended.c.departamento_id,
            usuarios_extended.c.cargo,
            usuarios_extended.c.telefono,
            usuarios_extended.c.extension,
            usuarios_extended.c.preferencias,
            usuarios_extended.c.activo,
            usuarios_extended.c.notas,
            usuarios_extended.c.fecha_creacion,
            usuarios_extended.c.fecha_actualizacion,
            departamentos.c.id.label('dept_id'),
            departamentos.c.codigo.label('dept_codigo'),
            departamentos.c.nombre.label('dept_nombre'),
            departamentos.c.activo.label('dept_activo'),
        ).select_from(
            usuarios_extended.join(
                departamentos,
                usuarios_extended.c.departamento_id == departamentos.c.id
            )
        ).where(usuarios_extended.c.id == id)

        result = conn.execute(query).first()

        if not result:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Usuario extendido no encontrado"}
            )

        return {
            "id": result.id,
            "authy_user_id": result.authy_user_id,
            "email": result.email,
            "departamento_id": result.departamento_id,
            "cargo": result.cargo,
            "telefono": result.telefono,
            "extension": result.extension,
            "preferencias": result.preferencias,
            "activo": result.activo,
            "notas": result.notas,
            "fecha_creacion": result.fecha_creacion,
            "fecha_actualizacion": result.fecha_actualizacion,
            "departamento": {
                "id": result.dept_id,
                "codigo": result.dept_codigo,
                "nombre": result.dept_nombre,
                "activo": result.dept_activo,
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener usuario extendido: {str(e)}"}
        )

@usuario_extended_router.get(
    "/usuarios-extended/by-authy-id/{authy_user_id}",
    tags=["Usuarios Extended"],
    response_model=UsuarioExtendedWithDepartamento
)
def get_usuario_extended_by_authy_id(authy_user_id: str, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        query = select(
            usuarios_extended.c.id,
            usuarios_extended.c.authy_user_id,
            usuarios_extended.c.email,
            usuarios_extended.c.departamento_id,
            usuarios_extended.c.cargo,
            usuarios_extended.c.telefono,
            usuarios_extended.c.extension,
            usuarios_extended.c.preferencias,
            usuarios_extended.c.activo,
            usuarios_extended.c.notas,
            usuarios_extended.c.fecha_creacion,
            usuarios_extended.c.fecha_actualizacion,
            departamentos.c.id.label('dept_id'),
            departamentos.c.codigo.label('dept_codigo'),
            departamentos.c.nombre.label('dept_nombre'),
            departamentos.c.activo.label('dept_activo'),
        ).select_from(
            usuarios_extended.join(
                departamentos,
                usuarios_extended.c.departamento_id == departamentos.c.id
            )
        ).where(usuarios_extended.c.authy_user_id == authy_user_id)

        result = conn.execute(query).first()

        if not result:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": f"Usuario con authy_user_id '{authy_user_id}' no encontrado"}
            )

        return {
            "id": result.id,
            "authy_user_id": result.authy_user_id,
            "email": result.email,
            "departamento_id": result.departamento_id,
            "cargo": result.cargo,
            "telefono": result.telefono,
            "extension": result.extension,
            "preferencias": result.preferencias,
            "activo": result.activo,
            "notas": result.notas,
            "fecha_creacion": result.fecha_creacion,
            "fecha_actualizacion": result.fecha_actualizacion,
            "departamento": {
                "id": result.dept_id,
                "codigo": result.dept_codigo,
                "nombre": result.dept_nombre,
                "activo": result.dept_activo,
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al obtener usuario extendido: {str(e)}"}
        )

@usuario_extended_router.post("/usuarios-extended", tags=["Usuarios Extended"], response_model=UsuarioExtendedOut)
def create_usuario_extended(usuario: UsuarioExtendedCreate, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing_authy = conn.execute(
            usuarios_extended.select().where(
                usuarios_extended.c.authy_user_id == usuario.authy_user_id
            )
        ).first()

        if existing_authy:
            return JSONResponse(
                status_code=400,
                content={"message": f"Ya existe un usuario extendido con el authy_user_id '{usuario.authy_user_id}'"}
            )

        dept_exists = conn.execute(
            departamentos.select().where(departamentos.c.id == usuario.departamento_id)
        ).first()

        if not dept_exists:
            return JSONResponse(
                status_code=400,
                content={"message": f"El departamento con ID {usuario.departamento_id} no existe"}
            )

        new_usuario = {
            "authy_user_id": usuario.authy_user_id,
            "email": usuario.email,
            "departamento_id": usuario.departamento_id,
            "cargo": usuario.cargo,
            "telefono": usuario.telefono,
            "extension": usuario.extension,
            "preferencias": usuario.preferencias,
            "activo": usuario.activo,
            "notas": usuario.notas,
            "creado_por": usuario.creado_por,
        }

        result = conn.execute(usuarios_extended.insert().values(new_usuario))

        created = conn.execute(
            usuarios_extended.select().where(usuarios_extended.c.id == result.lastrowid)
        ).first()

        return created

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al crear usuario extendido: {str(e)}"}
        )

@usuario_extended_router.put("/usuarios-extended/{id}", tags=["Usuarios Extended"], response_model=bool)
def update_usuario_extended(id: int, usuario: UsuarioExtendedUpdate, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing = conn.execute(
            usuarios_extended.select().where(usuarios_extended.c.id == id)
        ).first()

        if not existing:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"message": "Usuario extendido no encontrado"}
            )

        update_values = {}

        if usuario.email is not None:
            update_values['email'] = usuario.email

        if usuario.departamento_id is not None:
            
            dept_exists = conn.execute(
                departamentos.select().where(departamentos.c.id == usuario.departamento_id)
            ).first()
            if not dept_exists:
                return JSONResponse(
                    status_code=400,
                    content={"message": f"El departamento con ID {usuario.departamento_id} no existe"}
                )
            update_values['departamento_id'] = usuario.departamento_id

        if usuario.cargo is not None:
            update_values['cargo'] = usuario.cargo
        if usuario.telefono is not None:
            update_values['telefono'] = usuario.telefono
        if usuario.extension is not None:
            update_values['extension'] = usuario.extension
        if usuario.preferencias is not None:
            update_values['preferencias'] = usuario.preferencias
        if usuario.activo is not None:
            update_values['activo'] = usuario.activo
        if usuario.notas is not None:
            update_values['notas'] = usuario.notas
        if usuario.actualizado_por is not None:
            update_values['actualizado_por'] = usuario.actualizado_por

        if not update_values:
            return JSONResponse(
                status_code=400,
                content={"message": "No se enviaron campos para actualizar"}
            )

        result = conn.execute(
            usuarios_extended.update().values(**update_values).where(usuarios_extended.c.id == id)
        )

        if result.rowcount == 0:
            return Response(
                status_code=HTTP_404_NOT_FOUND,
                content="false".encode(),
                media_type="application/json"
            )

        return Response(
            status_code=HTTP_200_OK,
            content="true".encode(),
            media_type="application/json"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al actualizar usuario extendido: {str(e)}"}
        )

@usuario_extended_router.delete("/usuarios-extended/{id}", tags=["Usuarios Extended"], response_model=bool)
def delete_usuario_extended(id: int, conn: Connection = Depends(get_db_connection)):
    
    try:
        result = conn.execute(
            usuarios_extended.delete().where(usuarios_extended.c.id == id)
        )

        if result.rowcount == 0:
            return Response(
                status_code=HTTP_404_NOT_FOUND,
                content="false".encode(),
                media_type="application/json"
            )

        return Response(
            status_code=HTTP_200_OK,
            content="true".encode(),
            media_type="application/json"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al eliminar usuario extendido: {str(e)}"}
        )

@usuario_extended_router.post("/auth/enrich-session", tags=["Usuarios Extended"], response_model=SessionExtendedData)
def enrich_session(request: EnrichSessionRequest, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        query = select(
            usuarios_extended.c.id,
            usuarios_extended.c.authy_user_id,
            usuarios_extended.c.email,
            usuarios_extended.c.departamento_id,
            usuarios_extended.c.cargo,
            usuarios_extended.c.telefono,
            usuarios_extended.c.extension,
            usuarios_extended.c.preferencias,
            usuarios_extended.c.activo,
            departamentos.c.id.label('dept_id'),
            departamentos.c.codigo.label('dept_codigo'),
            departamentos.c.nombre.label('dept_nombre'),
        ).select_from(
            usuarios_extended.join(
                departamentos,
                usuarios_extended.c.departamento_id == departamentos.c.id
            )
        ).where(
            usuarios_extended.c.authy_user_id == request.authy_user_id
        )

        result = conn.execute(query).first()

        if not result:
            
            return SessionExtendedData(
                usuario_registrado=False,
                mensaje="Usuario no registrado en el sistema local. Contacte al administrador para asignar departamento."
            )

        preferencias_dict = None
        if result.preferencias:
            try:
                preferencias_dict = json.loads(result.preferencias)
            except:
                preferencias_dict = None

        return SessionExtendedData(
            usuario_registrado=True,
            departamento_codigo=result.dept_codigo,
            departamento_nombre=result.dept_nombre,
            departamento_id=result.dept_id,
            cargo=result.cargo,
            telefono=result.telefono,
            extension=result.extension,
            preferencias=preferencias_dict,
            mensaje="Datos locales cargados exitosamente"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error al enriquecer sesión: {str(e)}"}
        )

@usuario_extended_router.post("/usuarios-extended/registro-rapido", tags=["Usuarios Extended"], response_model=UsuarioExtendedOut)
def registro_rapido(request: RegistroRapidoRequest, conn: Connection = Depends(get_db_connection)):
    
    try:
        
        existing = conn.execute(
            usuarios_extended.select().where(
                usuarios_extended.c.authy_user_id == request.authy_user_id
            )
        ).first()

        if existing:
            return JSONResponse(
                status_code=400,
                content={"message": "El usuario ya está registrado"}
            )

        dept_exists = conn.execute(
            departamentos.select().where(departamentos.c.id == request.departamento_id)
        ).first()

        if not dept_exists:
            return JSONResponse(
                status_code=400,
                content={"message": f"El departamento con ID {request.departamento_id} no existe"}
            )

        new_usuario = {
            "authy_user_id": request.authy_user_id,
            "email": request.email,
            "departamento_id": request.departamento_id,
            "cargo": request.cargo,
            "activo": True,
            "creado_por": request.creado_por,
        }

        result = conn.execute(usuarios_extended.insert().values(new_usuario))

        created = conn.execute(
            usuarios_extended.select().where(usuarios_extended.c.id == result.lastrowid)
        ).first()

        return created

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error en registro rápido: {str(e)}"}
        )
