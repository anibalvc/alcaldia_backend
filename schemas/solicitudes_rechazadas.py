from typing import List, Optional
from pydantic import BaseModel

class SolicitudesRechazadasMuebles(BaseModel):
    id: Optional[int]
    fecha_solicitud: str
    nombre: str
    descripcion: str
    num_bien: int
    departamento: str
    solicitado_por: str
    tipo: str
    id_solicitud : int
    rechazada_por: str
    descripcion_rechazo: str
    tipo_bien: str

class SolicitudesRechazadasMueblesData(BaseModel):
    data: List[SolicitudesRechazadasMuebles]
