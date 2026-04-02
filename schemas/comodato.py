from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime
from enum import Enum as PyEnum

class TipoBien(str, PyEnum):
    mueble = "mueble"
    inmueble = "inmueble"
    automovil = "automovil"

class EstadoComodato(str, PyEnum):
    activo = "activo"
    vencido = "vencido"
    devuelto = "devuelto"
    cancelado = "cancelado"

class ComodatoCreate(BaseModel):
    tipo_bien: TipoBien
    bien_id: int = Field(..., gt=0, description="ID del bien en su tabla correspondiente")
    comodatario_nombre: str = Field(..., min_length=1, max_length=255)
    comodatario_cedula: str = Field(..., min_length=1, max_length=20)
    comodatario_telefono: Optional[str] = Field(None, max_length=50)
    comodatario_email: Optional[str] = Field(None, max_length=100)
    comodatario_direccion: Optional[str] = None
    comodante_nombre: Optional[str] = Field("Gobernación del Estado", max_length=255)
    comodante_representante: Optional[str] = Field(None, max_length=255)
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    condiciones: Optional[str] = None
    observaciones: Optional[str] = None
    creado_por: str = Field(..., max_length=100)

    @validator('fecha_fin')
    def validar_fecha_fin(cls, v, values):
        if v and 'fecha_inicio' in values and v < values['fecha_inicio']:
            raise ValueError('fecha_fin debe ser posterior a fecha_inicio')
        return v

class ComodatoUpdate(BaseModel):
    comodatario_telefono: Optional[str] = Field(None, max_length=50)
    comodatario_email: Optional[str] = Field(None, max_length=100)
    comodatario_direccion: Optional[str] = None
    fecha_fin: Optional[date] = None
    condiciones: Optional[str] = None
    observaciones: Optional[str] = None
    actualizado_por: str = Field(..., max_length=100)

class ComodatoDevolucion(BaseModel):
    fecha_devolucion: date
    observaciones: Optional[str] = None
    actualizado_por: str = Field(..., max_length=100)

class ComodatoCancelar(BaseModel):
    motivo: Optional[str] = None
    actualizado_por: str = Field(..., max_length=100)

class ComodatoOut(BaseModel):
    id: int
    numero_comodato: str
    tipo_bien: str
    bien_id: int
    codigo_bien: Optional[int]
    descripcion_bien: Optional[str]
    comodatario_nombre: str
    comodatario_cedula: str
    comodatario_telefono: Optional[str]
    comodatario_email: Optional[str]
    comodatario_direccion: Optional[str]
    comodante_nombre: Optional[str]
    comodante_representante: Optional[str]
    fecha_inicio: date
    fecha_fin: Optional[date]
    fecha_devolucion: Optional[date]
    documento_comodato: Optional[str]
    observaciones: Optional[str]
    condiciones: Optional[str]
    estado: str
    creado_por: Optional[str]
    fecha_creacion: Optional[datetime]
    actualizado_por: Optional[str]
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True

class ComodatoListItem(BaseModel):
    
    id: int
    numero_comodato: str
    tipo_bien: str
    codigo_bien: Optional[int]
    descripcion_bien: Optional[str]
    comodatario_nombre: str
    comodatario_cedula: str
    fecha_inicio: date
    fecha_fin: Optional[date]
    estado: str

    class Config:
        from_attributes = True
