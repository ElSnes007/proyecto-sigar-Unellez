# -*# -*- coding: utf-8 -*-
import os
import json
import calendar
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Intentar importar PIL (Pillow) para escalado de imagen de alta calidad
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Intentar importar ReportLab para generación nativa de PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Intentar importar requests para la futura integración del respaldo en la nube
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# --- CONFIGURACIÓN DE ALMACENAMIENTO LOCAL Y RESPALDO ---
ARCHIVO_BIENES = "bienes.json"
ARCHIVO_BAJAS = "bienes_bajas.json"
URL_RESPALDO_CLOUD = "https://script.google.com/macros/s/AKfycbyo4mwCjTwhYUuQ6siUEVbKuf4SE77_VKwuJbUcAc9gMFXLeMLpN59X2-tFsH17ae_bHg/exec"
ARCHIVO_LOGO = "UNELLEZ LOGO.png"  # Nombre exacto del archivo de logo en la carpeta

class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos")
        self.root.geometry("1120x740")
        self.root.minsize(1000, 650)
        
        # Estado del tema
        self.modo_oscuro = False

        # Paleta de Colores Pasteles y Oscuros
        self.PALETA = {
            "claro": {
                "bg_root": "#f8fafc",
                "bg_cintillo": "#002B49",
                "fg_cintillo": "#ffffff",
                "bg_panel": "#ffffff",
                "border_panel": "#cbd5e1",
                "fg_texto": "#0f172a",
                "fg_subtexto": "#475569",
                "entry_bg": "#ffffff",
                "entry_fg": "#0f172a",
                "entry_border": "#94a3b8",
                "tree_bg": "#ffffff",
                "tree_fg": "#0f172a",
                "tree_head_bg": "#002B49",
                "tree_head_fg": "#ffffff",
                "kpis": [
                    {"bg": "#f1f5f9", "border": "#475569", "text": "#334155", "val": "#0f172a", "sub": "#64748b"}, # Total
                    {"bg": "#ecfdf5", "border": "#10b981", "text": "#047857", "val": "#064e3b", "sub": "#059669"}, # Operativos
                    {"bg": "#f0f9ff", "border": "#0284c7", "text": "#0369a1", "val": "#0c4a6e", "sub": "#0284c7"}, # Preventivos
                    {"bg": "#fffbeb", "border": "#f59e0b", "text": "#b45309", "val": "#78350f", "sub": "#d97706"}, # Correctivos
                    {"bg": "#fff1f2", "border": "#f43f5e", "text": "#be123c", "val": "#881337", "sub": "#e11d48"}  # Desincorporados
                ]
            },
            "oscuro": {
                "bg_root": "#0f172a",
                "bg_cintillo": "#020617",
                "fg_cintillo": "#f8fafc",
                "bg_panel": "#1e293b",
                "border_panel": "#334155",
                "fg_texto": "#f8fafc",
                "fg_subtexto": "#cbd5e1",
                "entry_bg": "#334155",
                "entry_fg": "#ffffff",
                "entry_border": "#64748b",
                "tree_bg": "#1e293b",
                "tree_fg": "#f8fafc",
                "tree_head_bg": "#020617",
                "tree_head_fg": "#38bdf8",
                "kpis": [
                    {"bg": "#1e293b", "border": "#64748b", "text": "#cbd5e1", "val": "#f8fafc", "sub": "#94a3b8"}, # Total
                    {"bg": "#064e3b", "border": "#34d399", "text": "#a7f3d0", "val": "#ffffff", "sub": "#6ee7b7"}, # Operativos
                    {"bg": "#0c4a6e", "border": "#38bdf8", "text": "#bae6fd", "val": "#ffffff", "sub": "#7dd3fc"}, # Preventivos
                    {"bg": "#78350f", "border": "#fbbf24", "text": "#fde68a", "val": "#ffffff", "sub": "#fcd34d"}, # Correctivos
                    {"bg": "#881337", "border": "#fb7185", "text": "#fecdd3", "val": "#ffffff", "sub": "#fda4af"}  # Desinc
                ]
            }
        }
        
        self.root.configure(bg=self.PALETA["claro"]["bg_root"])
        
        # Estilos globales de Tkinter
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Lista local en memoria
        self.bienes = []

        # Listas para actualizar dinamismo de tema
        self.tarjetas_widgets = []
        self.labels_texto = []
        self.entries_widgets = []

        # Construcción de componentes gráficos
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
        self.crear_panel_acciones()
        
        # Aplicar estilo inicial
        self.aplicar_tema_widgets()

        # Cargar datos locales e inicializar
        self.bienes = self.cargar_datos_locales()
            
        self.actualizar_tabla()
        self.actualizar_metricas()
        self.calcular_proxima_fecha_mantenimiento()
        self.root.after(200, self.activar_foco_inicial)

    def activar_foco_inicial(self):
        self.root.focus_force()
        self.entry_id.focus_force()

    # --- 1. CINTILLO INSTITUCIONAL Y LOGO UNELLEZ ---
    def crear_cintillo_institucional(self):
        self.frame_cintillo = tk.Frame(self.root, bg="#002B49", height=42)
        self.frame_cintillo.pack(fill="x", side="top")
        
        # Contenedor para Logo + Texto
        frame_logo_titulo = tk.Frame(self.frame_cintillo, bg="#002B49")
        frame_logo_titulo.pack(side="left", padx=12, pady=4)

        # Cargar la imagen del logo
        self.logo_img = None
        if os.path.exists(ARCHIVO_LOGO):
            try:
                if HAS_PIL:
                    img_pil = Image.open(ARCHIVO_LOGO).resize((64, 64), Image.Resampling.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(img_pil)
                else:
                    raw_img = tk.PhotoImage(file=ARCHIVO_LOGO)
                    w_factor = max(1, raw_img.width() // 28)
                    h_factor = max(1, raw_img.height() // 28)
                    self.logo_img = raw_img.subsample(w_factor, h_factor)
            except Exception:
                self.logo_img = None

        if self.logo_img:
            lbl_logo = tk.Label(frame_logo_titulo, image=self.logo_img, bg="#002B49")
            lbl_logo.pack(side="left", padx=(0, 8))

        # Texto "UNELLEZ" destacado en naranja
        lbl_unellez = tk.Label(
            frame_logo_titulo, 
            text="UNELLEZ", 
            font=("Segoe UI", 13, "bold"), 
            fg="#FF6600", 
            bg="#002B49"
        )
        lbl_unellez.pack(side="left")

        # Botón para activar/desactivar Cuidado de Vista / Modo Oscuro
        self.btn_modo_oscuro = tk.Button(
            self.frame_cintillo,
            text="🌙 Cuidado de Vista",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b", fg="#f8fafc",
            activebackground="#334155", activeforeground="#ffffff",
            bd=0, padx=8, pady=2, cursor="hand2",
            command=self.toggle_modo_oscuro_animado
        )
        self.btn_modo_oscuro.pack(side="right", padx=(5, 12))

        self.lbl_estado_local = tk.Label(
            self.frame_cintillo, 
            text="● Modo Local (bienes.json)", 
            font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#002B49"
        )
        self.lbl_estado_local.pack(side="right", padx=5)

    # --- ANIMACIÓN Y CAMBIO DE TEMA ---
    def toggle_modo_oscuro_animado(self):
        self.modo_oscuro = not self.modo_oscuro
        
        color_inicio = self.PALETA["oscuro" if not self.modo_oscuro else "claro"]["bg_root"]
        color_fin = self.PALETA["oscuro" if self.modo_oscuro else "claro"]["bg_root"]
        
        rgb_inicio = self.hex_a_rgb(color_inicio)
        rgb_fin = self.hex_a_rgb(color_fin)
        
        self.animar_transicion_bg(rgb_inicio, rgb_fin, paso=0, total_pasos=12)

    def hex_a_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def rgb_a_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def animar_transicion_bg(self, rgb_inicio, rgb_fin, paso, total_pasos):
        if paso <= total_pasos:
            factor = paso / total_pasos
            r = int(rgb_inicio[0] + (rgb_fin[0] - rgb_inicio[0]) * factor)
            g = int(rgb_inicio[1] + (rgb_fin[1] - rgb_inicio[1]) * factor)
            b = int(rgb_inicio[2] + (rgb_fin[2] - rgb_inicio[2]) * factor)
            color_interp = self.rgb_a_hex((r, g, b))
            
            self.root.configure(bg=color_interp)
            self.frame_kpis.configure(bg=color_interp)
            self.frame_busqueda.configure(bg=color_interp)
            self.frame_tabla.configure(bg=color_interp)
            self.frame_acciones.configure(bg=color_interp)
            
            self.root.after(18, lambda: self.animar_transicion_bg(rgb_inicio, rgb_fin, paso + 1, total_pasos))
        else:
            self.aplicar_tema_widgets()

    def aplicar_tema_widgets(self):
        t = "oscuro" if self.modo_oscuro else "claro"
        pal = self.PALETA[t]

        if self.modo_oscuro:
            self.btn_modo_oscuro.config(text="☀️ Modo Claro", bg="#f59e0b", fg="#0f172a", activebackground="#fbbf24")
        else:
            self.btn_modo_oscuro.config(text="🌙 Cuidado de Vista", bg="#1e293b", fg="#f8fafc", activebackground="#334155")

        self.frame_form.config(bg=pal["bg_panel"], fg=pal["fg_texto"], highlightbackground=pal["border_panel"])
        for lbl in self.labels_texto:
            lbl.config(bg=pal["bg_panel"], fg=pal["fg_texto"])
            
        for f in self.frames_form_internos:
            f.config(bg=pal["bg_panel"])

        for entry in self.entries_widgets:
            entry.config(bg=pal["entry_bg"], fg=pal["entry_fg"], insertbackground=pal["entry_fg"], highlightbackground=pal["entry_border"])

        self.entry_proximo.config(bg=pal["bg_root"], fg=pal["fg_texto"])
        self.lbl_info_pie.config(bg=pal["bg_root"], fg=pal["fg_subtexto"])
        self.lbl_indicador_busqueda.config(bg=pal["bg_root"], fg=pal["fg_subtexto"])
        self.lbl_icon_buscar.config(bg=pal["bg_root"], fg=pal["fg_texto"])

        for i, card_info in enumerate(self.tarjetas_widgets):
            cfg = pal["kpis"][i]
            card_info["card"].config(bg=cfg["bg"], highlightbackground=cfg["border"])
            card_info["strip"].config(bg=cfg["border"])
            card_info["content"].config(bg=cfg["bg"])
            card_info["tit"].config(bg=cfg["bg"], fg=cfg["text"])
            card_info["val"].config(bg=cfg["bg"], fg=cfg["val"])
            card_info["sub"].config(bg=cfg["bg"], fg=cfg["sub"])

        self.style.configure("Treeview", background=pal["tree_bg"], foreground=pal["tree_fg"], fieldbackground=pal["tree_bg"])
        self.style.configure("Treeview.Heading", background=pal["tree_head_bg"], foreground=pal["tree_head_fg"])

    # --- 2. TARJETAS DE MÉTRICAS (KPIs) PASTEL ---
    def crear_panel_metricas(self):
        self.frame_kpis = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_kpis.pack(fill="x", padx=15, pady=(10, 5))

        for i in range(5):
            self.frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.lbl_val_total = self.crear_tarjeta(0, "TOTAL ACTIVOS", "0", "Bienes registrados")
        self.lbl_val_operativos = self.crear_tarjeta(1, "OPERATIVOS", "0", "En servicio activo")
        self.lbl_val_preventivos = self.crear_tarjeta(2, "PREVENTIVOS", "0", "Ciclo regular (+3M)")
        self.lbl_val_correctivos = self.crear_tarjeta(3, "CORRECTIVOS", "0", "Ajuste / Reparación")
        self.lbl_val_desincorporados = self.crear_tarjeta(4, "DESINCORPORADOS", "0", "Actas emitidas")

    def crear_tarjeta(self, col, titulo, valor_inic, subtitulo):
        card = tk.Frame(self.frame_kpis, highlightthickness=1, bd=0)
        card.grid(row=0, column=col, sticky="nsew", padx=3)

        left_strip = tk.Frame(card, width=5)
        left_strip.pack(side="left", fill="y")

        content = tk.Frame(card, padx=10, pady=6)
        content.pack(side="left", fill="both", expand=True)

        lbl_tit = tk.Label(content, text=titulo, font=("Segoe UI", 8, "bold"))
        lbl_tit.pack(anchor="w")

        lbl_val = tk.Label(content, text=valor_inic, font=("Segoe UI", 16, "bold"))
        lbl_val.pack(anchor="w")

        lbl_sub = tk.Label(content, text=subtitulo, font=("Segoe UI", 8, "bold"))
        lbl_sub.pack(anchor="w")

        self.tarjetas_widgets.append({
            "card": card, "strip": left_strip, "content": content,
            "tit": lbl_tit, "val": lbl_val, "sub": lbl_sub
        })

        return lbl_val

    def actualizar_metricas(self):
        total = len(self.bienes)
        operativos = 0
        preventivos = 0
        correctivos = 0
        
        desincorporados = 0
        if os.path.exists(ARCHIVO_BAJAS):
            try:
                with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                    bajas = json.load(f)
                    desincorporados = len(bajas)
            except Exception:
                desincorporados = 0

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

    # --- 3. FORMULARIO DE REGISTRO / EDICIÓN ---
    def crear_formulario(self):
        self.frame_form = tk.LabelFrame(
            self.root, text=" Registrar Activo y Gestión de Mantenimiento ",
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid"
        )
        self.frame_form.pack(fill="x", padx=15, pady=5)
        
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
        
        # Opciones fijas para la asignación
        opciones_asignacion = ["Departamento de Sistemas", "Administración", "Laboratorio 1", "Rectorado"]
        
        # Estilo personalizado para el Combobox (letras negras, fondo claro)
        estilo_combo = ttk.Style()
        estilo_combo.theme_use('clam')
        estilo_combo.configure(
            "TCombobox",
            fieldbackground="#f9f9f9",
            background="#ffffff",
            foreground="#000000"
        )
        estilo_combo.map(
            "TCombobox",
            fieldbackground=[("readonly", "#f9f9f9")],
            selectbackground=[("readonly", "#e0e0e0")],
            selectforeground=[("readonly", "#000000")]
        )

        self.combo_asignado = ttk.Combobox(
            self.frame_form, 
            values=opciones_asignacion, 
            font=("Segoe UI", 9), 
            state="readonly",
            style="TCombobox"
        )
        self.combo_asignado.grid(row=0, column=3, columnspan=3, padx=5, pady=4, sticky="ew")
        
        if opciones_asignacion:
            self.combo_asignado.current(0)
            
        frame_btn_form = tk.Frame(self.frame_form)
        frame_btn_form.grid(row=0, column=6, rowspan=4, padx=10, pady=4, sticky="ns")
        self.frames_form_internos.append(frame_btn_form)

        btn_agregar = tk.Button(frame_btn_form, text="Registrar Nuevo", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.agregar_bien, bd=0, padx=10, pady=4, cursor="hand2")
        btn_agregar.pack(fill="x", pady=2)
        
        btn_modificar = tk.Button(frame_btn_form, text="Guardar Cambios", bg="#059669", fg="white", font=("Segoe UI", 8, "bold"), command=self.actualizar_bien, bd=0, padx=10, pady=4, cursor="hand2")
        btn_modificar.pack(fill="x", pady=2)
        
        btn_limpiar = tk.Button(frame_btn_form, text="Limpiar Campos", bg="#6b7280", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_formulario, bd=0, padx=10, pady=3, cursor="hand2")
        btn_limpiar.pack(fill="x", pady=2)
        
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
        fecha_hoy = date.today().strftime("%d/%m/%Y")
        self.entry_fecha_mant = tk.Entry(self.frame_form, font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_fecha_mant.insert(0, fecha_hoy)
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

    # --- 4. PANEL DE BÚSQUEDA Y FILTRADO ---
    def crear_panel_busqueda(self):
        self.frame_busqueda = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_busqueda.pack(fill="x", padx=15, pady=(4, 2))
        
        self.lbl_icon_buscar = tk.Label(self.frame_busqueda, text="🔍 Buscar Activo:", font=("Segoe UI", 8, "bold"))
        self.lbl_icon_buscar.pack(side="left", padx=(0, 5))
        
        self.entry_buscar = tk.Entry(self.frame_busqueda, font=("Segoe UI", 9), relief="solid", bd=1, width=35)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        self.entries_widgets.append(self.entry_buscar)
        
        btn_limpiar_filtro = tk.Button(self.frame_busqueda, text="Limpiar Filtro", bg="#002B49", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_filtro_busqueda, bd=0, padx=8, pady=2, cursor="hand2")
        btn_limpiar_filtro.pack(side="left", padx=5)
        
        self.lbl_indicador_busqueda = tk.Label(self.frame_busqueda, text="(Doble clic en un registro para editar)", font=("Segoe UI", 8, "bold"))
        self.lbl_indicador_busqueda.pack(side="right")

    # --- 5. TABLA DE VISUALIZACIÓN ---
    def crear_tabla(self):
        self.frame_tabla = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_tabla.pack(fill="both", expand=True, padx=15, pady=4)
        
        columnas = ("id", "nombre", "asignado_a", "mantenimiento", "fecha_mant", "proximo_mant")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings")
        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción / Detalles del Bien")
        self.tabla.heading("asignado_a", text="Asignado a")
        self.tabla.heading("mantenimiento", text="Mantenimiento")
        self.tabla.heading("fecha_mant", text="Última Fecha")
        self.tabla.heading("proximo_mant", text="Próxima Fecha (Hábil)")
        
        self.tabla.column("id", width=85, anchor="center")
        self.tabla.column("nombre", width=350, anchor="w")
        self.tabla.column("asignado_a", width=170, anchor="w")
        self.tabla.column("mantenimiento", width=120, anchor="center")
        self.tabla.column("fecha_mant", width=105, anchor="center")
        self.tabla.column("proximo_mant", width=125, anchor="center")
        
        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        
        scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --- 6. BARRA DE ACCIONES INFERIOR ---
    def crear_panel_acciones(self):
        self.frame_acciones = tk.Frame(self.root, bg=self.PALETA["claro"]["bg_root"])
        self.frame_acciones.pack(fill="x", padx=15, pady=(4, 10))
        
        btn_cargar = tk.Button(self.frame_acciones, text="Cargar Seleccionado para Editar", bg="#D97706", fg="white", font=("Segoe UI", 8, "bold"), command=self.cargar_seleccion_para_editar, bd=0, padx=12, pady=5, cursor="hand2")
        btn_cargar.pack(side="left", padx=(0, 10))
        
        btn_eliminar = tk.Button(self.frame_acciones, text="Dar de Baja / Generar Acta PDF", bg="#DC2626", fg="white", font=("Segoe UI", 8, "bold"), command=self.dar_de_baja_bien, bd=0, padx=12, pady=5, cursor="hand2")
        btn_eliminar.pack(side="left", padx=(0, 10))

        btn_respaldo = tk.Button(self.frame_acciones, text="☁️ Respaldo en Nube (Próximamente)", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.respaldar_en_nube_placeholder, bd=0, padx=12, pady=5, cursor="hand2")
        btn_respaldo.pack(side="left")
        
        self.lbl_info_pie = tk.Label(self.frame_acciones, text="SIGAR V1.0 (Modo Local) — UNELLEZ", font=("Segoe UI", 8, "bold"))
        self.lbl_info_pie.pack(side="right", pady=3)

    # --- MANEJO DE PERSISTENCIA LOCAL (JSON) ---
    def cargar_datos_locales(self):
        if not os.path.exists(ARCHIVO_BIENES):
            return []
        try:
            with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudieron cargar los datos de {ARCHIVO_BIENES}:\n{e}")
            return []

    def guardar_datos_locales(self):
        try:
            with open(ARCHIVO_BIENES, "w", encoding="utf-8") as f:
                json.dump(self.bienes, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error de Escritura", f"No se pudo guardar la información en {ARCHIVO_BIENES}:\n{e}")
            return False

    def guardar_baja_local(self, registro_baja):
        bajas = []
        if os.path.exists(ARCHIVO_BAJAS):
            try:
                with open(ARCHIVO_BAJAS, "r", encoding="utf-8") as f:
                    bajas = json.load(f)
            except Exception:
                bajas = []
        bajas.append(registro_baja)
        try:
            with open(ARCHIVO_BAJAS, "w", encoding="utf-8") as f:
                json.dump(bajas, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Error en Registro de Baja", f"No se pudo registrar la baja en {ARCHIVO_BAJAS}:\n{e}")

    # --- MÉTODOS CRUD LOCALES ---
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
            "id": id_int, 
            "nombre": nombre_val, 
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else ""
        }
        
        self.bienes.append(nuevo_bien)
        if self.guardar_datos_locales():
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
            "id": id_int,
            "nombre": nombre_val,
            "asignado_a": asignado_val,
            "mantenimiento": mant_val,
            "fecha_mant": fecha_mant_val if mant_val != "No" else "N/A",
            "proximo_mant": proximo_val if mant_val != "No" else "N/A",
            "desc_mant": desc_mant_val if mant_val != "No" else ""
        }
        
        if self.guardar_datos_locales():
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
        
        if motivo is None:
            return
            
        motivo = motivo.strip()
        if not motivo:
            messagebox.showwarning("Motivo Requerido", "Debe ingresar una explicación para procesar la baja del activo.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Desincorporación", 
            f"¿Está seguro de desincorporar el activo ID {id_bien}?\n\nMotivo: {motivo}\n\nEsta acción removerá el bien del inventario activo y generará el acta PDF."
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
                "motivo_baja": motivo,
                "fecha_baja": fecha_hora_baja
            }
            
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            self.guardar_datos_locales()
            self.guardar_baja_local(registro_baja)
            
            archivo_generado = self.generar_acta_baja(registro_baja)
            
            self.actualizar_tabla()
            self.actualizar_metricas()
            self.limpiar_formulario()
            
            messagebox.showinfo(
                "Baja Procesada con Éxito", 
                f"El activo ID {id_bien} ha sido desincorporado.\n\n📄 Documento generado: {archivo_generado}"
            )

    def respaldar_en_nube_placeholder(self):
        # 1. Solicitar el correo electrónico mediante un cuadro de diálogo emergente
        correo_usuario = simpledialog.askstring(
            "Respaldo en la Nube - SIGAR",
            "Ingrese el correo electrónico autorizado para la cuenta de Google Drive / Nube:",
            parent=self.root
        )
        
        if correo_usuario is None:
            return  # Si el usuario cancela
            
        correo_usuario = correo_usuario.strip()
        if not correo_usuario or "@" not in correo_usuario:
            messagebox.showwarning("Correo Inválido", "Debe ingresar una dirección de correo electrónico válida.")
            return

        # 2. Verificar si existe el archivo de bienes localmente
        if not os.path.exists(ARCHIVO_BIENES):
            messagebox.showwarning("Sin Archivo", "No se encontró el archivo 'bienes.json' para respaldar.")
            return

        # 3. Validar si requests está disponible para hacer la petición al servidor o API en la nube
        if not HAS_REQUESTS:
            messagebox.showerror(
                "Librería Faltante", 
                "Para realizar la conexión con la nube, se requiere la librería 'requests'.\nInstálala ejecutando: pip install requests"
            )
            return

        # 4. Proceso de envío del respaldo a la nube
        try:
            # Cargamos el contenido del archivo JSON de bienes
            with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
                datos_bienes = json.load(f)

            payload = {
                "correo": correo_usuario,
                "fecha_respaldo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "total_bienes": len(datos_bienes),
                "bienes": datos_bienes
            }

            # Indicador visual de espera (opcional o mensaje directo)
            messagebox.showinfo("Conectando...", f"Preparando envío de respaldo para la cuenta:\n{correo_usuario}")

            # Petición POST hacia tu backend o API en la nube configurada
            response = requests.post(URL_RESPALDO_CLOUD, json=payload, timeout=15)

            if response.status_code == 200 or response.status_code == 201:
                messagebox.showinfo(
                    "Respaldo Exitoso", 
                    f"El respaldo de los activos se ha subido correctamente a la nube asociado al correo:\n{correo_usuario}"
                )
            else:
                messagebox.showerror(
                    "Error en la Nube", 
                    f"El servidor respondió con un código de error: {response.status_code}\nDetalle: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            messagebox.showerror(
                "Error de Conexión", 
                "No se pudo conectar con el servidor de respaldo en la nube.\nVerifique su conexión a internet.\n\nDetalle técnico: " + str(e)
            )
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar el respaldo:\n{e}")

    # --- GENERADOR DE REPORTES (PDF / TXT) ---
    def generar_acta_baja(self, registro):
        nombre_base = f"Acta_Baja_ID_{registro['id']}"
        
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
            c.drawString(50, height - 105, f"Fecha de Procesamiento: {registro['fecha_baja']}")
            c.drawString(50, height - 120, f"Código de Activo (ID): {registro['id']}")
            
            y = height - 155
            c.drawString(50, y, "DETALLES DEL EQUIPO / BIEN:")
            c.setFont("Helvetica", 10)
            c.drawString(70, y - 18, f"• Descripción / Equipo: {registro['nombre']}")
            c.drawString(70, y - 34, f"• Asignación Previa: {registro['asignado_a']}")
            c.drawString(70, y - 50, f"• Estado de Mantenimiento: {registro['mantenimiento']}")
            c.drawString(70, y - 66, f"• Último Mantenimiento: {registro['fecha_ultimo_mant']}")
            if registro['desc_mant']:
                c.drawString(70, y - 82, f"• Detalle Mantenimiento: {registro['desc_mant']}")
                
            y_motivo = y - 115
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_motivo, "JUSTIFICACIÓN / MOTIVO DE LA BAJA:")
            
            text_object = c.beginText(70, y_motivo - 18)
            text_object.setFont("Helvetica", 10)
            palabras = registro['motivo_baja'].split()
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
            c.drawCentredString(155, y_firma - 15, "Responsable del Bien / Unidad")
            c.drawCentredString(415, y_firma - 15, "Autorizado por (Unidad de Bienes UNELLEZ)")
            
            c.drawCentredString(width / 2, 40, "Documento oficial generado automáticamente por SIGAR V1.0")
            c.save()
            return archivo_pdf
        else:
            archivo_txt = f"{nombre_base}.txt"
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
Detalle Mantenimiento:   {registro['desc_mant']}

JUSTIFICACIÓN / MOTIVO DE LA BAJA:
----------------------------------------------------------------------
{registro['motivo_baja']}

======================================================================
FIRMAS AUTORIZADAS:


__________________________              __________________________
Responsable del Equipo                  Unidad de Bienes UNELLEZ
======================================================================
"""
            with open(archivo_txt, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return archivo_txt

    # --- FUNCIONES DE FILTRADO Y NAVEGACIÓN ---
    def filtrar_tabla(self, event=None):
        criterio = self.entry_buscar.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)
            
        for bien in self.bienes:
            id_str = str(bien["id"]).lower()
            nombre_str = str(bien["nombre"]).lower()
            asignado_str = str(bien.get("asignado_a", "")).lower()
            desc_str = str(bien.get("desc_mant", "")).lower()
            
            if criterio in id_str or criterio in nombre_str or criterio in asignado_str or criterio in desc_str:
                self.tabla.insert("", "end", values=(
                    bien["id"],
                    bien["nombre"],
                    bien.get("asignado_a", "N/A"),
                    bien.get("mantenimiento", "No"),
                    bien.get("fecha_mant", "N/A"),
                    bien.get("proximo_mant", "N/A")
                ))

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
            
            self.combo_asignado.set(bien.get("asignado_a", "Almacén / Stock"))
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

    def calcular_fecha_habil_3_meses(self, fecha_base):
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

    def al_cambiar_fecha(self, event=None):
        self.calcular_proxima_fecha_mantenimiento()

    def calcular_proxima_fecha_mantenimiento(self):
        fecha_str = self.entry_fecha_mant.get().strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(fecha_str, fmt).date()
                proxima_str = self.calcular_fecha_habil_3_meses(dt)
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
        for bien in getattr(self, 'bienes', []):
            self.tabla.insert("", "end", values=(
                bien["id"], 
                bien["nombre"], 
                bien.get("asignado_a", "N/A"),
                bien.get("mantenimiento", "No"),
                bien.get("fecha_mant", "N/A"),
                bien.get("proximo_mant", "N/A")
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()