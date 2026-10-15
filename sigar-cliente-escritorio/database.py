# -*- coding: utf-8 -*-
"""
Módulo de Persistencia Local y Respaldo - SIGART UNELLEZ VIPI
Proporciona operaciones I/O atómicas sobre archivos JSON y conexión de respaldo en la nube.
"""
import datetime
import json
import os
import shutil
import sys
from tkinter import messagebox, simpledialog

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def obtener_ruta_base():
    """Retorna la carpeta donde se encuentra el .exe compilado o el script en ejecución."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DIR_ACTUAL = obtener_ruta_base()

ARCHIVO_BIENES = os.path.join(DIR_ACTUAL, "bienes.json")
ARCHIVO_BAJAS = os.path.join(DIR_ACTUAL, "bajas.json")
ARCHIVO_TRASLADOS = os.path.join(DIR_ACTUAL, "traslados.json")
ARCHIVO_CONFIG = os.path.join(DIR_ACTUAL, "config.json")

URL_RESPALDO_CLOUD = (
    "https://script.google.com/macros/s/AKfycbx1XpJ3iOdqa1mPsivMLLjGF0-hZ_IwLXgTadbqSO66Nb7yzVC5E2s3BTlUpUMbG3TF3w/exec"
)


def _guardar_archivo_atomico(ruta_destino, datos):
    """Escribe los datos de forma atómica para evitar corrupción de archivos."""
    ruta_tmp = ruta_destino + ".tmp"
    ruta_bak = ruta_destino + ".bak"
    try:
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())

        if os.path.exists(ruta_destino):
            try:
                shutil.copyfile(ruta_destino, ruta_bak)
            except Exception:
                pass

        if os.path.exists(ruta_destino):
            os.replace(ruta_tmp, ruta_destino)
        else:
            os.rename(ruta_tmp, ruta_destino)
        return True
    except Exception as e:
        if os.path.exists(ruta_tmp):
            try:
                os.remove(ruta_tmp)
            except Exception:
                pass
        raise e


def cargar_datos_locales():
    """Carga los activos registrados en bienes.json."""
    if not os.path.exists(ARCHIVO_BIENES):
        return []
    try:
        with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        ruta_bak = ARCHIVO_BIENES + ".bak"
        if os.path.exists(ruta_bak):
            try:
                with open(ruta_bak, "r", encoding="utf-8") as f_bak:
                    return json.load(f_bak)
            except Exception:
                pass
        messagebox.showerror("Error de Lectura", f"No se pudo cargar {ARCHIVO_BIENES}:\n{e}")
        return []


def guardar_datos_locales(bienes):
    """Guarda la lista completa de bienes de forma atómica en bienes.json."""
    try:
        return _guardar_archivo_atomico(ARCHIVO_BIENES, bienes)
    except Exception as e:
        messagebox.showerror("Error de Escritura", f"No se pudo guardar la información en {ARCHIVO_BIENES}:\n{e}")
        return False


def cargar_historial_bajas():
    """Retorna la lista completa de activos desincorporados guardados en bajas.json."""
    if not os.path.exists(ARCHIVO_BAJAS):
        return []
    try:
        with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error de Lectura", f"No se pudo cargar el historial de bajas:\n{e}")
        return []


def cargar_bajas_locales():
    """Alias para cargar el historial de bajas."""
    return cargar_historial_bajas()


def guardar_baja_local(registro_baja):
    """Guarda un nuevo registro de desincorporación en bajas.json de forma atómica."""
    bajas = cargar_historial_bajas()
    bajas.append(registro_baja)
    try:
        return _guardar_archivo_atomico(ARCHIVO_BAJAS, bajas)
    except Exception as e:
        messagebox.showerror("Error de Registro", f"No se pudo guardar la baja en {ARCHIVO_BAJAS}:\n{e}")
        return False


def obtener_conteo_bajas():
    """Retorna la cantidad de activos dados de baja."""
    return len(cargar_historial_bajas())


def restaurar_baja_local(id_bien):
    """Restaura un bien desincorporado reintegrándolo al archivo principal de activos."""
    bajas = cargar_historial_bajas()
    bien_a_restaurar = next((b for b in bajas if b.get("id") == id_bien), None)

    if not bien_a_restaurar:
        return False, f"No se encontró el activo ID {id_bien} en las bajas."

    bajas_actualizadas = [b for b in bajas if b.get("id") != id_bien]
    try:
        _guardar_archivo_atomico(ARCHIVO_BAJAS, bajas_actualizadas)
    except Exception as e:
        return False, f"Error al actualizar el registro de bajas: {e}"

    bienes = cargar_datos_locales()
    nuevo_bien = {
        "id": bien_a_restaurar.get("id"),
        "nombre": bien_a_restaurar.get("nombre"),
        "asignado_a": bien_a_restaurar.get("asignado_a", "Departamento de Sistemas"),
        "mantenimiento": bien_a_restaurar.get("mantenimiento", "No"),
        "fecha_mant": bien_a_restaurar.get("fecha_ultimo_mant", datetime.date.today().strftime("%d/%m/%Y")),
        "proximo_mant": bien_a_restaurar.get("proximo_mant", "N/A"),
        "desc_mant": bien_a_restaurar.get("desc_mant", "Reincorporado desde Bajas"),
        "detalles_tecnicos": bien_a_restaurar.get("detalles_tecnicos", {}),
        "perifericos": bien_a_restaurar.get("perifericos", {})
    }

    bienes.append(nuevo_bien)
    if guardar_datos_locales(bienes):
        return True, f"El activo ID {id_bien} fue reincorporado exitosamente al inventario activo."
    return False, "Error al guardar el activo en el inventario principal."


def registrar_traslado_local(registro_traslado):
    """Guarda un registro de traslado en el historial local traslados.json."""
    traslados = []
    if os.path.exists(ARCHIVO_TRASLADOS):
        try:
            with open(ARCHIVO_TRASLADOS, "r", encoding="utf-8") as f:
                traslados = json.load(f)
        except Exception:
            traslados = []
    traslados.append(registro_traslado)
    try:
        return _guardar_archivo_atomico(ARCHIVO_TRASLADOS, traslados)
    except Exception as e:
        print(f"Error al registrar traslado: {e}")
        return False


def exportar_respaldo_nube_bd(parent_window=None):
    """Envía un paquete de respaldo local a Google Sheets vía Web App."""
    if not HAS_REQUESTS:
        messagebox.showerror(
            "Librería Requerida",
            "La librería 'requests' no está disponible en este entorno.",
            parent=parent_window,
        )
        return

    correo = simpledialog.askstring(
        "Respaldo en la Nube",
        "Ingrese el correo institucional autorizado para el respaldo:",
        parent=parent_window,
    )
    if not correo:
        return

    if "@" not in correo or "." not in correo:
        messagebox.showerror("Correo Inválido", "El formato del correo ingresado es incorrecto.", parent=parent_window)
        return

    lista_bienes = cargar_datos_locales()
    payload = {
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "correo": correo.strip(),
        "total_bienes": len(lista_bienes),
        "datos_bienes_json": json.dumps(lista_bienes, ensure_ascii=False),
    }

    try:
        res = requests.post(URL_RESPALDO_CLOUD, json=payload, timeout=15)
        if res.status_code in (200, 201):
            messagebox.showinfo(
                "Respaldo en la Nube",
                f"¡Respaldo sincronizado exitosamente con la nube!\nIdentificador: {correo}",
                parent=parent_window,
            )
        else:
            messagebox.showerror("Error en Nube", f"Respuesta del servidor ({res.status_code}):\n{res.text}", parent=parent_window)
    except Exception as e:
        messagebox.showerror("Error de Red", f"Fallo al conectar con el servicio en la nube:\n{e}", parent=parent_window)


def exportar_bd(ruta_destino):
    """Genera una copia íntegra del archivo de base de datos en la ruta solicitada."""
    try:
        if not os.path.exists(ARCHIVO_BIENES):
            guardar_datos_locales([])
        shutil.copyfile(ARCHIVO_BIENES, ruta_destino)
        return True, "Copia de respaldo exportada exitosamente."
    except Exception as e:
        return False, f"Fallo al exportar respaldo: {e}"


def importar_bd(ruta_origen):
    """Restaura la base de datos principal desde un archivo JSON externo."""
    try:
        with open(ruta_origen, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if not isinstance(datos, list):
            return False, "El archivo seleccionado no posee el formato de lista de bienes válido."
        guardar_datos_locales(datos)
        return True, "Base de datos restaurada correctamente."
    except Exception as e:
        return False, f"Fallo al importar la base de datos: {e}"

def actualizar_asignacion_bienes_trasladados(ids_trasladados, nuevo_destino):
    """Actualiza en bienes.json la dependencia asignada de los activos que fueron trasladados."""
    bienes = cargar_datos_locales()
    ids_set = {str(i) for i in ids_trasladados}
    modificado = False
    for b in bienes:
        if str(b.get("id")) in ids_set:
            b["asignado_a"] = nuevo_destino
            modificado = True
    if modificado:
        guardar_datos_locales(bienes)
    return modificado