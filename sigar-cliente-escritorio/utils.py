# -*- coding: utf-8 -*-
import calendar
import os
import sys
from datetime import date, datetime, timedelta
from tkinter import messagebox

# Importaciones opcionales con fallback
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def obtener_ruta_escritura_salida(nombre_archivo):
    """Obtiene la ruta física absoluta de la carpeta del ejecutable (.exe) o script."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nombre_archivo)


def calcular_fecha_habil_3_meses(fecha_base):
    m = fecha_base.month - 1 + 3
    y = fecha_base.year + m // 12
    m = m % 12 + 1
    d = min(fecha_base.day, calendar.monthrange(y, m)[1])
    proxima = date(y, m, d)
    if proxima.weekday() == 5:
        proxima += timedelta(days=2)
    elif proxima.weekday() == 6:
        proxima += timedelta(days=1)
    return proxima.strftime("%d/%m/%Y")


def generar_acta_baja(registro):
    nombre_base = f"Acta_Baja_ID_{registro['id']}"

    try:
        if HAS_REPORTLAB:
            archivo_pdf = obtener_ruta_escritura_salida(f"{nombre_base}.pdf")
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            width, height = letter

            c.setFont("Helvetica-Bold", 13)
            c.drawString(
                50,
                height - 50,
                "UNELLEZ - SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS (SIGAR)",
            )
            c.setFont("Helvetica-Bold", 11)
            c.drawString(
                50,
                height - 68,
                "ACTA DE DESINCORPORACIÓN Y BAJA OFICIAL DE ACTIVO",
            )
            c.setLineWidth(1)
            c.line(50, height - 76, width - 50, height - 76)

            c.setFont("Helvetica-Bold", 10)
            c.drawString(
                50,
                height - 105,
                f"Fecha de Procesamiento: {registro['fecha_baja']}",
            )
            c.drawString(
                50, height - 120, f"Código de Activo (ID): {registro['id']}"
            )

            y = height - 155
            c.drawString(50, y, "DETALLES DEL EQUIPO / BIEN:")
            c.setFont("Helvetica", 10)
            c.drawString(
                70, y - 18, f"• Descripción / Equipo: {registro['nombre']}"
            )
            c.drawString(
                70, y - 34, f"• Asignación Previa: {registro['asignado_a']}"
            )
            c.drawString(
                70, y - 50, f"• Estado de Mantenimiento: {registro['mantenimiento']}"
            )
            c.drawString(
                70,
                y - 66,
                f"• Último Mantenimiento: {registro['fecha_ultimo_mant']}",
            )
            if registro.get("desc_mant"):
                c.drawString(
                    70,
                    y - 82,
                    f"• Detalle Mantenimiento: {registro['desc_mant']}",
                )

            y_motivo = y - 115
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_motivo, "JUSTIFICACIÓN / MOTIVO DE LA BAJA:")

            text_object = c.beginText(70, y_motivo - 18)
            text_object.setFont("Helvetica", 10)
            palabras = registro.get("motivo_baja", "").split()
            linea = ""
            for word in palabras:
                if len(linea + " " + word) < 75:
                    linea += (" " if linea else "") + word
                else:
                    text_object.textLine(linea)
                    linea = word
            if linea:
                text_object.textLine(linea)
            c.drawText(text_object)

            y_firma = 140
            c.setLineWidth(0.8)
            c.line(70, y_firma, 240, y_firma)
            c.line(330, y_firma, 500, y_firma)

            c.setFont("Helvetica", 9)
            c.drawCentredString(
                155, y_firma - 15, "Responsable del Bien / Unidad"
            )
            c.drawCentredString(
                415, y_firma - 15, "Autorizado por (Unidad de Bienes UNELLEZ)"
            )

            c.drawCentredString(
                width / 2,
                40,
                "Documento oficial generado automáticamente por SIGAR V2.5",
            )
            c.save()
            return archivo_pdf
        else:
            archivo_txt = obtener_ruta_escritura_salida(f"{nombre_base}.txt")
            contenido = f"""======================================================================
UNELLEZ - SIGAR (SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS)
ACTA OFICIAL DE DESINCORPORACIÓN Y BAJA DE ACTIVO
======================================================================
Fecha de Procesamiento: {registro['fecha_baja']}
ID del Activo:           {registro['id']}

DETALLES DEL EQUIPO:
----------------------------------------------------------------------
Nombre / Descripción:    {registro['nombre']}
Asignación Anterior:     {registro['asignado_a']}
Mantenimiento:           {registro['mantenimiento']}
Último Mantenimiento:    {registro['fecha_ultimo_mant']}
Detalle Mantenimiento:   {registro.get('desc_mant', '')}

JUSTIFICACIÓN / MOTIVO DE LA BAJA:
----------------------------------------------------------------------
{registro.get('motivo_baja', '')}

======================================================================
FIRMAS AUTORIZADAS:


__________________________              __________________________
Responsable del Equipo                  Unidad de Bienes UNELLEZ
======================================================================
"""
            with open(archivo_txt, "w", encoding="utf-8") as f:
                f.write(contenido)
            return archivo_txt

    except Exception as e:
        messagebox.showerror(
            "Error al generar Acta",
            f"No se pudo guardar el archivo de la baja:\n\n{e}",
        )
        return None
