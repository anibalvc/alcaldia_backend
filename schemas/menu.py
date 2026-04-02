from typing import List, Optional
from pydantic import BaseModel

class MenuTemp(BaseModel):
    id: Optional[int]
    idPadre: Optional[int]
    ruta:str
    tieneItems: int
    vista: str

class MenuData(BaseModel):
    id: Optional[int]
    idPadre: Optional[int]
    vista: str
    ruta:str
    tieneItems: int
    items:Optional[List[MenuTemp]]

class MenuRol(BaseModel):
    id: Optional[int]
    idPadre: int
    rol: str

class Menu(BaseModel):
    data: List[MenuData]
    
class EspecialData(BaseModel):
    variable: int

class Especial(BaseModel):
    data: List[EspecialData]
