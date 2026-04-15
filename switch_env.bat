@echo off
REM =========================================
REM Script para Cambiar entre Entornos
REM =========================================

echo.
echo ==========================================
echo   CAMBIAR CONFIGURACION DE ENTORNO
echo ==========================================
echo.

echo Selecciona el entorno:
echo.
echo [1] LOCAL (desarrollo en tu máquina)
echo [2] PORTAINER (producción remota)
echo [3] Ver entorno actual
echo [0] Cancelar
echo.

set /p OPCION="Selecciona una opcion (0-3): "

if "%OPCION%"=="1" goto LOCAL
if "%OPCION%"=="2" goto PORTAINER
if "%OPCION%"=="3" goto MOSTRAR
if "%OPCION%"=="0" goto CANCELAR

echo.
echo Opcion invalida
pause
exit /b 1

:LOCAL
echo.
echo Cambiando a configuracion LOCAL...
if not exist .env.local (
    echo ERROR: No se encontro .env.local
    pause
    exit /b 1
)

REM Backup del .env actual
if exist .env (
    copy /Y .env .env.backup > nul
    echo [Backup] .env guardado como .env.backup
)

REM Copiar .env.local
copy /Y .env.local .env > nul
echo [OK] Configuracion LOCAL activada

echo.
echo Configuracion actual:
echo - Base de datos: mysql_db (local)
echo - Puerto: 3306
echo - Ambiente: development
echo - S3: Deshabilitado
echo.

echo Reinicia los servicios con: docker-compose restart
pause
exit /b 0

:PORTAINER
echo.
echo Cambiando a configuracion PORTAINER...

REM Backup del .env actual
if exist .env (
    copy /Y .env .env.backup > nul
    echo [Backup] .env guardado como .env.backup
)

REM Si existe .env.portainer, usarlo
if exist .env.portainer (
    copy /Y .env.portainer .env > nul
    echo [OK] Configuracion PORTAINER activada desde .env.portainer
) else (
    echo [INFO] Usando .env actual (ya configurado para Portainer)
)

echo.
echo Configuracion actual:
echo - Base de datos: mariadb (remoto)
echo - Puerto: 3306
echo - Ambiente: production
echo - S3: Habilitado (s3.gebne.org.ve)
echo.

echo NOTA: Esta configuracion es para el servidor remoto.
echo       NO ejecutes docker-compose up con esta config en local.
echo.
pause
exit /b 0

:MOSTRAR
echo.
echo ==========================================
echo   CONFIGURACION ACTUAL (.env)
echo ==========================================
echo.

if not exist .env (
    echo ERROR: No existe archivo .env
    pause
    exit /b 1
)

REM Mostrar configuración importante
findstr /C:"MYSQL_HOST" .env
findstr /C:"MYSQL_DATABASE" .env
findstr /C:"ENVIRONMENT" .env
findstr /C:"USE_S3_STORAGE" .env
findstr /C:"MINIO_HOST" .env

echo.
echo ==========================================

REM Determinar qué entorno es
findstr /C:"MYSQL_HOST=mysql_db" .env > nul
if errorlevel 0 (
    echo Parece ser configuracion LOCAL
) else (
    findstr /C:"MYSQL_HOST=mariadb" .env > nul
    if errorlevel 0 (
        echo Parece ser configuracion PORTAINER
    ) else (
        echo No se pudo determinar el entorno
    )
)

echo ==========================================
echo.
pause
exit /b 0

:CANCELAR
echo.
echo Operacion cancelada
pause
exit /b 0
