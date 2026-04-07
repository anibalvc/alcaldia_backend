import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from config.db import conn
from models.logs import logs
from fastapi import Request

class AuditLogger:
    
    @staticmethod
    def log_action(
        usuario: str,
        accion: str,
        modulo: str,
        registro_id: int,
        datos_anteriores: Optional[Dict[Any, Any]] = None,
        datos_nuevos: Optional[Dict[Any, Any]] = None,
        descripcion: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Optional[int]:
        """
        Registra una acción en el sistema de logs
        
        Args:
            usuario: Usuario que ejecuta la acción
            accion: Tipo de acción (CREATE, UPDATE, DELETE, DESINCORPORAR)
            modulo: Módulo afectado (MUEBLE, INMUEBLE, AUTOMOVIL, etc.)
            registro_id: ID del registro afectado
            datos_anteriores: Datos antes del cambio (para UPDATE/DELETE)
            datos_nuevos: Datos después del cambio (para CREATE/UPDATE)
            descripcion: Descripción legible de la acción
            request: Objeto Request de FastAPI para obtener IP y User-Agent
            
        Returns:
            ID del log creado o None si hubo error
        """
        try:
            # Convertir datos a JSON si existen
            datos_anteriores_json = json.dumps(datos_anteriores, default=str) if datos_anteriores else None
            datos_nuevos_json = json.dumps(datos_nuevos, default=str) if datos_nuevos else None
            
            # Extraer información del request si está disponible
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
            
            # Generar descripción automática si no se proporciona
            if not descripcion:
                descripcion = AuditLogger._generate_description(accion, modulo, registro_id)
            
            # Insertar el log
            result = conn.execute(logs.insert().values(
                fecha_hora=datetime.now(),
                usuario=usuario,
                accion=accion.upper(),
                modulo=modulo.upper(),
                registro_id=registro_id,
                datos_anteriores=datos_anteriores_json,
                datos_nuevos=datos_nuevos_json,
                descripcion=descripcion,
                ip_address=ip_address,
                user_agent=user_agent
            ))
            
            conn.commit()
            return result.inserted_primary_key[0]
            
        except SQLAlchemyError as e:
            print(f"Error al registrar log: {str(e)}")
            conn.rollback()
            return None
        except Exception as e:
            print(f"Error inesperado al registrar log: {str(e)}")
            return None
    
    @staticmethod
    def _generate_description(accion: str, modulo: str, registro_id: int) -> str:
        """Genera una descripción automática para el log"""
        acciones_es = {
            "CREATE": "creó",
            "UPDATE": "modificó", 
            "DELETE": "eliminó",
            "DESINCORPORAR": "desincorporó"
        }
        
        modulos_es = {
            "MUEBLE": "mueble",
            "INMUEBLE": "inmueble", 
            "AUTOMOVIL": "automóvil",
            "SOLICITUD": "solicitud",
            "USUARIO": "usuario"
        }
        
        accion_es = acciones_es.get(accion.upper(), accion.lower())
        modulo_es = modulos_es.get(modulo.upper(), modulo.lower())
        
        return f"Se {accion_es} el {modulo_es} con ID {registro_id}"
    
    @staticmethod
    def log_create(usuario: str, modulo: str, registro_id: int, datos: Dict[Any, Any], 
                  descripcion: Optional[str] = None, request: Optional[Request] = None) -> Optional[int]:
        """Shortcut para logs de creación"""
        return AuditLogger.log_action(
            usuario=usuario,
            accion="CREATE",
            modulo=modulo,
            registro_id=registro_id,
            datos_nuevos=datos,
            descripcion=descripcion,
            request=request
        )
    
    @staticmethod
    def log_update(usuario: str, modulo: str, registro_id: int, datos_anteriores: Dict[Any, Any],
                  datos_nuevos: Dict[Any, Any], descripcion: Optional[str] = None, 
                  request: Optional[Request] = None) -> Optional[int]:
        """Shortcut para logs de actualización"""
        return AuditLogger.log_action(
            usuario=usuario,
            accion="UPDATE", 
            modulo=modulo,
            registro_id=registro_id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            descripcion=descripcion,
            request=request
        )
    
    @staticmethod
    def log_delete(usuario: str, modulo: str, registro_id: int, datos: Dict[Any, Any],
                  descripcion: Optional[str] = None, request: Optional[Request] = None) -> Optional[int]:
        """Shortcut para logs de eliminación"""
        return AuditLogger.log_action(
            usuario=usuario,
            accion="DELETE",
            modulo=modulo, 
            registro_id=registro_id,
            datos_anteriores=datos,
            descripcion=descripcion,
            request=request
        )
    
    @staticmethod
    def log_desincorporar(usuario: str, modulo: str, registro_id: int, datos: Dict[Any, Any],
                         num_oficio: Optional[int] = None, descripcion: Optional[str] = None,
                         request: Optional[Request] = None) -> Optional[int]:
        """Shortcut para logs de desincorporación"""
        if not descripcion and num_oficio:
            descripcion = f"Se desincorporó el {modulo.lower()} con ID {registro_id} mediante oficio #{num_oficio}"
            
        return AuditLogger.log_action(
            usuario=usuario,
            accion="DESINCORPORAR",
            modulo=modulo,
            registro_id=registro_id, 
            datos_anteriores=datos,
            descripcion=descripcion,
            request=request
        )