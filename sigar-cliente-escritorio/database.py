# -*- coding: utf-8 -*-
import datetime
import json
import os
import shutil
import sys
from tkinter import messagebox, simpledialog
import requests


def obtener_ruta_base():
    """Retorna la carpeta donde se encuentra el .exe compilado
    o el directorio del script en modo desarrollo.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
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


def exportar_respaldo_nube_bd(parent_window=None):
    """Solicita el correo, empaqueta los bienes locales en JSON y los envía a Google Sheets."""
    correo = simpledialog.askstring(
        'Correo para la Nube',
        'Ingrese el correo electrónico vinculado para el respaldo:',
        parent=parent_window,
    )

    if not correo:
        return

    if '@' not in correo or '.' not in correo:
        messagebox.showerror(
            'Error',
            'El correo electrónico ingresado no es válido.',
            parent=parent_window,
        )
        return

    lista_bienes = cargar_datos_locales()
    total_bienes = len(lista_bienes)
    fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    payload = {
        'fecha': fecha_actual,
        'correo': correo.strip(),
        'total_bienes': total_bienes,
        'datos_bienes_json': json.dumps(lista_bienes, ensure_ascii=False),
    }

    try:
        response = requests.post(URL_RESPALDO_CLOUD, json=payload, timeout=15)

        if response.status_code in (200, 201):
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


def exportar_bd(ruta_destino):
    """Crea una copia de seguridad del archivo de bienes en la ruta seleccionada."""
    try:
        if not os.path.exists(ARCHIVO_BIENES):
            # Si no existe aún el JSON, crear uno vacío para evitar errores
            guardar_datos_locales([])
        shutil.copy(ARCHIVO_BIENES, ruta_destino)
        return True, "Copia de seguridad creada con éxito."
    except Exception as e:
        return False, f"Error al exportar la base de datos: {e}"


def importar_bd(ruta_origen):
    """Restaura la base de datos desde un archivo JSON externo."""
    try:
        shutil.copy(ruta_origen, ARCHIVO_BIENES)
        return True, "Base de datos restaurada correctamente."
    except Exception as e:
        return False, f"Error al importar la base de datos: {e}"


def cargar_bajas_locales():
    """Devuelve el historial de activos desincorporados."""
    return cargar_historial_bajas()


def restaurar_baja_local(id_bien):
    """Elimina el activo de bajas.json y lo reincorpora a bienes.json."""
    bajas = cargar_historial_bajas()
    bien_a_restaurar = next((b for b in bajas if b.get("id") == id_bien), None)

    if not bien_a_restaurar:
        return False, f"No se encontró el activo ID {id_bien} en el registro de bajas."

    bajas_actualizadas = [b for b in bajas if b.get("id") != id_bien]
    try:
        with open(ARCHIVO_BAJAS, 'w', encoding='utf-8') as f:
            json.dump(bajas_actualizadas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        return False, f"Error al actualizar bajas.json: {e}"

    bienes = cargar_datos_locales()
    nuevo_bien = {
        "id": bien_a_restaurar.get("id"),
        "nombre": bien_a_restaurar.get("nombre"),
        "asignado_a": bien_a_restaurar.get("asignado_a", "Departamento de Sistemas"),
        "mantenimiento": bien_a_restaurar.get("mantenimiento", "No"),
        "fecha_mant": bien_a_restaurar.get("fecha_ultimo_mant", "N/A"),
        "proximo_mant": "N/A",
        "desc_mant": bien_a_restaurar.get("desc_mant", ""),
    }

    bienes.append(nuevo_bien)
    if guardar_datos_locales(bienes):
        return True, f"El activo ID {id_bien} fue reincorporado con éxito al inventario."
    else:
        return False, "Error al guardar el activo en bienes.json."