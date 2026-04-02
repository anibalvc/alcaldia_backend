from typing import Optional
from pydantic import BaseModel

class Solicitud(BaseModel):
    id: Optional[int]
    num_bien: int
    descripcion: str
    serial: str
    fecha: str
    ingresado_por: str

class SolicitudUpdate(BaseModel):
    num_bien: Optional[int] = None
    descripcion: Optional[str] = None
    serial: Optional[str] = None
    fecha: Optional[str] = None
    ingresado_por: Optional[str] = None