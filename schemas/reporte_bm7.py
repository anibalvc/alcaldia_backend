from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class BienBM7Item(BaseModel):
    numero_catalogo: str
    cantidad: int = 1
    motivo: str
    codigo_bien: str
    nombre_descripcion: str
    orden_compra: str
    fecha_registro: str
    seriales: str
    valor_unitario: Decimal
    estado: str

class ReporteBM7Response(BaseModel):
    numero_acta: str
    municipio: str = "Mariño"
    estado_region: str = "Nueva Esparta"
    departamento: Optional[str] = None
    fecha_actual: str

    suscrito_nombre: str
    suscrito_cargo: str

    unidad_trabajo_nombre: str
    unidad_trabajo_ubicacion: str

    testigo1_nombre: str
    testigo2_nombre: str

    bienes: List[BienBM7Item]

    total_cantidad: int
    total_monto: Decimal

class BienDisponibleBM7(BaseModel):
    id: int
    tipo_bien: str  
    codigo_bien: str
    descripcion: str
    fecha_ingreso: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
