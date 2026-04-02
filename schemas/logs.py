from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LogBase(BaseModel):
    usuario: str
    accion: str
    modulo: str
    registro_id: int
    datos_anteriores: Optional[str] = None
    datos_nuevos: Optional[str] = None
    descripcion: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LogCreate(LogBase):
    pass

class Log(LogBase):
    id: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

class LogData(BaseModel):
    data: List[Log]

class LogResponse(BaseModel):
    message: str
    log_id: int