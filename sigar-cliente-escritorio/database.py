# -*- coding: utf-8 -*-
import json
import os
import sys
from tkinter import messagebox


def obtener_ruta_base():
  """Retorna la carpeta donde se encuentra el .exe compilado

  o el directorio del script en modo desarrollo.
  """
  if getattr(sys, 'frozen', False):
    # Si está congelado por PyInstaller, usa el directorio del ejecutable (.exe)
    return os.path.dirname(sys.executable)
  else:
    # Si corre desde el interprete normal de Python
    return os.path.dirname(os.path.abspath(__file__))


# Obtiene la ruta base dinámica según el entorno de ejecución
DIR_ACTUAL = obtener_ruta_base()

ARCHIVO_BIENES = os.path.join(DIR_ACTUAL, 'bienes.json')
ARCHIVO_BAJAS = os.path.join(DIR_ACTUAL, 'bajas.json')
ARCHIVO_CONFIG = os.path.join(DIR_ACTUAL, 'config.json')
URL_RESPALDO_CLOUD = 'https://sigar-unellez.onrender.com/api/respaldo'


def cargar_datos_locales():
  if not os.path.exists(ARCHIVO_BIENES):
    return []
  try:
    with open(ARCHIVO_BIENES, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception as e:
    messagebox.showerror(
        'Error de Lectura',
        f'No se pudieron cargar los datos de {ARCHIVO_BIENES}:\n{e}',
    )
    return []


def guardar_datos_locales(bienes):
  try:
    with open(ARCHIVO_BIENES, 'w', encoding='utf-8') as f:
      json.dump(bienes, f, ensure_ascii=False, indent=4)
    return True
  except Exception as e:
    messagebox.showerror(
        'Error de Escritura',
        f'No se pudo guardar la información en {ARCHIVO_BIENES}:\n{e}',
    )
    return False


def guardar_baja_local(registro_baja):
  bajas = []
  if os.path.exists(ARCHIVO_BAJAS):
    try:
      with open(ARCHIVO_BAJAS, 'r', encoding='utf-8') as f:
        bajas = json.load(f)
    except Exception:
      bajas = []
  bajas.append(registro_baja)
  try:
    with open(ARCHIVO_BAJAS, 'w', encoding='utf-8') as f:
      json.dump(bajas, f, ensure_ascii=False, indent=4)
  except Exception as e:
    messagebox.showerror(
        'Error en Registro de Baja',
        f'No se pudo registrar la baja en {ARCHIVO_BAJAS}:\n{e}',
    )


def obtener_conteo_bajas():
  if os.path.exists(ARCHIVO_BAJAS):
    try:
      with open(ARCHIVO_BAJAS, 'r', encoding='utf-8') as f:
        return len(json.load(f))
    except Exception:
      return 0
  return 0