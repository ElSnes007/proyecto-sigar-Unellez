# -*- coding: utf-8 -*-
"""
Script Maestro de Compilación - SIGART UNELLEZ VIPI
Empaqueta el proyecto con todas las librerías UCRT para Windows 7 de 32 bits.
"""
import glob
import os
import shutil
import sys
import PyInstaller.__main__

DIR_CLIENTE = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR_CLIENTE)

print("=" * 60)
print("     COMPILADOR MAESTRO SIGART - UNELLEZ VIPI (WIN 7)")
print("=" * 60)

# 1. Verificar versión y arquitectura de Python
bits = "32-bits (Intel)" if sys.maxsize <= 2**32 else "64-bits"
print(f"[*] Version de Python : {sys.version.split()[0]}")
print(f"[*] Arquitectura      : {bits}")

if sys.version_info >= (3, 9):
    print("\n[!] ADVERTENCIA: Se detectó Python 3.9 o superior.")
    print("    Para compatibilidad con Windows 7 se requiere Python 3.8 (venv_win32).")

# 2. Recolectar DLLs si no existen
DIR_DLLS = os.path.join(DIR_CLIENTE, "dlls_win7")
if not os.path.exists(DIR_DLLS) or not os.listdir(DIR_DLLS):
    if os.path.exists("recolectar_dlls.py"):
        print("\n[*] Ejecutando recolector de DLLs...")
        os.system(f'"{sys.executable}" recolectar_dlls.py')

# 3. Limpiar compilaciones previas
print("\n[*] Limpiando carpetas de compilaciones anteriores...")
for carpeta in ["build", "dist"]:
    if os.path.exists(carpeta):
        try:
            shutil.rmtree(carpeta, ignore_errors=True)
        except Exception:
            pass

# 4. Construir lista de DLLs sin errores de caracteres de Batch
argumentos_dlls = []
if os.path.exists(DIR_DLLS):
    dlls_encontradas = glob.glob(os.path.join(DIR_DLLS, "*.dll"))
    print(f"[*] Inyectando {len(dlls_encontradas)} DLLs de Windows 7 al ejecutable...")
    for ruta_dll in dlls_encontradas:
        nombre_dll = os.path.basename(ruta_dll)
        # Sintaxis de PyInstaller: origen;destino
        argumentos_dlls.extend(["--add-binary", f"{ruta_dll};."])

# 5. Argumentos completos de PyInstaller
argumentos_pyinstaller = [
    "login.py",
    "--noconsole",
    "--onefile",
    "--name=SIGART",
    "--add-data=iconos;iconos",
    "--add-data=UNELLEZ LOGO.png;.",
    "--add-data=lema_unellez_oro.png;.",
    "--collect-all=customtkinter",
    "--collect-all=reportlab",
    "--hidden-import=PIL",
    "--hidden-import=PIL._tkinter_finder",
    "--hidden-import=views",
    "--hidden-import=database",
    "--hidden-import=styles",
    "--hidden-import=utils",
    "--hidden-import=modals",
    "--hidden-import=main",
] + argumentos_dlls

print("\n[*] Empaquetando ejecutable con PyInstaller (esto tomará 1 minuto)...")
try:
    PyInstaller.__main__.run(argumentos_pyinstaller)
except Exception as e:
    print(f"\n[X] Error durante la ejecución de PyInstaller: {e}")

print("\n" + "=" * 60)
ruta_exe = os.path.join(DIR_CLIENTE, "dist", "SIGART.exe")
if os.path.exists(ruta_exe):
    tamano_mb = os.path.getsize(ruta_exe) / (1024 * 1024)
    print(f" [OK] COMPILACION EXITOSA")
    print(f" Ejecutable : dist\\SIGART.exe ({tamano_mb:.1f} MB)")
    print(f" Estado     : Listo y compatible con Windows 7")
else:
    print(" [X] La compilación no generó el archivo esperado.")
print("=" * 60)

input("\nPresione ENTER para salir...")