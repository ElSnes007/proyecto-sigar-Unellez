@echo off
title Compilador SIGAR - Generador de Ejecutable Local
color 0A
cls

echo ============================================================
echo               COMPILADOR DE APLICACION SIGAR                
echo ============================================================
echo.

:: 1. Limpieza de compilaciones previas
echo [*] Limpiando carpetas de compilaciones anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"

echo.
echo [*] Preparando parametros de compilacion...

:: 2. Configurar argumentos exactos e importaciones ocultas de Tkinter
set ARGS=--name="SIGAR_Launcher" --onefile --noconsole
set ARGS=%ARGS% --hidden-import "tkinter.filedialog"
set ARGS=%ARGS% --hidden-import "tkinter.messagebox"
set ARGS=%ARGS% --hidden-import "tkinter.ttk"
set ARGS=%ARGS% --hidden-import "PIL.ImageTk"

:: Agregar carpeta del cliente de escritorio
if exist "sigar-cliente-escritorio" (
    echo [+] Carpeta sigar-cliente-escritorio detectada.
    set ARGS=%ARGS% --add-data "sigar-cliente-escritorio;sigar-cliente-escritorio"
)

:: Agregar logo.png de la raiz
if exist "logo.png" (
    echo [+] Imagen logo.png detectada.
    set ARGS=%ARGS% --add-data "logo.png;."
)

:: Agregar config.json y acceso.json si existen en la raiz
if exist "config.json" set ARGS=%ARGS% --add-data "config.json;."
if exist "acceso.json" set ARGS=%ARGS% --add-data "acceso.json;."

echo.
echo [*] Iniciando compilacion de SIGAR con PyInstaller...
echo.

python -m PyInstaller %ARGS% login.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [OK] Compilacion completada con exito.
    echo [>] El ejecutable se encuentra en: dist\SIGAR_Launcher.exe
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo [X] Hubo un error durante la compilacion.
    echo ============================================================
)

echo.
pause