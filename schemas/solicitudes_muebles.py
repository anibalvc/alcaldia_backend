from typing import List, Optional
from pydantic import BaseModel

class SolicitudesMuebles(BaseModel):
    id: Optional[int]
    fecha_solicitud: str
    marca: Optional[str]
    modelo: Optional[str]
    serial: Optional[str]
    responsable: Optional[str]
    descripcion: str
    num_bien: int
    departamento: str
    solicitado_por: str
    tipo: str

class RechazarSolicitudesMuebles(BaseModel):
    id: Optional[int]
    fecha_solicitud: str
    nombre: str
    descripcion: str
    rechazada_por: str
    descripcion_rechazo: str
    num_bien: int
    departamento: str
    solicitado_por: str
    tipo: str

class SolicitudesMueblesUpdate(BaseModel):
    fecha_solicitud: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    responsable: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    num_bien: Optional[int] = None
    departamento: Optional[str] = None
    solicitado_por: Optional[str] = None
    tipo: Optional[str] = None

class SolicitudesMueblesPOSTResponse(BaseModel):
    data: bool

class SolicitudesMueblesData(BaseModel):
    data: List[SolicitudesMuebles]

class ImportResultado(BaseModel):
    
    total_procesados: int
    exitosos: int
    fallidos: int
    errores: List[dict]  
    solicitudes_creadas: List[int]
