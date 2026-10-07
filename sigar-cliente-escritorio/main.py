# -*- coding: utf-8 -*-
import os
import sys
import ctypes
from datetime import date, datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk

from login import AuthApp
from modals import VentanaDesincorporados, VentanaRespaldos

from PIL import Image, ImageOps


def colorear_icono_png(ruta_png, color_hex):
    """
    Carga un PNG con transparencia y cambia el color de su silueta al color_hex indicado.
    """
    if not os.path.exists(ruta_png) or not HAS_PIL:
        return None
    try_img = Image.open(ruta_png).convert("RGBA")
    
    # Separar canal Alfa (transparencia)
    r, g, b, alpha = try_img.split()
    
    # Crear imagen sólida con el color deseado
    color_solido = Image.new("RGBA", try_img.size, color_hex)
    
    # Aplicar la máscara alfa original
    color_solido.putalpha(alpha)
    return color_solido


# Configuración global de CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def obtener_ruta_base():
    """Obtiene la ruta base adecuada tanto en modo script como empaquetado con PyInstaller."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


DIR_ACTUAL = obtener_ruta_base()
if DIR_ACTUAL not in sys.path:
    sys.path.insert(0, DIR_ACTUAL)

from database import (
    cargar_datos_locales,
    guardar_baja_local,
    guardar_datos_locales,
    obtener_conteo_bajas,
)
from styles import (
    FONT_BOLD,
    FONT_KPI_TIT,
    FONT_KPI_VAL,
    FONT_LABEL,
    PALETA,
    cargar_preferencia_tema,
    guardar_preferencia_tema,
    obtener_estilo_kpi,
    obtener_ruta_icono
)
from utils import (
    HAS_PIL,
    calcular_fecha_habil_3_meses,
    generar_acta_baja,
)

if HAS_PIL:
    from PIL import Image, ImageTk

ARCHIVO_LOGO = os.path.join(DIR_ACTUAL, "UNELLEZ LOGO.png")
PATH_LEMA = os.path.join(DIR_ACTUAL, "lema_unellez_oro.png")


def iniciar_sistema():
    root = ctk.CTk()
    root.withdraw()

    login_win = AuthApp(root)

    if getattr(login_win, "autenticado", False):
        root.deiconify()
        app = InventarioBienesApp(root)
        root.mainloop()
    else:
        root.destroy()


class InventarioBienesApp:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos"
        )
        self.root.geometry("1024x720")
        self.root.minsize(850, 580)

        self.modo_actual = cargar_preferencia_tema()
        self.modo_oscuro = self.modo_actual == "oscuro"
        ctk.set_appearance_mode("Dark" if self.modo_oscuro else "Light")

        self.filtro_metrica_activa = "TODOS"

        try:
            self.root.state("zoomed")
        except Exception:
            pass

        # Configuración del Grid Principal
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Cintillo
        self.root.rowconfigure(1, weight=0)  # KPIs
        self.root.rowconfigure(2, weight=0)  # Formulario
        self.root.rowconfigure(3, weight=0)  # Búsqueda
        self.root.rowconfigure(4, weight=1)  # Tabla
        self.root.rowconfigure(5, weight=0)  # Acciones

        self.PALETA = PALETA
        self.bienes = []
        self.tarjetas_widgets = []

        # Construcción GUI
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
        self.crear_menu_contextual()
        self.crear_panel_acciones()

        # Aplicar el tema seleccionado
        self.aplicar_tema_widgets()

        # Carga de datos inicial
        self.bienes = cargar_datos_locales()
        self.actualizar_tabla()
        self.actualizar_metricas()
        self.calcular_proxima_fecha_mantenimiento()
        self.root.after(200, self.activar_foco_inicial)

    def activar_foco_inicial(self):
        self.root.focus_force()
        self.entry_id.focus_force()

    # --- CINTILLO INSTITUCIONAL ---
    def crear_cintillo_institucional(self):
        self.frame_cintillo = ctk.CTkFrame(
            self.root, fg_color="#1C2F46", corner_radius=0, height=48
        )
        self.frame_cintillo.grid(row=0, column=0, sticky="ew")
        self.frame_cintillo.pack_propagate(False)

        # Contenedor
        frame_logo_titulo = ctk.CTkFrame(self.frame_cintillo, fg_color="transparent")
        frame_logo_titulo.pack(side="left", padx=12, pady=3)

        # 1. Ícono Logo UNELLEZ
        self.logo_img = None
        if os.path.exists(ARCHIVO_LOGO) and HAS_PIL:
            try:
                img_pil = Image.open(ARCHIVO_LOGO)
                self.logo_img = ctk.CTkImage(
                    light_image=img_pil, dark_image=img_pil, size=(30, 30)
                )
                lbl_logo = ctk.CTkLabel(
                    frame_logo_titulo, image=self.logo_img, text=""
                )
                lbl_logo.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        # 2. Texto "UNELLEZ"
        lbl_unellez = ctk.CTkLabel(
            frame_logo_titulo,
            text="UNELLEZ",
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"),
            text_color="#FF6600",
        )
        lbl_unellez.pack(side="left")

        # 3. Separador Vertical (Línea física uniforme)
        lbl_separador = ctk.CTkLabel(
            frame_logo_titulo,
            text="|",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#565D68",
        )
        lbl_separador.pack(side="left", padx=(15, 2), pady=(0, 8))

        if os.path.exists(PATH_LEMA) and HAS_PIL:
            try:
                img_lema_pil = Image.open(PATH_LEMA).convert("RGBA")
                target_height = 160
                aspect_ratio = img_lema_pil.width / img_lema_pil.height
                target_width = int(target_height * aspect_ratio)

                self.img_lema_oro = ctk.CTkImage(
                    light_image=img_lema_pil,
                    dark_image=img_lema_pil,
                    size=(target_width, target_height),
                )
                lbl_lema = ctk.CTkLabel(
                    frame_logo_titulo, 
                    image=self.img_lema_oro, 
                    text=""
                )
                lbl_lema.pack(side="left", padx=(0, 0), pady=6)
            except Exception as e:
                print(f"Error cargando lema: {e}")

        # Botón de modo visual (solo ícono)
        self.btn_modo_oscuro = ctk.CTkButton(
            self.frame_cintillo,
            text="",
            width=36,
            height=36,
            fg_color="#1e293b",
            hover_color="#334155",
            corner_radius=8,
            command=self.toggle_modo_oscuro_animado,
        )
        self.btn_modo_oscuro.pack(side="right", padx=12, pady=6)

    def toggle_modo_oscuro_animado(self):
        self.modo_oscuro = not self.modo_oscuro
        self.modo_actual = "oscuro" if self.modo_oscuro else "claro"
        ctk.set_appearance_mode("Dark" if self.modo_oscuro else "Light")
        self.aplicar_tema_widgets()

    def aplicar_tema_widgets(self):
        self.modo_oscuro = self.modo_actual == "oscuro"
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]
        guardar_preferencia_tema(self.modo_actual)

        if hasattr(self, "btn_modo_oscuro"):
            if self.modo_oscuro:
                archivo_png = "tema_claro.png"
                color_icono = "#FFFFFF"
                fg_btn = "#d97706"
                hover_btn = "#b45309"
            else:
                archivo_png = "tema_oscuro.png"
                color_icono = "#F8FAFC"
                fg_btn = "#1e293b"
                hover_btn = "#334155"

            ruta_png_modo = obtener_ruta_icono(archivo_png)
            
            if os.path.exists(ruta_png_modo) and HAS_PIL:
                img_coloreada = colorear_icono_png(ruta_png_modo, color_icono)
                if img_coloreada:
                    ctk_img_modo = ctk.CTkImage(
                        light_image=img_coloreada,
                        dark_image=img_coloreada,
                        size=(20, 20)
                    )
                    self.btn_modo_oscuro.configure(
                        image=ctk_img_modo,
                        text="",
                        fg_color=fg_btn,
                        hover_color=hover_btn
                    )
                    self.ref_img_btn_modo = ctk_img_modo
                else:
                    self.btn_modo_oscuro.configure(
                        text="", fg_color=fg_btn, hover_color=hover_btn
                    )
            else:
                self.btn_modo_oscuro.configure(
                    text="", fg_color=fg_btn, hover_color=hover_btn
                )

        self.actualizar_estilo_tarjetas_kpi()

        # Estilizado del Treeview
        if hasattr(self, "tabla"):
            style = ttk.Style()
            style.theme_use("clam")

            tree_bg = pal["tree_bg"]
            tree_fg = pal["tree_fg"]
            head_bg = pal["tree_head_bg"]
            head_fg = pal["tree_head_fg"]
            tree_bg_odd = "#1e293b" if self.modo_oscuro else "#f1f5f9"

            style.configure(
                "Treeview",
                background=tree_bg,
                foreground=tree_fg,
                fieldbackground=tree_bg,
                font=("Segoe UI", 9),
                rowheight=25,
                borderwidth=0,
            )
            style.map(
                "Treeview",
                background=[("selected", "#0284c7")],
                foreground=[("selected", "#ffffff")],
            )
            style.configure(
                "Treeview.Heading",
                background=head_bg,
                foreground=head_fg,
                font=("Segoe UI", 9, "bold"),
                relief="flat",
            )
            style.map(
                "Treeview.Heading",
                background=[("active", head_bg)],
                foreground=[("active", head_fg)],
            )

            self.tabla.tag_configure("par", background=tree_bg, foreground=tree_fg)
            self.tabla.tag_configure(
                "impar", background=tree_bg_odd, foreground=tree_fg
            )

    # --- TARJETAS MÉTRICAS ---
    def crear_panel_metricas(self):
        self.frame_kpis = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_kpis.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 5))

        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.tarjetas_widgets = []
        metricas = [
            ("TOTAL ACTIVOS", "0", "Bienes registrados", "total_activos.png", "TODOS"),
            ("OPERATIVOS", "0", "En servicio activo", "operativos.png", "OPERATIVOS"),
            ("PREVENTIVOS", "0", "Limpieza / Mantenimiento (Ciclo regular +3M)", "preventivos.png", "PREVENTIVOS"),
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

    def crear_tarjeta(self, col, titulo, valor_inicial, subtitulo, nombre_archivo_png, clave="TODOS"):
        card = ctk.CTkFrame(
            self.frame_kpis,
            corner_radius=10,
            border_width=1,
            cursor="hand2",
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(6, 2))

        lbl_check = ctk.CTkLabel(
            top_frame,
            text="",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
        )
        lbl_check.pack(side="left", padx=(0, 2))

        lbl_tit = ctk.CTkLabel(
            top_frame,
            text=titulo,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            anchor="w",
        )
        lbl_tit.pack(side="left", fill="x", expand=True)

        linea_separadora = ctk.CTkFrame(card, height=2, corner_radius=0)
        linea_separadora.pack(anchor="w", fill="x", padx=(10, 90), pady=(0, 4))

        body_frame = ctk.CTkFrame(card, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        val_frame = ctk.CTkFrame(body_frame, fg_color="transparent")
        val_frame.pack(fill="x", expand=True)
        val_frame.columnconfigure(0, weight=1)

        lbl_val = ctk.CTkLabel(
            val_frame,
            text=valor_inicial,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            anchor="w",
        )
        lbl_val.grid(row=0, column=0, sticky="w")

        lbl_icon = ctk.CTkLabel(
            val_frame,
            text="",
            anchor="e"
        )
        lbl_icon.grid(row=0, column=1, sticky="e")

        lbl_sub = ctk.CTkLabel(
            body_frame,
            text=subtitulo,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            anchor="w",
        )
        lbl_sub.pack(fill="x")

        elementos = [
            card, top_frame, body_frame, val_frame,
            lbl_check, lbl_tit, lbl_icon, lbl_val, lbl_sub, linea_separadora
        ]
        for elem in elementos:
            elem.bind("<Button-1>", lambda event, c=clave: self.filtrar_por_metrica(c))

        # Obtener ruta absoluta centralizada desde styles.py
        ruta_png = obtener_ruta_icono(nombre_archivo_png)

        self.tarjetas_widgets.append({
            "card": card,
            "check": lbl_check,
            "tit": lbl_tit,
            "icon": lbl_icon,
            "val": lbl_val,
            "sub": lbl_sub,
            "linea": linea_separadora,
            "clave": clave,
            "titulo_original": titulo,
            "ruta_png": ruta_png,
            "ctk_img_ref": None
        })
        return lbl_val
    
    def actualizar_estilo_tarjetas_kpi(self):
        for i, card_info in enumerate(self.tarjetas_widgets):
            clave_kpi = card_info["clave"]
            esta_activa = self.filtro_metrica_activa == clave_kpi and clave_kpi != "TODOS"
            estilo = obtener_estilo_kpi(self.modo_oscuro, i, esta_activa)

            color_acento = estilo["color_acento"]

            card_info["card"].configure(
                fg_color=estilo["bg_tarjeta"],
                border_color=estilo["borde_color"],
                border_width=estilo["grosor_borde"],
            )
            card_info["check"].configure(
                text="●" if esta_activa else "",
                text_color=estilo["color_indicador"],
            )
            card_info["tit"].configure(text_color=color_acento)
            card_info["val"].configure(text_color=estilo["color_val"])
            card_info["sub"].configure(text_color=estilo["color_sub"])
            
            if "linea" in card_info:
                card_info["linea"].configure(fg_color=color_acento)

            ruta_png = card_info.get("ruta_png", "")
            if os.path.exists(ruta_png) and HAS_PIL:
                img_coloreada = colorear_icono_png(ruta_png, color_acento)
                if img_coloreada:
                    ctk_img = ctk.CTkImage(
                        light_image=img_coloreada,
                        dark_image=img_coloreada,
                        size=(32, 32)
                    )
                    card_info["icon"].configure(image=ctk_img, text="")
                    card_info["ctk_img_ref"] = ctk_img
                else:
                    card_info["icon"].configure(text="📊", text_color=color_acento)
            else:
                card_info["icon"].configure(text="📊", text_color=color_acento)

    # --- FORMULARIO ---
    def crear_formulario(self):
        self.frame_form = ctk.CTkFrame(self.root, corner_radius=10)
        self.frame_form.grid(row=2, column=0, sticky="ew", padx=15, pady=2)
        self.frame_form.columnconfigure(1, weight=1)
        self.frame_form.columnconfigure(3, weight=2)
        self.frame_form.columnconfigure(5, weight=1)

        lbl_titulo_seccion = ctk.CTkLabel(
            self.frame_form,
            text=" REGISTRO Y EDICIÓN DE ACTIVOS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#0284c7" if not self.modo_oscuro else "#38bdf8",
            anchor="w"
        )
        lbl_titulo_seccion.grid(row=0, column=0, columnspan=6, padx=12, pady=(6, 2), sticky="w")

        lbl1 = ctk.CTkLabel(
            self.frame_form,
            text="ID único:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl1.grid(row=1, column=0, padx=(12, 5), pady=3, sticky="e")

        self.entry_id = ctk.CTkEntry(
            self.frame_form, font=("Segoe UI", 11), height=28
        )
        self.entry_id.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        lbl2 = ctk.CTkLabel(
            self.frame_form,
            text="Asignado a:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl2.grid(row=1, column=2, padx=(10, 5), pady=3, sticky="e")

        opciones_asignacion = [
            "Departamento de Sistemas",
            "Administración",
            "Laboratorio 1",
            "Rectorado",
        ]
        self.combo_asignado = ctk.CTkOptionMenu(
            self.frame_form, values=opciones_asignacion, height=28
        )
        self.combo_asignado.grid(
            row=1, column=3, columnspan=3, padx=5, pady=3, sticky="ew"
        )

        frame_btn_form = ctk.CTkFrame(self.frame_form, fg_color="transparent")
        frame_btn_form.grid(
            row=1, column=6, rowspan=4, padx=(10, 12), pady=3, sticky="ns"
        )

        ctk.CTkButton(
            frame_btn_form,
            text="Registrar Nuevo",
            fg_color="#0284C7",
            hover_color="#0369a1",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.agregar_bien,
            height=26,
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            frame_btn_form,
            text="Guardar Cambios",
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.actualizar_bien,
            height=26,
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            frame_btn_form,
            text="Limpiar Campos",
            fg_color="#475569",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.limpiar_formulario,
            height=26,
        ).pack(fill="x", pady=2)

        lbl3 = ctk.CTkLabel(
            self.frame_form,
            text="Descripción / Nombre:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl3.grid(row=2, column=0, padx=(12, 5), pady=3, sticky="e")

        self.entry_nombre = ctk.CTkEntry(
            self.frame_form, font=("Segoe UI", 11), height=28
        )
        self.entry_nombre.grid(
            row=2, column=1, columnspan=5, padx=5, pady=3, sticky="ew"
        )

        lbl4 = ctk.CTkLabel(
            self.frame_form,
            text="¿Mantenimiento?:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl4.grid(row=3, column=0, padx=(12, 5), pady=3, sticky="e")

        self.combo_mant = ctk.CTkOptionMenu(
            self.frame_form,
            values=["No", "Sí (Preventivo)", "Sí (Correctivo)"],
            height=28,
        )
        self.combo_mant.set("No")
        self.combo_mant.grid(row=3, column=1, padx=5, pady=3, sticky="w")

        lbl5 = ctk.CTkLabel(
            self.frame_form,
            text="Fecha (DD/MM/AAAA):",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl5.grid(row=3, column=2, padx=(10, 5), pady=3, sticky="e")

        self.entry_fecha_mant = ctk.CTkEntry(
            self.frame_form, font=("Segoe UI", 11), height=28
        )
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha_mant.grid(row=3, column=3, padx=5, pady=3, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.formatear_y_validar_fecha)

        lbl6 = ctk.CTkLabel(
            self.frame_form,
            text="Próximo (Hábil +3M):",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl6.grid(row=3, column=4, padx=(10, 5), pady=3, sticky="e")

        self.entry_proximo = ctk.CTkEntry(
            self.frame_form,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=28,
            state="readonly",
        )
        self.entry_proximo.grid(row=3, column=5, padx=5, pady=3, sticky="ew")

        lbl7 = ctk.CTkLabel(
            self.frame_form,
            text="Detalle / Observación:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl7.grid(row=4, column=0, padx=(12, 5), pady=3, sticky="e")

        self.entry_desc_mant = ctk.CTkEntry(
            self.frame_form, font=("Segoe UI", 11), height=28
        )
        self.entry_desc_mant.grid(
            row=4, column=1, columnspan=5, padx=5, pady=(3, 6), sticky="ew"
        )

    # --- BÚSQUEDA ---
    def crear_panel_busqueda(self):
        self.frame_busqueda = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_busqueda.grid(
            row=3, column=0, sticky="ew", padx=15, pady=(4, 2)
        )

        self.lbl_buscar = ctk.CTkLabel(
            self.frame_busqueda,
            text="🔍 Buscar Activo:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.lbl_buscar.pack(side="left", padx=(0, 6))

        self.entry_buscar = ctk.CTkEntry(
            self.frame_busqueda, font=("Segoe UI", 11), width=240, height=28
        )
        self.entry_buscar.pack(side="left", padx=4)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)

        self.btn_limpiar_filtro = ctk.CTkButton(
            self.frame_busqueda,
            text="Limpiar Filtro",
            fg_color="#002B49",
            hover_color="#001F35",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            command=self.limpiar_filtro_busqueda,
        )
        self.btn_limpiar_filtro.pack(side="left", padx=6)

        self.lbl_indicador_busqueda = ctk.CTkLabel(
            self.frame_busqueda,
            text="(Doble clic para editar / Clic derecho para opciones)",
            font=ctk.CTkFont(size=10),
            text_color="#94a3b8",
        )
        self.lbl_indicador_busqueda.pack(side="right")

    # --- TABLA DE DATOS Y MENÚ CONTEXTUAL ---
    def crear_tabla(self):
        self.frame_tabla = ctk.CTkFrame(self.root, corner_radius=8)
        self.frame_tabla.grid(row=4, column=0, sticky="nsew", padx=15, pady=(2, 2))
        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        columnas = (
            "id",
            "nombre",
            "asignado_a",
            "mantenimiento",
            "fecha_mant",
            "proximo_mant",
        )
        self.tabla = ttk.Treeview(
            self.frame_tabla, columns=columnas, show="headings"
        )
        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción / Detalles del Bien")
        self.tabla.heading("asignado_a", text="Asignado a")
        self.tabla.heading("mantenimiento", text="Mantenimiento")
        self.tabla.heading("fecha_mant", text="Última Fecha")
        self.tabla.heading("proximo_mant", text="Próxima Fecha (Hábil)")

        self.tabla.column("id", width=75, minwidth=50, anchor="center", stretch=False)
        self.tabla.column("nombre", width=220, minwidth=150, anchor="w", stretch=True)
        self.tabla.column("asignado_a", width=140, minwidth=120, anchor="w", stretch=True)
        self.tabla.column("mantenimiento", width=115, minwidth=90, anchor="center", stretch=False)
        self.tabla.column("fecha_mant", width=100, minwidth=85, anchor="center", stretch=False)
        self.tabla.column("proximo_mant", width=145, minwidth=135, anchor="center", stretch=False)

        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        self.tabla.bind("<Button-3>", self.mostrar_menu_contextual)
        self.tabla.bind("<Button-2>", self.mostrar_menu_contextual)

        scrollbar = ctk.CTkScrollbar(self.frame_tabla, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=2)

    def crear_menu_contextual(self):
        self.menu_contextual = tk.Menu(
            self.root, tearoff=0, font=("Segoe UI", 9)
        )
        self.menu_contextual.add_command(
            label="✏️ Editar Activo", command=self.cargar_seleccion_para_editar
        )
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="❌ Dar de Baja / Generar Acta PDF",
            command=self.dar_de_baja_bien,
            foreground="#dc2626",
            activeforeground="#ffffff",
            activebackground="#dc2626",
        )

    def mostrar_menu_contextual(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            self.tabla.selection_set(item)
            self.tabla.focus(item)
            self.menu_contextual.post(event.x_root, event.y_root)

    # --- ACCIONES / PANEL INFERIOR ---
    def crear_panel_acciones(self):
        self.frame_acciones = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_acciones.grid(
            row=5, column=0, sticky="ew", padx=15, pady=(2, 8)
        )

        self.btn_centro_respaldos = ctk.CTkButton(
            self.frame_acciones,
            text="☁ Centro de Respaldos",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=30,
            command=self.abrir_ventana_respaldos,
        )
        self.btn_centro_respaldos.pack(side="left")

        self.lbl_info_pie = ctk.CTkLabel(
            self.frame_acciones,
            text="SIGAR V2.5 — UNELLEZ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        )
        self.lbl_info_pie.pack(side="right", pady=3)

    def abrir_ventana_respaldos(self):
        VentanaRespaldos(
            self.root,
            self.PALETA,
            self.modo_oscuro,
            obtener_bienes_callback=lambda: self.bienes,
        )

    # --- LÓGICA CRUD Y OPERACIONES ---
    def agregar_bien(self):
        id_val = self.entry_id.get().strip()
        nombre_val = self.entry_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()
        mant_val = self.combo_mant.get()
        fecha_mant_val = self.entry_fecha_mant.get().strip()
        proximo_val = self.entry_proximo.get().strip()
        desc_mant_val = self.entry_desc_mant.get().strip()

        if not id_val or not nombre_val or not asignado_val:
            messagebox.showwarning(
                "Campos Incompletos",
                "Por favor, complete el ID, Nombre/Descripción y 'Asignado a'.",
            )
            return

        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning(
                "Tipo Incorrecto", "El ID debe ser un número entero."
            )
            return

        if any(b["id"] == id_int for b in self.bienes):
            messagebox.showwarning(
                "ID Duplicado",
                f"El activo con ID {id_int} ya existe en el sistema.",
            )
            return

        nuevo_bien = {
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else "",
        }

        self.bienes.append(nuevo_bien)
        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo(
                "Registro Exitoso",
                "El activo ha sido guardado localmente en bienes.json.",
            )

    def actualizar_bien(self):
        id_val = self.entry_id.get().strip()
        if not id_val:
            messagebox.showwarning(
                "Sin ID",
                "Ingrese o seleccione el ID del activo que desea actualizar.",
            )
            return

        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("Tipo Incorrecto", "El ID debe ser numérico.")
            return

        nombre_val = self.entry_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()
        mant_val = self.combo_mant.get()
        fecha_mant_val = self.entry_fecha_mant.get().strip()
        proximo_val = self.entry_proximo.get().strip()
        desc_mant_val = self.entry_desc_mant.get().strip()

        if not nombre_val or not asignado_val:
            messagebox.showwarning(
                "Campos Incompletos",
                "Por favor, complete la Descripción/Nombre y 'Asignado a'.",
            )
            return

        index = next((i for i, b in enumerate(self.bienes) if b["id"] == id_int), None)
        if index is None:
            messagebox.showerror(
                "No Encontrado",
                f"No se encontró ningún activo con el ID {id_int}.",
            )
            return

        self.bienes[index] = {
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else "",
        }

        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo(
                "Actualización Exitosa",
                f"Los datos del activo ID {id_int} han sido modificados localmente.",
            )

    def dar_de_baja_bien(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, seleccione un elemento de la tabla para darlo de baja.",
            )
            return

        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])
        nombre_bien = item["values"][1]

        motivo = simpledialog.askstring(
            "Justificación de Baja",
            f"Indique el motivo por el cual se da de baja el activo ID {id_bien}:\n({nombre_bien})",
            parent=self.root,
        )
        if not motivo or not motivo.strip():
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Desincorporación",
            f"¿Está seguro de desincorporar el activo ID {id_bien}?\n\nMotivo: {motivo.strip()}",
        )
        if confirmacion:
            bien_objetivo = next((b for b in self.bienes if b["id"] == id_bien), None)
            fecha_hora_baja = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            registro_baja = {
                "id": id_bien,
                "nombre": nombre_bien,
                "asignado_a": (
                    bien_objetivo.get("asignado_a", "N/A") if bien_objetivo else "N/A"
                ),
                "mantenimiento": (
                    bien_objetivo.get("mantenimiento", "N/A") if bien_objetivo else "N/A"
                ),
                "fecha_ultimo_mant": (
                    bien_objetivo.get("fecha_mant", "N/A") if bien_objetivo else "N/A"
                ),
                "desc_mant": (
                    bien_objetivo.get("desc_mant", "") if bien_objetivo else ""
                ),
                "motivo_baja": motivo.strip(),
                "fecha_baja": fecha_hora_baja,
            }

            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            guardar_datos_locales(self.bienes)
            guardar_baja_local(registro_baja)
            archivo_generado = generar_acta_baja(registro_baja)

            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo(
                "Baja Procesada",
                f"El activo ID {id_bien} ha sido desincorporado.\n📄 Documento: {archivo_generado}",
            )

    # --- FILTRADO Y NAVEGACIÓN ---
    def filtrar_por_metrica(self, clave):
        if clave == "DESINCORPORADOS":
            self.mostrar_ventana_desincorporados()
            return

        if self.filtro_metrica_activa == clave and clave != "TODOS":
            self.filtro_metrica_activa = "TODOS"
        else:
            self.filtro_metrica_activa = clave

        self.actualizar_estilo_tarjetas_kpi()
        self.filtrar_tabla()

    def mostrar_ventana_desincorporados(self):
        VentanaDesincorporados(self.root, self.PALETA, self.modo_oscuro)

    def actualizar_metricas(self):
        total = len(self.bienes)
        operativos = 0
        preventivos = 0
        correctivos = 0
        desincorporados = obtener_conteo_bajas()

        for b in self.bienes:
            mant = str(b.get("mantenimiento", "")).strip()
            if "Preventivo" in mant:
                preventivos += 1
            elif "Correctivo" in mant:
                correctivos += 1
            else:
                operativos += 1

        self.lbl_val_total.configure(text=str(total))
        self.lbl_val_operativos.configure(text=str(operativos))
        self.lbl_val_preventivos.configure(text=str(preventivos))
        self.lbl_val_correctivos.configure(text=str(correctivos))
        self.lbl_val_desincorporados.configure(text=str(desincorporados))

    def filtrar_tabla(self, event=None):
        criterio = self.entry_buscar.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        i = 0
        for bien in self.bienes:
            id_str = str(bien["id"]).lower()
            nombre_str = str(bien["nombre"]).lower()
            asignado_str = str(bien.get("asignado_a", "")).lower()
            desc_str = str(bien.get("desc_mant", "")).lower()
            mant_str = str(bien.get("mantenimiento", "")).strip()

            cumple_metrica = True
            if self.filtro_metrica_activa == "OPERATIVOS":
                cumple_metrica = mant_str == "No"
            elif self.filtro_metrica_activa == "PREVENTIVOS":
                cumple_metrica = "Preventivo" in mant_str
            elif self.filtro_metrica_activa == "CORRECTIVOS":
                cumple_metrica = "Correctivo" in mant_str

            if not cumple_metrica:
                continue

            if (
                criterio in id_str
                or criterio in nombre_str
                or criterio in asignado_str
                or criterio in desc_str
            ):
                tag_fila = "par" if i % 2 == 0 else "impar"
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        bien["id"],
                        bien["nombre"],
                        bien.get("asignado_a", "N/A"),
                        bien.get("mantenimiento", "No"),
                        bien.get("fecha_mant", "N/A"),
                        bien.get("proximo_mant", "N/A"),
                    ),
                    tags=(tag_fila,),
                )
                i += 1

    def limpiar_filtro_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.filtro_metrica_activa = "TODOS"
        self.actualizar_estilo_tarjetas_kpi()
        self.actualizar_tabla()

    def cargar_seleccion_para_editar(self, event=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, seleccione un elemento de la tabla para editar.",
            )
            return

        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])

        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if bien:
            self.entry_id.delete(0, tk.END)
            self.entry_id.insert(0, str(bien["id"]))
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.insert(0, bien["nombre"])
            self.combo_asignado.set(
                bien.get("asignado_a", "Departamento de Sistemas")
            )
            self.combo_mant.set(bien.get("mantenimiento", "No"))
            self.entry_fecha_mant.delete(0, tk.END)
            self.entry_fecha_mant.insert(
                0, bien.get("fecha_mant", date.today().strftime("%d/%m/%Y"))
            )
            self.entry_desc_mant.delete(0, tk.END)
            self.entry_desc_mant.insert(0, bien.get("desc_mant", ""))
            self.calcular_proxima_fecha_mantenimiento()
            self.entry_nombre.focus_force()

    def limpiar_formulario(self):
        self.entry_id.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_desc_mant.delete(0, tk.END)
        self.entry_fecha_mant.delete(0, tk.END)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.combo_mant.set("No")
        self.calcular_proxima_fecha_mantenimiento()
        self.entry_id.focus_force()

    def formatear_y_validar_fecha(self, event=None):
        if event and event.keysym in (
            "BackSpace",
            "Delete",
            "Left",
            "Right",
            "Tab",
            "Shift_L",
            "Shift_R",
        ):
            self.calcular_proxima_fecha_mantenimiento()
            return

        texto_actual = self.entry_fecha_mant.get()
        if len(texto_actual) == 10 and texto_actual.count("/") == 2:
            self.calcular_proxima_fecha_mantenimiento()
            return

        partes = texto_actual.split("/")
        dia = "".join(c for c in partes[0] if c.isdigit())[:2]
        mes = "".join(c for c in partes[1] if c.isdigit())[:2] if len(partes) > 1 else ""
        anio = "".join(c for c in partes[2] if c.isdigit())[:4] if len(partes) > 2 else ""

        fecha_formateada = dia
        if len(dia) == 2 or len(partes) > 1:
            fecha_formateada += "/" + mes
        if len(mes) == 2 or len(partes) > 2:
            fecha_formateada += "/" + anio

        if texto_actual != fecha_formateada:
            self.entry_fecha_mant.delete(0, tk.END)
            self.entry_fecha_mant.insert(0, fecha_formateada)

        self.calcular_proxima_fecha_mantenimiento()

    def calcular_proxima_fecha_mantenimiento(self):
        fecha_str = self.entry_fecha_mant.get().strip()

        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(fecha_str, fmt).date()
                proxima_str = calcular_fecha_habil_3_meses(dt)

                self.entry_proximo.configure(
                    fg_color="#1e293b" if self.modo_oscuro else "#f8fafc",
                    text_color="#f8fafc" if self.modo_oscuro else "#0f172a",
                )
                self.entry_proximo.configure(state="normal")
                self.entry_proximo.delete(0, tk.END)
                self.entry_proximo.insert(0, proxima_str)
                self.entry_proximo.configure(state="readonly")
                return proxima_str
            except ValueError:
                pass

        self.entry_proximo.configure(fg_color="#f9cece", text_color="#dc2626")
        self.entry_proximo.configure(state="normal")
        self.entry_proximo.delete(0, tk.END)
        self.entry_proximo.insert(0, "Formato Inválido")
        self.entry_proximo.configure(state="readonly")
        return None

    def actualizar_tabla(self):
        self.filtrar_tabla()


os.chdir(obtener_ruta_base())

if __name__ == "__main__":
    root = ctk.CTk()
    app = InventarioBienesApp(root)
    root.mainloop()