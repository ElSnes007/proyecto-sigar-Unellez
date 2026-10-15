# -*- coding: utf-8 -*-
"""
Recolector de DLLs del Universal C Runtime (UCRT) para Windows 7 (32 bits)
Copia todas las api-ms-win-*.dll y ucrtbase.dll para compilación portable.
"""
import glob
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(BASE_DIR, "dlls_win7")

print("[*] Preparando carpeta de DLLs para Windows 7...")
os.makedirs(DESTINO, exist_ok=True)

# 1. Buscar primero en los SDKs oficiales de Windows (Redistributable limpia de 32 bits)
rutas_sdk = [
    r"C:\Program Files (x86)\Windows Kits\10\Redist\*\ucrt\DLLs\x86",
    r"C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x86",
    r"C:\Program Files\Windows Kits\10\Redist\*\ucrt\DLLs\x86",
]

origen_encontrado = None
for patron in rutas_sdk:
    coincidencias = glob.glob(patron)
    if coincidencias:
        origen_encontrado = coincidencias[-1]
        break

# 2. Si no hay Windows SDK instalado, usar las librerías de 32 bits de SysWOW64
if not origen_encontrado:
    if os.path.exists(r"C:\Windows\SysWOW64"):
        origen_encontrado = r"C:\Windows\SysWOW64"
    else:
        origen_encontrado = r"C:\Windows\System32"

print(f"[*] Extrayendo DLLs desde: {origen_encontrado}")

patrones_copia = [
    os.path.join(origen_encontrado, "api-ms-win-*.dll"),
    os.path.join(origen_encontrado, "ucrtbase.dll"),
    os.path.join(origen_encontrado, "vcruntime140.dll"),
]

total_copiadas = 0
for patron in patrones_copia:
    for archivo in glob.glob(patron):
        nombre = os.path.basename(archivo)
        destino_archivo = os.path.join(DESTINO, nombre)
        try:
            shutil.copyfile(archivo, destino_archivo)
            total_copiadas += 1
        except Exception:
            pass

# Asegurar vcruntime140 de Python
if hasattr(sys, "base_prefix"):
    py_vcruntime = os.path.join(sys.base_prefix, "vcruntime140.dll")
    if os.path.exists(py_vcruntime):
        shutil.copyfile(py_vcruntime, os.path.join(DESTINO, "vcruntime140.dll"))

print(f"[OK] Se recolectaron exitosamente {total_copiadas} DLLs en: {DESTINO}")