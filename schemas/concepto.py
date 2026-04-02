from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum as PyEnum
from datetime import datetime

class TipoMovimiento(str, PyEnum):
    ingreso = "ingreso"
    egreso = "egreso"
    ambos = "ambos"

class ConceptoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20)
    descripcion: str = Field(..., min_length=1, max_length=255)
    tipo: TipoMovimiento
    creado_por: str = Field(..., max_length=100)

class ConceptoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    descripcion: Optional[str] = Field(None, min_length=1, max_length=255)
    tipo: Optional[TipoMovimiento] = None
    estado: Optional[bool] = None

class ConceptoOut(BaseModel):
    id: int
    codigo: str
    descripcion: str
    tipo: str
    estado: bool
    creado_por: Optional[str]
    fecha_creacion: Optional[datetime]

    class Config:
        from_attributes = True
