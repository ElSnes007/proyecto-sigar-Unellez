# -*- coding: utf-8 -*-
import datetime
import json
import os
import sys
from tkinter import messagebox, simpledialog
import requests


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

# URL del Web App de Google Apps Script para respaldos en la nube
URL_RESPALDO_CLOUD = 'https://script.google.com/macros/s/AKfycbx1XpJ3iOdqa1mPsivMLLjGF0-hZ_IwLXgTadbqSO66Nb7yzVC5E2s3BTlUpUMbG3TF3w/exec'


def cargar_datos_locales():
  """Carga los datos locales del sistema desde bienes.json."""
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
  """Guarda los datos en el almacenamiento local en bienes.json."""
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


def cargar_historial_bajas():
  """Retorna la lista completa de activos dados de baja guardados en bajas.json."""
  if not os.path.exists(ARCHIVO_BAJAS):
    return []
  try:
    with open(ARCHIVO_BAJAS, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception as e:
    messagebox.showerror(
        'Error de Lectura',
        f'No se pudieron cargar los datos de desincorporaciones ({ARCHIVO_BAJAS}):\n{e}',
    )
    return []


def guardar_baja_local(registro_baja):
  """Guarda un nuevo registro de baja en bajas.json."""
  bajas = cargar_historial_bajas()
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
  """Retorna el número de registros guardados en bajas.json."""
  return len(cargar_historial_bajas())


# --- FUNCIÓN REAL PARA EL RESPALDO EN LA NUBE ---
def exportar_respaldo_nube_bd(parent_window=None):
  """Solicita el correo, empaqueta los bienes locales en JSON y los envía a Google Sheets."""
  # 1. Solicitar el correo mediante ventana emergente vinculada al padre
  correo = simpledialog.askstring(
      'Correo para la Nube',
      'Ingrese el correo electrónico vinculado para el respaldo:',
      parent=parent_window,
  )

  if not correo:
    return  # Si el usuario cancela, no hace nada

  if '@' not in correo or '.' not in correo:
    messagebox.showerror(
        'Error',
        'El correo electrónico ingresado no es válido.',
        parent=parent_window,
    )
    return

  # 2. Cargar los datos locales reales desde bienes.json
  lista_bienes = cargar_datos_locales()
  total_bienes = len(lista_bienes)
  fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  # 3. Preparar el paquete con las columnas exactas de tu Google Sheets
  payload = {
      'fecha': fecha_actual,
      'correo': correo.strip(),
      'total_bienes': total_bienes,
      'datos_bienes_json': json.dumps(lista_bienes, ensure_ascii=False),
  }

  try:
    # 4. Enviar los datos a la nube mediante una petición HTTP POST real
    response = requests.post(URL_RESPALDO_CLOUD, json=payload, timeout=15)

    if response.status_code == 200 or response.status_code == 201:
      messagebox.showinfo(
          'Éxito',
          f'¡Respaldo enviado y registrado en Google Sheets con éxito!\nAsociado a: {correo}',
          parent=parent_window,
      )
    else:
      messagebox.showerror(
          'Error del Servidor',
          f'No se pudo guardar en la nube (Código {response.status_code}):\n{response.text}',
          parent=parent_window,
      )

  except requests.exceptions.RequestException as e:
    messagebox.showerror(
        'Error de Conexión',
        f'No se pudo conectar con Google Apps Script.\nVerifique su conexión a internet.\n\nDetalles: {str(e)}',
        parent=parent_window,
    )