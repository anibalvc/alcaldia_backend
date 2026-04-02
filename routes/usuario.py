from typing import List, Union
from fastapi import APIRouter, Response
from config.db import conn
from models.usuario import usuarios
from schemas.usuario import Usuario, UsuarioData, UsuarioOut, Login, UsuarioUpdate
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse

from cryptography.fernet import Fernet

usuario = APIRouter()

@usuario.get("/usuario", tags=["Usuario"], response_model=UsuarioData)
def get_usuarios(usuario: str | None = None, departamento: str | None = None, rol: str | None = None):

    if usuario:
        return {"data": conn.execute(usuarios.select().where(usuarios.c.usuario == usuario)).fetchall()}
    if departamento:
        return {"data": conn.execute(usuarios.select().where(usuarios.c.departamento == departamento)).fetchall()}
    if rol:
        return {"data": conn.execute(usuarios.select().where(usuarios.c.rol == rol)).fetchall()}

    return {"data": conn.execute(usuarios.select()).fetchall()}

@usuario.post("/usuario/login", tags=["Usuario"], response_model=List[Usuario] | Usuario)
def login(login: Login):

    result = conn.execute(usuarios.select().where(
        usuarios.c.usuario == login.usuario, usuarios.c.clave == login.clave)).first()
    if not result:
        return JSONResponse(status_code=400, content={"message": "No se encontro el usuario"}, media_type="application/json")

    return result

@usuario.post("/usuario", tags=["Usuario"], response_model=UsuarioOut)
def create_user(usuario: Usuario, ingresadoPor: str):

    new_usuario = {"nombre": usuario.nombre, "departamento": usuario.departamento,
                   "rol": usuario.rol, "ingresado_por": ingresadoPor, "usuario": usuario.usuario, "clave": usuario.clave}

    if conn.execute(usuarios.select().where(usuarios.c.usuario == new_usuario["usuario"])).rowcount > 0:
        return JSONResponse(status_code=400, content={"message": "Usuario duplicado"}, media_type="application/json")

    result = conn.execute(usuarios.insert().values(new_usuario))
    conn.commit()
    return conn.execute(usuarios.select().where(usuarios.c.id == result.lastrowid)).first()

@usuario.put("/usuario/{id}", tags=["Usuario"], response_model=bool)
def update_user(id: int, user: UsuarioUpdate):

    usuario_anterior = conn.execute(usuarios.select().where(usuarios.c.id == id)).first()
    if usuario_anterior is None:
        return JSONResponse(status_code=404, content={"message": "Usuario no encontrado"}, media_type="application/json")

    if user.usuario is not None and user.usuario != usuario_anterior.usuario:
        if conn.execute(usuarios.select().where(usuarios.c.usuario == user.usuario)).rowcount > 0:
            return JSONResponse(status_code=400, content={"message": "Usuario duplicado"}, media_type="application/json")

    update_values = {}
    
    if user.usuario is not None:
        update_values['usuario'] = user.usuario
    if user.clave is not None:
        update_values['clave'] = user.clave
    if user.nombre is not None:
        update_values['nombre'] = user.nombre
    if user.departamento is not None:
        update_values['departamento'] = user.departamento
    if user.rol is not None:
        update_values['rol'] = user.rol

    if not update_values:
        return JSONResponse(status_code=400, content={"message": "No se enviaron campos para actualizar"}, media_type="application/json")

    result = conn.execute(usuarios.update().values(**update_values).where(usuarios.c.id == id))

    if result.rowcount == 0:
        conn.commit()
        return Response(status_code=HTTP_404_NOT_FOUND, content="false".encode(), media_type="application/json")
    
    conn.commit()
    return Response(status_code=HTTP_200_OK, content="true".encode(), media_type="application/json")

@usuario.delete("/usuario/{id}", tags=["Usuario"], response_model=bool)
def delete_user(id: int):

    result = conn.execute(usuarios.delete().where(usuarios.c.id == id))

    if result.rowcount == 0:
        conn.commit()
        return Response(status_code=HTTP_404_NOT_FOUND, content="false".encode(), media_type="application/json")

    return Response(status_code=HTTP_200_OK, content="true".encode(), media_type="application/json")
