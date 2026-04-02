from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class BM1Item(BaseModel):
    
    numero_catalogo: str
    codigo_bien: int
    descripcion: str
    cantidad: int = 1
    orden_compra: Optional[str] = ""
    fecha_registro: Optional[str] = ""
    fecha_compra: Optional[str] = ""
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    ubicacion: str
    seriales: Optional[str] = ""
    responsable: Optional[str] = ""
    valor: Decimal
    estado: str

class BM1Totales(BaseModel):
    
    total_elementos: int
    elementos_incorporados: int
    elementos_desincorporados: int
    inventario_inicial: int
    total_inventario_monetario: Decimal
    monto_incorporaciones: Decimal
    monto_desincorporaciones: Decimal
    inventario_inicial_monetario: Decimal

class BM1Response(BaseModel):
    
    items: List[BM1Item]
    totales: BM1Totales
    departamento: Optional[str] = None
    fecha_corte: str
