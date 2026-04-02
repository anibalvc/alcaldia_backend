from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DepartamentoBase(BaseModel):
    
    codigo: int = Field(..., description="Código numérico único del departamento")
    nombre: str = Field(..., max_length=255, description="Nombre completo del departamento")
    descripcion: Optional[str] = Field(None, description="Descripción del departamento")
    responsable: Optional[str] = Field(None, max_length=255, description="Nombre del responsable")
    director: Optional[str] = Field(None, max_length=255, description="Director del departamento (se usará en BM-7)")
    ubicacion: Optional[str] = Field(None, max_length=255, description="Ubicación física")
    telefono: Optional[str] = Field(None, max_length=50, description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=255, description="Email de contacto")

class DepartamentoCreate(DepartamentoBase):
    
    activo: Optional[bool] = Field(True, description="Estado del departamento")
    creado_por: Optional[str] = Field(None, max_length=255, description="Usuario que crea el registro")

class DepartamentoUpdate(BaseModel):
    
    codigo: Optional[int] = Field(None)
    nombre: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None
    responsable: Optional[str] = Field(None, max_length=255)
    director: Optional[str] = Field(None, max_length=255)
    ubicacion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None
    actualizado_por: Optional[str] = Field(None, max_length=255)

class DepartamentoOut(DepartamentoBase):
    
    id: int
    activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None

    class Config:
        from_attributes = True

class DepartamentoSimple(BaseModel):
    
    id: int
    codigo: int
    nombre: str
    activo: bool

    class Config:
        from_attributes = True

class DepartamentoData(BaseModel):
    
    data: List[DepartamentoOut]
