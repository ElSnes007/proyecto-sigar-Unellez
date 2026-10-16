# -*- coding: utf-8 -*-
"""
Módulo de Utilidades, Validaciones y Generación de Documentación Institucional en PDF - SIGART UNELLEZ VIPI
Incluye parche de compatibilidad para Python 3.8 (Win32) y ReportLab.
"""
import calendar
import os
import sys
from datetime import date, datetime, timedelta
from tkinter import messagebox

# =========================================================================
# PARCHE DE COMPATIBILIDAD CRÍTICO PARA PYTHON 3.8 / WIN32 (usedforsecurity)
# =========================================================================
import hashlib
try:
    import _hashlib
    if hasattr(_hashlib, 'openssl_md5'):
        _orig_openssl_md5 = _hashlib.openssl_md5
        def _safe_openssl_md5(*args, **kwargs):
            kwargs.pop('usedforsecurity', None)
            return _orig_openssl_md5(*args, **kwargs)
        _hashlib.openssl_md5 = _safe_openssl_md5
except Exception:
    pass

_orig_hashlib_md5 = hashlib.md5
def _safe_hashlib_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _orig_hashlib_md5(*args, **kwargs)
hashlib.md5 = _safe_hashlib_md5

_orig_hashlib_new = hashlib.new
def _safe_hashlib_new(name, *args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _orig_hashlib_new(name, *args, **kwargs)
hashlib.new = _safe_hashlib_new
# =========================================================================

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


TIPOS_ACTIVOS_VALIDOS = (
    "Seleccione el equipo",
    "Laptop",
    "Computadora de escritorio",
    "Impresora",
    "Router",
    "Switch de red",
    "Escáner",
    "Monitor",
)


def es_verdadero(val):
    """Evalúa de forma estricta valores booleanos soportando string, numérico y bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("true", "si", "sí", "1", "s", "yes")
    return False


def obtener_ruta_escritura_salida(nombre_archivo):
    """Obtiene la ruta física absoluta de la carpeta de trabajo del ejecutable o script."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, nombre_archivo)


def validar_fecha_ddmmaaaa(fecha_str):
    """Valida si una cadena cumple con el formato DD/MM/AAAA y representa una fecha real."""
    if not fecha_str or len(fecha_str) != 10:
        return False
    partes = fecha_str.split("/")
    if len(partes) != 3:
        return False
    try:
        dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
        if anio < 1990 or anio > 2100:
            return False
        datetime(anio, mes, dia)
        return True
    except ValueError:
        return False


def calcular_fecha_habil_3_meses(fecha_base):
    """Calcula la próxima fecha de mantenimiento preventivo a 3 meses hábiles."""
    m = fecha_base.month - 1 + 3
    y = fecha_base.year + m // 12
    m = m % 12 + 1
    d = min(fecha_base.day, calendar.monthrange(y, m)[1])
    proxima = date(y, m, d)

    if proxima.weekday() == 5:      # Sábado -> Lunes
        proxima += timedelta(days=2)
    elif proxima.weekday() == 6:    # Domingo -> Lunes
        proxima += timedelta(days=1)

    return proxima.strftime("%d/%m/%Y")


# =========================================================================
# GENERADOR PDF: ACTA DE DESINCORPORACIÓN Y BAJA
# =========================================================================
def generar_acta_baja(registro):
    """Genera el Acta Oficial de Desincorporación y Baja en formato PDF institucional."""
    id_activo = registro.get("id", "N/A")
    nombre_pdf = f"Acta_Baja_ID_{id_activo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    archivo_salida = obtener_ruta_escritura_salida(nombre_pdf)

    detalles = registro.get("detalles_tecnicos") or registro.get("perifericos") or {}
    lineas_eval = []
    tipo = registro.get("nombre", "")

    if tipo == "Computadora de escritorio":
        cpu_info = detalles.get("cpu", {})
        lineas_eval.append(f"• CPU / Torre: [{cpu_info.get('estado', 'N/A')}] - {cpu_info.get('detalle', '')}")
        comp_int = cpu_info.get("componentes_internos", {})
        if comp_int:
            for k_c, v_c in comp_int.items():
                lineas_eval.append(f"  - {k_c.replace('_', ' ').capitalize()}: {v_c}")
        if es_verdadero(detalles.get("incluye_perifericos", False)):
            lineas_eval.append("• Modalidad: Combo Completo (Con Periféricos Vinculados)")
            for p_k, p_nom in [("monitor", "Monitor"), ("teclado", "Teclado"), ("mouse", "Mouse")]:
                p_dat = detalles.get(p_k, {})
                lineas_eval.append(f"  - {p_nom}: [{p_dat.get('estado', 'N/A')}] {p_dat.get('detalle', '')}")
        else:
            lineas_eval.append("• Modalidad: Chasis Individual (Sin Periféricos Vinculados)")

    elif tipo == "Laptop":
        for k, lbl in [("pantalla", "Pantalla"), ("teclado", "Teclado"), ("mouse_touchpad", "Mouse/Touchpad"), ("carcasa_puertos", "Carcasa/Puertos")]:
            inf = detalles.get(k, {})
            lineas_eval.append(f"• {lbl}: [{inf.get('estado', 'N/A')}] {inf.get('detalle', '')}")

    elif tipo == "Impresora":
        for k, lbl in [("impresion", "Impresión"), ("copia", "Copiado"), ("scanner", "Escáner")]:
            inf = detalles.get(k, {})
            lineas_eval.append(f"• {lbl}: [{inf.get('estado', 'N/A')}] {inf.get('detalle', '')}")

    elif tipo in ["Router", "Switch de red"]:
        lineas_eval.append(f"• Marca: {detalles.get('marca', 'N/A')} | Modelo: {detalles.get('modelo', 'N/A')}")
        lineas_eval.append(f"• Estado General: [{detalles.get('estado_general', 'N/A')}]")
        if detalles.get("detalle_falla"):
            lineas_eval.append(f"• Falla Especificada: {detalles.get('detalle_falla')}")
    else:
        for k, v in detalles.items():
            if isinstance(v, dict):
                lineas_eval.append(f"• {k.upper()}: [{v.get('estado', 'N/A')}] {v.get('detalle', '')}")

    if not HAS_REPORTLAB:
        archivo_txt = archivo_salida.replace(".pdf", ".txt")
        with open(archivo_txt, "w", encoding="utf-8") as f:
            f.write(f"ACTA DE BAJA ID {id_activo}\nMotivo: {registro.get('motivo_baja')}")
        return archivo_txt

    try:
        c = canvas.Canvas(archivo_salida, pagesize=letter)
        w, h = letter

        # Membrete institucional
        c.setFillColorRGB(0.0, 0.17, 0.29)  # Azul UNELLEZ
        c.rect(40, h - 55, w - 80, 30, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 42, "UNIVERSIDAD NACIONAL EXPERIMENTAL DE LOS LLANOS OCCIDENTALES 'EZEQUIEL ZAMORA'")
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(w / 2, h - 51, "COORDINACIÓN DE TECNOLOGÍA Y SERVICIOS DE INFORMACIÓN (CTSI) - UNELLEZ VIPI")

        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, h - 75, "ACTA OFICIAL DE DESINCORPORACIÓN Y BAJA DE ACTIVO")
        c.setLineWidth(0.8)
        c.setStrokeColorRGB(0.8, 0.4, 0.0)
        c.line(40, h - 82, w - 40, h - 82)

        # Metadatos del registro
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, h - 100, f"Referencia: CTSI-BAJA-{id_activo}-{datetime.now().strftime('%Y%m%d')}")
        c.drawString(380, h - 100, f"Fecha: {registro.get('fecha_baja', datetime.now().strftime('%d/%m/%Y %H:%M'))}")

        # Bloque 1: Identificación
        y = h - 120
        c.setFillColorRGB(0.93, 0.95, 0.98)
        c.rect(40, y - 5, w - 80, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.0, 0.2, 0.4)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, y, "1. IDENTIFICACIÓN Y ASIGNACIÓN DEL BIEN")

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        y -= 18
        c.drawString(50, y, f"• Código ID: #{id_activo}")
        c.drawString(200, y, f"• Tipo de Bien: {registro.get('nombre', 'N/A')}")
        y -= 14
        c.drawString(50, y, f"• Dependencia Anterior: {registro.get('asignado_a', 'N/A')}")
        c.drawString(350, y, f"• Régimen Mant.: {registro.get('mantenimiento', 'N/A')}")
        y -= 14
        c.drawString(50, y, f"• Última Fecha Mant.: {registro.get('fecha_ultimo_mant', 'N/A')}")
        if registro.get("desc_mant"):
            y -= 14
            c.drawString(50, y, f"• Observación Previa: {registro.get('desc_mant')[:80]}")

        # Bloque 2: Evaluación Técnica
        y -= 22
        c.setFillColorRGB(0.93, 0.95, 0.98)
        c.rect(40, y - 5, w - 80, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.0, 0.2, 0.4)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, y, "2. EVALUACIÓN Y DIAGNÓSTICO TÉCNICO DE SALIDA")

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 8)
        y -= 16
        for linea in lineas_eval[:8]:
            c.drawString(50, y, linea[:95])
            y -= 12

        # Bloque 3: Justificación
        y -= 10
        c.setFillColorRGB(0.93, 0.95, 0.98)
        c.rect(40, y - 5, w - 80, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.0, 0.2, 0.4)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, y, "3. MOTIVO Y JUSTIFICACIÓN TÉCNICA DE LA DESINCORPORACIÓN")

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        y -= 18
        motivo = registro.get("motivo_baja", "Sin justificación.")
        palabras = motivo.split()
        l_txt = ""
        for p in palabras:
            if len(l_txt + " " + p) < 95:
                l_txt += (" " if l_txt else "") + p
            else:
                c.drawString(50, y, l_txt)
                y -= 13
                l_txt = p
        if l_txt:
            c.drawString(50, y, l_txt)

        # Firmas
        y_firma = 110
        c.setLineWidth(0.7)
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.line(55, y_firma, 205, y_firma)
        c.line(235, y_firma, 385, y_firma)
        c.line(415, y_firma, 565, y_firma)

        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(130, y_firma - 12, "RESPONSABLE DEL ÁREA")
        c.drawCentredString(310, y_firma - 12, "COORDINACIÓN CTSI VIPI")
        c.drawCentredString(490, y_firma - 12, "BIENES PÚBLICOS / AUDITORÍA")

        c.setFont("Helvetica", 7)
        c.drawCentredString(130, y_firma - 22, "Entrega y Custodia")
        c.drawCentredString(310, y_firma - 22, "Evaluación Técnica")
        c.drawCentredString(490, y_firma - 22, "Control Patrimonial")

        # Pie
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(45, 35, "Documento oficial generado por la plataforma SIGART — UNELLEZ VIPI")
        c.drawRightString(w - 45, 35, f"Impreso: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        c.save()
        return archivo_salida
    except Exception as e:
        messagebox.showerror("Error al Generar PDF", f"Fallo al emitir el documento PDF:\n{e}")
        return None


# =========================================================================
# GENERADOR PDF: ACTA DE TRASLADO DE EQUIPOS
# =========================================================================
def generar_acta_traslado(datos_traslado):
    """Genera el Acta Oficial de Traslado de Equipos Tecnológicos en formato PDF."""
    ref_acta = datos_traslado.get("referencia", f"TRASLADO-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    nombre_pdf = f"Acta_{ref_acta}.pdf"
    archivo_salida = obtener_ruta_escritura_salida(nombre_pdf)

    if not HAS_REPORTLAB:
        archivo_txt = archivo_salida.replace(".pdf", ".txt")
        with open(archivo_txt, "w", encoding="utf-8") as f:
            f.write(f"ACTA DE TRASLADO {ref_acta}")
        return archivo_txt

    try:
        c = canvas.Canvas(archivo_salida, pagesize=letter)
        w, h = letter

        # Membrete institucional superior
        c.setFillColorRGB(0.0, 0.17, 0.29)
        c.rect(40, h - 55, w - 80, 30, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 42, "UNIVERSIDAD NACIONAL EXPERIMENTAL DE LOS LLANOS OCCIDENTALES 'EZEQUIEL ZAMORA'")
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(w / 2, h - 51, "COORDINACIÓN DE TECNOLOGÍA Y SERVICIOS DE INFORMACIÓN (CTSI) - VICERRECTORADO VIPI")

        # Título del documento
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, h - 75, "ACTA OFICIAL DE TRASLADO Y CUSTODIA DE EQUIPOS")
        c.setLineWidth(0.8)
        c.setStrokeColorRGB(0.8, 0.4, 0.0)
        c.line(40, h - 82, w - 40, h - 82)

        # Referencia y fecha
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, h - 100, f"Referencia: CTSI-{ref_acta}")
        c.drawString(380, h - 100, f"Fecha de Emisión: {datos_traslado.get('fecha', datetime.now().strftime('%d/%m/%Y'))}")

        # Bloque 1: Ubicaciones
        y = h - 120
        c.setFillColorRGB(0.93, 0.95, 0.98)
        c.rect(40, y - 5, w - 80, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.0, 0.2, 0.4)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, y, "1. PROCEDENCIA Y DESTINO DEL TRASLADO")

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        y -= 17
        c.drawString(50, y, f"• Dependencia(s) de Origen: {datos_traslado.get('origen', 'N/A')[:85]}")
        y -= 14
        c.drawString(50, y, f"• Dependencia de Destino:   {datos_traslado.get('destino', 'N/A')}")
        y -= 14
        c.drawString(50, y, f"• Motivo del Traslado:     {datos_traslado.get('motivo', 'Reasignación operativa')[:85]}")
        y -= 14
        c.drawString(50, y, f"• Condiciones de Entrega:   {datos_traslado.get('observaciones', 'Equipos verificados')[:85]}")

        # Bloque 2: Tabla de Equipos (AQUÍ ESTÁ EXACTAMENTE UNA SOLA VEZ)
        y -= 22
        c.setFillColorRGB(0.93, 0.95, 0.98)
        c.rect(40, y - 5, w - 80, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.0, 0.2, 0.4)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(45, y, "2. RELACIÓN DE EQUIPOS Y ACTIVOS A TRASLADAR")

        # Cabecera de la tabla
        y -= 18
        c.setFillColorRGB(0.85, 0.88, 0.92)
        c.rect(45, y - 4, w - 90, 14, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y, "N°")
        c.drawString(75, y, "ID")
        c.drawString(110, y, "Descripción del Activo")
        c.drawString(330, y, "Asignación Previa")
        c.drawString(490, y, "Estado")

        # Filas de la tabla de equipos
        c.setFont("Helvetica", 8)
        y -= 14
        for idx, it in enumerate(datos_traslado.get("equipos", []), start=1):
            if y < 140:
                break
            c.drawString(50, y, f"{idx:02d}")
            c.drawString(75, y, f"#{it.get('id', 'N/A')}")
            c.drawString(110, y, str(it.get('nombre', 'Equipo'))[:45])
            c.drawString(330, y, str(it.get('asignado_a', 'N/A'))[:32])
            c.drawString(490, y, "Operativo")
            y -= 12

        # Cláusula de Custodia
        y = min(y - 8, 160)
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(45, y, "El custodio receptor asume la guarda, conservación y uso debido de los bienes a partir de la firma de la presente acta.")

        # Bloque de Firmas
        y_firma = 100
        c.setLineWidth(0.7)
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.line(55, y_firma, 205, y_firma)
        c.line(235, y_firma, 385, y_firma)
        c.line(415, y_firma, 565, y_firma)

        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(130, y_firma - 12, "AUTORIZADO POR")
        c.drawCentredString(310, y_firma - 12, "RECIBIDO CONFORME")
        c.drawCentredString(490, y_firma - 12, "CONTROL PATRIMONIAL")

        c.setFont("Helvetica", 7)
        jefe_nom = datos_traslado.get("firma_jefe_nombre", "Jefe de CTSI")
        rec_nom = datos_traslado.get("firma_receptor_nombre", "Custodio Receptor")
        c.drawCentredString(130, y_firma - 22, f"{jefe_nom}")
        c.drawCentredString(130, y_firma - 31, f"C.I.: {datos_traslado.get('firma_jefe_ci', 'V-')}")

        c.drawCentredString(310, y_firma - 22, f"{rec_nom}")
        c.drawCentredString(310, y_firma - 31, f"C.I.: {datos_traslado.get('firma_receptor_ci', 'V-')}")

        c.drawCentredString(490, y_firma - 22, "Bienes Públicos UNELLEZ")
        c.drawCentredString(490, y_firma - 31, "Auditoría Interna")

        # Pie de página
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(45, 30, "Documento oficial generado por la plataforma SIGART — UNELLEZ VIPI")
        c.drawRightString(w - 45, 30, f"Impreso: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        c.save()
        return archivo_salida
    except Exception as e:
        messagebox.showerror("Error al Generar PDF", f"Fallo al emitir el documento PDF:\n{e}")
        return None