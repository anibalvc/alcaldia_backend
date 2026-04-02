from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Text, DateTime
from config.db import meta

logs = Table("logs", meta, 
    Column("id", Integer, primary_key=True, index=True),
    Column("fecha_hora", DateTime),
    Column("usuario", String(255)),
    Column("accion", String(50)),  
    Column("modulo", String(50)),  
    Column("registro_id", Integer),  
    Column("datos_anteriores", Text),  
    Column("datos_nuevos", Text),  
    Column("descripcion", String(500)),  
    Column("ip_address", String(45)),  
    Column("user_agent", Text)  
)
