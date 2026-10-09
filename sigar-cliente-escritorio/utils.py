# -*- coding: utf-8 -*-
"""
SIGAR (UNELLEZ) - utils.py
Cálculos de fechas hábiles, detección de periféricos y generación de actas de desincorporación.
Compatible con Python 3.8.10+
"""
import os
import calendar
import unicodedata
from datetime import datetime, date, timedelta

# Importaciones opcionales con fallback seguro
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


# Palabras clave que indican activo informático compuesto
PALABRAS_CLAVE_COMPUESTOS = [
    "computadora", "computador", "pc", "escritorio", "desktop",
    "laptop", "portatil", "portátil", "servidor", "server",
    "all in one", "aio", "workstation", "estacion de trabajo",
    "estación de trabajo", "ordenador", "cpu", "clon", "clone"
]


def es_activo_compuesto(texto):
    """Evalúa si la descripción o nombre corresponde a un equipo compuesto con periféricos."""
    if not texto:
        return False
    def quitar_tildes(cadena):
        return ''.join(c for c in unicodedata.normalize('NFD', cadena) if unicodedata.category(c) != 'Mn')
    
    texto_norm = quitar_tildes(str(texto).lower().strip())
    for clave in PALABRAS_CLAVE_COMPUESTOS:
        if quitar_tildes(clave) in texto_norm:
            return True
    return False


def calcular_fecha_habil_3_meses(fecha_base):
    """Calcula la próxima fecha de mantenimiento regular a 3 meses hábiles."""
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
    """Genera el acta oficial de desincorporación en formato PDF o TXT de respaldo."""
    nombre_base = f"Acta_Baja_ID_{registro.get('id', 'N/A')}"
    
    if HAS_REPORTLAB:
        archivo_pdf = f"{nombre_base}.pdf"
        c = canvas.Canvas(archivo_pdf, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, height - 50, "UNELLEZ - SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS (SIGAR)")
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, height - 68, "ACTA DE DESINCORPORACIÓN Y BAJA OFICIAL DE ACTIVO")
        c.setLineWidth(1)
        c.line(50, height - 76, width - 50, height - 76)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 105, f"Fecha de Procesamiento: {registro.get('fecha_baja', 'N/A')}")
        c.drawString(50, height - 120, f"Código de Activo (ID): {registro.get('id', 'N/A')}")
        
        y = height - 150
        c.drawString(50, y, "DETALLES DEL EQUIPO / BIEN:")
        c.setFont("Helvetica", 10)
        c.drawString(70, y - 18, f"• Descripción / Equipo: {registro.get('nombre', 'N/A')}")
        c.drawString(70, y - 34, f"• Asignación Previa: {registro.get('asignado_a', 'N/A')}")
        c.drawString(70, y - 50, f"• Estado de Mantenimiento: {registro.get('mantenimiento', 'N/A')}")
        c.drawString(70, y - 66, f"• Último Mantenimiento: {registro.get('fecha_ultimo_mant', 'N/A')}")
        if registro.get('desc_mant'):
            c.drawString(70, y - 82, f"• Detalle Mantenimiento: {registro.get('desc_mant')}")
            
        # Desglose de Periféricos si existen
        perifs = registro.get("perifericos")
        offset = 98
        if perifs and isinstance(perifs, dict):
            c.setFont("Helvetica-Bold", 9)
            c.drawString(70, y - offset, "• Desglose de Periféricos al momento de la baja:")
            offset += 14
            c.setFont("Helvetica", 8)
            for k, nom in [("monitor", "Monitor"), ("teclado", "Teclado"), ("mouse", "Mouse"), ("cpu", "CPU/Internos")]:
                p_data = perifs.get(k, {})
                c.drawString(85, y - offset, f"- {nom}: [{p_data.get('estado', 'N/A')}] {p_data.get('detalle', '')}")
                offset += 12

        y_motivo = y - offset - 15
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_motivo, "JUSTIFICACIÓN / MOTIVO DE LA BAJA:")
        
        text_object = c.beginText(70, y_motivo - 18)
        text_object.setFont("Helvetica", 10)
        palabras = str(registro.get('motivo_baja', '')).split()
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
        
        y_firma = 120
        c.setLineWidth(0.8)
        c.line(70, y_firma, 240, y_firma)
        c.line(330, y_firma, 500, y_firma)
        
        c.setFont("Helvetica", 9)
        c.drawCentredString(155, y_firma - 15, "Responsable del Bien / Unidad")
        c.drawCentredString(415, y_firma - 15, "Autorizado por (Unidad de Bienes UNELLEZ)")
        
        c.drawCentredString(width / 2, 35, "Documento oficial generado automáticamente por SIGAR V2.5")
        c.save()
        return archivo_pdf
    else:
        archivo_txt = f"{nombre_base}.txt"
        perifs = registro.get("perifericos", {})
        perifs_txt = ""
        if perifs:
            perifs_txt = "\nDESGLOSE DE PERIFÉRICOS:\n----------------------------------------------------------------------\n"
            for k, nom in [("monitor", "Monitor"), ("teclado", "Teclado"), ("mouse", "Mouse"), ("cpu", "CPU/Internos")]:
                p_data = perifs.get(k, {})
                perifs_txt += f"- {nom}: [{p_data.get('estado', 'N/A')}] {p_data.get('detalle', '')}\n"

        contenido = f"""======================================================================
UNELLEZ - SIGAR (SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS)
ACTA OFICIAL DE DESINCORPORACIÓN Y BAJA DE ACTIVO
======================================================================
Fecha de Procesamiento: {registro.get('fecha_baja', 'N/A')}
ID del Activo:           {registro.get('id', 'N/A')}

DETALLES DEL EQUIPO:
----------------------------------------------------------------------
Nombre / Descripción:    {registro.get('nombre', 'N/A')}
Asignación Anterior:     {registro.get('asignado_a', 'N/A')}
Mantenimiento:           {registro.get('mantenimiento', 'N/A')}
Último Mantenimiento:    {registro.get('fecha_ultimo_mant', 'N/A')}
Detalle Mantenimiento:   {registro.get('desc_mant', '')}
{perifs_txt}
JUSTIFICACIÓN / MOTIVO DE LA BAJA:
----------------------------------------------------------------------
{registro.get('motivo_baja', '')}

======================================================================
FIRMAS AUTORIZADAS:


__________________________              __________________________
Responsable del Equipo                  Unidad de Bienes UNELLEZ
======================================================================
"""
        with open(archivo_txt, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return archivo_txt