from typing import List, Optional
from pydantic import BaseModel

class SolicitudesDesincorporarMuebles(BaseModel):
    id: Optional[int]
    fecha_solicitud: str
    nombre: str
    descripcion: str
    num_bien: int
    departamento: str
    solicitado_por: str
    tipo: str
    num_oficio:int

class RechazarSolicitudesDesincorporarMuebles(BaseModel):
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

class SolicitudesDesincorporarMueblesUpdate(BaseModel):
    nombre: str
    descripcion: str
    num_bien: int

class SolicitudesDesincorporarMueblesPOSTResponse(BaseModel):
    data: bool

class SolicitudesDesincorporarMueblesData(BaseModel):
    data: List[SolicitudesDesincorporarMuebles]

class SolicitudesDesincorporarMueblesData(BaseModel):
    data: List[SolicitudesDesincorporarMuebles]
