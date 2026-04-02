from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class BienArchivoBase(BaseModel):
    descripcion: Optional[str] = None

class BienArchivoCreate(BienArchivoBase):
    bien_id: int = Field(..., description="ID interno del bien")
    numero_bien: str = Field(..., max_length=50, description="Número de bien visible (ej: MUE-001)")
    bien_tipo: str = Field(..., description="Tipo de bien: mueble, inmueble, automovil")
    subido_por: str = Field(..., max_length=100, description="Usuario que sube el archivo")

    @validator('bien_tipo')
    def validate_bien_tipo(cls, v):
        if v not in ['mueble', 'inmueble', 'automovil']:
            raise ValueError('bien_tipo debe ser: mueble, inmueble o automovil')
        return v

class BienArchivoResponse(BienArchivoBase):
    id: int
    bien_id: int
    numero_bien: str
    bien_tipo: str
    nombre_archivo: str
    nombre_original: str
    tipo_archivo: str
    extension: str
    tamaño_bytes: int
    ruta_archivo: str  
    url_acceso: str
    thumbnail_path: Optional[str] = None
    checksum_md5: Optional[str] = None
    
    s3_bucket: Optional[str] = None
    s3_object_key: Optional[str] = None
    storage_type: str = "local"  
    
    subido_por: str
    fecha_subida: datetime
    modificado_por: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    activo: bool

    class Config:
        from_attributes = True

class BienArchivoUpdate(BaseModel):
    descripcion: Optional[str] = None
    modificado_por: str = Field(..., max_length=100)

class BienArchivoDelete(BaseModel):
    eliminado_por: str = Field(..., max_length=100, description="Usuario que elimina el archivo")

class BienArchivosData(BaseModel):
    data: List[BienArchivoResponse]
    total: int

class UploadResponse(BaseModel):
    success: bool
    message: str
    archivos_subidos: List[BienArchivoResponse]

class ArchivosStats(BaseModel):
    total_archivos: int
    total_imagenes: int
    total_documentos: int
    tamaño_total_mb: float
    ultimo_archivo: Optional[datetime] = None

class ArchivosFiltros(BaseModel):
    tipo_archivo: Optional[str] = Field(None, description="imagen o documento")
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    subido_por: Optional[str] = None

    @validator('tipo_archivo')
    def validate_tipo_archivo(cls, v):
        if v is not None and v not in ['imagen', 'documento']:
            raise ValueError('tipo_archivo debe ser: imagen o documento')
        return v

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None
