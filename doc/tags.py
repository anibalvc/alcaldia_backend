from fastapi import FastAPI

tags_metadata = [
    {
        "name": "Usuario",
        "description": "Operaciones relacionadas con usuarios del sistema"
    },
    {
        "name": "Solicitud",
        "description": "Gestión de solicitudes generales"
    },
    {
        "name": "Mueble",
        "description": "Gestión de bienes muebles"
    },
    {
        "name": "Inmueble",
        "description": "Gestión de bienes inmuebles"
    },
    {
        "name": "Automovil",
        "description": "Gestión de vehículos y automóviles"
    },
    {
        "name": "Menu",
        "description": "Configuración de menús del sistema"
    },
    {
        "name": "Solicitudes Muebles",
        "description": "Solicitudes específicas para bienes muebles"
    },
    {
        "name": "Solicitudes Desincorporar Muebles",
        "description": "Solicitudes de desincorporación de bienes muebles"
    },
    {
        "name": "Archivos",
        "description": "Sistema de gestión de archivos (imágenes y documentos) para bienes"
    },
    {
        "name": "Reportes",
        "description": "Generación de reportes e informes del sistema (BM-1, BM-4, etc.)"
    },
    {
        "name": "Departamentos",
        "description": "Gestión de departamentos de la organización"
    },
    {
        "name": "Usuarios Extended",
        "description": "Extensión de usuarios de Authy con información local (departamento, cargo, etc.)"
    }
]