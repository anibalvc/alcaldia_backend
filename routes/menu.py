from typing import List
from fastapi import APIRouter, Response
from config.db import conn
from models.menu import menus, roles, especial
from schemas.menu import Especial, Menu, MenuData
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from fastapi.responses import JSONResponse
from sqlalchemy.sql import or_
from typing import List, Union

from cryptography.fernet import Fernet

menu = APIRouter()

@menu.get("/menu", tags=["Menu"], response_model=Union[Menu, List[Menu]])
def get_menu(rol: str):
    try:
        
        result = conn.execute(menus.select()).fetchall()
        row_as_dict = [dict(row._mapping) for row in result]

        allRoles = conn.execute(roles.select().where(roles.c.rol == rol)).fetchall()
        allRoles_dict = [dict(row._mapping) for row in allRoles]

        fmenu = []
        for menu in row_as_dict:
            if menu["idPadre"] is None:
                fmenu.append(menu)
            for rol in allRoles_dict:
                if rol["idMenuHijo"] == menu["id"]:
                    fmenu.append(menu)

        final = []
        for menuItem in fmenu:
            if menuItem["idPadre"] is None:
                temp = dict(menuItem)
                temp["items"] = []
                final.append(temp)
            hijosTemp = []
            for fitem in fmenu:
                if menuItem["id"] == fitem["idPadre"]:
                    for i, elem in enumerate(final):
                        if elem["id"] == fitem["idPadre"]:
                            hijosTemp.append(fitem)
            for i, elem in enumerate(final):
                if hijosTemp:
                    if elem["id"] == hijosTemp[0]["idPadre"]:
                        final[i]['items'] = hijosTemp

        for recorrido in final[:]:  
            if recorrido["tieneItems"] == 1 and not recorrido["items"]:
                final.remove(recorrido)

        return {"data": final}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)}, media_type="application/json")

@menu.get("/especial", tags=["Menu"], response_model=Especial)
def get_especial():

    return {"data": conn.execute(especial.select()).fetchall()}
