from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class DepartamentoBM4Item(BaseModel):
    
    ubicacion: str  
    descripcion: str  
    existencia_anterior: Decimal  
    inc: Decimal  
    desinc: Decimal  
    existencia_actual: Decimal  
    observaciones: Optional[str] = None  

    class Config:
        from_attributes = True

class ReporteBM4Response(BaseModel):
    
    titulo: str  
    periodo: str  
    mes: int  
    anio: int  
    departamentos: List[DepartamentoBM4Item]  
    total_existencia_anterior: Decimal  
    total_inc: Decimal  
    total_desinc: Decimal  
    total_existencia_actual: Decimal  

    responsable_nombre: str  
    responsable_cargo: str  
    decreto_numero: str  
    gaceta_numero: str  

    class Config:
        from_attributes = True

class GenerarReporteBM4Request(BaseModel):
    
    mes: int  
    anio: int  
    tipo_bien: str = "muebles"  

    class Config:
        from_attributes = True
