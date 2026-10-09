# -*- coding: utf-8 -*-
"""
SIGAR (UNELLEZ) - database.py
Gestión de persistencia local en JSON y sincronización con el respaldo en la nube.
Compatible con Python 3.8.10+
"""
import os
import datetime
import json
from tkinter import messagebox, simpledialog

# Importación con fallback seguro para peticiones HTTP
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_BIENES = os.path.join(DIR_ACTUAL, "bienes.json") 
ARCHIVO_BAJAS = os.path.join(DIR_ACTUAL, "bajas.json")
ARCHIVO_CONFIG = os.path.join(DIR_ACTUAL, "config.json")
URL_RESPALDO_CLOUD = "https://script.google.com/macros/s/AKfycbx1XpJ3iOdqa1mPsivMLLjGF0-hZ_IwLXgTadbqSO66Nb7yzVC5E2s3BTlUpUMbG3TF3w/exec"


def cargar_datos_locales():
    """Carga los datos locales del sistema desde bienes.json."""
    if os.path.exists(ARCHIVO_BIENES):
        try:
            with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al leer bienes.json: {e}")
            return []
    return []


def guardar_datos_locales(datos):
    """Guarda la lista completa de bienes en bienes.json."""
    try:
        with open(ARCHIVO_BIENES, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return False


def guardar_baja_local(baja):
    """Registra una desincorporación en bajas.json."""
    bajas = []
    if os.path.exists(ARCHIVO_BAJAS):
        try:
            with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                bajas = json.load(f)
        except Exception:
            bajas = []
    bajas.append(baja)
    try:
        with open(ARCHIVO_BAJAS, "w", encoding="utf-8") as f:
            json.dump(bajas, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error al registrar baja: {e}")
        return False


def obtener_conteo_bajas():
    """Obtiene el número de activos desincorporados registrados."""
    if os.path.exists(ARCHIVO_BAJAS):
        try:
            with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                return len(datos)
        except Exception:
            return 0
    return 0


def exportar_respaldo_nube_bd(parent_window=None):
    """Solicita el correo, empaqueta los bienes locales en JSON y los envía a Google Sheets."""
    if not HAS_REQUESTS:
        messagebox.showerror(
            "Librería Requerida",
            "La librería 'requests' no está instalada. Ejecute: pip install requests",
            parent=parent_window
        )
        return

    correo = simpledialog.askstring(
        "Correo para la Nube", 
        "Ingrese el correo electrónico vinculado para el respaldo:", 
        parent=parent_window
    )
    
    if not correo:
        return
    
    if "@" not in correo or "." not in correo:
        messagebox.showerror("Error", "El correo electrónico ingresado no es válido.", parent=parent_window)
        return

    lista_bienes = cargar_datos_locales()
    total_bienes = len(lista_bienes)
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "fecha": fecha_actual,
        "correo": correo.strip(),
        "total_bienes": total_bienes,
        "datos_bienes_json": json.dumps(lista_bienes, ensure_ascii=False)
    }

    try:
        response = requests.post(URL_RESPALDO_CLOUD, json=payload, timeout=15)
        if response.status_code in [200, 201]:
            messagebox.showinfo(
                "Éxito", 
                f"¡Respaldo enviado y registrado en Google Sheets con éxito!\nAsociado a: {correo}", 
                parent=parent_window
            )
        else:
            messagebox.showerror(
                "Error del Servidor", 
                f"No se pudo guardar en la nube (Código {response.status_code}):\n{response.text}", 
                parent=parent_window
            )
    except Exception as e:
        messagebox.showerror(
            "Error de Conexión", 
            f"No se pudo conectar con el servicio en la nube.\nVerifique su conexión a internet.\n\nDetalles: {str(e)}", 
            parent=parent_window
        )