from typing import List, Optional
from pydantic import BaseModel, validator, Field
from decimal import Decimal

class Inmueble(BaseModel):
    id: Optional[int] = None
    fecha_ingreso: str
    orden_pago: int
    partida_compra: int
    num_factura: int
    nombre: str
    descripcion: str

    valor_inicial: Decimal = Field(..., gt=0)
    valor_actual: Decimal = Field(..., gt=0)
    num_bien: int
    departamento: str
    num_expediente: str
    num_expediente: str
    concepto_incorporacion: Optional[str] = None
    ingresado_por: str

class InmuebleUpdate(BaseModel):
    nombre: Optional[str] = None
    orden_pago: Optional[int] = None
    partida_compra: Optional[int] = None
    num_factura: Optional[int] = None
    descripcion: Optional[str] = None
    valor_inicial: Optional[Decimal] = Field(None, gt=0)
    valor_actual: Optional[Decimal] = Field(None, gt=0)
    num_bien: Optional[int] = None
    departamento: Optional[str] = None
    num_expediente: Optional[str] = None

class InmuebleDelete(BaseModel):
    id: Optional[int]
    fecha_ingreso: str
    orden_pago: int
    partida_compra: int
    num_factura: int
    nombre: str
    descripcion: str
    valor_inicial: Decimal
    valor_actual: Decimal
    num_bien: int
    num_oficio: int
    departamento: str
    num_expediente: str
    ingresado_por: str
    eliminado_por: str
    concepto_incorporacion: Optional[str]
    concepto_desincorporacion: Optional[str]

class InmueblePOSTResponse(BaseModel):
    data: bool

class InmuebleData(BaseModel):
    data: List[Inmueble]

class InmuebleDeleteData(BaseModel):
    data: List[InmuebleDelete]
