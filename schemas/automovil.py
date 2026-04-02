from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Automovil(BaseModel):
    id: Optional[int] = None
    fecha_ingreso: str
    marca: str
    modelo: str
    año: Optional[int] = None
    color: Optional[str] = None
    placa: Optional[str] = None
    estatus: Optional[str] = None
    operatividad: Optional[str] = None
    orden_pago: int
    partida_compra: int
    num_factura: int
    num_factura: int
    valor_inicial: Decimal = Field(..., gt=0)
    valor_actual: Decimal = Field(..., gt=0)
    num_bien: int
    num_serial_motor: str
    num_serial_carroceria: str
    num_expediente: str
    departamento: str
    ingresado_por: str
    concepto_incorporacion: Optional[str] = None
    chofer: str

    class Config:
        from_attributes = True

class AutomovilUpdate(BaseModel):
    fecha_ingreso: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[int] = None
    color: Optional[str] = None
    placa: Optional[str] = None
    estatus: Optional[str] = None
    operatividad: Optional[str] = None
    orden_pago: Optional[int] = None
    partida_compra: Optional[int] = None
    num_factura: Optional[int] = None
    valor_inicial: Optional[Decimal] = Field(None, gt=0)
    valor_actual: Optional[Decimal] = Field(None, gt=0)
    num_bien: Optional[int] = None
    num_serial_motor: Optional[str] = None
    num_serial_carroceria: Optional[str] = None
    num_expediente: Optional[str] = None
    departamento: Optional[str] = None
    chofer: Optional[str] = None

class AutomovilDelete(BaseModel):
    fecha_ingreso: str
    marca: str
    modelo: str
    año: Optional[int]
    color: Optional[str]
    placa: Optional[str]
    estatus: Optional[str]
    operatividad: Optional[str]
    orden_pago: int
    partida_compra: int
    num_factura: int
    valor_inicial: Decimal
    valor_actual: Decimal
    num_bien: int
    num_serial_motor: str
    num_serial_carroceria: str
    num_expediente: str
    num_oficio: int
    departamento: str
    ingresado_por: str
    eliminado_por: str
    concepto_incorporacion: Optional[str]
    concepto_desincorporacion: Optional[str]

class AutomovilPOSTResponse(BaseModel):
    data: bool

class AutomovilData(BaseModel):
    data: List[Automovil]

class AutomovilDeleteData(BaseModel):
    data: List[AutomovilDelete]
