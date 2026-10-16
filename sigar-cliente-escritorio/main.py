# -*- coding: utf-8 -*-
"""
Módulo Principal de la Aplicación SIGART - UNELLEZ VIPI
Controlador de interfaz gráfica con Menú Flotante (Drawer Overlay) sobre el contenido.
Elimina al 100% la pantalla negra, los parpadeos y los recálculos de geometría.
"""
import ctypes
import os
import sys
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import customtkinter as ctk

from database import (
    cargar_datos_locales,
    guardar_baja_local,
    guardar_datos_locales,
    obtener_conteo_bajas,
)
from modals import (
    VentanaDesincorporados,
    VentanaDiagnosticoTecnico,
    VentanaFichaTecnica,
    VentanaRespaldos,
)
from styles import (
    PALETA,
    cargar_preferencia_tema,
    guardar_preferencia_tema,
    obtener_estilo_kpi,
    obtener_ruta_icono,
)
from utils import (
    HAS_PIL,
    TIPOS_ACTIVOS_VALIDOS,
    calcular_fecha_habil_3_meses,
    es_verdadero,
    generar_acta_baja,
    validar_fecha_ddmmaaaa,
)
from views import VistaTraslado

if HAS_PIL:
    from PIL import Image, ImageTk


def colorear_icono_png(ruta_png, color_hex):
    """Carga un PNG y tiñe su silueta con el color hexadecimal indicado."""
    if not os.path.exists(ruta_png) or not HAS_PIL:
        return None
    try:
        img_original = Image.open(ruta_png).convert("RGBA")
        _, _, _, alpha = img_original.split()
        color_solido = Image.new("RGBA", img_original.size, color_hex)
        color_solido.putalpha(alpha)
        return color_solido
    except Exception:
        return None


# Configuración de apariencia
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Configuración de DPI segura para Windows 7
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def obtener_ruta_base():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


DIR_ACTUAL = obtener_ruta_base()
if DIR_ACTUAL not in sys.path:
    sys.path.insert(0, DIR_ACTUAL)

ARCHIVO_LOGO = os.path.join(DIR_ACTUAL, "UNELLEZ LOGO.png")
PATH_LEMA = os.path.join(DIR_ACTUAL, "lema_unellez_oro.png")


def verificar_informacion_completa(bien):
    """Verifica si el activo cuenta con diagnóstico técnico exhaustivo."""
    detalles = bien.get("detalles_tecnicos") or bien.get("perifericos") or {}
    if not detalles:
        return False

    tipo = bien.get("nombre", "")
    if tipo == "Computadora de escritorio":
        cpu_data = detalles.get("cpu", {})
        if not cpu_data:
            return False
        if "Dañad" in cpu_data.get("estado", "") and not cpu_data.get("detalle", "").strip():
            return False
        if es_verdadero(detalles.get("incluye_perifericos", False)):
            for k in ["monitor", "teclado", "mouse"]:
                p_dat = detalles.get(k, {})
                if "Dañad" in p_dat.get("estado", "") and not p_dat.get("detalle", "").strip():
                    return False
        return True

    elif tipo in ["Router", "Switch de red"]:
        marca = detalles.get("marca", "").strip()
        modelo = detalles.get("modelo", "").strip()
        if not marca or not modelo:
            return False
        if detalles.get("estado_general") in ["Funcional con fallas", "Dañado"] and not detalles.get("detalle_falla", "").strip():
            return False
        return True

    else:
        for info in detalles.values():
            if isinstance(info, dict):
                if "Dañad" in info.get("estado", "") and not info.get("detalle", "").strip():
                    return False
    return True


class InventarioBienesApp:

    def __init__(self, root):
        self.root = root
        self.root.title("SIGART (UNELLEZ VIPI) - Sistema de Inventario y Gestión de Activos")
        self.root.geometry("1180x740")
        self.root.minsize(940, 620)

        self.modo_actual = cargar_preferencia_tema()
        self.modo_oscuro = self.modo_actual == "oscuro"
        ctk.set_appearance_mode("Dark" if self.modo_oscuro else "Light")

        self.filtro_metrica_activa = "TODOS"
        self.datos_tecnicos_temporales = None
        self.imagenes_tabla_ref = []
        self.menu_abierto = False

        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Cintillo
        self.root.rowconfigure(1, weight=1)  # Contenedor Maestro
        self.root.rowconfigure(2, weight=0)  # Pie de página

        self.PALETA = PALETA
        self.bienes = []
        self.tarjetas_widgets = []

        self.img_advertencia = None
        self.img_transparente = None
        self.cargar_iconos_auxiliares()

        self.crear_cintillo_institucional()
        self.crear_contenedor_principal()
        self.crear_menu_flotante_drawer()
        self.crear_panel_acciones()

        self.aplicar_tema_widgets()

        # Detector de clics para cerrar el menú si se hace clic afuera
        self.root.bind("<Button-1>", self.detectar_clic_fuera_del_menu, add="+")

        self.recargar_datos_completos()
        self.root.after(200, self.activar_foco_inicial)

    def activar_foco_inicial(self):
        self.root.focus_force()
        if hasattr(self, "entry_id"):
            self.entry_id.focus_force()

    def cargar_iconos_auxiliares(self):
        ruta_adv = obtener_ruta_icono("advertencia.png")
        if os.path.exists(ruta_adv) and HAS_PIL:
            color = "#f59e0b" if self.modo_oscuro else "#d97706"
            col_img = colorear_icono_png(ruta_adv, color)
            if col_img:
                img_p = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
                img_p.paste(col_img.resize((16, 16)), (8, 0))
                self.img_advertencia = ImageTk.PhotoImage(img_p)
        if HAS_PIL:
            img_v = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
            self.img_transparente = ImageTk.PhotoImage(img_v)
        else:
            self.img_transparente = ""

    # ================= CINTILLO INSTITUCIONAL =================
    def crear_cintillo_institucional(self):
        self.frame_cintillo = ctk.CTkFrame(self.root, fg_color="#1C2F46", corner_radius=0, height=52)
        self.frame_cintillo.grid(row=0, column=0, sticky="ew")
        self.frame_cintillo.pack_propagate(False)

        frame_logo_titulo = ctk.CTkFrame(self.frame_cintillo, fg_color="transparent")
        frame_logo_titulo.pack(side="left", padx=10, pady=2)

        # Botón para desplegar el Menú Flotante
        self.btn_menu_trigger = ctk.CTkButton(
            frame_logo_titulo,
            text="☰  MENÚ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            width=85,
            height=34,
            fg_color="#002B49",
            hover_color="#034b7f",
            corner_radius=6,
            command=self.toggle_menu_flotante
        )
        self.btn_menu_trigger.pack(side="left", padx=(0, 10))

        # Logo UNELLEZ
        if os.path.exists(ARCHIVO_LOGO) and HAS_PIL:
            try:
                img_pil = Image.open(ARCHIVO_LOGO)
                self.logo_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(30, 30))
                ctk.CTkLabel(frame_logo_titulo, image=self.logo_img, text="").pack(side="left", padx=(0, 6))
            except Exception:
                pass

        # Texto UNELLEZ
        ctk.CTkLabel(
            frame_logo_titulo, text="UNELLEZ",
            font=ctk.CTkFont(family="Georgia", size=21, weight="bold"), text_color="#FF6600"
        ).pack(side="left")

        # Separador
        ctk.CTkLabel(
            frame_logo_titulo, text="|",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color="#565D68"
        ).pack(side="left", padx=(10, 8))

        # Lema con recorte automático de transparencia
        if os.path.exists(PATH_LEMA) and HAS_PIL:
            try:
                img_lema_pil = Image.open(PATH_LEMA).convert("RGBA")
                bbox = img_lema_pil.getbbox()
                if bbox:
                    img_lema_pil = img_lema_pil.crop(bbox)
                    target_height = 24
                    aspect_ratio = img_lema_pil.width / img_lema_pil.height
                    target_width = int(target_height * aspect_ratio)
                else:
                    target_height = 140
                    aspect_ratio = img_lema_pil.width / img_lema_pil.height
                    target_width = int(target_height * aspect_ratio)

                self.img_lema_oro = ctk.CTkImage(
                    light_image=img_lema_pil,
                    dark_image=img_lema_pil,
                    size=(target_width, target_height)
                )
                lbl_lema = ctk.CTkLabel(frame_logo_titulo, image=self.img_lema_oro, text="")
                lbl_lema.pack(side="left", padx=(2, 0), pady=0)
            except Exception as e:
                print(f"Error cargando lema: {e}")

        # Botón modo oscuro
        self.btn_modo_oscuro = ctk.CTkButton(
            self.frame_cintillo, text="", width=36, height=36,
            fg_color="#1e293b", hover_color="#334155", corner_radius=8,
            command=self.toggle_modo_oscuro,
        )
        self.btn_modo_oscuro.pack(side="right", padx=12, pady=6)

    def toggle_modo_oscuro(self):
        self.modo_oscuro = not self.modo_oscuro
        self.modo_actual = "oscuro" if self.modo_oscuro else "claro"
        ctk.set_appearance_mode("Dark" if self.modo_oscuro else "Light")
        self.cargar_iconos_auxiliares()
        self.aplicar_tema_widgets()

    # ================= CONTENEDOR PRINCIPAL FIJO (100% ESTABLE) =================
    def crear_contenedor_principal(self):
        self.frame_cuerpo_general = ctk.CTkFrame(self.root, fg_color="transparent", corner_radius=0)
        self.frame_cuerpo_general.grid(row=1, column=0, sticky="nsew")
        self.frame_cuerpo_general.rowconfigure(0, weight=1)
        self.frame_cuerpo_general.columnconfigure(0, weight=1)

        # 1. Vista de Inventario Principal (Ocupa el 100% de la pantalla de forma fija)
        self.vista_inventario = ctk.CTkFrame(self.frame_cuerpo_general, fg_color="transparent")
        self.vista_inventario.rowconfigure(3, weight=1)
        self.vista_inventario.columnconfigure(0, weight=1)

        self.crear_panel_metricas(self.vista_inventario)
        self.crear_formulario(self.vista_inventario)
        self.crear_panel_busqueda(self.vista_inventario)
        self.crear_tabla(self.vista_inventario)
        self.crear_menu_contextual()

        # 2. Vista de Traslado de Equipos
        self.vista_traslado = VistaTraslado(
            self.frame_cuerpo_general,
            obtener_bienes_callback=lambda: self.bienes,
            modo_oscuro=self.modo_oscuro,
            paleta=self.PALETA,
            actualizar_inventario_callback=self.recargar_datos_completos
        )

        self.vista_inventario.grid(row=0, column=0, sticky="nsew")

    # ================= MENÚ FLOTANTE PURO (SIN ERROR DE PLACE) =================
    def crear_menu_flotante_drawer(self):
        # En CustomTkinter, width y height se declaran AQUÍ en el constructor
        self.drawer = ctk.CTkFrame(
            self.frame_cuerpo_general,
            width=260,
            height=380,
            corner_radius=10,
            fg_color="#0b1324" if self.modo_oscuro else "#0f172a",
            border_width=2,
            border_color="#0284c7"
        )
        self.drawer.pack_propagate(False)

        # Cabecera del menú flotante
        f_head_drawer = ctk.CTkFrame(self.drawer, fg_color="transparent")
        f_head_drawer.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            f_head_drawer, text="🧭 NAVEGACIÓN",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left")

        btn_cerrar_drawer = ctk.CTkButton(
            f_head_drawer, text="✕", width=30, height=30,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent", hover_color="#dc2626",
            command=self.cerrar_menu_flotante
        )
        btn_cerrar_drawer.pack(side="right")

        ctk.CTkFrame(self.drawer, height=1, fg_color="#1e293b").pack(fill="x", padx=12, pady=(0, 10))

        # Opciones de navegación
        self.btn_nav_inv = ctk.CTkButton(
            self.drawer, text="📦  Inventario Activo", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7", hover_color="#0369a1", anchor="w", height=40,
            command=lambda: self.navegar_y_cerrar("inventario")
        )
        self.btn_nav_inv.pack(fill="x", padx=12, pady=5)

        self.btn_nav_doc = ctk.CTkButton(
            self.drawer, text="📄  Acta de Traslado", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", hover_color="#1e293b", anchor="w", height=40,
            command=lambda: self.navegar_y_cerrar("traslado")
        )
        self.btn_nav_doc.pack(fill="x", padx=12, pady=5)

        self.btn_nav_bajas = ctk.CTkButton(
            self.drawer, text="❌  Activos de Baja", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", hover_color="#1e293b", anchor="w", height=40,
            command=lambda: [self.cerrar_menu_flotante(), self.mostrar_ventana_desincorporados()]
        )
        self.btn_nav_bajas.pack(fill="x", padx=12, pady=5)

        self.btn_nav_resp = ctk.CTkButton(
            self.drawer, text="💾  Centro de Respaldos", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", hover_color="#1e293b", anchor="w", height=40,
            command=lambda: [self.cerrar_menu_flotante(), self.abrir_ventana_respaldos()]
        )
        self.btn_nav_resp.pack(fill="x", padx=12, pady=5)

        # Pie institucional
        ctk.CTkLabel(
            self.drawer, text="SIGART V2.6 — UNELLEZ VIPI\nCoordinación CTSI",
            font=ctk.CTkFont(size=9), text_color="#64748b", justify="center"
        ).pack(side="bottom", pady=15)

    def toggle_menu_flotante(self):
        if self.menu_abierto:
            self.cerrar_menu_flotante()
        else:
            self.abrir_menu_flotante()

    def abrir_menu_flotante(self):
        self.menu_abierto = True
        # CORRECCIÓN: Solo se pasa x e y (width y height se toman del constructor)
        self.drawer.place(x=10, y=10)
        self.drawer.lift()

    def cerrar_menu_flotante(self):
        self.menu_abierto = False
        self.drawer.place_forget()

    def detectar_clic_fuera_del_menu(self, event):
        """Si el menú está abierto y el usuario hace clic afuera de él, se cierra solo."""
        if not self.menu_abierto:
            return
        try:
            x, y = event.x_root, event.y_root
            dx1 = self.drawer.winfo_rootx()
            dy1 = self.drawer.winfo_rooty()
            dx2 = dx1 + self.drawer.winfo_width()
            dy2 = dy1 + self.drawer.winfo_height()

            # Si el clic no fue dentro del menú ni en el botón que lo abre, cerrarlo
            btn_x1 = self.btn_menu_trigger.winfo_rootx()
            btn_y1 = self.btn_menu_trigger.winfo_rooty()
            btn_x2 = btn_x1 + self.btn_menu_trigger.winfo_width()
            btn_y2 = btn_y1 + self.btn_menu_trigger.winfo_height()

            clic_en_drawer = (dx1 <= x <= dx2 and dy1 <= y <= dy2)
            clic_en_boton = (btn_x1 <= x <= btn_x2 and btn_y1 <= y <= btn_y2)

            if not clic_en_drawer and not clic_en_boton:
                self.cerrar_menu_flotante()
        except Exception:
            pass

    def navegar_y_cerrar(self, vista):
        self.cerrar_menu_flotante()
        self.mostrar_vista(vista)

    def mostrar_vista(self, nombre_vista):
        if nombre_vista == "inventario":
            self.vista_traslado.grid_forget()
            self.vista_inventario.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_inv.configure(fg_color="#0284c7")
            self.btn_nav_doc.configure(fg_color="transparent")
        elif nombre_vista == "traslado":
            self.vista_inventario.grid_forget()
            self.vista_traslado.cargar_equipos_en_tabla()
            self.vista_traslado.grid(row=0, column=0, sticky="nsew")
            self.btn_nav_doc.configure(fg_color="#0284c7")
            self.btn_nav_inv.configure(fg_color="transparent")

    # ================= TARJETAS KPI (SIMÉTRICAS: EXACTO 20% CADA UNA) =================
    def crear_panel_metricas(self, parent):
        self.frame_kpis = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_kpis.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))

        # 5 columnas idénticas
        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi_col")

        self.tarjetas_widgets = []
        metricas = [
            ("TOTAL ACTIVOS", "0", "Bienes registrados", "total_activos.png", "TODOS"),
            ("OPERATIVOS", "0", "En servicio activo", "operativos.png", "OPERATIVOS"),
            ("PREVENTIVOS", "0", "Ciclo regular (+3M)", "preventivos.png", "PREVENTIVOS"),
            ("CORRECTIVOS", "0", "Ajuste / Reparación", "correctivos.png", "CORRECTIVOS"),
            ("DESINCORPORADOS", "0", "Actas emitidas", "desincorporados.png", "DESINCORPORADOS"),
        ]

        for col, (titulo, valor, sub, nombre_archivo_png, clave) in enumerate(metricas):
            val_widget = self.crear_tarjeta(col, titulo, valor, sub, nombre_archivo_png, clave)
            if col == 0:
                self.lbl_val_total = val_widget
            elif col == 1:
                self.lbl_val_operativos = val_widget
            elif col == 2:
                self.lbl_val_preventivos = val_widget
            elif col == 3:
                self.lbl_val_correctivos = val_widget
            elif col == 4:
                self.lbl_val_desincorporados = val_widget

    def crear_tarjeta(self, col, titulo, valor_inicial, subtitulo, nombre_archivo_png, clave):
        card = ctk.CTkFrame(self.frame_kpis, corner_radius=10, border_width=1, cursor="hand2")
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=8, pady=(4, 2))

        lbl_check = ctk.CTkLabel(top_frame, text="", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"))
        lbl_check.pack(side="left", padx=(0, 2))

        lbl_tit = ctk.CTkLabel(top_frame, text=titulo, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), anchor="w")
        lbl_tit.pack(side="left", fill="x", expand=True)

        linea = ctk.CTkFrame(card, height=2, corner_radius=0)
        linea.pack(anchor="w", fill="x", padx=(8, 25), pady=(0, 2))

        val_frame = ctk.CTkFrame(card, fg_color="transparent")
        val_frame.pack(fill="x", padx=8, pady=(2, 2))
        val_frame.columnconfigure(0, weight=1)

        lbl_val = ctk.CTkLabel(val_frame, text=valor_inicial, font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), anchor="w")
        lbl_val.grid(row=0, column=0, sticky="w")

        lbl_icon = ctk.CTkLabel(val_frame, text="", anchor="e")
        lbl_icon.grid(row=0, column=1, sticky="e")

        lbl_sub = ctk.CTkLabel(card, text=subtitulo, font=ctk.CTkFont(family="Segoe UI", size=9), anchor="w")
        lbl_sub.pack(fill="x", padx=8, pady=(0, 4))

        for elem in [card, top_frame, val_frame, lbl_check, lbl_tit, lbl_icon, lbl_val, lbl_sub, linea]:
            elem.bind("<Button-1>", lambda event, c=clave: self.filtrar_por_metrica(c))

        self.tarjetas_widgets.append({
            "card": card, "check": lbl_check, "tit": lbl_tit, "icon": lbl_icon,
            "val": lbl_val, "sub": lbl_sub, "linea": linea, "clave": clave,
            "ruta_png": obtener_ruta_icono(nombre_archivo_png)
        })
        return lbl_val

    # ================= FORMULARIO PRINCIPAL =================
    def crear_formulario(self, parent):
        self.frame_form = ctk.CTkFrame(parent, corner_radius=10)
        self.frame_form.grid(row=1, column=0, sticky="ew", padx=12, pady=2)
        self.frame_form.columnconfigure(1, weight=1)
        self.frame_form.columnconfigure(3, weight=2)
        self.frame_form.columnconfigure(5, weight=1)

        lbl_titulo_seccion = ctk.CTkLabel(
            self.frame_form, text="📝 REGISTRO Y GESTIÓN DE BIENES TECNOLÓGICOS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#0284c7" if not self.modo_oscuro else "#38bdf8", anchor="w"
        )
        lbl_titulo_seccion.grid(row=0, column=0, columnspan=6, padx=12, pady=(6, 2), sticky="w")

        # Fila 1: ID y Asignado a
        ctk.CTkLabel(self.frame_form, text="ID Único:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, padx=(12, 5), pady=3, sticky="e")
        self.entry_id = ctk.CTkEntry(self.frame_form, font=("Segoe UI", 11), height=28)
        self.entry_id.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        ctk.CTkLabel(self.frame_form, text="Asignado a:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=2, padx=(10, 5), pady=3, sticky="e")
        opciones_asig = [
            "Departamento de Sistemas", "Administración", "Laboratorio 1", "Rectorado",
            "Control de Estudios", "Servicios Generales", "Planificación y Presupuesto",
            "Coordinación de Docencia", "Comunicaciones y Prensa", "Secretaría Ejecutiva", "Recursos Humanos"
        ]
        self.combo_asignado = ctk.CTkOptionMenu(self.frame_form, values=opciones_asig, height=28)
        self.combo_asignado.grid(row=1, column=3, columnspan=3, padx=5, pady=3, sticky="ew")

        # Botones del formulario
        f_btn = ctk.CTkFrame(self.frame_form, fg_color="transparent")
        f_btn.grid(row=1, column=6, rowspan=5, padx=(10, 12), pady=3, sticky="ns")

        ctk.CTkButton(f_btn, text="Registrar Nuevo", fg_color="#0284C7", hover_color="#0369a1", font=ctk.CTkFont(size=11, weight="bold"), height=26, command=self.agregar_bien).pack(fill="x", pady=2)
        ctk.CTkButton(f_btn, text="Guardar Cambios", fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"), height=26, command=self.actualizar_bien).pack(fill="x", pady=2)
        ctk.CTkButton(f_btn, text="Limpiar Campos", fg_color="#475569", hover_color="#334155", font=ctk.CTkFont(size=11, weight="bold"), height=26, command=self.limpiar_formulario).pack(fill="x", pady=2)

        # Fila 2: Tipo de Equipo
        ctk.CTkLabel(self.frame_form, text="Tipo de Equipo:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, padx=(12, 5), pady=3, sticky="e")
        self.combo_nombre = ctk.CTkOptionMenu(self.frame_form, values=TIPOS_ACTIVOS_VALIDOS, height=28, command=self.al_cambiar_tipo_activo)
        self.combo_nombre.set(TIPOS_ACTIVOS_VALIDOS[0])
        self.combo_nombre.grid(row=2, column=1, columnspan=5, padx=5, pady=3, sticky="ew")

        # Fila 3: Mantenimiento, Fecha y Próximo
        ctk.CTkLabel(self.frame_form, text="Mantenimiento:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=0, padx=(12, 5), pady=3, sticky="e")
        self.combo_mant = ctk.CTkOptionMenu(self.frame_form, values=["No", "Sí (Preventivo)", "Sí (Correctivo)"], height=28)
        self.combo_mant.set("No")
        self.combo_mant.grid(row=3, column=1, padx=5, pady=3, sticky="w")

        ctk.CTkLabel(self.frame_form, text="Fecha (DD/MM/AAAA):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=2, padx=(10, 5), pady=3, sticky="e")
        self.entry_fecha_mant = ctk.CTkEntry(self.frame_form, font=("Segoe UI", 11), height=28)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha_mant.grid(row=3, column=3, padx=5, pady=3, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.formatear_y_validar_fecha_mascara)

        ctk.CTkLabel(self.frame_form, text="Próximo (+3M Hábil):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=3, column=4, padx=(10, 5), pady=3, sticky="e")
        
        self.entry_proximo = ctk.CTkEntry(
            self.frame_form,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=28,
            state="readonly",
            fg_color=("#ffffff", "#090d16"),
            text_color=("#0f172a", "#f8fafc")
        )
        self.entry_proximo.grid(row=3, column=5, padx=5, pady=3, sticky="ew")

        # Fila 4: Observación
        ctk.CTkLabel(self.frame_form, text="Detalle / Observación:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=4, column=0, padx=(12, 5), pady=3, sticky="e")
        self.entry_desc_mant = ctk.CTkEntry(self.frame_form, font=("Segoe UI", 11), height=28)
        self.entry_desc_mant.grid(row=4, column=1, columnspan=5, padx=5, pady=3, sticky="ew")

        # Fila 5: Badge y Acceso a Diagnóstico Técnico
        f_badge = ctk.CTkFrame(self.frame_form, fg_color="transparent")
        f_badge.grid(row=5, column=0, columnspan=6, padx=12, pady=(4, 6), sticky="ew")

        self.badge_diagnostico = ctk.CTkFrame(f_badge, corner_radius=6, border_width=1)
        self.badge_diagnostico.pack(side="left", fill="y", pady=2)

        self.lbl_estado_diagnostico = ctk.CTkLabel(
            self.badge_diagnostico, text="  DIAGNÓSTICO TÉCNICO: Sin Seleccionar  ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold")
        )
        self.lbl_estado_diagnostico.pack(padx=8, pady=4)

        ctk.CTkButton(
            f_badge, text="🛠 Completar / Editar Diagnóstico Técnico",
            fg_color="#0284C7", hover_color="#0369a1", font=ctk.CTkFont(size=11, weight="bold"),
            height=28, command=self.abrir_modal_diagnostico
        ).pack(side="right")

        self.calcular_proxima_fecha_mantenimiento()

    def al_cambiar_tipo_activo(self, tipo=None):
        self.datos_tecnicos_temporales = None
        self.actualizar_badge_diagnostico(es_completo=False)

    def actualizar_badge_diagnostico(self, es_completo=False, sin_seleccion=False):
        if sin_seleccion:
            bg_c = "#1e293b" if self.modo_oscuro else "#e2e8f0"
            border_c = "#475569" if self.modo_oscuro else "#94a3b8"
            text_c = "#94a3b8" if self.modo_oscuro else "#475569"
            texto = "  DIAGNÓSTICO TÉCNICO: Sin Seleccionar  "
        elif es_completo:
            bg_c = "#064e3b" if self.modo_oscuro else "#dcfce7"
            border_c = "#10b981"
            text_c = "#6ee7b7" if self.modo_oscuro else "#15803d"
            texto = "  DIAGNÓSTICO TÉCNICO: Completo y Verificado 100%  "
        else:
            bg_c = "#451a03" if self.modo_oscuro else "#fef3c7"
            border_c = "#f59e0b"
            text_c = "#fcd34d" if self.modo_oscuro else "#b45309"
            texto = "  DIAGNÓSTICO TÉCNICO: [INCOMPLETO] Datos o verificación pendiente  "

        self.badge_diagnostico.configure(fg_color=bg_c, border_color=border_c)
        self.lbl_estado_diagnostico.configure(text=texto, text_color=text_c)

    # ================= MÁSCARA Y VALIDACIÓN DE FECHAS =================
    def formatear_y_validar_fecha_mascara(self, event=None):
        if event and event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            self.calcular_proxima_fecha_mantenimiento()
            return

        txt = self.entry_fecha_mant.get()
        digitos = "".join(c for c in txt if c.isdigit())[:8]

        formateado = ""
        if len(digitos) > 0:
            formateado += digitos[:2]
        if len(digitos) >= 3:
            formateado += "/" + digitos[2:4]
        if len(digitos) >= 5:
            formateado += "/" + digitos[4:8]

        if txt != formateado:
            self.entry_fecha_mant.delete(0, tk.END)
            self.entry_fecha_mant.insert(0, formateado)

        self.calcular_proxima_fecha_mantenimiento()

    def calcular_proxima_fecha_mantenimiento(self):
        fecha_str = self.entry_fecha_mant.get().strip()

        if validar_fecha_ddmmaaaa(fecha_str):
            try:
                dia, mes, anio = map(int, fecha_str.split("/"))
                dt = date(anio, mes, dia)
                prox = calcular_fecha_habil_3_meses(dt)

                self.entry_proximo.configure(
                    state="normal",
                    fg_color=("#ffffff", "#090d16"),
                    text_color=("#0f172a", "#f8fafc")
                )
                self.entry_proximo.delete(0, tk.END)
                self.entry_proximo.insert(0, prox)
                self.entry_proximo.configure(state="readonly")
                return prox
            except Exception:
                pass

        self.entry_proximo.configure(
            state="normal",
            fg_color=("#fee2e2", "#7f1d1d"),
            text_color=("#991b1b", "#fca5a5")
        )
        self.entry_proximo.delete(0, tk.END)
        self.entry_proximo.insert(0, "Fecha Inválida")
        self.entry_proximo.configure(state="readonly")
        return None

    # ================= BÚSQUEDA Y FILTRADO =================
    def crear_panel_busqueda(self, parent):
        self.frame_busqueda = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_busqueda.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 2))

        ctk.CTkLabel(self.frame_busqueda, text="Buscar Activo:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))

        self.entry_buscar = ctk.CTkEntry(self.frame_busqueda, font=("Segoe UI", 11), width=260, height=28)
        self.entry_buscar.pack(side="left", padx=4)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)

        ctk.CTkButton(
            self.frame_busqueda, text="Limpiar Filtro", fg_color="#002B49", hover_color="#001F35",
            font=ctk.CTkFont(size=11, weight="bold"), height=28, command=self.limpiar_filtro_busqueda
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            self.frame_busqueda, text="(Doble clic: Editar / Clic derecho: Opciones y Ficha)",
            font=ctk.CTkFont(size=10), text_color="#94a3b8"
        ).pack(side="right")

    # ================= TABLA DE DATOS =================
    def crear_tabla(self, parent):
        self.frame_tabla = ctk.CTkFrame(parent, corner_radius=6, border_width=0)
        self.frame_tabla.grid(row=3, column=0, sticky="nsew", padx=12, pady=4)
        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        cols = ("id", "nombre", "asignado_a", "mantenimiento", "fecha_mant", "proximo_mant")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="tree headings")

        # Encabezados
        self.tabla.heading("#0", text="⚠️", anchor="center")
        self.tabla.heading("id", text="ID Activo", anchor="center")
        self.tabla.heading("nombre", text="Descripción / Equipo Tecnológico", anchor="w")
        self.tabla.heading("asignado_a", text="Asignado a / Área", anchor="w")
        self.tabla.heading("mantenimiento", text="Régimen Mant.", anchor="center")
        self.tabla.heading("fecha_mant", text="Fecha Mant./Ingreso", anchor="center")
        self.tabla.heading("proximo_mant", text="Próx. Fecha Hábil (+3M)", anchor="center")

        # Anchos proporcionales
        self.tabla.column("#0", width=34, minwidth=34, anchor="center", stretch=False)
        self.tabla.column("id", width=70, minwidth=55, anchor="center", stretch=False)
        self.tabla.column("nombre", width=260, minwidth=180, anchor="w", stretch=True)
        self.tabla.column("asignado_a", width=185, minwidth=150, anchor="w", stretch=False)
        self.tabla.column("mantenimiento", width=130, minwidth=115, anchor="center", stretch=False)
        self.tabla.column("fecha_mant", width=115, minwidth=95, anchor="center", stretch=False)
        self.tabla.column("proximo_mant", width=155, minwidth=135, anchor="center", stretch=False)

        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        self.tabla.bind("<Button-3>", self.mostrar_menu_contextual)

        sc = ctk.CTkScrollbar(self.frame_tabla, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sc.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        sc.grid(row=0, column=1, sticky="ns", padx=(0, 2))

    def crear_menu_contextual(self):
        self.menu_contextual = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        self.menu_contextual.add_command(label="Editar Activo", command=self.cargar_seleccion_para_editar)
        self.menu_contextual.add_command(label="Ver Ficha Técnica / Diagnóstico", command=self.ver_ficha_tecnica)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="Dar de Baja / Generar Acta (PDF)",
            command=self.dar_de_baja_bien,
            foreground="#ea580c"
        )
        self.menu_contextual.add_command(
            label="🗑 Eliminar Activo (Sin Acta)",
            command=self.eliminar_bien_directo,
            foreground="#dc2626"
        )

    def mostrar_menu_contextual(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            self.tabla.selection_set(item)
            self.tabla.focus(item)
            self.menu_contextual.post(event.x_root, event.y_root)

    # ================= PIE DE PÁGINA =================
    def crear_panel_acciones(self):
        self.frame_pie = ctk.CTkFrame(self.root, fg_color="transparent", height=24)
        self.frame_pie.grid(row=2, column=0, sticky="ew", padx=15, pady=(2, 6))

        ctk.CTkLabel(
            self.frame_pie, text="SIGART V2.6 — UNELLEZ VIPI (Soporte Win7/10/11 x86-x64)",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8"
        ).pack(side="right")

    # ================= OPERACIONES CRUD =================
    def agregar_bien(self):
        id_val = self.entry_id.get().strip()
        nombre_val = self.combo_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()

        if not id_val or not nombre_val or nombre_val == "Seleccione el equipo" or not asignado_val:
            messagebox.showwarning("Incompleto", "Complete el ID, seleccione un equipo válido y asigne un área.")
            return

        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("ID Inválido", "El ID debe ser estrictamente numérico.")
            return

        if any(b["id"] == id_int for b in self.bienes):
            messagebox.showwarning("ID Duplicado", f"El activo ID #{id_int} ya existe en el sistema.")
            return

        fecha_mant_val = self.entry_fecha_mant.get().strip()
        if not validar_fecha_ddmmaaaa(fecha_mant_val):
            messagebox.showwarning("Fecha Inválida", "La fecha ingresada debe tener el formato DD/MM/AAAA.")
            return

        proximo_val = self.calcular_proxima_fecha_mantenimiento() or "N/A"
        mant_val = self.combo_mant.get()
        desc_mant_val = self.entry_desc_mant.get().strip()

        datos_tecnicos = self.datos_tecnicos_temporales or self.generar_preset_por_defecto(nombre_val)

        nuevo_bien = {
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val,
            "proximo_mant": proximo_val,
            "desc_mant": desc_mant_val,
            "detalles_tecnicos": datos_tecnicos,
            "perifericos": datos_tecnicos
        }

        self.bienes.append(nuevo_bien)
        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Éxito", f"Activo ID #{id_int} registrado exitosamente.")

    def actualizar_bien(self):
        id_val = self.entry_id.get().strip()
        if not id_val:
            messagebox.showwarning("Sin ID", "Seleccione o ingrese el ID del activo a actualizar.")
            return

        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("ID Inválido", "El ID debe ser numérico.")
            return

        idx = next((i for i, b in enumerate(self.bienes) if b["id"] == id_int), None)
        if idx is None:
            messagebox.showerror("No Encontrado", f"No se encontró ningún activo con el ID #{id_int}.")
            return

        nombre_val = self.combo_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()
        fecha_mant_val = self.entry_fecha_mant.get().strip()

        if not validar_fecha_ddmmaaaa(fecha_mant_val):
            messagebox.showwarning("Fecha Inválida", "La fecha ingresada debe tener el formato DD/MM/AAAA.")
            return

        proximo_val = self.calcular_proxima_fecha_mantenimiento() or "N/A"
        mant_val = self.combo_mant.get()
        desc_mant_val = self.entry_desc_mant.get().strip()

        datos_tecnicos = self.datos_tecnicos_temporales or self.bienes[idx].get("detalles_tecnicos") or self.generar_preset_por_defecto(nombre_val)

        self.bienes[idx] = {
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val,
            "proximo_mant": proximo_val,
            "desc_mant": desc_mant_val,
            "detalles_tecnicos": datos_tecnicos,
            "perifericos": datos_tecnicos
        }

        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Actualización", f"Activo ID #{id_int} modificado con persistencia exitosa.")

    def eliminar_bien_directo(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Sin Selección", "Seleccione un activo para eliminar.")
            return

        id_bien = int(self.tabla.item(sel[0])["values"][0])
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if not bien:
            return

        confirm = messagebox.askyesno(
            "Confirmar Eliminación Directa",
            f"¿Está seguro de eliminar definitivamente el activo ID #{id_bien} ({bien.get('nombre')})?\n\n"
            "Esta acción NO generará acta de baja y quitará el registro del sistema.",
            icon="warning"
        )
        if confirm:
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            if guardar_datos_locales(self.bienes):
                self.actualizar_tabla()
                self.actualizar_metricas()
                self.limpiar_formulario()
                messagebox.showinfo("Activo Eliminado", f"El activo ID #{id_bien} ha sido eliminado definitivamente.")

    def generar_preset_por_defecto(self, tipo_activo):
        if tipo_activo == "Computadora de escritorio":
            return {
                "incluye_perifericos": False,
                "cpu": {
                    "estado": "Operativo al 100%",
                    "detalle": "En buen estado operativo",
                    "componentes_internos": {
                        "placa_madre": "Operativo", "procesador": "Operativo",
                        "memoria_ram": "Operativo", "disco_duro": "Operativo", "fuente_poder": "Operativo"
                    }
                },
                "monitor": {"estado": "No Asignado (Solo Case)", "detalle": ""},
                "teclado": {"estado": "No Asignado (Solo Case)", "detalle": ""},
                "mouse": {"estado": "No Asignado (Solo Case)", "detalle": ""}
            }
        elif tipo_activo == "Laptop":
            return {
                "pantalla": {"estado": "Operativa", "detalle": "Operativo"},
                "teclado": {"estado": "Operativo", "detalle": "Operativo"},
                "mouse_touchpad": {"estado": "Operativo", "detalle": "Operativo"},
                "carcasa_puertos": {"estado": "Sin daños", "detalle": "Operativo"}
            }
        elif tipo_activo == "Impresora":
            return {
                "impresion": {"estado": "Operativa", "detalle": "Operativo"},
                "copia": {"estado": "Operativa", "detalle": "Operativo"},
                "scanner": {"estado": "Operativa", "detalle": "Operativo"}
            }
        elif tipo_activo in ["Router", "Switch de red"]:
            return {"marca": "Cisco / TP-Link", "modelo": "Estándar", "estado_general": "Funcional", "detalle_falla": ""}
        return {}

    def limpiar_formulario(self):
        self.entry_id.delete(0, tk.END)
        self.combo_nombre.set(TIPOS_ACTIVOS_VALIDOS[0])
        self.entry_desc_mant.delete(0, tk.END)
        self.entry_fecha_mant.delete(0, tk.END)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.combo_mant.set("No")
        self.datos_tecnicos_temporales = None
        self.actualizar_badge_diagnostico(sin_seleccion=True)
        self.calcular_proxima_fecha_mantenimiento()
        self.entry_id.focus_force()

    def cargar_seleccion_para_editar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        item = self.tabla.item(sel[0])
        id_bien = int(item["values"][0])
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if not bien:
            return

        self.entry_id.delete(0, tk.END)
        self.entry_id.insert(0, str(bien["id"]))

        nom = bien.get("nombre", "")
        self.combo_nombre.set(nom if nom in TIPOS_ACTIVOS_VALIDOS else TIPOS_ACTIVOS_VALIDOS[0])
        self.combo_asignado.set(bien.get("asignado_a", "Departamento de Sistemas"))
        self.combo_mant.set(bien.get("mantenimiento", "No"))

        self.entry_fecha_mant.delete(0, tk.END)
        self.entry_fecha_mant.insert(0, bien.get("fecha_mant", date.today().strftime("%d/%m/%Y")))

        self.entry_desc_mant.delete(0, tk.END)
        self.entry_desc_mant.insert(0, bien.get("desc_mant", ""))

        self.calcular_proxima_fecha_mantenimiento()

        self.datos_tecnicos_temporales = bien.get("detalles_tecnicos") or bien.get("perifericos") or {}
        es_comp = verificar_informacion_completa(bien)
        self.actualizar_badge_diagnostico(es_completo=es_comp)

    def abrir_modal_diagnostico(self):
        tipo = self.combo_nombre.get()
        if tipo == "Seleccione el equipo":
            messagebox.showwarning("Selección Requerida", "Seleccione un tipo de equipo válido antes de diagnosticar.")
            return
        VentanaDiagnosticoTecnico(
            self.root, tipo, self.PALETA, self.modo_oscuro,
            datos_previos=self.datos_tecnicos_temporales,
            guardar_callback=self.guardar_diagnostico_desde_modal
        )

    def guardar_diagnostico_desde_modal(self, datos_res):
        self.datos_tecnicos_temporales = datos_res
        bien_temp = {"nombre": self.combo_nombre.get(), "detalles_tecnicos": datos_res}
        es_comp = verificar_informacion_completa(bien_temp)
        self.actualizar_badge_diagnostico(es_completo=es_comp)

        id_val = self.entry_id.get().strip()
        if id_val.isdigit():
            id_int = int(id_val)
            idx = next((i for i, b in enumerate(self.bienes) if b["id"] == id_int), None)
            if idx is not None:
                self.bienes[idx]["detalles_tecnicos"] = datos_res
                self.bienes[idx]["perifericos"] = datos_res
                guardar_datos_locales(self.bienes)
                self.actualizar_tabla()

    def ver_ficha_tecnica(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Sin Selección", "Seleccione un activo para consultar su ficha técnica.")
            return
        id_bien = int(self.tabla.item(sel[0])["values"][0])
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if bien:
            VentanaFichaTecnica(self.root, bien, self.modo_oscuro, self.PALETA)

    def dar_de_baja_bien(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Sin Selección", "Seleccione un activo para tramitar su desincorporación.")
            return
        id_bien = int(self.tabla.item(sel[0])["values"][0])
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if not bien:
            return

        motivo = simpledialog.askstring("Justificación de Baja", f"Indique el motivo técnico de baja del Activo #{id_bien}:", parent=self.root)
        if not motivo or not motivo.strip():
            return

        if messagebox.askyesno("Confirmar", f"¿Está seguro de desincorporar formalmente el Activo ID #{id_bien}?\nMotivo: {motivo}"):
            registro_baja = {
                "id": id_bien,
                "nombre": bien.get("nombre", "N/A"),
                "asignado_a": bien.get("asignado_a", "N/A"),
                "mantenimiento": bien.get("mantenimiento", "No"),
                "fecha_ultimo_mant": bien.get("fecha_mant", "N/A"),
                "desc_mant": bien.get("desc_mant", ""),
                "detalles_tecnicos": bien.get("detalles_tecnicos", {}),
                "motivo_baja": motivo.strip(),
                "fecha_baja": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }

            archivo_acta = generar_acta_baja(registro_baja)
            if archivo_acta:
                self.bienes = [b for b in self.bienes if b["id"] != id_bien]
                guardar_datos_locales(self.bienes)
                guardar_baja_local(registro_baja)

                self.actualizar_tabla()
                self.actualizar_metricas()
                self.limpiar_formulario()
                messagebox.showinfo("Baja Procesada", f"El activo ha sido desincorporado exitosamente.\n\nActa emitida en PDF:\n{archivo_acta}")
            else:
                messagebox.showwarning("Atención", "No se pudo generar el PDF del acta. La operación de desincorporación ha sido cancelada para proteger el registro.")

    # ================= RECARGA Y TEMA =================
    def recargar_datos_completos(self):
        self.bienes = cargar_datos_locales()
        self.actualizar_tabla()
        self.actualizar_metricas()

    def filtrar_por_metrica(self, clave):
        if clave == "DESINCORPORADOS":
            self.mostrar_ventana_desincorporados()
            return
        self.filtro_metrica_activa = "TODOS" if self.filtro_metrica_activa == clave else clave
        self.actualizar_estilo_tarjetas_kpi()
        self.filtrar_tabla()

    def mostrar_ventana_desincorporados(self):
        VentanaDesincorporados(self.root, self.PALETA, self.modo_oscuro)

    def abrir_ventana_respaldos(self):
        VentanaRespaldos(self.root, self.PALETA, self.modo_oscuro, obtener_bienes_callback=lambda: self.bienes)

    def actualizar_metricas(self):
        tot = len(self.bienes)
        op, prev, corr = 0, 0, 0
        for b in self.bienes:
            m = str(b.get("mantenimiento", ""))
            if "Preventivo" in m:
                prev += 1
            elif "Correctivo" in m:
                corr += 1
            else:
                op += 1
        self.lbl_val_total.configure(text=str(tot))
        self.lbl_val_operativos.configure(text=str(op))
        self.lbl_val_preventivos.configure(text=str(prev))
        self.lbl_val_correctivos.configure(text=str(corr))
        self.lbl_val_desincorporados.configure(text=str(obtener_conteo_bajas()))

    def filtrar_tabla(self, event=None):
        crit = self.entry_buscar.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.imagenes_tabla_ref.clear()

        i = 0
        for bien in self.bienes:
            id_s = str(bien["id"]).lower()
            nom_s = str(bien["nombre"]).lower()
            asig_s = str(bien.get("asignado_a", "")).lower()
            desc_s = str(bien.get("desc_mant", "")).lower()
            mant_s = str(bien.get("mantenimiento", "")).strip()

            cumple = True
            if self.filtro_metrica_activa == "OPERATIVOS":
                cumple = (mant_s == "No")
            elif self.filtro_metrica_activa == "PREVENTIVOS":
                cumple = ("Preventivo" in mant_s)
            elif self.filtro_metrica_activa == "CORRECTIVOS":
                cumple = ("Correctivo" in mant_s)

            if not cumple:
                continue

            if crit in id_s or crit in nom_s or crit in asig_s or crit in desc_s:
                tag = "par" if i % 2 == 0 else "impar"
                es_comp = verificar_informacion_completa(bien)
                img = self.img_advertencia if (not es_comp and self.img_advertencia) else self.img_transparente
                if img:
                    self.imagenes_tabla_ref.append(img)

                self.tabla.insert(
                    "", "end", text="", image=img,
                    values=(
                        bien["id"], bien["nombre"], bien.get("asignado_a", "N/A"),
                        bien.get("mantenimiento", "No"), bien.get("fecha_mant", "N/A"),
                        bien.get("proximo_mant", "N/A")
                    ),
                    tags=(tag,)
                )
                i += 1

    def limpiar_filtro_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.filtro_metrica_activa = "TODOS"
        self.actualizar_estilo_tarjetas_kpi()
        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.filtrar_tabla()

    def actualizar_estilo_tarjetas_kpi(self):
        for i, card_info in enumerate(self.tarjetas_widgets):
            clave = card_info["clave"]
            activa = (self.filtro_metrica_activa == clave and clave != "TODOS")
            est = obtener_estilo_kpi(self.modo_oscuro, i, activa)
            color_ac = est["color_acento"]

            card_info["card"].configure(fg_color=est["bg_tarjeta"], border_color=est["borde_color"], border_width=est["grosor_borde"])
            card_info["check"].configure(text="●" if activa else "", text_color=est["color_indicador"])
            card_info["tit"].configure(text_color=color_ac)
            card_info["val"].configure(text_color=est["color_val"])
            card_info["sub"].configure(text_color=est["color_sub"])
            card_info["linea"].configure(fg_color=color_ac)

            ruta = card_info.get("ruta_png", "")
            if os.path.exists(ruta) and HAS_PIL:
                col_img = colorear_icono_png(ruta, color_ac)
                if col_img:
                    ctk_i = ctk.CTkImage(light_image=col_img, dark_image=col_img, size=(28, 28))
                    card_info["icon"].configure(image=ctk_i, text="")
                else:
                    card_info["icon"].configure(text="•", text_color=color_ac)

    def aplicar_tema_widgets(self):
        pal = self.PALETA["oscuro" if self.modo_oscuro else "claro"]
        guardar_preferencia_tema(self.modo_actual)

        # Botón de modo oscuro
        if hasattr(self, "btn_modo_oscuro"):
            archivo = "tema_claro.png" if self.modo_oscuro else "tema_oscuro.png"
            color_i = "#FFFFFF" if self.modo_oscuro else "#F8FAFC"
            ruta = obtener_ruta_icono(archivo)
            if os.path.exists(ruta) and HAS_PIL:
                col_i = colorear_icono_png(ruta, color_i)
                if col_i:
                    ctk_img = ctk.CTkImage(light_image=col_i, dark_image=col_i, size=(18, 18))
                    self.btn_modo_oscuro.configure(image=ctk_img, text="", fg_color="#d97706" if self.modo_oscuro else "#1e293b")

        # Color del panel flotante
        if hasattr(self, "drawer"):
            self.drawer.configure(fg_color="#0b1324" if self.modo_oscuro else "#0f172a")

        self.actualizar_estilo_tarjetas_kpi()

        # Fix de color de fondo para el campo 'proximo'
        if hasattr(self, "entry_proximo"):
            self.entry_proximo.configure(
                fg_color=("#ffffff", "#090d16"),
                text_color=("#0f172a", "#f8fafc")
            )
            self.calcular_proxima_fecha_mantenimiento()

        # Diagnóstico badge
        if hasattr(self, "badge_diagnostico"):
            if not self.entry_id.get().strip():
                self.actualizar_badge_diagnostico(sin_seleccion=True)
            else:
                comp = False
                if self.datos_tecnicos_temporales:
                    comp = verificar_informacion_completa({"nombre": self.combo_nombre.get(), "detalles_tecnicos": self.datos_tecnicos_temporales})
                self.actualizar_badge_diagnostico(es_completo=comp)

        # Treeview styling
        if hasattr(self, "tabla"):
            style = ttk.Style()
            style.theme_use("clam")
            tree_bg = pal["tree_bg"]
            tree_fg = pal["tree_fg"]
            tree_bg_odd = "#111d33" if self.modo_oscuro else "#f1f5f9"

            style.configure(
                "Treeview",
                background=tree_bg,
                foreground=tree_fg,
                fieldbackground=tree_bg,
                font=("Segoe UI", 9),
                rowheight=26,
                borderwidth=0,
                relief="flat"
            )
            style.map("Treeview", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])
            style.configure(
                "Treeview.Heading",
                background=pal["tree_head_bg"],
                foreground=pal["tree_head_fg"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                borderwidth=0
            )

            self.tabla.tag_configure("par", background=tree_bg, foreground=tree_fg)
            self.tabla.tag_configure("impar", background=tree_bg_odd, foreground=tree_fg)
            self.actualizar_tabla()


os.chdir(obtener_ruta_base())

if __name__ == "__main__":
    root = ctk.CTk()
    app = InventarioBienesApp(root)
    root.mainloop()