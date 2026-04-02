from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from schemas.departamento import DepartamentoSimple

class UsuarioExtendedBase(BaseModel):
    
    authy_user_id: str = Field(..., max_length=100, description="ID del usuario en Authy")
    email: EmailStr = Field(..., description="Email del usuario")
    departamento_id: int = Field(..., description="ID del departamento")
    cargo: Optional[str] = Field(None, max_length=255, description="Cargo del usuario")
    telefono: Optional[str] = Field(None, max_length=50, description="Teléfono de contacto")
    extension: Optional[str] = Field(None, max_length=20, description="Extensión telefónica")

class UsuarioExtendedCreate(UsuarioExtendedBase):
    
    preferencias: Optional[str] = Field(None, description="Preferencias del usuario en formato JSON string")
    activo: Optional[bool] = Field(True, description="Estado del usuario")
    notas: Optional[str] = Field(None, description="Notas administrativas")
    creado_por: Optional[str] = Field(None, max_length=255, description="Usuario que crea el registro")

class UsuarioExtendedUpdate(BaseModel):
    
    email: Optional[EmailStr] = None
    departamento_id: Optional[int] = None
    cargo: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    extension: Optional[str] = Field(None, max_length=20)
    preferencias: Optional[str] = None
    activo: Optional[bool] = None
    notas: Optional[str] = None
    actualizado_por: Optional[str] = Field(None, max_length=255)

class UsuarioExtendedOut(UsuarioExtendedBase):
    
    id: int
    preferencias: Optional[str] = None  
    activo: bool
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None

    class Config:
        from_attributes = True

class UsuarioExtendedWithDepartamento(BaseModel):
    
    id: int
    authy_user_id: str
    email: str
    departamento_id: int
    cargo: Optional[str] = None
    telefono: Optional[str] = None
    extension: Optional[str] = None
    preferencias: Optional[str] = None
    activo: bool
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    departamento: Optional[DepartamentoSimple] = None

    class Config:
        from_attributes = True

class UsuarioExtendedData(BaseModel):
    
    data: List[UsuarioExtendedOut]

class EnrichSessionRequest(BaseModel):
    
    authy_user_id: str = Field(..., description="ID del usuario en Authy")
    email: EmailStr = Field(..., description="Email del usuario (para validación)")

class SessionExtendedData(BaseModel):

    usuario_registrado: bool = Field(..., description="Si el usuario está registrado localmente")
    departamento_codigo: Optional[str] = None
    departamento_nombre: Optional[str] = None
    departamento_id: Optional[int] = None
    cargo: Optional[str] = None
    telefono: Optional[str] = None
    extension: Optional[str] = None
    preferencias: Optional[Dict[str, Any]] = None

    mensaje: Optional[str] = Field(
        None,
        description="Mensaje informativo sobre el estado del registro"
    )

class RegistroRapidoRequest(BaseModel):
    
    authy_user_id: str = Field(..., description="ID del usuario en Authy")
    email: EmailStr
    departamento_id: int
    cargo: Optional[str] = None
    creado_por: str = Field(default="AUTO_REGISTER", description="Usuario que crea el registro")
