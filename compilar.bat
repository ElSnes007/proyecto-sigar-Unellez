@echo off
title Compilador Automatico SIGAR (Windows 7 / 32-bit)
color 0A

echo =====================================================
echo    COMPILADOR AUTOMATICO SIGAR UNELLEZ (32-BIT)
echo =====================================================
echo.

:: Asegurar que la terminal trabaje en la ruta exacta de este archivo
cd /d "%~dp0"

:: 1. Verificar si existe el entorno venv32; si no, crearlo con Python 3.8 (32-bit)
if not exist "venv32\Scripts\activate.bat" (
    echo [1/4] No se encontro venv32. Creando entorno con Python 3.8 (32-bit)...
    py -3.8-32 -m venv venv32
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] No se pudo crear el entorno de 32 bits.
        echo Asegurate de haber instalado Python 3.8.9 (32-bit) en el sistema.
        goto FIN
    )
) else (
    echo [1/4] Entorno venv32 detectado correctamente.
)

:: 2. Activar entorno virtual
echo [2/4] Activando entorno virtual de 32 bits...
call venv32\Scripts\activate.bat

:: 3. Instalar / actualizar librerias requeridas
echo [3/4] Instalando / verificando dependencias (requests, reportlab, pyinstaller)...
pip install --quiet --upgrade pip
pip install requests reportlab pyinstaller

:: 4. Compilar con PyInstaller
echo.
echo [4/4] Compilando ejecutable para Windows 7 / 8 / 10 / 11 (32 y 64 bits)...
pyinstaller --onefile --noconsole --name="SIGAR_UNELLEZ_x86" login.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo =====================================================
    echo   ¡COMPILACION EXITOSA! 
    echo   El ejecutable compatible se creo en:
    echo   dist\SIGAR_UNELLEZ_x86.exe
    echo =====================================================
) else (
    echo =====================================================
    echo   [ERROR] Ocurrio un fallo durante la compilacion.
    echo =====================================================
)

:FIN
echo.
pause