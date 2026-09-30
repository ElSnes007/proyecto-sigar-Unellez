# -*- coding: utf-8 -*-
import os
import json
from tkinter import messagebox

# Obtiene la carpeta exacta donde vive database.py (sigar-cliente-escritorio)
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_BIENES = os.path.join(DIR_ACTUAL,"bienes.json") 
ARCHIVO_BAJAS = os.path.join(DIR_ACTUAL, "bajas.json")
ARCHIVO_CONFIG = os.path.join(DIR_ACTUAL, "config.json")
URL_RESPALDO_CLOUD = "https://sigar-unellez.onrender.com/api/respaldo"


def cargar_datos_locales():
    if not os.path.exists(ARCHIVO_BIENES):
        return []
    try:
        with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error de Lectura", f"No se pudieron cargar los datos de {ARCHIVO_BIENES}:\n{e}")
        return []


def guardar_datos_locales(bienes):
    try:
        with open(ARCHIVO_BIENES, "w", encoding="utf-8") as f:
            json.dump(bienes, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("Error de Escritura", f"No se pudo guardar la información en {ARCHIVO_BIENES}:\n{e}")
        return False


def guardar_baja_local(registro_baja):
    bajas = []
    if os.path.exists(ARCHIVO_BAJAS):
        try:
            with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                bajas = json.load(f)
        except Exception:
            bajas = []
    bajas.append(registro_baja)
    try:
        with open(ARCHIVO_BAJAS, "w", encoding="utf-8") as f:
            json.dump(bajas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Error en Registro de Baja", f"No se pudo registrar la baja en {ARCHIVO_BAJAS}:\n{e}")


def obtener_conteo_bajas():
    if os.path.exists(ARCHIVO_BAJAS):
        try:
            with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                return len(json.load(f))
        except Exception:
            return 0
    return 0