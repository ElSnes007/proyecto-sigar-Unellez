# -*- coding: utf-8 -*-
from datetime import date, datetime
import os
import sys
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from login import AuthApp  # Importación directa del módulo

try:
    # Hace que la aplicación sea DPI Aware en Windows
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Process_Per_Monitor_DPI_Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def iniciar_sistema():
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal mientras valida credenciales

    # Lanzar la ventana de login
    login_win = AuthApp(root)

    # Verificar si el usuario se autenticó correctamente
    if getattr(login_win, "autenticado", False):
        root.deiconify()  # Mostrar la interfaz principal
        app = InventarioBienesApp(root)
        root.mainloop()
    else:
        root.destroy()  # Cerrar si canceló o falló el login


def obtener_ruta_base():
    """Obtiene la ruta base adecuada tanto en modo script como empaquetado con PyInstaller."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# Registrar la ruta base en sys.path antes de cualquier importación de módulos locales
DIR_ACTUAL = obtener_ruta_base()
if DIR_ACTUAL not in sys.path:
    sys.path.insert(0, DIR_ACTUAL)

from database import (
    ARCHIVO_BAJAS,
    URL_RESPALDO_CLOUD,
    cargar_datos_locales,
    cargar_historial_bajas,
    exportar_respaldo_nube_bd,
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
    hex_a_rgb,
    rgb_a_hex,
)
from utils import (
    HAS_PIL,
    HAS_REQUESTS,
    calcular_fecha_habil_3_meses,
    generar_acta_baja,
)

if HAS_PIL:
    from PIL import Image, ImageTk

# Definición dinámica de imágenes
ARCHIVO_LOGO = os.path.join(DIR_ACTUAL, "UNELLEZ LOGO.png")
PATH_LEMA = os.path.join(DIR_ACTUAL, "lema_unellez_oro.png")


class InventarioBienesApp:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos"
        )
        self.root.geometry("1024x680")
        self.root.minsize(800, 500)

        self.modo_actual = cargar_preferencia_tema()
        self.modo_oscuro = self.modo_actual == "oscuro"
        self.filtro_metrica_activa = "TODOS"  # Estado del filtro por KPI

        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Cintillo
        self.root.rowconfigure(1, weight=0)  # KPIs
        self.root.rowconfigure(2, weight=0)  # Formulario
        self.root.rowconfigure(3, weight=0)  # Búsqueda
        self.root.rowconfigure(4, weight=1)  # Tabla
        self.root.rowconfigure(5, weight=0)  # Acciones

        self.PALETA = PALETA
        self.root.configure(bg=self.PALETA[self.modo_actual]["bg_root"])

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.bienes = []
        self.tarjetas_widgets = []
        self.labels_texto = []
        self.entries_widgets = []

        # Construcción GUI
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
        self.crear_menu_contextual()
        self.crear_panel_acciones()

        # Aplicar tema
        self.aplicar_tema_widgets()

        # Cargar datos
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
        self.frame_cintillo = tk.Frame(self.root, bg="#002B49", height=44)
        self.frame_cintillo.grid(row=0, column=0, sticky="ew")
        self.frame_cintillo.pack_propagate(False)

        frame_logo_titulo = tk.Frame(self.frame_cintillo, bg="#002B49")
        frame_logo_titulo.pack(side="left", padx=12, pady=2)

        self.logo_img = None
        if os.path.exists(ARCHIVO_LOGO):
            try:
                if HAS_PIL:
                    img_pil = Image.open(ARCHIVO_LOGO).resize(
                        (34, 34), Image.Resampling.LANCZOS
                    )
                    self.logo_img = ImageTk.PhotoImage(img_pil)
                else:
                    raw_img = tk.PhotoImage(file=ARCHIVO_LOGO)
                    w_factor = max(1, raw_img.width() // 34)
                    h_factor = max(1, raw_img.height() // 34)
                    self.logo_img = raw_img.subsample(w_factor, h_factor)
            except Exception:
                self.logo_img = None

        if self.logo_img:
            lbl_logo = tk.Label(
                frame_logo_titulo, image=self.logo_img, bg="#002B49"
            )
            lbl_logo.pack(side="left", padx=(0, 8))

        lbl_unellez = tk.Label(
            frame_logo_titulo,
            text="UNELLEZ",
            font=("Segoe UI", 13, "bold"),
            fg="#FF6600",
            bg="#002B49",
        )
        lbl_unellez.pack(side="left")

        lbl_separador = tk.Label(
            frame_logo_titulo,
            text="|",
            font=("Segoe UI", 12, "bold"),
            fg="#475569",
            bg="#002B49",
        )
        lbl_separador.pack(side="left", padx=(10, 10))

        if os.path.exists(PATH_LEMA) and HAS_PIL:
            try:
                img_lema_pil = Image.open(PATH_LEMA).convert("RGBA")
                if hasattr(img_lema_pil, "get_flattened_data"):
                    pixels = list(img_lema_pil.get_flattened_data())
                else:
                    pixels = list(img_lema_pil.getdata())

                new_data = [
                    (
                        (255, 255, 255, 0)
                        if item[0] > 230 and item[1] > 230 and item[2] > 230
                        else item
                    )
                    for item in pixels
                ]
                img_lema_pil.putdata(new_data)

                bbox = img_lema_pil.getbbox()
                if bbox:
                    img_lema_pil = img_lema_pil.crop(bbox)

                target_height = 18
                aspect_ratio = img_lema_pil.width / img_lema_pil.height
                target_width = int(target_height * aspect_ratio)

                img_lema_pil = img_lema_pil.resize(
                    (target_width, target_height), Image.Resampling.LANCZOS
                )
                self.img_lema_oro = ImageTk.PhotoImage(img_lema_pil)
                lbl_lema = tk.Label(
                    frame_logo_titulo,
                    image=self.img_lema_oro,
                    bg="#002B49",
                    bd=0,
                )
                lbl_lema.pack(side="left", pady=(1, 0))
            except Exception as e:
                print(f"Error cargando lema: {e}")

        self.btn_modo_oscuro = tk.Button(
            self.frame_cintillo,
            text="🌙 Cuidado de Vista",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#f8fafc",
            activebackground="#334155",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            relief="flat",
        )
        self.btn_modo_oscuro.config(command=self.toggle_modo_oscuro_animado)
        self.btn_modo_oscuro.pack(side="right", padx=12, pady=7)

    # --- TEMA MODO OSCURO / CLARO ---
    def toggle_modo_oscuro_animado(self):
        color_inicio = self.PALETA["oscuro" if self.modo_oscuro else "claro"][
            "bg_root"
        ]
        self.modo_oscuro = not self.modo_oscuro
        self.modo_actual = "oscuro" if self.modo_oscuro else "claro"
        color_fin = self.PALETA["oscuro" if self.modo_oscuro else "claro"][
            "bg_root"
        ]

        rgb_inicio = hex_a_rgb(color_inicio)
        rgb_fin = hex_a_rgb(color_fin)
        self.animar_transicion_bg(rgb_inicio, rgb_fin, paso=0, total_pasos=12)

    def animar_transicion_bg(self, rgb_inicio, rgb_fin, paso, total_pasos):
        if paso <= total_pasos:
            factor = paso / total_pasos
            r = int(rgb_inicio[0] + (rgb_fin[0] - rgb_inicio[0]) * factor)
            g = int(rgb_inicio[1] + (rgb_fin[1] - rgb_inicio[1]) * factor)
            b = int(rgb_inicio[2] + (rgb_fin[2] - rgb_inicio[2]) * factor)
            color_interp = rgb_a_hex((r, g, b))

            self.root.configure(bg=color_interp)
            self.frame_kpis.configure(bg=color_interp)
            if hasattr(self, "frame_busqueda"):
                self.frame_busqueda.configure(bg=color_interp)
            self.frame_tabla.configure(bg=color_interp)
            self.frame_acciones.configure(bg=color_interp)
            self.root.after(
                18,
                lambda: self.animar_transicion_bg(
                    rgb_inicio, rgb_fin, paso + 1, total_pasos
                ),
            )
        else:
            self.aplicar_tema_widgets()

    def aplicar_tema_widgets(self):
        self.modo_oscuro = self.modo_actual == "oscuro"
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]
        guardar_preferencia_tema(self.modo_actual)

        self.root.config(bg=pal["bg_root"])
        if hasattr(self, "frame_kpis"):
            self.frame_kpis.config(bg=pal["bg_root"])
        if hasattr(self, "frame_busqueda"):
            self.frame_busqueda.config(bg=pal["bg_root"])
        if hasattr(self, "frame_tabla"):
            self.frame_tabla.config(bg=pal["bg_root"])
        if hasattr(self, "frame_acciones"):
            self.frame_acciones.config(bg=pal["bg_root"])

        if hasattr(self, "btn_modo_oscuro"):
            if self.modo_oscuro:
                self.btn_modo_oscuro.config(
                    text="☀️ Modo Claro",
                    bg="#d97706",
                    fg="#ffffff",
                    activebackground="#b45309",
                    activeforeground="#ffffff",
                )
            else:
                self.btn_modo_oscuro.config(
                    text="🌙 Cuidado de Vista",
                    bg="#1e293b",
                    fg="#f8fafc",
                    activebackground="#334155",
                    activeforeground="#ffffff",
                )

        fg_texto_modo = pal["fg_texto"]
        bg_panel_modo = pal["bg_panel"]

        if hasattr(self, "frame_form"):
            self.frame_form.config(
                bg=bg_panel_modo,
                fg=fg_texto_modo,
                bd=0,
                highlightthickness=1,
                highlightbackground=pal["border_panel"],
                highlightcolor=pal["border_panel"],
            )

        for lbl in getattr(self, "labels_texto", []):
            lbl.config(bg=bg_panel_modo, fg=fg_texto_modo, font=FONT_LABEL)

        for f in getattr(self, "frames_form_internos", []):
            f.config(bg=bg_panel_modo)

        for entry in getattr(self, "entries_widgets", []):
            entry.config(
                bg=pal["entry_bg"],
                fg=pal["entry_fg"],
                insertbackground=pal["entry_fg"],
                highlightbackground=pal["entry_border"],
                highlightthickness=1,
                font=FONT_LABEL,
                bd=0,
            )

        self.style.theme_use("default")
        self.style.configure(
            "TCombobox",
            fieldbackground=pal["entry_bg"],
            background=pal["entry_bg"],
            foreground=pal["entry_fg"],
            darkcolor=pal["entry_bg"],
            lightcolor=pal["entry_bg"],
            selectbackground=pal["entry_bg"],
            selectforeground=pal["entry_fg"],
            arrowcolor=fg_texto_modo,
            font=FONT_LABEL,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", pal["entry_bg"])],
            foreground=[("readonly", pal["entry_fg"])],
        )

        if hasattr(self, "entry_proximo"):
            self.entry_proximo.config(font=FONT_BOLD)
            # Re-evaluar la fecha para recalcular el color del texto (normal vs. rojo según el modo)
            self.calcular_proxima_fecha_mantenimiento()

        if hasattr(self, "lbl_info_pie"):
            self.lbl_info_pie.config(
                bg=pal["bg_root"], fg=pal["fg_subtexto"], font=FONT_LABEL
            )
        if hasattr(self, "lbl_indicador_busqueda"):
            self.lbl_indicador_busqueda.config(
                bg=pal["bg_root"], fg=pal["fg_subtexto"], font=FONT_LABEL
            )
        if hasattr(self, "lbl_icon_buscar"):
            self.lbl_icon_buscar.config(
                bg=pal["bg_root"], fg=pal["fg_texto"], font=FONT_LABEL
            )

        # Ajuste dinámico de contraste para el Botón Centro de Respaldos
        if hasattr(self, "btn_centro_respaldos"):
            if self.modo_oscuro:
                self.btn_centro_respaldos.config(
                    bg="#183056",
                    fg="#f8fafc",
                    activebackground="#0A2B5A",
                    activeforeground="#ffffff",
                    bd=0,
                    highlightthickness=0,
                )
            else:
                self.btn_centro_respaldos.config(
                    bg="#42ADF8",
                    fg="#ffffff",
                    activebackground="#44a2ff",
                    activeforeground="#ffffff",
                    bd=0,
                    highlightthickness=0,
                )

        # Renderizar estado de tarjetas KPI
        self.actualizar_estilo_tarjetas_kpi()

        if hasattr(self, "tabla"):
            tree_bg_even = pal["tree_bg"] if not self.modo_oscuro else "#1e293b"
            tree_bg_odd = pal["bg_root"] if not self.modo_oscuro else "#0f172a"

            self.style.configure(
                "Treeview",
                background=tree_bg_even,
                foreground=pal["tree_fg"],
                fieldbackground=tree_bg_even,
                font=("Segoe UI", 9),
                rowheight=28,
                borderwidth=0,
            )
            self.style.map(
                "Treeview",
                background=[("selected", "#2563eb")],
                foreground=[("selected", "#ffffff")],
            )
            self.style.configure(
                "Treeview.Heading",
                background=pal["tree_head_bg"],
                foreground=pal["tree_head_fg"],
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                borderwidth=1,
            )
            self.style.map(
                "Treeview.Heading",
                background=[("active", pal["tree_head_bg"])],
                foreground=[("active", pal["tree_head_fg"])],
            )

            self.tabla.tag_configure(
                "par", background=tree_bg_even, foreground=pal["tree_fg"]
            )
            self.tabla.tag_configure(
                "impar", background=tree_bg_odd, foreground=pal["tree_fg"]
            )

    def actualizar_estilo_tarjetas_kpi(self):
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        for i, card_info in enumerate(getattr(self, "tarjetas_widgets", [])):
            cfg = pal["kpis"][i]
            clave_kpi = card_info["clave"]
            titulo_base = card_info["titulo_original"]
            color_acento = cfg["text"]

            esta_activa = (
                self.filtro_metrica_activa == clave_kpi and clave_kpi != "TODOS"
            )

            bg_tarjeta = cfg["active_bg"] if esta_activa else cfg["bg"]
            borde_color = cfg["active_border"] if esta_activa else cfg["border"]

            grosor_borde = 3 if esta_activa else 1
            padx_comp = 6 if esta_activa else 8
            pady_comp = 4 if esta_activa else 6

            card_info["card"].config(
                bg=bg_tarjeta,
                highlightbackground=borde_color,
                highlightcolor=borde_color,
                highlightthickness=grosor_borde,
            )
            card_info["strip"].config(
                bg=color_acento if not esta_activa else borde_color
            )

            card_info["content"].config(
                bg=bg_tarjeta, padx=padx_comp, pady=pady_comp
            )

            if "top_frame" in card_info:
                card_info["top_frame"].config(bg=bg_tarjeta)
            if "left_col" in card_info:
                card_info["left_col"].config(bg=bg_tarjeta)
            if "right_col" in card_info:
                card_info["right_col"].config(bg=bg_tarjeta)
            card_info["head"].config(bg=bg_tarjeta)

            if "linea" in card_info:
                card_info["linea"].config(
                    bg=borde_color if esta_activa else color_acento
                )

            # Configuración del Check Independiente
            if "check" in card_info:
                card_info["check"].config(
                    text="●" if esta_activa else "",      # Se muestra solo si la tarjeta está activa
                    bg=bg_tarjeta,
                    fg=borde_color if esta_activa else color_acento,
                    font=("Consolas", 15, "bold")         # Tamaño y fuente independiente
                )

            # Título limpio sin añadir caracteres Unicode pegados
            card_info["tit"].config(
                text=titulo_base,
                bg=bg_tarjeta,
                fg=borde_color if esta_activa else color_acento,
                font=FONT_KPI_TIT,
            )
            card_info["sub"].config(
                bg=bg_tarjeta, fg=cfg["sub"], font=FONT_LABEL
            )
            card_info["icon"].config(
                bg=bg_tarjeta, fg=borde_color if esta_activa else color_acento
            )
            card_info["val"].config(
                bg=bg_tarjeta, fg=cfg["val"], font=FONT_KPI_VAL
            )
            
    # --- TARJETAS MÉTRICAS ---
    def crear_panel_metricas(self):
        self.frame_kpis = tk.Frame(
            self.root, bg=self.PALETA["claro"]["bg_root"]
        )
        self.frame_kpis.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 5))

        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.tarjetas_widgets = []
        metricas = [
            ("TOTAL ACTIVOS", "0", "Bienes registrados", "📋", "TODOS"),
            ("OPERATIVOS", "0", "En servicio activo", "🟢", "OPERATIVOS"),
            ("PREVENTIVOS", "0", "Ciclo regular (+3M)", "🔧", "PREVENTIVOS"),
            ("CORRECTIVOS", "0", "Ajuste / Reparación", "⚠️", "CORRECTIVOS"),
            ("DESINCORPORADOS", "0", "Actas emitidas", "❌", "DESINCORPORADOS"),
        ]

        for col, (titulo, valor, sub, icono, clave) in enumerate(metricas):
            val_widget = self.crear_tarjeta(col, titulo, valor, sub, icono, clave)
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

    def crear_tarjeta(
        self,
        col,
        titulo,
        valor_inicial,
        subtitulo,
        icono="📊",
        clave="TODOS",
        color_acento="#1E3A8A",
    ):
        # Determinar estado activo y color de fondo de la tarjeta
        es_activa = (self.filtro_metrica_activa == clave and clave != "TODOS")
        t = "oscuro" if self.modo_oscuro else "claro"
        cfg = self.PALETA[t]["kpis"][col]
        bg_tarjeta = cfg["active_bg"] if es_activa else cfg["bg"]

        card = tk.Frame(
            self.frame_kpis, bd=0, highlightthickness=1, cursor="hand2"
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        strip = tk.Frame(
            card,
            width=4,
            bg=color_acento,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        strip.pack(side="left", fill="y")

        content = tk.Frame(card, bd=0, highlightthickness=0, cursor="hand2")
        content.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        # Contenedor superior para el título e icono
        top_frame = tk.Frame(
            content, bg=bg_tarjeta, bd=0, highlightthickness=0, cursor="hand2"
        )
        top_frame.pack(fill="x")

        # Indicador tipo punto activo (Dot)
        lbl_check = tk.Label(
            top_frame,
            text="● " if es_activa else "",
            font=("Segoe UI", 9, "bold"),
            fg=color_acento,
            bg=bg_tarjeta,
            cursor="hand2",
        )
        lbl_check.pack(side="left", padx=(0, 2))

        lbl_tit = tk.Label(
            top_frame,
            text=titulo,
            font=("Segoe UI", 8, "bold"),
            fg=color_acento,
            bg=bg_tarjeta,
            anchor="w",
            cursor="hand2",
        )
        lbl_tit.pack(side="left", fill="x", expand=True)

        # Línea divisoria horizontal limpia
        linea_div = tk.Frame(
            content,
            height=2,
            bg=color_acento,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        linea_div.pack(fill="x", pady=(2, 6))

        body_frame = tk.Frame(content, bd=0, highlightthickness=0, cursor="hand2")
        body_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(
            body_frame, bd=0, highlightthickness=0, cursor="hand2"
        )
        left_col.pack(side="left", fill="both", expand=True)

        lbl_val = tk.Label(
            left_col,
            text=valor_inicial,
            font=("Segoe UI", 18, "bold"),
            anchor="w",
            cursor="hand2",
        )
        lbl_val.pack(fill="x")

        lbl_sub = tk.Label(
            left_col,
            text=subtitulo,
            font=("Segoe UI", 8),
            fg=color_acento,
            anchor="w",
            cursor="hand2",
        )
        lbl_sub.pack(fill="x")

        right_col = tk.Frame(
            body_frame, width=35, bd=0, highlightthickness=0, cursor="hand2"
        )
        right_col.pack_propagate(False)
        right_col.pack(side="right", fill="y")

        lbl_icon = tk.Label(
            right_col,
            text=icono,
            font=("Segoe UI", 16),
            fg=color_acento,
            anchor="e",
            cursor="hand2",
        )
        lbl_icon.pack(expand=True, fill="both")

        elementos_clic = [
            card,
            strip,
            content,
            top_frame,
            lbl_check,
            lbl_tit,
            linea_div,
            body_frame,
            left_col,
            lbl_val,
            lbl_sub,
            right_col,
            lbl_icon,
        ]
        for elem in elementos_clic:
            elem.bind(
                "<Button-1>", lambda event, c=clave: self.filtrar_por_metrica(c)
            )

        self.tarjetas_widgets.append({
            "card": card,
            "strip": strip,
            "content": content,
            "top_frame": top_frame,
            "linea": linea_div,
            "head": body_frame,
            "left_col": left_col,
            "right_col": right_col,
            "check": lbl_check,
            "tit": lbl_tit,
            "icon": lbl_icon,
            "val": lbl_val,
            "sub": lbl_sub,
            "acento": color_acento,
            "clave": clave,
            "titulo_original": titulo,
        })
        return lbl_val

    def validar_entrada_fecha(self, P, S):
        """
        P: Texto que resultaría si se acepta la modificación.
        S: Carácter/texto insertado.
        """
        if P == "":
            return True

        # Permitir solo números y la barra '/'
        if not all(c.isdigit() or c == "/" for c in S):
            return False

        # Formato completo DD/MM/AAAA no excede los 10 caracteres
        if len(P) > 10:
            return False

        return True

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

    # --- VENTANA EMERGENTE PARA MOSTRAR EQUIPOS DESINCORPORADOS ---
    def mostrar_ventana_desincorporados(self):
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        ventana_bajas = tk.Toplevel(self.root)
        ventana_bajas.title("SIGAR - Historial de Activos Desincorporados")
        ventana_bajas.geometry("800x420")
        ventana_bajas.configure(bg=pal["bg_root"])
        ventana_bajas.transient(self.root)
        ventana_bajas.grab_set()

        ventana_bajas.update_idletasks()
        w = ventana_bajas.winfo_width()
        h = ventana_bajas.winfo_height()
        x = (ventana_bajas.winfo_screenwidth() // 2) - (w // 2)
        y = (ventana_bajas.winfo_screenheight() // 2) - (h // 2)
        ventana_bajas.geometry(f"{w}x{h}+{x}+{y}")

        lbl_titulo = tk.Label(
            ventana_bajas,
            text="❌ REGISTRO DE ACTAS DE DESINCORPORACIÓN Y BAJA",
            font=("Segoe UI", 11, "bold"),
            fg="#dc2626",
            bg=pal["bg_root"],
            pady=10,
        )
        lbl_titulo.pack()

        frame_tabla_bajas = tk.Frame(ventana_bajas, bg=pal["bg_root"])
        frame_tabla_bajas.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        cols = ("id", "nombre", "asignado_a", "fecha_baja", "motivo")
        tabla_bajas = ttk.Treeview(
            frame_tabla_bajas, columns=cols, show="headings"
        )

        tabla_bajas.heading("id", text="ID Activo")
        tabla_bajas.heading("nombre", text="Descripción / Bien")
        tabla_bajas.heading("asignado_a", text="Asignación Previa")
        tabla_bajas.heading("fecha_baja", text="Fecha Procesamiento")
        tabla_bajas.heading("motivo", text="Motivo / Justificación")

        tabla_bajas.column("id", width=70, anchor="center")
        tabla_bajas.column("nombre", width=200, anchor="w")
        tabla_bajas.column("asignado_a", width=140, anchor="w")
        tabla_bajas.column("fecha_baja", width=130, anchor="center")
        tabla_bajas.column("motivo", width=220, anchor="w")

        scroll_bajas = ttk.Scrollbar(
            frame_tabla_bajas, orient="vertical", command=tabla_bajas.yview
        )
        tabla_bajas.configure(yscrollcommand=scroll_bajas.set)

        tabla_bajas.pack(side="left", fill="both", expand=True)
        scroll_bajas.pack(side="right", fill="y")

        lista_bajas = cargar_historial_bajas()
        for i, reg in enumerate(lista_bajas):
            tag_fila = "par" if i % 2 == 0 else "impar"
            tabla_bajas.insert(
                "",
                "end",
                values=(
                    reg.get("id", "N/A"),
                    reg.get("nombre", "N/A"),
                    reg.get("asignado_a", "N/A"),
                    reg.get("fecha_baja", "N/A"),
                    reg.get("motivo_baja", "Sin justificación"),
                ),
                tags=(tag_fila,),
            )

        if not lista_bajas:
            lbl_vacio = tk.Label(
                ventana_bajas,
                text="No hay actas de desincorporación registradas.",
                font=("Segoe UI", 9, "italic"),
                fg=pal["fg_subtexto"],
                bg=pal["bg_root"],
            )
            lbl_vacio.pack(pady=10)

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

        self.lbl_val_total.config(text=str(total))
        self.lbl_val_operativos.config(text=str(operativos))
        self.lbl_val_preventivos.config(text=str(preventivos))
        self.lbl_val_correctivos.config(text=str(correctivos))
        self.lbl_val_desincorporados.config(text=str(desincorporados))

    # --- FORMULARIO ---
    def crear_formulario(self):
        self.frame_form = tk.LabelFrame(
            self.root,
            text=" Registrar Activo y Gestión de Mantenimiento ",
            font=("Segoe UI", 9, "bold"),
            bd=1,
            relief="solid",
        )
        self.frame_form.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        self.frame_form.columnconfigure(1, weight=1)
        self.frame_form.columnconfigure(3, weight=2)
        self.frame_form.columnconfigure(5, weight=1)

        self.frames_form_internos = []

        lbl1 = tk.Label(
            self.frame_form, text="ID único:", font=("Segoe UI", 8, "bold")
        )
        lbl1.grid(row=0, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_id = tk.Entry(
            self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1
        )
        self.entry_id.grid(row=0, column=1, padx=5, pady=4, ipady=3, sticky="ew")

        lbl2 = tk.Label(
            self.frame_form, text="Asignado a:", font=("Segoe UI", 8, "bold")
        )
        lbl2.grid(row=0, column=2, padx=(10, 5), pady=4, sticky="e")

        opciones_asignacion = [
            "Departamento de Sistemas",
            "Administración",
            "Laboratorio 1",
            "Rectorado",
        ]
        self.combo_asignado = ttk.Combobox(
            self.frame_form,
            values=opciones_asignacion,
            font=("Segoe UI", 9),
            state="readonly",
            style="TCombobox",
        )
        self.combo_asignado.grid(
            row=0, column=3, columnspan=3, padx=5, pady=4, sticky="ew"
        )
        if opciones_asignacion:
            self.combo_asignado.current(0)

        frame_btn_form = tk.Frame(self.frame_form)
        frame_btn_form.grid(
            row=0, column=6, rowspan=4, padx=(12, 8), pady=4, sticky="ns"
        )
        self.frames_form_internos.append(frame_btn_form)

        tk.Button(
            frame_btn_form,
            text="Registrar Nuevo",
            bg="#0284C7",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            command=self.agregar_bien,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(fill="x", pady=2)
        tk.Button(
            frame_btn_form,
            text="Guardar Cambios",
            bg="#059669",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            command=self.actualizar_bien,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(fill="x", pady=2)
        tk.Button(
            frame_btn_form,
            text="Limpiar Campos",
            bg="#475569",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            command=self.limpiar_formulario,
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
        ).pack(fill="x", pady=2)

        lbl3 = tk.Label(
            self.frame_form,
            text="Descripción / Nombre:",
            font=("Segoe UI", 8, "bold"),
        )
        lbl3.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_nombre = tk.Entry(
            self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1
        )
        self.entry_nombre.grid(
            row=1, column=1, columnspan=5, padx=5, pady=4, ipady=3, sticky="ew"
        )

        lbl4 = tk.Label(
            self.frame_form,
            text="¿Mantenimiento?:",
            font=("Segoe UI", 8, "bold"),
        )
        lbl4.grid(row=2, column=0, padx=(10, 5), pady=4, sticky="e")
        self.combo_mant = ttk.Combobox(
            self.frame_form,
            values=["No", "Sí (Preventivo)", "Sí (Correctivo)"],
            font=("Segoe UI", 9),
            width=15,
            state="readonly",
        )
        self.combo_mant.current(0)
        self.combo_mant.grid(row=2, column=1, padx=5, pady=4, sticky="w")

        lbl5 = tk.Label(
            self.frame_form,
            text="Fecha (DD/MM/AAAA):",
            font=("Segoe UI", 8, "bold"),
        )
        lbl5.grid(row=2, column=2, padx=(10, 5), pady=4, sticky="e")
        # Registrar el comando de validación nativo de Tkinter
        vcmd_fecha = (self.root.register(self.validar_entrada_fecha), "%P", "%S")

        self.entry_fecha_mant = tk.Entry(
            self.frame_form,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
            validate="key",             # Validar en cada pulsación de tecla
            validatecommand=vcmd_fecha,  # Bloquea letras ANTES de renderizarlas
        )
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha_mant.grid(row=2, column=3, padx=5, pady=4, ipady=3, sticky="ew")

        # Mantenemos el auto-formato con las barras al soltar la tecla
        self.entry_fecha_mant.bind("<KeyRelease>", self.formatear_y_validar_fecha)

        lbl6 = tk.Label(
            self.frame_form,
            text="Próximo (Hábil +3M):",
            font=("Segoe UI", 8, "bold"),
        )
        lbl6.grid(row=2, column=4, padx=(10, 5), pady=4, sticky="e")
        self.entry_proximo = tk.Entry( 
            self.frame_form, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, state="readonly"
        )
        self.entry_proximo.grid(row=2, column=5, padx=5, pady=4, ipady=3, sticky="ew")

        lbl7 = tk.Label(
            self.frame_form,
            text="Detalle / Observación:",
            font=("Segoe UI", 8, "bold"),
        )
        lbl7.grid(row=3, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_desc_mant = tk.Entry(
            self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1
        )
        self.entry_desc_mant.grid(
            row=3, column=1, columnspan=5, padx=5, pady=4, ipady=3, sticky="ew"
        )

        self.labels_texto.extend([lbl1, lbl2, lbl3, lbl4, lbl5, lbl6, lbl7])
        self.entries_widgets.extend([
            self.entry_id,
            self.entry_nombre,
            self.entry_fecha_mant,
            self.entry_desc_mant,
        ])

    # --- BÚSQUEDA ---
    def crear_panel_busqueda(self):
        self.frame_busqueda = tk.Frame(
            self.root, bg=self.PALETA["claro"]["bg_root"]
        )
        self.frame_busqueda.grid(
            row=3, column=0, sticky="ew", padx=15, pady=(4, 2)
        )

        self.lbl_icon_buscar = tk.Label(
            self.frame_busqueda,
            text="🔍 Buscar Activo:",
            font=("Segoe UI", 8, "bold"),
        )
        self.lbl_icon_buscar.pack(side="left", padx=(0, 5))

        self.entry_buscar = tk.Entry(
            self.frame_busqueda,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
            width=22,
        )
        self.entry_buscar.pack(side="left", padx=5, ipady=3)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        self.entries_widgets.append(self.entry_buscar)

        tk.Button(
            self.frame_busqueda,
            text="Limpiar Filtro",
            bg="#002B49",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            command=self.limpiar_filtro_busqueda,
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
        ).pack(side="left", padx=5)

        self.lbl_indicador_busqueda = tk.Label(
            self.frame_busqueda,
            text="(Doble clic para editar / Clic derecho para opciones)",
            font=("Segoe UI", 8, "bold"),
        )
        self.lbl_indicador_busqueda.pack(side="right")

    # --- TABLA DE DATOS Y MENÚ CONTEXTUAL ---
    def crear_tabla(self):
        self.frame_tabla = tk.Frame(
            self.root, bg=self.PALETA["claro"]["bg_root"]
        )
        self.frame_tabla.grid(row=4, column=0, sticky="nsew", padx=15, pady=4)
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

        self.tabla.column(
            "id", width=70, minwidth=50, anchor="center", stretch=False
        )
        self.tabla.column(
            "nombre", width=220, minwidth=150, anchor="w", stretch=True
        )
        self.tabla.column(
            "asignado_a", width=140, minwidth=120, anchor="w", stretch=True
        )
        self.tabla.column(
            "mantenimiento",
            width=115,
            minwidth=90,
            anchor="center",
            stretch=False,
        )
        self.tabla.column(
            "fecha_mant",
            width=100,
            minwidth=85,
            anchor="center",
            stretch=False,
        )
        self.tabla.column(
            "proximo_mant",
            width=145,
            minwidth=135,
            anchor="center",
            stretch=False,
        )

        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        self.tabla.bind("<Button-3>", self.mostrar_menu_contextual)
        self.tabla.bind("<Button-2>", self.mostrar_menu_contextual)

        scrollbar = ttk.Scrollbar(
            self.frame_tabla, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

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
        self.frame_acciones = tk.Frame(
            self.root, bg=self.PALETA["claro"]["bg_root"]
        )
        self.frame_acciones.grid(
            row=5, column=0, sticky="ew", padx=15, pady=(2, 8)
        )

        separador = ttk.Separator(self.frame_acciones, orient="horizontal")
        separador.pack(fill="x", pady=(0, 6))

        # Asignación a self.btn_centro_respaldos para control de estilo dinámico
        self.btn_centro_respaldos = tk.Button(
            self.frame_acciones,
            text="☁️ Centro de Respaldos",
            font=("Segoe UI", 8, "bold"),
            command=self.abrir_ventana_respaldos,
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            relief="flat",
        )
        self.btn_centro_respaldos.pack(side="left")

        self.lbl_info_pie = tk.Label(
            self.frame_acciones,
            text="SIGAR V2.5 — UNELLEZ",
            font=("Segoe UI", 8, "bold"),
        )
        self.lbl_info_pie.pack(side="right", pady=3)

    # --- VENTANA EMERGENTE DE RESPALDOS ---
    def abrir_ventana_respaldos(self):
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        modal = tk.Toplevel(self.root)
        modal.title("Gestión y Centro de Respaldos")
        modal.geometry("420x280")
        modal.resizable(False, False)
        modal.configure(bg=pal["bg_root"])
        modal.transient(self.root)
        modal.grab_set()

        modal.update_idletasks()
        w = modal.winfo_width()
        h = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (w // 2)
        y = (modal.winfo_screenheight() // 2) - (h // 2)
        modal.geometry(f"{w}x{h}+{x}+{y}")

        lbl_titulo = tk.Label(
            modal,
            text="☁️ Sincronización y Respaldos",
            font=("Segoe UI", 12, "bold"),
            fg=pal["fg_texto"],
            bg=pal["bg_root"],
        )
        lbl_titulo.pack(pady=(15, 5))

        lbl_sub = tk.Label(
            modal,
            text="Seleccione la acción de respaldo que desea ejecutar:",
            font=("Segoe UI", 8),
            fg=pal["fg_subtexto"],
            bg=pal["bg_root"],
        )
        lbl_sub.pack(pady=(0, 15))

        frame_botones = tk.Frame(modal, bg=pal["bg_root"])
        frame_botones.pack(fill="both", expand=True, padx=25, pady=5)

        btn_nube = tk.Button(
            frame_botones,
            text="☁️ Exportar / Guardar Respaldo en la Nube",
            bg="#0284C7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: self.accion_guardar_nube(modal),
        )
        btn_nube.pack(fill="x", pady=4)

        btn_importar = tk.Button(
            frame_botones,
            text="📥 Importar / Restaurar desde la Nube",
            bg="#0D9488",
            fg="white",
            activebackground="#0F766E",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: self.accion_importar_nube(modal),
        )
        btn_importar.pack(fill="x", pady=4)

        btn_local = tk.Button(
            frame_botones,
            text="💾 Guardar Respaldo Local (Copiar JSON)",
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: self.accion_guardar_local(modal),
        )
        btn_local.pack(fill="x", pady=4)

    # --- ACCIONES FRONTEND DE RESPALDO ---
    def accion_guardar_nube(self, modal):
        if not HAS_REQUESTS:
            messagebox.showinfo(
                "Librería Pendiente",
                "Se requiere la librería 'requests' instalada para enviar datos"
                " a la API.",
                parent=modal,
            )
            return

        exportar_respaldo_nube_bd(parent_window=modal)
        messagebox.showinfo(
            "Conexión Backend",
            "Frontend preparado para enviar datos al servidor"
            f" API:\n\nEndpoint: {URL_RESPALDO_CLOUD}\n\nEstructura JSON lista.",
            parent=modal,
        )

    def accion_importar_nube(self, modal):
        if not HAS_REQUESTS:
            messagebox.showinfo(
                "Librería Pendiente",
                "Se requiere la librería 'requests' instalada para recibir"
                " datos de la API.",
                parent=modal,
            )
            return

        messagebox.showinfo(
            "Conexión Backend",
            "Frontend preparado para consultar e importar datos desde la"
            f" API:\n\nEndpoint: {URL_RESPALDO_CLOUD}",
            parent=modal,
        )

    def accion_guardar_local(self, modal):
        try:
            filename = filedialog.asksaveasfilename(
                parent=modal,
                title="Guardar Respaldo Local",
                defaultextension=".json",
                filetypes=[
                    ("Archivos JSON", "*.json"),
                    ("Todos los archivos", "*.*"),
                ],
                initialfile=(
                    f"respaldo_sigar_{date.today().strftime('%Y%m%d')}.json"
                ),
            )
            if filename:
                import json

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.bienes, f, ensure_ascii=False, indent=4)
                messagebox.showinfo(
                    "Respaldo Guardado",
                    "El respaldo local ha sido guardado exitosamente"
                    f" en:\n{filename}",
                    parent=modal,
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo guardar el respaldo local: {e}",
                parent=modal,
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
            messagebox.showwarning(
                "Tipo Incorrecto", "El ID debe ser numérico."
            )
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

        index = next(
            (i for i, b in enumerate(self.bienes) if b["id"] == id_int), None
        )
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
                f"Los datos del activo ID {id_int} han sido modificados"
                " localmente.",
            )

    def dar_de_baja_bien(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, seleccione un elemento de la tabla para darlo de"
                " baja.",
            )
            return

        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])
        nombre_bien = item["values"][1]

        motivo = simpledialog.askstring(
            "Justificación de Baja",
            f"Indique el motivo por el cual se da de baja el activo ID"
            f" {id_bien}:\n({nombre_bien})",
            parent=self.root,
        )
        if not motivo or not motivo.strip():
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Desincorporación",
            f"¿Está seguro de desincorporar el activo ID {id_bien}?\n\nMotivo:"
            f" {motivo.strip()}",
        )
        if confirmacion:
            bien_objetivo = next(
                (b for b in self.bienes if b["id"] == id_bien), None
            )
            fecha_hora_baja = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            registro_baja = {
                "id": id_bien,
                "nombre": nombre_bien,
                "asignado_a": (
                    bien_objetivo.get("asignado_a", "N/A")
                    if bien_objetivo
                    else "N/A"
                ),
                "mantenimiento": (
                    bien_objetivo.get("mantenimiento", "N/A")
                    if bien_objetivo
                    else "N/A"
                ),
                "fecha_ultimo_mant": (
                    bien_objetivo.get("fecha_mant", "N/A")
                    if bien_objetivo
                    else "N/A"
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
                f"El activo ID {id_bien} ha sido desincorporado.\n📄 Documento:"
                f" {archivo_generado}",
            )

    # --- FILTRADO Y NAVEGACIÓN ---
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
        self.combo_mant.current(0)
        self.calcular_proxima_fecha_mantenimiento()
        self.entry_id.focus_force()

    def al_cambiar_fecha(self, event=None):
        self.calcular_proxima_fecha_mantenimiento()

    def formatear_y_validar_fecha(self, event=None):
        # Ignorar teclas de navegación y borrado
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

        # Si ya tiene la longitud final completa, no formateamos más
        if len(texto_actual) == 10 and texto_actual.count("/") == 2:
            self.calcular_proxima_fecha_mantenimiento()
            return

        # Dividimos por las barras que haya escrito el usuario
        partes = texto_actual.split("/")
        
        # Limpiamos cada parte dejando solo números
        dia = "".join(c for c in partes[0] if c.isdigit())[:2]
        mes = "".join(c for c in partes[1] if c.isdigit())[:2] if len(partes) > 1 else ""
        anio = "".join(c for c in partes[2] if c.isdigit())[:4] if len(partes) > 2 else ""

        # Reconstruimos la fecha según el flujo de escritura
        fecha_formateada = dia

        # AUTO-COMPLETAR o MANTENER BARRA 1
        # Si el día tiene 2 dígitos o si el usuario escribió la primera barra
        if len(dia) == 2 or len(partes) > 1:
            fecha_formateada += "/" + mes

        # AUTO-COMPLETAR o MANTENER BARRA 2
        # Si el mes tiene 2 dígitos o si el usuario escribió la segunda barra
        if len(mes) == 2 or len(partes) > 2:
            fecha_formateada += "/" + anio

        # Evitamos reescritura innecesaria si el texto ya coincide
        if texto_actual != fecha_formateada:
            pos_cursor = self.entry_fecha_mant.index(tk.INSERT)
            self.entry_fecha_mant.delete(0, tk.END)
            self.entry_fecha_mant.insert(0, fecha_formateada)

            # Reajuste inteligente de posición del cursor
            diferencia = len(fecha_formateada) - len(texto_actual)
            nueva_pos = pos_cursor + diferencia
            self.entry_fecha_mant.icursor(max(0, nueva_pos))

        self.calcular_proxima_fecha_mantenimiento()

    def calcular_proxima_fecha_mantenimiento(self):
        fecha_str = self.entry_fecha_mant.get().strip()
        t = "oscuro" if self.modo_oscuro else "claro"
        
        # Colores de estado normal (del tema actual)
        bg_normal = self.PALETA[t]["bg_root"]
        fg_normal = self.PALETA[t]["fg_texto"]
        
        # Colores de estado de error (Fondo y Texto según el tema)
        if self.modo_oscuro:
            bg_error = "#f9cece"  # Fondo rojo vino oscuro
            fg_error = "#dc2626"  # Texto salmón/rojo claro
        else:
            bg_error = "#f9cece"  # Fondo rosa/rojo muy claro
            fg_error = "#dc2626"  # Texto rojo oscuro intenso

        # Habilitar temporalmente la edición para actualizar el contenido
        self.entry_proximo.config(state="normal")

        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(fecha_str, fmt).date()
                proxima_str = calcular_fecha_habil_3_meses(dt)
                
                # Restaurar colores normales cuando la fecha sea válida
                self.entry_proximo.config(bg=bg_normal, fg=fg_normal, readonlybackground=bg_normal)
                self.entry_proximo.delete(0, tk.END)
                self.entry_proximo.insert(0, proxima_str)
                self.entry_proximo.config(state="readonly")
                return proxima_str
            except ValueError:
                pass

        # Si el formato es inválido, aplicar colores de alerta y bloquear
        self.entry_proximo.config(bg=bg_error, fg=fg_error, readonlybackground=bg_error)
        self.entry_proximo.delete(0, tk.END)
        self.entry_proximo.insert(0, "Formato Inválido")
        self.entry_proximo.config(state="readonly")
        return None

    def actualizar_tabla(self):
        self.filtrar_tabla()


os.chdir(obtener_ruta_base())

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()