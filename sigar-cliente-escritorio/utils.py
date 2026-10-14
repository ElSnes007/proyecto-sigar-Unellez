# -*- coding: utf-8 -*-
import calendar
import os
import sys
import unicodedata
from datetime import date, datetime, timedelta
from tkinter import messagebox

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


# Lista oficial de tipos de activos del sistema SIGAR
TIPOS_ACTIVOS_VALIDOS = [
    "Seleccione el equipo",
    "Laptop",
    "Computadora de escritorio",
    "Impresora",
    "Router",
    "Switch de red"
]


def obtener_ruta_escritura_salida(nombre_archivo):
    """Obtiene la ruta física absoluta de la carpeta del ejecutable (.exe) o script."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nombre_archivo)


def es_activo_compuesto(texto):
    """Evalúa si el tipo de activo requiere subformulario técnico de diagnóstico."""
    if not texto:
        return False
    texto_limpio = str(texto).strip()
    return any(tipo.lower() in texto_limpio.lower() for tipo in TIPOS_ACTIVOS_VALIDOS)


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
    """Genera el acta oficial de desincorporación en formato PDF o TXT con desglose técnico e impresiones seguras."""
    nombre_base = f"Acta_Baja_ID_{registro.get('id', 'N/A')}"
    detalles = registro.get("detalles_tecnicos") or registro.get("perifericos") or {}

    # Preparar texto de detalles técnicos según el tipo de activo
    lineas_tecnicas = []
    if detalles and isinstance(detalles, dict):
        if "pantalla" in detalles or "carcasa_puertos" in detalles:
            # Laptop
            for clave, nom in [("pantalla", "Pantalla"), ("teclado", "Teclado"), ("mouse_touchpad", "Mouse / Touchpad"), ("carcasa_puertos", "Carcasa / Puertos")]:
                d = detalles.get(clave, {})
                if isinstance(d, dict):
                    lineas_tecnicas.append(f"- {nom}: [{d.get('estado', 'N/A')}] {d.get('detalle', 'Sin observaciones')}")
        elif "impresion" in detalles or "copia" in detalles or "scanner" in detalles:
            # Impresora
            for clave, nom in [("impresion", "Impresión Simple"), ("copia", "Función Copia"), ("scanner", "Función Scanner")]:
                d = detalles.get(clave, {})
                if isinstance(d, dict):
                    lineas_tecnicas.append(f"- {nom}: [{d.get('estado', 'N/A')}] {d.get('detalle', 'Sin observaciones')}")
        elif "marca" in detalles and ("modelo" in detalles or "estado_general" in detalles):
            # Router o Switch de red
            marca = detalles.get("marca", "N/A")
            modelo = detalles.get("modelo", "N/A")
            estado = detalles.get("estado_general", "N/A")
            falla = detalles.get("detalle_falla", "Sin anomalías reportadas")
            lineas_tecnicas.append(f"- Marca: {marca} | Modelo: {modelo}")
            lineas_tecnicas.append(f"- Estado General: [{estado}]")
            if falla:
                lineas_tecnicas.append(f"- Descripción de Falla: {falla}")
        else:
            # Computadora de escritorio
            for clave, nom in [("monitor", "Monitor / Pantalla"), ("teclado", "Teclado"), ("mouse", "Mouse"), ("cpu", "CPU / Internos")]:
                d = detalles.get(clave, {})
                if isinstance(d, dict) and d:
                    lineas_tecnicas.append(f"- {nom}: [{d.get('estado', 'N/A')}] {d.get('detalle', 'Sin observaciones')}")

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
                f"Fecha de Procesamiento: {registro.get('fecha_baja', 'N/A')}",
            )
            c.drawString(
                50, height - 120, f"Código de Activo (ID): {registro.get('id', 'N/A')}"
            )

            y = height - 148
            c.drawString(50, y, "DETALLES DEL EQUIPO / BIEN:")
            c.setFont("Helvetica", 10)
            c.drawString(
                70, y - 16, f"• Descripción / Equipo: {registro.get('nombre', 'N/A')}"
            )
            c.drawString(
                70, y - 32, f"• Asignación Previa: {registro.get('asignado_a', 'N/A')}"
            )
            c.drawString(
                70, y - 48, f"• Estado de Mantenimiento: {registro.get('mantenimiento', 'N/A')}"
            )
            c.drawString(
                70,
                y - 64,
                f"• Último Mantenimiento: {registro.get('fecha_ultimo_mant', 'N/A')}",
            )
            if registro.get("desc_mant"):
                c.drawString(
                    70,
                    y - 80,
                    f"• Detalle Mantenimiento: {registro.get('desc_mant')}",
                )

            offset = 96
            if lineas_tecnicas:
                c.setFont("Helvetica-Bold", 9)
                c.drawString(70, y - offset, "• Evaluación Técnica y Diagnóstico Funcional:")
                offset += 14
                c.setFont("Helvetica", 8)
                for lin in lineas_tecnicas:
                    c.drawString(85, y - offset, lin)
                    offset += 12

            y_motivo = y - offset - 15
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_motivo, "JUSTIFICACIÓN / MOTIVO DE LA BAJA:")

            text_object = c.beginText(70, y_motivo - 18)
            text_object.setFont("Helvetica", 10)
            palabras = str(registro.get("motivo_baja", "")).split()
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
            c.line(width - 240, y_firma, width - 70, y_firma)

            c.setFont("Helvetica", 9)
            c.drawCentredString(
                155, y_firma - 14, "Firma del Responsable del Área"
            )
            c.drawCentredString(
                width - 155, y_firma - 14, "Auditoría / Bienes Nacionales UNELLEZ"
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
            contenido_lineas = [
                "=" * 72,
                "UNELLEZ - SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS (SIGAR)",
                "ACTA OFICIAL DE DESINCORPORACIÓN Y BAJA DE ACTIVO",
                "=" * 72,
                f"Fecha de Procesamiento: {registro.get('fecha_baja', 'N/A')}",
                f"ID del Activo:          {registro.get('id', 'N/A')}",
                "",
                "DETALLES DEL EQUIPO:",
                "-" * 72,
                f"Nombre / Descripción:    {registro.get('nombre', 'N/A')}",
                f"Asignación Anterior:     {registro.get('asignado_a', 'N/A')}",
                f"Mantenimiento:           {registro.get('mantenimiento', 'N/A')}",
                f"Último Mantenimiento:    {registro.get('fecha_ultimo_mant', 'N/A')}",
                f"Detalle Mantenimiento:   {registro.get('desc_mant', '')}",
                ""
            ]

            if lineas_tecnicas:
                contenido_lineas.append("EVALUACIÓN TÉCNICA Y DIAGNÓSTICO FUNCIONAL:")
                contenido_lineas.append("-" * 45)
                for lin in lineas_tecnicas:
                    contenido_lineas.append(lin)
                contenido_lineas.append("")

            contenido_lineas.extend([
                "JUSTIFICACIÓN / MOTIVO DE LA BAJA:",
                "-" * 72,
                f"{registro.get('motivo_baja', '')}",
                "",
                "=" * 72,
                "FIRMAS AUTORIZADAS:",
                "",
                "",
                "__________________________              __________________________",
                "Responsable del Equipo                  Unidad de Bienes UNELLEZ",
                "=" * 72,
            ])

            contenido = "\n".join(contenido_lineas)
            with open(archivo_txt, "w", encoding="utf-8") as f:
                f.write(contenido)
            return archivo_txt

    except Exception as e:
        messagebox.showerror(
            "Error al generar Acta",
            f"No se pudo guardar el archivo de la baja:\n\n{e}",
        )
        return None