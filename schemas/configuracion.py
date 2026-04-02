from pydantic import BaseModel
from typing import Optional

class ConfiguracionCreate(BaseModel):
    clave: str
    valor: str
    grupo: Optional[str] = None
    descripcion: Optional[str] = None

class ConfiguracionUpdate(BaseModel):
    valor: Optional[str] = None
    grupo: Optional[str] = None
    descripcion: Optional[str] = None

class ConfiguracionOut(BaseModel):
    clave: str
    valor: Optional[str]
    grupo: Optional[str]
    descripcion: Optional[str]

    class Config:
        from_attributes = True
