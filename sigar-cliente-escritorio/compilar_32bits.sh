#!/usr/bin/env bash

echo "====================================================="
echo "   COMPILADOR AUTOMATICO BASH - SIGAR (32-BIT)"
echo "====================================================="
echo ""

# Ir al directorio donde está ubicado este script
cd "$(dirname "$0")"

# 1. Crear entorno virtual de 32 bits si no existe
if [ ! -d "venv32" ]; then
    echo "[1/4] Creando entorno venv32 con Python 3.8 (32 bits)..."
    py -3.8-32 -m venv venv32
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] No se pudo crear el entorno. Verifica que Python 3.8 (32-bit) esté instalado."
        exit 1
    fi
else
    echo "[1/4] Entorno venv32 detectado."
fi

# 2. Activar entorno virtual
echo "[2/4] Activando entorno virtual..."
if [ -f "venv32/Scripts/activate" ]; then
    source venv32/Scripts/activate
else
    echo "[ERROR] No se encontró el script de activación del entorno."
    exit 1
fi

# 3. Instalar dependencias requeridas
echo "[3/4] Instalando librerías (requests, reportlab, pyinstaller)..."
python -m pip install --quiet --upgrade pip
pip install requests reportlab pyinstaller

# 4. Compilar ejecutable compatible con Windows 7/8/10/11 (32 y 64 bits)
echo ""
echo "[4/4] Compilando ejecutable x86..."
pyinstaller --onefile --noconsole --name="SIGAR_UNELLEZ_x86" login.py

if [ $? -eq 0 ]; then
    echo ""
    echo "====================================================="
    echo "   ¡COMPILACION EXITOSA!"
    echo "   Ejecutable generado en: dist/SIGAR_UNELLEZ_x86.exe"
    echo "====================================================="
else
    echo ""
    echo "====================================================="
    echo "   [ERROR] Ocurrió un fallo durante la compilación."
    echo "====================================================="
    exit 1
fi