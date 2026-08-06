@echo off
title Compilador Automático SIGAR - PyInstaller
color 0A

echo =====================================================
echo       COMPILANDO APLICACION SIGAR UNELLEZ
echo =====================================================
echo.

:: Asegurar que la terminal trabaje en la ruta exacta de este archivo
cd /d "%~dp0"

:: 1. Activar el entorno virtual si existe
if exist "venv32\Scripts\activate.bat" (
    echo [1/3] Activando entorno virtual de 32 bits (venv32)...
    call venv32\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [1/3] Activando entorno virtual (venv)...
    call venv\Scripts\activate.bat
) else (
    echo [1/3] No se detecto carpeta venv. Utilizando Python del sistema...
)

echo.
echo [2/3] Ejecutando PyInstaller para generar el ejecutable...
pyinstaller --onefile --noconsole --name="SIGAR_UNELLEZ" login.py

echo.
:: 3. Verificar si el ejecutable se creó correctamente
if %ERRORLEVEL% EQU 0 (
    echo =====================================================
    echo   ¡COMPILACION EXITOSA! 
    echo   El ejecutable se encuentra en: dist\SIGAR_UNELLEZ.exe
    echo =====================================================
) else (
    echo =====================================================
    echo   [ERROR] Ocurrio un fallo durante la compilacion.
    echo =====================================================
)

echo.
pause