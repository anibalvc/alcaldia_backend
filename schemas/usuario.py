from pydantic import BaseModel
from typing import List, Optional, Union

class Usuario(BaseModel):
    id: Optional[int]
    usuario: str
    clave: str
    nombre: str
    departamento: str
    rol: str
    ingresado_por: str
    
    class Config:
	    from_attributes = True

class UsuarioData(BaseModel):
    data: List[Usuario]

class UsuarioOut(BaseModel):
    id: Optional[int]
    usuario: str
    nombre: str
    departamento: str
    rol: str
    ingresado_por: str

    class Config:
	    from_attributes = True

class UsuarioUpdate(BaseModel):
    usuario: Optional[str] = None
    clave: Optional[str] = None
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    rol: Optional[str] = None

class Login(BaseModel):
    usuario: str
    clave: str
