# -*- coding: utf-8 -*-
"""
SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos
Módulo Principal de Interfaz Gráfica Tkinter con soporte para Activos Compuestos y Periféricos.
Compatible con Python 3.8.10+
"""
import os
import sys
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Registrar la subcarpeta en sys.path para importar styles, utils y database
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
if DIR_ACTUAL not in sys.path:
    sys.path.insert(0, DIR_ACTUAL)

from styles import (
    PALETA, FONT_LABEL, FONT_BOLD, FONT_KPI_VAL, FONT_KPI_TIT,
    cargar_preferencia_tema, guardar_preferencia_tema, hex_a_rgb, rgb_a_hex
)
from utils import (
    HAS_PIL, HAS_REQUESTS, calcular_fecha_habil_3_meses, generar_acta_baja, es_activo_compuesto
)
if HAS_PIL:
    from PIL import Image, ImageTk

from database import (
    ARCHIVO_BAJAS, URL_RESPALDO_CLOUD, cargar_datos_locales,
    guardar_datos_locales, guardar_baja_local, obtener_conteo_bajas,
    exportar_respaldo_nube_bd
)

# Definición dinámica de imágenes institucionales
ARCHIVO_LOGO = os.path.join(DIR_ACTUAL, "UNELLEZ LOGO.png")
PATH_LEMA = os.path.join(DIR_ACTUAL, "lema_unellez_oro.png")


class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos")
        self.root.geometry("1060x720")
        self.root.minsize(820, 560)

        self.modo_actual = cargar_preferencia_tema()
        self.modo_oscuro = (self.modo_actual == "oscuro")
        self.filtro_metrica_activa = "TODOS"
        
        # Estados para el subformulario dinámico de componentes y periféricos
        self.subform_desplegado = False
        self.subform_manual_toggle = False

        try:
            self.root.state('zoomed')
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
        self.frames_form_internos = []

        # Construcción GUI
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
        self.crear_menu_contextual()
        self.crear_panel_acciones()
        
        # Aplicar tema visual inicial
        self.aplicar_tema_widgets()

        # Cargar datos locales iniciales
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
                    img_pil = Image.open(ARCHIVO_LOGO).resize((34, 34), Image.Resampling.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(img_pil)
                else:
                    raw_img = tk.PhotoImage(file=ARCHIVO_LOGO)
                    w_factor = max(1, raw_img.width() // 34)
                    h_factor = max(1, raw_img.height() // 34)
                    self.logo_img = raw_img.subsample(w_factor, h_factor)
            except Exception:
                self.logo_img = None

        if self.logo_img:
            lbl_logo = tk.Label(frame_logo_titulo, image=self.logo_img, bg="#002B49")
            lbl_logo.pack(side="left", padx=(0, 8))

        lbl_unellez = tk.Label(
            frame_logo_titulo, text="UNELLEZ", font=("Segoe UI", 13, "bold"), fg="#FF6600", bg="#002B49"
        )
        lbl_unellez.pack(side="left")

        lbl_separador = tk.Label(
            frame_logo_titulo, text="|", font=("Segoe UI", 12, "bold"), fg="#475569", bg="#002B49"
        )
        lbl_separador.pack(side="left", padx=(10, 10))

        if os.path.exists(PATH_LEMA):
            try:
                img_lema_pil = Image.open(PATH_LEMA).convert("RGBA")
                pixels = list(img_lema_pil.getdata())
                new_data = [
                    (255, 255, 255, 0) if item[0] > 230 and item[1] > 230 and item[2] > 230 else item
                    for item in pixels
                ]
                img_lema_pil.putdata(new_data)
                bbox = img_lema_pil.getbbox()
                if bbox:
                    img_lema_pil = img_lema_pil.crop(bbox)

                target_height = 18
                aspect_ratio = img_lema_pil.width / img_lema_pil.height
                target_width = int(target_height * aspect_ratio)

                img_lema_pil = img_lema_pil.resize((target_width, target_height), Image.Resampling.LANCZOS)
                self.img_lema_oro = ImageTk.PhotoImage(img_lema_pil)
                lbl_lema = tk.Label(frame_logo_titulo, image=self.img_lema_oro, bg="#002B49", bd=0)
                lbl_lema.pack(side="left")
            except Exception as e:
                print(f"Error cargando lema: {e}")

        self.btn_modo_oscuro = tk.Button(
            self.frame_cintillo, text="🌙 Cuidado de Vista", font=("Segoe UI", 8, "bold"),
            bg="#1e293b", fg="#f8fafc", activebackground="#334155", activeforeground="#ffffff",
            bd=0, padx=8, pady=2, cursor="hand2", command=self.toggle_modo_oscuro_animado
        )
        self.btn_modo_oscuro.pack(side="right", padx=12, pady=8)

    # --- TEMA MODO OSCURO / CLARO ---
    def toggle_modo_oscuro_animado(self):
        color_inicio = self.PALETA["oscuro" if self.modo_oscuro else "claro"]["bg_root"]
        self.modo_oscuro = not self.modo_oscuro
        self.modo_actual = "oscuro" if self.modo_oscuro else "claro"
        color_fin = self.PALETA["oscuro" if self.modo_oscuro else "claro"]["bg_root"]

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
            if hasattr(self, 'frame_busqueda'):
                self.frame_busqueda.configure(bg=color_interp)
            self.frame_tabla.configure(bg=color_interp)
            self.frame_acciones.configure(bg=color_interp)
            self.root.after(18, lambda: self.animar_transicion_bg(rgb_inicio, rgb_fin, paso + 1, total_pasos))
        else:
            self.aplicar_tema_widgets()

    def aplicar_tema_widgets(self):
        self.modo_oscuro = (self.modo_actual == "oscuro")
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]
        guardar_preferencia_tema(self.modo_actual)

        self.root.config(bg=pal["bg_root"])
        if hasattr(self, 'frame_kpis'): self.frame_kpis.config(bg=pal["bg_root"])
        if hasattr(self, 'frame_busqueda'): self.frame_busqueda.config(bg=pal["bg_root"])
        if hasattr(self, 'frame_tabla'): self.frame_tabla.config(bg=pal["bg_root"])
        if hasattr(self, 'frame_acciones'): self.frame_acciones.config(bg=pal["bg_root"])

        if hasattr(self, 'btn_modo_oscuro'):
            if self.modo_oscuro:
                self.btn_modo_oscuro.config(text="☀️ Modo Claro", bg="#f59e0b", fg="#0f172a", activebackground="#fbbf24")
            else:
                self.btn_modo_oscuro.config(text="🌙 Cuidado de Vista", bg="#1e293b", fg="#f8fafc", activebackground="#334155")

        fg_texto_modo = pal["fg_texto"]
        bg_panel_modo = pal["bg_panel"]

        if hasattr(self, 'frame_form'):
            self.frame_form.config(
                bg=bg_panel_modo, fg=fg_texto_modo, bd=0, highlightthickness=1,
                highlightbackground=pal["border_panel"], highlightcolor=pal["border_panel"]
            )
            
        if hasattr(self, 'frame_subform_container'):
            self.frame_subform_container.config(
                bg=bg_panel_modo, highlightbackground=pal["border_panel"]
            )
            if hasattr(self, 'frame_sub_header'):
                self.frame_sub_header.config(bg=bg_panel_modo)
            if hasattr(self, 'lbl_titulo_sub'):
                self.lbl_titulo_sub.config(bg=bg_panel_modo, fg="#38bdf8" if self.modo_oscuro else "#0284c7")
            if hasattr(self, 'lbl_sub_hint'):
                self.lbl_sub_hint.config(bg=bg_panel_modo, fg=pal["fg_subtexto"])
            if hasattr(self, 'grid_perif'):
                self.grid_perif.config(bg=bg_panel_modo)

        if hasattr(self, 'perifericos_widgets'):
            sub_card_bg = "#15203b" if self.modo_oscuro else "#f8fafc"
            for clave, p_data in self.perifericos_widgets.items():
                p_data["card"].config(
                    bg=sub_card_bg, fg="#38bdf8" if self.modo_oscuro else "#0369a1",
                    highlightbackground=pal["border_panel"]
                )
                p_data["lbl_estado"].config(bg=sub_card_bg, fg=fg_texto_modo)
                p_data["lbl_detalle"].config(bg=sub_card_bg, fg=fg_texto_modo)

        for lbl in getattr(self, 'labels_texto', []):
            try:
                lbl.config(bg=bg_panel_modo, fg=fg_texto_modo, font=FONT_LABEL)
            except Exception:
                pass
            
        for f in getattr(self, 'frames_form_internos', []):
            try:
                f.config(bg=bg_panel_modo)
            except Exception:
                pass

        for entry in getattr(self, 'entries_widgets', []):
            try:
                entry.config(
                    bg=pal["entry_bg"], fg=pal["entry_fg"], insertbackground=pal["entry_fg"],
                    highlightbackground=pal["entry_border"], highlightthickness=1, font=FONT_LABEL, bd=0
                )
            except Exception:
                pass

        self.style.theme_use("default")
        self.style.configure(
            "TCombobox", fieldbackground=pal["entry_bg"], background=pal["entry_bg"],
            foreground=pal["entry_fg"], darkcolor=pal["entry_bg"], lightcolor=pal["entry_bg"],
            selectbackground=pal["entry_bg"], selectforeground=pal["entry_fg"], arrowcolor=fg_texto_modo, font=FONT_LABEL
        )
        self.style.map("TCombobox", fieldbackground=[("readonly", pal["entry_bg"])], foreground=[("readonly", pal["entry_fg"])])

        if hasattr(self, 'entry_proximo'):
            self.entry_proximo.config(bg=pal["bg_root"], fg=pal["fg_texto"], font=FONT_BOLD)
        if hasattr(self, 'lbl_info_pie'):
            self.lbl_info_pie.config(bg=pal["bg_root"], fg=pal["fg_subtexto"], font=FONT_LABEL)
        if hasattr(self, 'lbl_indicador_busqueda'):
            self.lbl_indicador_busqueda.config(bg=pal["bg_root"], fg=pal["fg_subtexto"], font=FONT_LABEL)
        if hasattr(self, 'lbl_icon_buscar'):
            self.lbl_icon_buscar.config(bg=pal["bg_root"], fg=pal["fg_texto"], font=FONT_LABEL)

        self.actualizar_estilo_tarjetas_kpi()

        if hasattr(self, 'tabla'):
            tree_bg_even = pal["tree_bg"] if not self.modo_oscuro else "#1e293b"
            tree_bg_odd = pal["bg_root"] if not self.modo_oscuro else "#0f172a"

            self.style.configure(
                "Treeview", background=tree_bg_even, foreground=pal["tree_fg"],
                fieldbackground=tree_bg_even, font=("Segoe UI", 9), rowheight=30, borderwidth=0
            )
            self.style.map("Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])
            self.style.configure(
                "Treeview.Heading", background=pal["tree_head_bg"], foreground=pal["tree_head_fg"],
                font=("Segoe UI", 9, "bold"), relief="flat", borderwidth=1
            )
            self.style.map("Treeview.Heading", background=[("active", pal["tree_head_bg"])], foreground=[("active", pal["tree_head_fg"])])

            self.tabla.tag_configure("par", background=tree_bg_even, foreground=pal["tree_fg"])
            self.tabla.tag_configure("impar", background=tree_bg_odd, foreground=pal["tree_fg"])

    def actualizar_estilo_tarjetas_kpi(self):
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        for i, card_info in enumerate(getattr(self, 'tarjetas_widgets', [])):
            cfg = pal["kpis"][i]
            clave_kpi = card_info["clave"]
            titulo_base = card_info["titulo_original"]
            color_acento = cfg["text"]

            esta_activa = (self.filtro_metrica_activa == clave_kpi and clave_kpi != "TODOS")

            bg_tarjeta = cfg["active_bg"] if esta_activa else cfg["bg"]
            borde_color = cfg["active_border"] if esta_activa else cfg["border"]
            
            grosor_borde = 3 if esta_activa else 1
            padx_comp = 6 if esta_activa else 8
            pady_comp = 4 if esta_activa else 6

            texto_titulo = f"✓ {titulo_base}" if esta_activa else titulo_base

            card_info["card"].config(
                bg=bg_tarjeta,
                highlightbackground=borde_color,
                highlightcolor=borde_color,
                highlightthickness=grosor_borde
            )
            card_info["strip"].config(bg=color_acento if not esta_activa else borde_color)
            card_info["content"].config(bg=bg_tarjeta, padx=padx_comp, pady=pady_comp)

            if "top_frame" in card_info: card_info["top_frame"].config(bg=bg_tarjeta)
            if "left_col" in card_info: card_info["left_col"].config(bg=bg_tarjeta)
            if "right_col" in card_info: card_info["right_col"].config(bg=bg_tarjeta)
            card_info["head"].config(bg=bg_tarjeta)

            if "linea" in card_info: card_info["linea"].config(bg=borde_color if esta_activa else color_acento)

            card_info["tit"].config(text=texto_titulo, bg=bg_tarjeta, fg=borde_color if esta_activa else color_acento, font=FONT_KPI_TIT)
            card_info["sub"].config(bg=bg_tarjeta, fg=cfg["sub"], font=FONT_LABEL)
            card_info["icon"].config(bg=bg_tarjeta, fg=borde_color if esta_activa else color_acento)
            card_info["val"].config(bg=bg_tarjeta, fg=cfg["val"], font=FONT_KPI_VAL)

    # --- TARJETAS MÉTRICAS ---
    def crear_panel_metricas(self):
        self.frame_kpis = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_kpis.grid(row=1, column=0, sticky="ew", padx=15, pady=(8, 2))

        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.tarjetas_widgets = []
        metricas = [
            ("TOTAL ACTIVOS", "0", "Bienes registrados", "📋", "TODOS"),
            ("OPERATIVOS", "0", "En servicio activo", "🟢", "OPERATIVOS"),
            ("PREVENTIVOS", "0", "Ciclo regular (+3M)", "🔧", "PREVENTIVOS"),
            ("CORRECTIVOS", "0", "Ajuste / Reparación", "⚠️", "CORRECTIVOS"),
            ("DESINCORPORADOS", "0", "Actas emitidas", "❌", "DESINCORPORADOS")
        ]

        for col, (titulo, valor, sub, icono, clave) in enumerate(metricas):
            val_widget = self.crear_tarjeta(col, titulo, valor, sub, icono, clave)
            if col == 0: self.lbl_val_total = val_widget
            elif col == 1: self.lbl_val_operativos = val_widget
            elif col == 2: self.lbl_val_preventivos = val_widget
            elif col == 3: self.lbl_val_correctivos = val_widget
            elif col == 4: self.lbl_val_desincorporados = val_widget

    def crear_tarjeta(self, col, titulo, valor_inicial, subtitulo, icono="📊", clave="TODOS", color_acento="#1E3A8A"):
        card = tk.Frame(self.frame_kpis, bd=0, highlightthickness=1, cursor="hand2")
        card.grid(row=0, column=col, sticky="nsew", padx=3)

        strip = tk.Frame(card, width=4, bg=color_acento, bd=0, highlightthickness=0, cursor="hand2")
        strip.pack(side="left", fill="y")

        content = tk.Frame(card, bd=0, highlightthickness=0, cursor="hand2")
        content.pack(side="left", fill="both", expand=True, padx=8, pady=5)

        top_frame = tk.Frame(content, bd=0, highlightthickness=0, cursor="hand2")
        top_frame.pack(fill="x")

        lbl_tit = tk.Label(top_frame, text=titulo, font=("Segoe UI", 8, "bold"), fg=color_acento, anchor="w", cursor="hand2")
        lbl_tit.pack(fill="x")

        linea_div = tk.Frame(top_frame, height=2, bg=color_acento, bd=0, highlightthickness=0, cursor="hand2")
        linea_div.pack(fill="x", pady=(2, 4))

        body_frame = tk.Frame(content, bd=0, highlightthickness=0, cursor="hand2")
        body_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(body_frame, bd=0, highlightthickness=0, cursor="hand2")
        left_col.pack(side="left", fill="both", expand=True)

        lbl_val = tk.Label(left_col, text=valor_inicial, font=("Segoe UI", 16, "bold"), anchor="w", cursor="hand2")
        lbl_val.pack(fill="x")

        lbl_sub = tk.Label(left_col, text=subtitulo, font=("Segoe UI", 7), fg=color_acento, anchor="w", cursor="hand2")
        lbl_sub.pack(fill="x")

        right_col = tk.Frame(body_frame, width=30, bd=0, highlightthickness=0, cursor="hand2")
        right_col.pack_propagate(False)
        right_col.pack(side="right", fill="y")

        lbl_icon = tk.Label(right_col, text=icono, font=("Segoe UI", 14), fg=color_acento, anchor="e", cursor="hand2")
        lbl_icon.pack(expand=True, fill="both")

        elementos_clic = [card, strip, content, top_frame, lbl_tit, linea_div, body_frame, left_col, lbl_val, lbl_sub, right_col, lbl_icon]
        for elem in elementos_clic:
            elem.bind("<Button-1>", lambda event, c=clave: self.filtrar_por_metrica(c))

        self.tarjetas_widgets.append({
            "card": card, "strip": strip, "content": content, "top_frame": top_frame,
            "linea": linea_div, "head": body_frame, "left_col": left_col, "right_col": right_col,
            "tit": lbl_tit, "icon": lbl_icon, "val": lbl_val, "sub": lbl_sub, "acento": color_acento,
            "clave": clave, "titulo_original": titulo
        })
        return lbl_val

    def filtrar_por_metrica(self, clave):
        if self.filtro_metrica_activa == clave and clave != "TODOS":
            self.filtro_metrica_activa = "TODOS"
        else:
            self.filtro_metrica_activa = clave

        self.actualizar_estilo_tarjetas_kpi()
        self.filtrar_tabla()

    def actualizar_metricas(self):
        total = len(self.bienes)
        operativos = 0
        preventivos = 0
        correctivos = 0
        desincorporados = obtener_conteo_bajas()

        for b in self.bienes:
            mant = str(b.get("mantenimiento", "")).strip()
            if "Preventivo" in mant: preventivos += 1
            elif "Correctivo" in mant: correctivos += 1
            else: operativos += 1

        self.lbl_val_total.config(text=str(total))
        self.lbl_val_operativos.config(text=str(operativos))
        self.lbl_val_preventivos.config(text=str(preventivos))
        self.lbl_val_correctivos.config(text=str(correctivos))
        self.lbl_val_desincorporados.config(text=str(desincorporados))

    # --- FORMULARIO & SUBFORMULARIO DE PERIFÉRICOS ---
    def crear_formulario(self):
        self.frame_form = tk.LabelFrame(
            self.root, text=" Registrar Activo y Gestión de Mantenimiento ",
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid"
        )
        self.frame_form.grid(row=2, column=0, sticky="ew", padx=15, pady=4)
        self.frame_form.columnconfigure(1, weight=1)
        self.frame_form.columnconfigure(3, weight=2)
        self.frame_form.columnconfigure(5, weight=1)
        
        self.frames_form_internos = []
        
        lbl1 = tk.Label(self.frame_form, text="ID único:", font=("Segoe UI", 8, "bold"))
        lbl1.grid(row=0, column=0, padx=(10, 5), pady=3, sticky="e")
        self.entry_id = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_id.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        
        lbl2 = tk.Label(self.frame_form, text="Asignado a:", font=("Segoe UI", 8, "bold"))
        lbl2.grid(row=0, column=2, padx=(10, 5), pady=3, sticky="e")
        
        opciones_asignacion = ["Departamento de Sistemas", "Administración", "Laboratorio 1", "Rectorado"]
        self.combo_asignado = ttk.Combobox(
            self.frame_form, values=opciones_asignacion, font=("Segoe UI", 9), state="readonly", style="TCombobox"
        )
        self.combo_asignado.grid(row=0, column=3, columnspan=3, padx=5, pady=3, sticky="ew")
        if opciones_asignacion: self.combo_asignado.current(0)
            
        frame_btn_form = tk.Frame(self.frame_form)
        frame_btn_form.grid(row=0, column=6, rowspan=4, padx=10, pady=3, sticky="ns")
        self.frames_form_internos.append(frame_btn_form)

        tk.Button(frame_btn_form, text="Registrar Nuevo", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.agregar_bien, bd=0, padx=10, pady=3, cursor="hand2").pack(fill="x", pady=2)
        tk.Button(frame_btn_form, text="Guardar Cambios", bg="#059669", fg="white", font=("Segoe UI", 8, "bold"), command=self.actualizar_bien, bd=0, padx=10, pady=3, cursor="hand2").pack(fill="x", pady=2)
        
        # Botón para alternar la Ficha de Periféricos manualmente
        self.btn_toggle_perifericos = tk.Button(
            frame_btn_form, text="⚙️ Ficha Periféricos", font=("Segoe UI", 8, "bold"),
            bg="#334155", fg="#ffffff", command=self.toggle_manual_perifericos, bd=0, padx=8, pady=2, cursor="hand2"
        )
        self.btn_toggle_perifericos.pack(fill="x", pady=2)

        tk.Button(frame_btn_form, text="Limpiar Campos", bg="#6b7280", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_formulario, bd=0, padx=10, pady=2, cursor="hand2").pack(fill="x", pady=2)
        
        lbl3 = tk.Label(self.frame_form, text="Descripción / Nombre:", font=("Segoe UI", 8, "bold"))
        lbl3.grid(row=1, column=0, padx=(10, 5), pady=3, sticky="e")
        self.entry_nombre = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_nombre.grid(row=1, column=1, columnspan=5, padx=5, pady=3, sticky="ew")
        self.entry_nombre.bind("<KeyRelease>", self.al_cambiar_texto_nombre)

        lbl4 = tk.Label(self.frame_form, text="¿Mantenimiento?:", font=("Segoe UI", 8, "bold"))
        lbl4.grid(row=2, column=0, padx=(10, 5), pady=3, sticky="e")
        self.combo_mant = ttk.Combobox(self.frame_form, values=["No", "Sí (Preventivo)", "Sí (Correctivo)"], font=("Segoe UI", 9), width=15, state="readonly")
        self.combo_mant.current(0)
        self.combo_mant.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        
        lbl5 = tk.Label(self.frame_form, text="Fecha (DD/MM/AAAA):", font=("Segoe UI", 8, "bold"))
        lbl5.grid(row=2, column=2, padx=(10, 5), pady=3, sticky="e")
        self.entry_fecha_mant = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha_mant.grid(row=2, column=3, padx=5, pady=3, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.al_cambiar_fecha)
        
        lbl6 = tk.Label(self.frame_form, text="Próximo (Hábil +3M):", font=("Segoe UI", 8, "bold"))
        lbl6.grid(row=2, column=4, padx=(10, 5), pady=3, sticky="e")
        self.entry_proximo = tk.Entry(self.frame_form, font=("Segoe UI", 9, "bold"), relief="solid", bd=1)
        self.entry_proximo.grid(row=2, column=5, padx=5, pady=3, sticky="ew")
        
        lbl7 = tk.Label(self.frame_form, text="Detalle / Observación:", font=("Segoe UI", 8, "bold"))
        lbl7.grid(row=3, column=0, padx=(10, 5), pady=3, sticky="e")
        self.entry_desc_mant = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_desc_mant.grid(row=3, column=1, columnspan=5, padx=5, pady=3, sticky="ew")

        self.labels_texto.extend([lbl1, lbl2, lbl3, lbl4, lbl5, lbl6, lbl7])
        self.entries_widgets.extend([self.entry_id, self.entry_nombre, self.entry_fecha_mant, self.entry_desc_mant])

        # Construir subformulario expandible para periféricos
        self.construir_subformulario_perifericos()

    def construir_subformulario_perifericos(self):
        """Construye el contenedor expandible para detallar componentes de activos compuestos."""
        self.frame_subform_container = tk.Frame(self.frame_form, bd=0, highlightthickness=1)
        self.frame_subform_container.grid(row=4, column=0, columnspan=7, sticky="ew", padx=8, pady=(4, 6))
        self.frame_subform_container.grid_forget()

        # Barra de encabezado del subformulario
        self.frame_sub_header = tk.Frame(self.frame_subform_container)
        self.frame_sub_header.pack(fill="x", padx=8, pady=(4, 2))

        self.lbl_titulo_sub = tk.Label(
            self.frame_sub_header, 
            text="🖥️ Ficha Técnica de Periféricos e Integridad de Equipos de Computación", 
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_titulo_sub.pack(side="left")

        self.lbl_sub_hint = tk.Label(
            self.frame_sub_header,
            text="(Activo Compuesto detectado — Ingrese el estado de cada componente)",
            font=("Segoe UI", 7)
        )
        self.lbl_sub_hint.pack(side="left", padx=(6, 0))

        # Botón de preset rápido
        btn_preset_ok = tk.Button(
            self.frame_sub_header, text="⚡ Todos Operativos", font=("Segoe UI", 7, "bold"),
            bg="#0284c7", fg="white", bd=0, padx=6, pady=1, cursor="hand2", command=self.aplicar_preset_operativo
        )
        btn_preset_ok.pack(side="right", padx=(0, 4))

        self.perifericos_widgets = {}
        elementos = [
            ("Monitor / Pantalla", "monitor", ["Operativo", "Parpadeos intermitentes", "Rayones visibles", "Líneas en pantalla", "Inoperativo", "N/A"]),
            ("Teclado", "teclado", ["Operativo", "Falla teclas específicas", "Teclas trabadas / duras", "Inoperativo", "N/A"]),
            ("Mouse", "mouse", ["Operativo", "Falla de clic", "Problema sensor / scroll", "Inoperativo", "N/A"]),
            ("Componentes / CPU", "cpu", ["Operativo", "Mantenimiento requerido", "Sobrecalentamiento / Ruido", "Falla RAM / Disco", "No enciende", "N/A"])
        ]

        self.grid_perif = tk.Frame(self.frame_subform_container)
        self.grid_perif.pack(fill="x", padx=8, pady=(2, 6))

        for idx, (label_txt, clave, opciones_estado) in enumerate(elementos):
            self.grid_perif.columnconfigure(idx, weight=1)
            
            card = tk.LabelFrame(self.grid_perif, text=f" {label_txt} ", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=5, pady=4)
            card.grid(row=0, column=idx, sticky="nsew", padx=3, pady=2)

            lbl_est = tk.Label(card, text="Estado:", font=("Segoe UI", 7))
            lbl_est.pack(anchor="w")
            combo_est = ttk.Combobox(card, values=opciones_estado, font=("Segoe UI", 8), state="readonly")
            combo_est.current(0)
            combo_est.pack(fill="x", pady=(0, 2))

            lbl_obs = tk.Label(card, text="Detalle / Observación:", font=("Segoe UI", 7))
            lbl_obs.pack(anchor="w")
            entry_obs = tk.Entry(card, font=("Segoe UI", 8), relief="solid", bd=1)
            entry_obs.pack(fill="x")
            self.entries_widgets.append(entry_obs)

            self.perifericos_widgets[clave] = {
                "card": card,
                "lbl_estado": lbl_est,
                "lbl_detalle": lbl_obs,
                "estado": combo_est,
                "observacion": entry_obs
            }

    def aplicar_preset_operativo(self):
        """Rellena rápidamente los campos con estado 100% operativo."""
        if hasattr(self, 'perifericos_widgets'):
            for p_data in self.perifericos_widgets.values():
                p_data["estado"].set("Operativo")
                p_data["observacion"].delete(0, tk.END)
                p_data["observacion"].insert(0, "En buen estado operativo")

    def toggle_manual_perifericos(self):
        self.subform_manual_toggle = True
        if self.subform_desplegado:
            self.ocultar_subformulario_perifericos()
        else:
            self.mostrar_subformulario_perifericos()

    def al_cambiar_texto_nombre(self, event=None):
        texto = self.entry_nombre.get().strip()
        if es_activo_compuesto(texto):
            if not self.subform_desplegado:
                self.mostrar_subformulario_perifericos()
        else:
            if self.subform_desplegado and not self.subform_manual_toggle:
                if not self.tiene_datos_en_perifericos():
                    self.ocultar_subformulario_perifericos()

    def mostrar_subformulario_perifericos(self):
        self.frame_subform_container.grid(row=4, column=0, columnspan=7, sticky="ew", padx=8, pady=(4, 6))
        self.subform_desplegado = True
        self.btn_toggle_perifericos.config(text="⚙️ Ficha Activa (▲)", bg="#0284c7", fg="#ffffff")
        self.aplicar_tema_widgets()

    def ocultar_subformulario_perifericos(self):
        self.frame_subform_container.grid_forget()
        self.subform_desplegado = False
        self.btn_toggle_perifericos.config(
            text="⚙️ Ficha Periféricos",
            bg="#334155" if self.modo_oscuro else "#475569",
            fg="#ffffff"
        )

    def tiene_datos_en_perifericos(self):
        if not hasattr(self, 'perifericos_widgets'):
            return False
        for p_data in self.perifericos_widgets.values():
            if p_data["estado"].get() not in ["Operativo", "N/A"] or p_data["observacion"].get().strip():
                return True
        return False

    def obtener_datos_perifericos_actualizados(self):
        """Extrae el estado y las observaciones modificadas de los periféricos."""
        perifs_dict = {}
        if hasattr(self, 'perifericos_widgets') and self.subform_desplegado:
            for clave, widgets in self.perifericos_widgets.items():
                perifs_dict[clave] = {
                    "estado": widgets["estado"].get(),
                    "detalle": widgets["observacion"].get().strip()
                }
        return perifs_dict

    def cargar_perifericos_en_formulario(self, bien):
        """Visualiza y carga los datos de periféricos del bien seleccionado en el subformulario."""
        perifs = bien.get("perifericos", {})
        if perifs:
            self.mostrar_subformulario_perifericos()
            self.subform_manual_toggle = True
            for clave, p_data in perifs.items():
                if clave in self.perifericos_widgets:
                    self.perifericos_widgets[clave]["estado"].set(p_data.get("estado", "Operativo"))
                    self.perifericos_widgets[clave]["observacion"].delete(0, tk.END)
                    self.perifericos_widgets[clave]["observacion"].insert(0, p_data.get("detalle", ""))
        else:
            self.ocultar_subformulario_perifericos()
            self.subform_manual_toggle = False

    # --- BÚSQUEDA ---
    def crear_panel_busqueda(self):
        self.frame_busqueda = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_busqueda.grid(row=3, column=0, sticky="ew", padx=15, pady=(2, 2))
        
        self.lbl_icon_buscar = tk.Label(self.frame_busqueda, text="🔍 Buscar Activo:", font=("Segoe UI", 8, "bold"))
        self.lbl_icon_buscar.pack(side="left", padx=(0, 5))
        
        self.entry_buscar = tk.Entry(self.frame_busqueda, font=("Segoe UI", 9), relief="solid", bd=1, width=22)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        self.entries_widgets.append(self.entry_buscar)
        
        tk.Button(self.frame_busqueda, text="Limpiar Filtro", bg="#002B49", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_filtro_busqueda, bd=0, padx=8, pady=2, cursor="hand2").pack(side="left", padx=5)
        
        self.lbl_indicador_busqueda = tk.Label(self.frame_busqueda, text="(Doble clic para editar / Clic derecho para opciones)", font=("Segoe UI", 8, "bold"))
        self.lbl_indicador_busqueda.pack(side="right")

    # --- TABLA DE DATOS Y MENÚ CONTEXTUAL ---
    def crear_tabla(self):
        self.frame_tabla = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_tabla.grid(row=4, column=0, sticky="nsew", padx=15, pady=2)
        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "asignado_a", "mantenimiento", "fecha_mant", "proximo_mant")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings")
        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción / Detalles del Bien")
        self.tabla.heading("asignado_a", text="Asignado a")
        self.tabla.heading("mantenimiento", text="Mantenimiento")
        self.tabla.heading("fecha_mant", text="Última Fecha")
        self.tabla.heading("proximo_mant", text="Próxima Fecha (Hábil)")
        
        self.tabla.column("id", width=60, minwidth=50, anchor="center", stretch=False)
        self.tabla.column("nombre", width=220, minwidth=150, anchor="w", stretch=True)
        self.tabla.column("asignado_a", width=140, minwidth=120, anchor="w", stretch=True)
        self.tabla.column("mantenimiento", width=105, minwidth=90, anchor="center", stretch=False)
        self.tabla.column("fecha_mant", width=90, minwidth=85, anchor="center", stretch=False)
        self.tabla.column("proximo_mant", width=145, minwidth=135, anchor="center", stretch=False)
        
        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        self.tabla.bind("<Button-3>", self.mostrar_menu_contextual)
        self.tabla.bind("<Button-2>", self.mostrar_menu_contextual)
        
        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def crear_menu_contextual(self):
        self.menu_contextual = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 9))
        self.menu_contextual.add_command(label="✏️ Editar Activo", command=self.cargar_seleccion_para_editar)
        self.menu_contextual.add_command(label="🖥️ Ver Ficha de Periféricos", command=self.ver_ficha_perifericos_popup)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="❌ Dar de Baja / Generar Acta PDF",
            command=self.dar_de_baja_bien,
            foreground="#dc2626", activeforeground="#ffffff", activebackground="#dc2626"
        )

    def mostrar_menu_contextual(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            self.tabla.selection_set(item)
            self.tabla.focus(item)
            self.menu_contextual.post(event.x_root, event.y_root)

    #----- Ventana emergente para Ficha Tecnica ---------
    def ver_ficha_perifericos_popup(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un activo de la tabla.", parent=self.root)
            return
            
        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])
        
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if not bien:
            return

        perifs = bien.get("perifericos", {})
        
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        modal = tk.Toplevel(self.root)
        modal.title(f"Ficha de Periféricos - Activo ID: {id_bien}")
        modal.geometry("450x460")
        modal.resizable(False, False)
        modal.configure(bg=pal["bg_root"])
        modal.transient(self.root)
        modal.grab_set()

        # Centrar ventana
        modal.update_idletasks()
        w = modal.winfo_width()
        h = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (w // 2)
        y = (modal.winfo_screenheight() // 2) - (h // 2)
        modal.geometry(f"{w}x{h}+{x}+{y}")

        # Cabecera con márgenes mejorados
        tk.Label(
            modal, text="🖥️  Ficha Técnica de Periféricos", 
            font=("Segoe UI", 11, "bold"), fg=pal["fg_texto"], bg=pal["bg_root"]
        ).pack(pady=(15, 2))
        
        tk.Label(
            modal, text=f"Equipo: {bien.get('nombre', 'N/A')}", 
            font=("Segoe UI", 9, "bold"), fg=pal["fg_subtexto"], bg=pal["bg_root"]
        ).pack(pady=(0, 12))

        # Contenedor principal de detalles
        frame_detalles = tk.Frame(modal, bg=pal["bg_panel"], bd=1, relief="solid")
        frame_detalles.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        if not perifs:
            tk.Label(
                frame_detalles, text="Este activo no registra periféricos asociados.", 
                font=("Segoe UI", 9), fg=pal["fg_subtexto"], bg=pal["bg_panel"]
            ).pack(expand=True, pady=20)
        else:
            nombres_perif = {"monitor": "Monitor", "teclado": "Teclado", "mouse": "Mouse", "cpu": "CPU / Internos"}
            
            for clave, nombre_legible in nombres_perif.items():
                p_data = perifs.get(clave, {})
                estado = p_data.get("estado", "Operativo")
                detalle = p_data.get("detalle", "").strip()

                # Definir colores y símbolos según el estado
                if estado == "Operativo":
                    simbolo, color_estado = "🟢", "#16a34a" if not self.modo_oscuro else "#4ade80"
                elif estado == "Dañado":
                    simbolo, color_estado = "🔴", "#dc2626" if not self.modo_oscuro else "#f87171"
                elif estado == "Ausente":
                    simbolo, color_estado = "🟡", "#ca8a04" if not self.modo_oscuro else "#facc15"
                else:
                    simbolo, color_estado = "⚪", pal["fg_subtexto"]

                # Tarjeta individual para cada periférico
                item_frame = tk.Frame(frame_detalles, bg=pal["bg_panel"], bd=1, relief="flat")
                item_frame.pack(fill="x", padx=12, pady=6)

                # Línea superior: Nombre y Estado con símbolo y color
                header_row = tk.Frame(item_frame, bg=pal["bg_panel"])
                header_row.pack(fill="x", anchor="w")

                tk.Label(
                    header_row, text=f"• {nombre_legible}:", 
                    font=("Segoe UI", 9, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"], anchor="w"
                ).pack(side="left")

                tk.Label(
                    header_row, text=f" {simbolo} {estado}", 
                    font=("Segoe UI", 9, "bold"), fg=color_estado, bg=pal["bg_panel"], anchor="w"
                ).pack(side="left", padx=8)

                # Línea inferior: Observación técnica ubicada debajo del diagnóstico
                if detalle:
                    obs_frame = tk.Frame(item_frame, bg=pal["bg_panel"])
                    obs_frame.pack(fill="x", anchor="w", padx=10, pady=(4, 2))
                    
                    # Línea 1: Título de la sección
                    tk.Label(
                        obs_frame, text="Observaciones Técnicas:", 
                        font=("Segoe UI", 8, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"], anchor="w"
                    ).pack(fill="x", anchor="w")
                    
                    # Línea 2: Texto de la descripción con fuente Consolas y wraplength para evitar cortes
                    tk.Label(
                        obs_frame, text=detalle, 
                        font=("Segoe UI", 11), fg=pal["fg_texto"], bg=pal["bg_panel"], 
                        anchor="w", justify="left", wraplength=380
                    ).pack(fill="x", anchor="w", pady=(2, 0))

        # Botón de cierre
        tk.Button(
            modal, text="Cerrar", bg="#002B49", fg="white", 
            font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=6, cursor="hand2",
            command=modal.destroy
        ).pack(pady=(0, 15))

    # --- ACCIONES / PANEL INFERIOR ---
    def crear_panel_acciones(self):
        self.frame_acciones = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_acciones.grid(row=5, column=0, sticky="ew", padx=15, pady=(2, 8))
        
        tk.Button(
            self.frame_acciones, text="☁️ Centro de Respaldos", bg="#0284C7", fg="white",
            activebackground="#0369a1", activeforeground="white", font=("Segoe UI", 8, "bold"),
            command=self.abrir_ventana_respaldos, bd=0, padx=14, pady=5, cursor="hand2"
        ).pack(side="left")
        
        self.lbl_info_pie = tk.Label(self.frame_acciones, text="SIGAR V2.5 — UNELLEZ", font=("Segoe UI", 8, "bold"))
        self.lbl_info_pie.pack(side="right", pady=2)

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

        tk.Label(modal, text="☁️ Sincronización y Respaldos", font=("Segoe UI", 12, "bold"), fg=pal["fg_texto"], bg=pal["bg_root"]).pack(pady=(15, 5))
        tk.Label(modal, text="Seleccione la acción de respaldo que desea ejecutar:", font=("Segoe UI", 8), fg=pal["fg_subtexto"], bg=pal["bg_root"]).pack(pady=(0, 15))

        frame_botones = tk.Frame(modal, bg=pal["bg_root"])
        frame_botones.pack(fill="both", expand=True, padx=25, pady=5)

        tk.Button(frame_botones, text="☁️ Exportar / Guardar Respaldo en la Nube", bg="#0284C7", fg="white", font=("Segoe UI", 9, "bold"), bd=0, pady=8, cursor="hand2", command=lambda: self.accion_guardar_nube(modal)).pack(fill="x", pady=4)
        tk.Button(frame_botones, text="📥 Importar / Restaurar desde la Nube", bg="#0D9488", fg="white", font=("Segoe UI", 9, "bold"), bd=0, pady=8, cursor="hand2", command=lambda: self.accion_importar_nube(modal)).pack(fill="x", pady=4)
        tk.Button(frame_botones, text="💾 Guardar Respaldo Local (Copiar JSON)", bg="#475569", fg="white", font=("Segoe UI", 9, "bold"), bd=0, pady=8, cursor="hand2", command=lambda: self.accion_guardar_local(modal)).pack(fill="x", pady=4)

    def accion_guardar_nube(self, modal):
        try:
            modal.destroy()
        except Exception:
            pass
        exportar_respaldo_nube_bd(parent_window=self.root)

    def accion_importar_nube(self, modal):
        if not HAS_REQUESTS:
            messagebox.showinfo("Librería Pendiente", "Se requiere la librería 'requests' instalada para recibir datos de la API.", parent=modal)
            return
        messagebox.showinfo("Conexión Backend", f"Frontend preparado para consultar e importar datos desde la API:\n\nEndpoint: {URL_RESPALDO_CLOUD}", parent=modal)

    def accion_guardar_local(self, modal):
        try:
            filename = filedialog.asksaveasfilename(
                parent=modal, title="Guardar Respaldo Local", defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                initialfile=f"respaldo_sigar_{date.today().strftime('%Y%m%d')}.json"
            )
            if filename:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.bienes, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Respaldo Guardado", f"El respaldo local ha sido guardado exitosamente en:\n{filename}", parent=modal)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el respaldo local: {e}", parent=modal)

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
            messagebox.showwarning("Campos Incompletos", "Por favor, complete el ID, Nombre/Descripción y 'Asignado a'.")
            return
            
        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("Tipo Incorrecto", "El ID debe ser un número entero.")
            return

        if any(b["id"] == id_int for b in self.bienes):
            messagebox.showwarning("ID Duplicado", f"El activo con ID {id_int} ya existe en el sistema.")
            return

        perifs_dict = self.obtener_datos_perifericos_actualizados()
            
        nuevo_bien = {
            "id": id_int, 
            "nombre": nombre_val, 
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else "",
            "perifericos": perifs_dict if self.subform_desplegado else {}
        }
        
        self.bienes.append(nuevo_bien)
        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Registro Exitoso", "El activo ha sido guardado localmente en bienes.json.")

    def actualizar_bien(self):
        id_val = self.entry_id.get().strip()
        if not id_val:
            messagebox.showwarning("Sin ID", "Ingrese o seleccione el ID del activo que desea actualizar.")
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
            messagebox.showwarning("Campos Incompletos", "Por favor, complete la Descripción/Nombre y 'Asignado a'.")
            return

        index = next((i for i, b in enumerate(self.bienes) if b["id"] == id_int), None)
        if index is None:
            messagebox.showerror("No Encontrado", f"No se encontró ningún activo con el ID {id_int}.")
            return

        perifs_dict = self.obtener_datos_perifericos_actualizados()

        self.bienes[index] = {
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else "",
            "perifericos": perifs_dict if self.subform_desplegado else {}
        }
        
        if guardar_datos_locales(self.bienes):
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Actualización Exitosa", f"Los datos del activo ID {id_int} han sido modificados localmente.")

    def dar_de_baja_bien(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un elemento de la tabla para darlo de baja.")
            return
            
        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])
        nombre_bien = item["values"][1]
        
        motivo = simpledialog.askstring(
            "Justificación de Baja", 
            f"Indique el motivo por el cual se da de baja el activo ID {id_bien}:\n({nombre_bien})",
            parent=self.root
        )
        if not motivo or not motivo.strip():
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Desincorporación", 
            f"¿Está seguro de desincorporar el activo ID {id_bien}?\n\nMotivo: {motivo.strip()}"
        )
        if confirmacion:
            bien_objetivo = next((b for b in self.bienes if b["id"] == id_bien), None)
            fecha_hora_baja = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            registro_baja = {
                "id": id_bien, 
                "nombre": nombre_bien,
                "asignado_a": bien_objetivo.get("asignado_a", "N/A") if bien_objetivo else "N/A",
                "mantenimiento": bien_objetivo.get("mantenimiento", "N/A") if bien_objetivo else "N/A",
                "fecha_ultimo_mant": bien_objetivo.get("fecha_mant", "N/A") if bien_objetivo else "N/A",
                "desc_mant": bien_objetivo.get("desc_mant", "") if bien_objetivo else "",
                "perifericos": bien_objetivo.get("perifericos", {}) if bien_objetivo else {},
                "motivo_baja": motivo.strip(), 
                "fecha_baja": fecha_hora_baja
            }
            
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            guardar_datos_locales(self.bienes)
            guardar_baja_local(registro_baja)
            archivo_generado = generar_acta_baja(registro_baja)
            
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Baja Procesada", f"El activo ID {id_bien} ha sido desincorporado.\n📄 Documento: {archivo_generado}")

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
                cumple_metrica = (mant_str == "No")
            elif self.filtro_metrica_activa == "PREVENTIVOS":
                cumple_metrica = ("Preventivo" in mant_str)
            elif self.filtro_metrica_activa == "CORRECTIVOS":
                cumple_metrica = ("Correctivo" in mant_str)
            elif self.filtro_metrica_activa == "DESINCORPORADOS":
                cumple_metrica = False

            if not cumple_metrica:
                continue

            if criterio in id_str or criterio in nombre_str or criterio in asignado_str or criterio in desc_str:
                tag_fila = "par" if i % 2 == 0 else "impar"
                self.tabla.insert("", "end", values=(
                    bien["id"], bien["nombre"], bien.get("asignado_a", "N/A"),
                    bien.get("mantenimiento", "No"), bien.get("fecha_mant", "N/A"), bien.get("proximo_mant", "N/A")
                ), tags=(tag_fila,))
                i += 1

    def limpiar_filtro_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
        self.filtro_metrica_activa = "TODOS"
        self.actualizar_estilo_tarjetas_kpi()
        self.actualizar_tabla()

    def cargar_seleccion_para_editar(self, event=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un elemento de la tabla para editar.")
            return
            
        item = self.tabla.item(seleccion[0])
        id_bien = int(item["values"][0])
        
        bien = next((b for b in self.bienes if b["id"] == id_bien), None)
        if bien:
            self.entry_id.delete(0, tk.END)
            self.entry_id.insert(0, str(bien["id"]))
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.insert(0, bien["nombre"])
            self.combo_asignado.set(bien.get("asignado_a", "Departamento de Sistemas"))
            self.combo_mant.set(bien.get("mantenimiento", "No"))
            self.entry_fecha_mant.delete(0, tk.END)
            self.entry_fecha_mant.insert(0, bien.get("fecha_mant", date.today().strftime("%d/%m/%Y")))
            self.entry_desc_mant.delete(0, tk.END)
            self.entry_desc_mant.insert(0, bien.get("desc_mant", ""))
            self.calcular_proxima_fecha_mantenimiento()

            # Carga automática de los periféricos asociados al activo
            self.cargar_perifericos_en_formulario(bien)

            self.entry_nombre.focus_force()

    def limpiar_formulario(self):
        self.entry_id.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_desc_mant.delete(0, tk.END)
        self.entry_fecha_mant.delete(0, tk.END)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.combo_mant.current(0)
        
        if hasattr(self, 'perifericos_widgets'):
            for p_data in self.perifericos_widgets.values():
                p_data["estado"].current(0)
                p_data["observacion"].delete(0, tk.END)
        self.ocultar_subformulario_perifericos()
        self.subform_manual_toggle = False

        self.calcular_proxima_fecha_mantenimiento()
        self.entry_id.focus_force()

    def al_cambiar_fecha(self, event=None):
        self.calcular_proxima_fecha_mantenimiento()

    def calcular_proxima_fecha_mantenimiento(self):
        fecha_str = self.entry_fecha_mant.get().strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(fecha_str, fmt).date()
                proxima_str = calcular_fecha_habil_3_meses(dt)
                self.entry_proximo.delete(0, tk.END)
                self.entry_proximo.insert(0, proxima_str)
                return proxima_str
            except ValueError:
                pass
        self.entry_proximo.delete(0, tk.END)
        self.entry_proximo.insert(0, "Formato Inválido")
        return None

    def actualizar_tabla(self):
        self.filtrar_tabla()


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()