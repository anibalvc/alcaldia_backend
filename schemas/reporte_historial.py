from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum

class ReporteTipoEnum(str, PyEnum):
    BM1 = "BM1"
    BM2 = "BM2"
    BM4 = "BM4"
    BM7 = "BM7"

class DetalleBien(BaseModel):
    tipo_bien: str  
    bien_id: int
    codigo_bien: Optional[int] = None

class ReporteGenerarRequest(BaseModel):
    tipo_reporte: ReporteTipoEnum
    generado_por: str
    departamento: str
    observaciones: Optional[str] = None
    bienes: List[DetalleBien] 

class ReporteHistorialOut(BaseModel):
    id: int
    numero_reporte: str
    tipo_reporte: str
    fecha_generacion: datetime
    generado_por: Optional[str]
    departamento: Optional[str]
    observaciones: Optional[str]

    class Config:
        from_attributes = True

class ReporteDetalleOut(BaseModel):
    id: int
    reporte_id: int
    tipo_bien: str
    bien_id: int
    codigo_bien: Optional[int]

    class Config:
        from_attributes = True
