# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Registrar la subcarpeta en sys.path para importar styles, utils y database
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
if DIR_ACTUAL not in sys.path:
    sys.path.insert(0, DIR_ACTUAL)

from styles import (
    PALETA, FONT_LABEL, FONT_BOLD, FONT_KPI_VAL, FONT_KPI_TIT,
    cargar_preferencia_tema, guardar_preferencia_tema, hex_a_rgb, rgb_a_hex
)
from utils import (
    HAS_PIL, HAS_REQUESTS, calcular_fecha_habil_3_meses, generar_acta_baja
)
if HAS_PIL:
    from PIL import Image, ImageTk

from database import (
    ARCHIVO_BAJAS, URL_RESPALDO_CLOUD, cargar_datos_locales,
    guardar_datos_locales, guardar_baja_local, obtener_conteo_bajas
)

# Definición dinámica de imágenes
ARCHIVO_LOGO = os.path.join(DIR_ACTUAL, "UNELLEZ LOGO.png")
PATH_LEMA = os.path.join(DIR_ACTUAL, "lema_unellez_oro.png")


class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos")
        self.root.geometry("1024x680")
        self.root.minsize(800, 500)
        
        self.modo_actual = cargar_preferencia_tema()
        self.modo_oscuro = (self.modo_actual == "oscuro")

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

        # Construcción GUI
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
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

        # Lema en una sola línea
        if os.path.exists(PATH_LEMA):
            try:
                img_lema_pil = Image.open(PATH_LEMA).convert("RGBA")
                datas = img_lema_pil.getdata()
                new_data = []
                for item in datas:
                    if item[0] > 230 and item[1] > 230 and item[2] > 230:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
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

        for lbl in getattr(self, 'labels_texto', []):
            lbl.config(bg=bg_panel_modo, fg=fg_texto_modo, font=FONT_LABEL)
            
        for f in getattr(self, 'frames_form_internos', []):
            f.config(bg=bg_panel_modo)

        for entry in getattr(self, 'entries_widgets', []):
            entry.config(
                bg=pal["entry_bg"], fg=pal["entry_fg"], insertbackground=pal["entry_fg"],
                highlightbackground=pal["entry_border"], highlightthickness=1, font=FONT_LABEL, bd=0
            )

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

        for i, card_info in enumerate(getattr(self, 'tarjetas_widgets', [])):
            cfg = pal["kpis"][i]
            bg_tarjeta = cfg["bg"]
            color_texto_acento = cfg["text"]

            card_info["card"].config(bg=bg_tarjeta, highlightbackground=cfg["border"])
            card_info["strip"].config(bg=cfg["border"])
            card_info["content"].config(bg=bg_tarjeta)

            if "top_frame" in card_info: card_info["top_frame"].config(bg=bg_tarjeta)
            if "left_col" in card_info: card_info["left_col"].config(bg=bg_tarjeta)
            if "right_col" in card_info: card_info["right_col"].config(bg=bg_tarjeta)
            card_info["head"].config(bg=bg_tarjeta)

            if "linea" in card_info: card_info["linea"].config(bg=color_texto_acento)

            card_info["tit"].config(bg=bg_tarjeta, fg=color_texto_acento, font=FONT_KPI_TIT)
            card_info["sub"].config(bg=bg_tarjeta, fg=cfg["sub"], font=FONT_LABEL)
            card_info["icon"].config(bg=bg_tarjeta, fg=color_texto_acento)
            card_info["val"].config(bg=bg_tarjeta, fg=cfg["val"], font=FONT_KPI_VAL)

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

    # --- TARJETAS MÉTRICAS ---
    def crear_panel_metricas(self):
        self.frame_kpis = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_kpis.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 5))

        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.tarjetas_widgets = []
        metricas = [
            ("TOTAL ACTIVOS", "0", "Bienes registrados", "📋"),
            ("OPERATIVOS", "0", "En servicio activo", "🟢"),
            ("PREVENTIVOS", "0", "Ciclo regular (+3M)", "🔧"),
            ("CORRECTIVOS", "0", "Ajuste / Reparación", "⚠️"),
            ("DESINCORPORADOS", "0", "Actas emitidas", "❌")
        ]

        for col, (titulo, valor, sub, icono) in enumerate(metricas):
            val_widget = self.crear_tarjeta(col, titulo, valor, sub, icono)
            if col == 0: self.lbl_val_total = val_widget
            elif col == 1: self.lbl_val_operativos = val_widget
            elif col == 2: self.lbl_val_preventivos = val_widget
            elif col == 3: self.lbl_val_correctivos = val_widget
            elif col == 4: self.lbl_val_desincorporados = val_widget

    def crear_tarjeta(self, col, titulo, valor_inicial, subtitulo, icono="📊", color_acento="#1E3A8A"):
        card = tk.Frame(self.frame_kpis, bd=0, highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        strip = tk.Frame(card, width=4, bg=color_acento, bd=0, highlightthickness=0)
        strip.pack(side="left", fill="y")

        content = tk.Frame(card, bd=0, highlightthickness=0)
        content.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        top_frame = tk.Frame(content, bd=0, highlightthickness=0)
        top_frame.pack(fill="x")

        lbl_tit = tk.Label(top_frame, text=titulo, font=("Segoe UI", 8, "bold"), fg=color_acento, anchor="w")
        lbl_tit.pack(fill="x")

        linea_div = tk.Frame(top_frame, height=2, bg=color_acento, bd=0, highlightthickness=0)
        linea_div.pack(fill="x", pady=(2, 6))

        body_frame = tk.Frame(content, bd=0, highlightthickness=0)
        body_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(body_frame, bd=0, highlightthickness=0)
        left_col.pack(side="left", fill="both", expand=True)

        lbl_val = tk.Label(left_col, text=valor_inicial, font=("Segoe UI", 18, "bold"), anchor="w")
        lbl_val.pack(fill="x")

        lbl_sub = tk.Label(left_col, text=subtitulo, font=("Segoe UI", 8), fg=color_acento, anchor="w")
        lbl_sub.pack(fill="x")

        right_col = tk.Frame(body_frame, width=35, bd=0, highlightthickness=0)
        right_col.pack_propagate(False)
        right_col.pack(side="right", fill="y")

        lbl_icon = tk.Label(right_col, text=icono, font=("Segoe UI", 16), fg=color_acento, anchor="e")
        lbl_icon.pack(expand=True, fill="both")

        self.tarjetas_widgets.append({
            "card": card, "strip": strip, "content": content, "top_frame": top_frame,
            "linea": linea_div, "head": body_frame, "left_col": left_col, "right_col": right_col,
            "tit": lbl_tit, "icon": lbl_icon, "val": lbl_val, "sub": lbl_sub, "acento": color_acento
        })
        return lbl_val

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

    # --- FORMULARIO ---
    def crear_formulario(self):
        self.frame_form = tk.LabelFrame(
            self.root, text=" Registrar Activo y Gestión de Mantenimiento ",
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid"
        )
        self.frame_form.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        self.frame_form.columnconfigure(1, weight=1)
        self.frame_form.columnconfigure(3, weight=2)
        self.frame_form.columnconfigure(5, weight=1)
        
        self.frames_form_internos = []
        
        lbl1 = tk.Label(self.frame_form, text="ID único:", font=("Segoe UI", 8, "bold"))
        lbl1.grid(row=0, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_id = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_id.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        
        lbl2 = tk.Label(self.frame_form, text="Asignado a:", font=("Segoe UI", 8, "bold"))
        lbl2.grid(row=0, column=2, padx=(10, 5), pady=4, sticky="e")
        
        opciones_asignacion = ["Departamento de Sistemas", "Administración", "Laboratorio 1", "Rectorado"]
        self.combo_asignado = ttk.Combobox(
            self.frame_form, values=opciones_asignacion, font=("Segoe UI", 9), state="readonly", style="TCombobox"
        )
        self.combo_asignado.grid(row=0, column=3, columnspan=3, padx=5, pady=4, sticky="ew")
        if opciones_asignacion: self.combo_asignado.current(0)
            
        frame_btn_form = tk.Frame(self.frame_form)
        frame_btn_form.grid(row=0, column=6, rowspan=4, padx=10, pady=4, sticky="ns")
        self.frames_form_internos.append(frame_btn_form)

        tk.Button(frame_btn_form, text="Registrar Nuevo", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.agregar_bien, bd=0, padx=10, pady=4, cursor="hand2").pack(fill="x", pady=2)
        tk.Button(frame_btn_form, text="Guardar Cambios", bg="#059669", fg="white", font=("Segoe UI", 8, "bold"), command=self.actualizar_bien, bd=0, padx=10, pady=4, cursor="hand2").pack(fill="x", pady=2)
        tk.Button(frame_btn_form, text="Limpiar Campos", bg="#6b7280", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_formulario, bd=0, padx=10, pady=3, cursor="hand2").pack(fill="x", pady=2)
        
        lbl3 = tk.Label(self.frame_form, text="Descripción / Nombre:", font=("Segoe UI", 8, "bold"))
        lbl3.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_nombre = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_nombre.grid(row=1, column=1, columnspan=5, padx=5, pady=4, sticky="ew")
        
        lbl4 = tk.Label(self.frame_form, text="¿Mantenimiento?:", font=("Segoe UI", 8, "bold"))
        lbl4.grid(row=2, column=0, padx=(10, 5), pady=4, sticky="e")
        self.combo_mant = ttk.Combobox(self.frame_form, values=["No", "Sí (Preventivo)", "Sí (Correctivo)"], font=("Segoe UI", 9), width=15, state="readonly")
        self.combo_mant.current(0)
        self.combo_mant.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        
        lbl5 = tk.Label(self.frame_form, text="Fecha (DD/MM/AAAA):", font=("Segoe UI", 8, "bold"))
        lbl5.grid(row=2, column=2, padx=(10, 5), pady=4, sticky="e")
        self.entry_fecha_mant = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_fecha_mant.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha_mant.grid(row=2, column=3, padx=5, pady=4, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.al_cambiar_fecha)
        
        lbl6 = tk.Label(self.frame_form, text="Próximo (Hábil +3M):", font=("Segoe UI", 8, "bold"))
        lbl6.grid(row=2, column=4, padx=(10, 5), pady=4, sticky="e")
        self.entry_proximo = tk.Entry(self.frame_form, font=("Segoe UI", 9, "bold"), relief="solid", bd=1)
        self.entry_proximo.grid(row=2, column=5, padx=5, pady=4, sticky="ew")
        
        lbl7 = tk.Label(self.frame_form, text="Detalle / Observación:", font=("Segoe UI", 8, "bold"))
        lbl7.grid(row=3, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_desc_mant = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_desc_mant.grid(row=3, column=1, columnspan=5, padx=5, pady=4, sticky="ew")

        self.labels_texto.extend([lbl1, lbl2, lbl3, lbl4, lbl5, lbl6, lbl7])
        self.entries_widgets.extend([self.entry_id, self.entry_nombre, self.entry_fecha_mant, self.entry_desc_mant])

    # --- BÚSQUEDA ---
    def crear_panel_busqueda(self):
        self.frame_busqueda = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_busqueda.grid(row=3, column=0, sticky="ew", padx=15, pady=(4, 2))
        
        self.lbl_icon_buscar = tk.Label(self.frame_busqueda, text="🔍 Buscar Activo:", font=("Segoe UI", 8, "bold"))
        self.lbl_icon_buscar.pack(side="left", padx=(0, 5))
        
        self.entry_buscar = tk.Entry(self.frame_busqueda, font=("Segoe UI", 9), relief="solid", bd=1, width=20)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        self.entries_widgets.append(self.entry_buscar)
        
        tk.Button(self.frame_busqueda, text="Limpiar Filtro", bg="#002B49", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_filtro_busqueda, bd=0, padx=8, pady=2, cursor="hand2").pack(side="left", padx=5)
        
        self.lbl_indicador_busqueda = tk.Label(self.frame_busqueda, text="(Doble clic en un registro para editar)", font=("Segoe UI", 8, "bold"))
        self.lbl_indicador_busqueda.pack(side="right")

    # --- TABLA DE DATOS ---
    def crear_tabla(self):
        self.frame_tabla = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_tabla.grid(row=4, column=0, sticky="nsew", padx=15, pady=4)
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
        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    # --- ACCIONES ---
    def crear_panel_acciones(self):
        self.frame_acciones = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_acciones.grid(row=5, column=0, sticky="ew", padx=15, pady=(4, 10))
        
        tk.Button(self.frame_acciones, text="Cargar Seleccionado para Editar", bg="#D97706", fg="white", font=("Segoe UI", 8, "bold"), command=self.cargar_seleccion_para_editar, bd=0, padx=12, pady=5, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(self.frame_acciones, text="Dar de Baja / Generar Acta PDF", bg="#DC2626", fg="white", font=("Segoe UI", 8, "bold"), command=self.dar_de_baja_bien, bd=0, padx=12, pady=5, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(self.frame_acciones, text="☁️ Respaldo en Nube (Próximamente)", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.respaldar_en_nube_placeholder, bd=0, padx=12, pady=5, cursor="hand2").pack(side="left")
        
        self.lbl_info_pie = tk.Label(self.frame_acciones, text="SIGAR V2.5 — UNELLEZ", font=("Segoe UI", 8, "bold"))
        self.lbl_info_pie.pack(side="right", pady=3)

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
            
        nuevo_bien = {
            "id": id_int, "nombre": nombre_val, "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else ""
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
            
        self.bienes[index] = {
            "id": id_int, "nombre": nombre_val, "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else ""
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
                "id": id_bien, "nombre": nombre_bien,
                "asignado_a": bien_objetivo.get("asignado_a", "N/A") if bien_objetivo else "N/A",
                "mantenimiento": bien_objetivo.get("mantenimiento", "N/A") if bien_objetivo else "N/A",
                "fecha_ultimo_mant": bien_objetivo.get("fecha_mant", "N/A") if bien_objetivo else "N/A",
                "desc_mant": bien_objetivo.get("desc_mant", "") if bien_objetivo else "",
                "motivo_baja": motivo.strip(), "fecha_baja": fecha_hora_baja
            }
            
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            guardar_datos_locales(self.bienes)
            guardar_baja_local(registro_baja)
            archivo_generado = generar_acta_baja(registro_baja)
            
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            messagebox.showinfo("Baja Procesada", f"El activo ID {id_bien} ha sido desincorporado.\n📄 Documento: {archivo_generado}")

    def respaldar_en_nube_placeholder(self):
        if not HAS_REQUESTS:
            messagebox.showinfo("Respaldo en Nube", "Instale 'requests' para activar esta función (pip install requests).")
            return
        messagebox.showinfo("Módulo de Respaldo", f"Esta función enviará bienes.json a {URL_RESPALDO_CLOUD}.")

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

            if criterio in id_str or criterio in nombre_str or criterio in asignado_str or criterio in desc_str:
                tag_fila = "par" if i % 2 == 0 else "impar"
                self.tabla.insert("", "end", values=(
                    bien["id"], bien["nombre"], bien.get("asignado_a", "N/A"),
                    bien.get("mantenimiento", "No"), bien.get("fecha_mant", "N/A"), bien.get("proximo_mant", "N/A")
                ), tags=(tag_fila,))
                i += 1

    def limpiar_filtro_busqueda(self):
        self.entry_buscar.delete(0, tk.END)
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
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        
        for i, bien in enumerate(getattr(self, 'bienes', [])):
            tag_fila = "par" if i % 2 == 0 else "impar"
            self.tabla.insert("", "end", values=(
                bien["id"], bien["nombre"], bien.get("asignado_a", "N/A"),
                bien.get("mantenimiento", "No"), bien.get("fecha_mant", "N/A"), bien.get("proximo_mant", "N/A")
            ), tags=(tag_fila,))


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()