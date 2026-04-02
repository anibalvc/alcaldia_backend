from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

class Mueble(BaseModel):
    id: Optional[int] = None
    fecha_ingreso: str
    fecha_compra: Optional[str] = None
    orden_pago: int
    partida_compra: int
    num_factura: int
    num_catalogo: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    responsable: str
    estado: Optional[str] = None
    esTecnologia: int
    marca: Optional[str] = None
    descripcion: str
    valor_inicial: Decimal = Field(..., gt=0)
    valor_actual: Decimal = Field(..., gt=0)
    num_bien: int
    departamento: str
    concepto_incorporacion: Optional[int] = None
    ingresado_por: str

class MuebleUpdate(BaseModel):
    orden_pago: Optional[int] = None
    partida_compra: Optional[int] = None
    num_factura: Optional[int] = None
    esTecnologia: Optional[int] = None
    marca: Optional[str] = None
    num_catalogo: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    responsable: Optional[str] = None
    estado: Optional[str] = None
    descripcion: Optional[str] = None
    valor_inicial: Optional[Decimal] = Field(None, gt=0)
    valor_actual: Optional[Decimal] = Field(None, gt=0)
    num_bien: Optional[int] = None
    departamento: Optional[str] = None

class MuebleDelete(BaseModel):
    id: Optional[int]
    fecha_ingreso: str
    fecha_compra: Optional[str]
    orden_pago: int
    partida_compra: int
    num_factura: int
    num_catalogo: Optional[str]
    modelo: Optional[str]
    serial: Optional[str]
    responsable: Optional[str]
    estado: Optional[str]
    marca: Optional[str]
    esTecnologia: int
    descripcion: str
    valor_inicial: Decimal
    valor_actual: Decimal
    num_bien: int
    num_oficio: int
    departamento: str
    ingresado_por: str
    eliminado_por: str
    concepto_incorporacion: Optional[str]
    concepto_desincorporacion: Optional[str]

class MueblePOSTResponse(BaseModel):
    data: bool

class MuebleData(BaseModel):
    data: List[Mueble]

class MuebleDeleteData(BaseModel):
    data: List[MuebleDelete]

class ErrorResponse(BaseModel):
    success: bool
    message: str

class ImportMuebleResultado(BaseModel):
    
    total_procesados: int
    exitosos: int
    fallidos: int
    errores: List[dict]  
    muebles_creados: List[int]
