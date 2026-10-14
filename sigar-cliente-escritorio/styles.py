# -*- coding: utf-8 -*-
import json
import os
import sys
import tkinter as tk
from tkinter import ttk

CONFIG_FILE = "config.json"


def obtener_ruta_guardado():
    """Obtiene la ruta física del ejecutable o script actual (fuera de sys._MEIPASS)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_base():
    """Obtiene la ruta base adecuada tanto en modo script como empaquetado con PyInstaller."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_icono(nombre_archivo):
    """
    Retorna la ruta absoluta de un ícono dentro de la carpeta 'iconos' 
    buscando prioritariamente en la carpeta del ejecutable/proyecto.
    """
    base_dir = obtener_ruta_guardado()
    ruta = os.path.join(base_dir, "iconos", nombre_archivo)
    
    # Si no existe en la ruta de guardado, buscar en la ruta base (_MEIPASS / temp)
    if not os.path.exists(ruta):
        ruta_alt = os.path.join(obtener_ruta_base(), "iconos", nombre_archivo)
        if os.path.exists(ruta_alt):
            return ruta_alt
            
    return ruta


ARCHIVO_CONFIG_TEMA = "config_app.json"
ARCHIVO_PREFERENCIAS = os.path.join(
    obtener_ruta_guardado(), ARCHIVO_CONFIG_TEMA
)

# Tipografías estándar del sistema SIGAR
FONT_TITLE = ("Segoe UI", 10, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_KPI_VAL = ("Segoe UI", 18, "bold")
FONT_KPI_TIT = ("Segoe UI", 8, "bold")

# Paleta de colores integral para Modo Claro y Modo Oscuro
PALETA = {
    "claro": {
        "bg_root": "#f8fafc",
        "bg_cintillo": "#002B49",
        "fg_cintillo": "#ffffff",
        "bg_panel": "#ffffff",
        "fg_texto": "#0f172a",
        "fg_subtexto": "#64748b",
        "border_panel": "#cbd5e1",
        "entry_bg": "#ffffff",
        "entry_fg": "#0f172a",
        "entry_border": "#94a3b8",
        "tree_bg": "#ffffff",
        "tree_fg": "#1e293b",
        "tree_head_bg": "#002B49",
        "tree_head_fg": "#ffffff",
        "kpis": [
            # 0: TOTAL ACTIVOS (Verde)
            {
                "bg": "#f0fdf4", "active_bg": "#dcfce7", "border": "#86efac", "active_border": "#22c55e",
                "text": "#166534", "sub": "#15803d", "val": "#14532d"
            },
            # 1: OPERATIVOS (Azul)
            {
                "bg": "#eff6ff", "active_bg": "#dbeafe", "border": "#93c5fd", "active_border": "#3b82f6",
                "text": "#1e40af", "sub": "#1d4ed8", "val": "#1e3a8a"
            },
            # 2: PREVENTIVOS (Amarillo)
            {
                "bg": "#fefce8", "active_bg": "#fef9c3", "border": "#fde047", "active_border": "#eab308",
                "text": "#a16207", "sub": "#854d0e", "val": "#713f12"
            },
            # 3: CORRECTIVOS (Naranja)
            {
                "bg": "#fff7ed", "active_bg": "#ffedd5", "border": "#fdba74", "active_border": "#f97316",
                "text": "#c2410c", "sub": "#9a3412", "val": "#7c2d12"
            },
            # 4: DESINCORPORADOS (Rojo)
            {
                "bg": "#fef2f2", "active_bg": "#fee2e2", "border": "#fca5a5", "active_border": "#ef4444",
                "text": "#991b1b", "sub": "#b91c1c", "val": "#7f1d1d"
            }
        ]
    },
    "oscuro": {
        "bg_root": "#0f172a",
        "bg_cintillo": "#001F35",
        "fg_cintillo": "#f8fafc",
        "bg_panel": "#1e293b",
        "fg_texto": "#f8fafc",
        "fg_subtexto": "#94a3b8",
        "border_panel": "#334155",
        "entry_bg": "#090d16",
        "entry_fg": "#f8fafc",
        "entry_border": "#475569",
        "tree_bg": "#1e293b",
        "tree_fg": "#f8fafc",
        "tree_head_bg": "#001f35",
        "tree_head_fg": "#ffffff",
        "kpis": [
            # 0: TOTAL ACTIVOS (Verde)
            {
                "bg": "#064e3b", "active_bg": "#065f46", "border": "#059669", "active_border": "#34d399",
                "text": "#6ee7b7", "sub": "#a7f3d0", "val": "#ffffff"
            },
            # 1: OPERATIVOS (Azul)
            {
                "bg": "#1e3a8a", "active_bg": "#1d4ed8", "border": "#3b82f6", "active_border": "#60a5fa",
                "text": "#93c5fd", "sub": "#bfdbfe", "val": "#ffffff"
            },
            # 2: PREVENTIVOS (Amarillo)
            {
                "bg": "#713f12", "active_bg": "#854d0e", "border": "#eab308", "active_border": "#facc15",
                "text": "#fde047", "sub": "#fef08a", "val": "#ffffff"
            },
            # 3: CORRECTIVOS (Naranja)
            {
                "bg": "#7c2d12", "active_bg": "#9a3412", "border": "#ea580c", "active_border": "#fb923c",
                "text": "#ffedd5", "sub": "#fed7aa", "val": "#ffffff"
            },
            # 4: DESINCORPORADOS (Rojo)
            {
                "bg": "#7f1d1d", "active_bg": "#991b1b", "border": "#dc2626", "active_border": "#f87171",
                "text": "#fca5a5", "sub": "#fee2e2", "val": "#ffffff"
            }
        ]
    }
}


def obtener_estilo_kpi(modo_oscuro, índice, esta_activa):
    """Retorna las propiedades visuales necesarias para renderizar una tarjeta KPI."""
    t = "oscuro" if modo_oscuro else "claro"
    cfg = PALETA[t]["kpis"][índice]

    bg_tarjeta = cfg["active_bg"] if esta_activa else cfg["bg"]
    borde_color = cfg["active_border"] if esta_activa else cfg["border"]

    return {
        "bg_tarjeta": bg_tarjeta,
        "borde_color": borde_color,
        "grosor_borde": 2 if esta_activa else 1,
        "color_acento": cfg["text"],
        "color_sub": cfg["sub"],
        "color_val": cfg["val"],
        "color_indicador": borde_color if esta_activa else cfg["text"],
    }


def cargar_preferencia_tema():
    """Carga el último tema seleccionado por el usuario desde el archivo de configuración local."""
    target_file = ARCHIVO_PREFERENCIAS if os.path.exists(ARCHIVO_PREFERENCIAS) else ARCHIVO_CONFIG_TEMA
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modo", data.get("tema", "oscuro"))
        except Exception:
            return "oscuro"
    return "oscuro"


def guardar_preferencia_tema(modo):
    """Guarda la preferencia de tema actual en el archivo de configuración."""
    try:
        data = {}
        if os.path.exists(ARCHIVO_PREFERENCIAS):
            try:
                with open(ARCHIVO_PREFERENCIAS, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["modo"] = modo
        data["tema"] = modo
        with open(ARCHIVO_PREFERENCIAS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error guardando preferencia de tema: {e}")


def hex_a_rgb(hex_str):
    """Convierte un color en formato hexadecimal (ej. '#0f172a') a una tupla RGB."""
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgb_a_hex(rgb_tuple):
    """Convierte una tupla RGB a un string en formato hexadecimal."""
    return "#{:02x}{:02x}{:02x}".format(*rgb_tuple)


def construir_subformulario_dinamico(frame_dinamico, tipo_activo, modo_oscuro, pal, lbl_titulo_sub, datos_previos=None):
    """Genera dinámicamente el subformulario de diagnóstico técnico según el tipo de activo."""
    for widget in frame_dinamico.winfo_children():
        widget.destroy()

    subform_widgets = {}
    datos = datos_previos or {}

    bg_panel_actual = pal["bg_panel"]
    fg_texto_actual = pal["fg_texto"]
    entry_bg_actual = pal["entry_bg"]
    entry_fg_actual = pal["entry_fg"]
    border_actual = pal["border_panel"]

    frame_dinamico.config(bg=bg_panel_actual)

    def crear_tarjeta_unificada(parent, titulo_card):
        outer = tk.Frame(parent, bg=border_actual, bd=1, relief="solid")
        inner = tk.Frame(outer, bg=bg_panel_actual, padx=6, pady=6)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        lbl_titulo = tk.Label(
            inner, text=titulo_card, 
            font=("Segoe UI", 8, "bold"), 
            fg="#38bdf8" if modo_oscuro else "#0284c7", 
            bg=bg_panel_actual, anchor="w"
        )
        lbl_titulo.pack(fill="x", pady=(0, 4))
        return outer, inner

    # LAPTOP & COMPUTADORA DE ESCRITORIO
    if tipo_activo in ["Laptop", "Computadora de escritorio"]:
        titulo_lbl = "💻 Diagnóstico de Laptop — Componentes y Periféricos" if tipo_activo == "Laptop" else "🖥️ Diagnóstico de Escritorio — Componentes y Periféricos"
        lbl_titulo_sub.config(text=titulo_lbl)
        
        if tipo_activo == "Laptop":
            componentes = [
                ("Pantalla", "pantalla", ["Operativa", "Rayones visibles", "Parpadeos intermitentes", "Líneas visibles", "Dañada"]),
                ("Teclado", "teclado", ["Operativo", "Falla de teclas específicas", "Teclas trabadas o duras", "Dañado"]),
                ("Mouse / Touchpad", "mouse_touchpad", ["Operativo", "Falla en el sensor", "Dañado"]),
                ("Carcasa / Puertos", "carcasa_puertos", ["Sin daños", "Puerto USB dañado", "Puerto HDMI dañado", "Puerto de carga dañado", "Bisagra rota"])
            ]
        else:
            componentes = [
                ("Monitor / Pantalla", "monitor", ["Operativo", "Rayones visibles", "Parpadeos intermitentes", "Líneas visibles", "Dañado"]),
                ("Teclado", "teclado", ["Operativo", "Falla de teclas específicas", "Teclas trabadas o duras", "Dañado"]),
                ("Mouse", "mouse", ["Operativo", "Falla en el sensor", "Falla de clic", "Dañado"]),
                ("CPU / Internos", "cpu", ["Operativo al 100%", "Falla de fuente", "Problemas de disco/sistema", "Requiere mantenimiento/limpieza", "Dañado"])
            ]

        for idx, (label_txt, clave, opciones) in enumerate(componentes):
            frame_dinamico.columnconfigure(idx, weight=1)
            
            card_outer, card_inner = crear_tarjeta_unificada(frame_dinamico, label_txt)
            card_outer.grid(row=0, column=idx, sticky="nsew", padx=3, pady=2)

            lbl_est = tk.Label(card_inner, text="Estado rápido:", font=("Segoe UI", 7), bg=bg_panel_actual, fg=fg_texto_actual)
            lbl_est.pack(anchor="w")
            combo_est = ttk.Combobox(card_inner, values=opciones, font=("Segoe UI", 8), state="readonly", style="TCombobox")
            combo_est.pack(fill="x", pady=(0, 2))
            
            val_est = datos.get(clave, {}).get("estado", opciones[0])
            combo_est.set(val_est if val_est in opciones else opciones[0])

            lbl_obs = tk.Label(card_inner, text="Detalle / Observación:", font=("Segoe UI", 7), bg=bg_panel_actual, fg=fg_texto_actual)
            lbl_obs.pack(anchor="w")
            entry_obs = tk.Entry(
                card_inner, font=("Segoe UI", 8), relief="solid", bd=1,
                bg=entry_bg_actual, fg=entry_fg_actual, insertbackground=fg_texto_actual,
                highlightbackground=pal["entry_border"], highlightthickness=1
            )
            entry_obs.pack(fill="x")
            val_det = datos.get(clave, {}).get("detalle", "")
            if val_det:
                entry_obs.insert(0, val_det)

            subform_widgets[clave] = {
                "card": card_outer, "lbl_estado": lbl_est, "lbl_detalle": lbl_obs,
                "combo_estado": combo_est, "entry_obs": entry_obs
            }

    # IMPRESORA
    elif tipo_activo == "Impresora":
        lbl_titulo_sub.config(text="🖨️ Diagnóstico Funcional de Impresora")
        categorias = [
            ("1. Impresión simple", "impresion", ["Operativa", "Atasco de papel", "Daño/desgaste de rodillo", "Falta de tinta/tóner", "Problema de drivers", "Desconfigurada"]),
            ("2. Funcionalidad de Copia", "copia", ["Operativa", "No copia", "El rodillo se traba", "Desconfigurada"]),
            ("3. Funcionalidad de Scanner", "scanner", ["Operativa", "Cristal dañado", "Fallas en el sensor del scanner"])
        ]

        for idx, (label_txt, clave, opciones) in enumerate(categorias):
            frame_dinamico.columnconfigure(idx, weight=1)
            
            card_outer, card_inner = crear_tarjeta_unificada(frame_dinamico, label_txt)
            card_outer.grid(row=0, column=idx, sticky="nsew", padx=4, pady=2)

            lbl_est = tk.Label(card_inner, text="Estado funcional:", font=("Segoe UI", 7), bg=bg_panel_actual, fg=fg_texto_actual)
            lbl_est.pack(anchor="w")
            combo_est = ttk.Combobox(card_inner, values=opciones, font=("Segoe UI", 8), state="readonly", style="TCombobox")
            combo_est.pack(fill="x", pady=(0, 2))

            val_est = datos.get(clave, {}).get("estado", opciones[0])
            combo_est.set(val_est if val_est in opciones else opciones[0])

            lbl_obs = tk.Label(card_inner, text="Detalle de anomalía:", font=("Segoe UI", 7), bg=bg_panel_actual, fg=fg_texto_actual)
            lbl_obs.pack(anchor="w")
            entry_obs = tk.Entry(
                card_inner, font=("Segoe UI", 8), relief="solid", bd=1,
                bg=entry_bg_actual, fg=entry_fg_actual, insertbackground=fg_texto_actual,
                highlightbackground=pal["entry_border"], highlightthickness=1
            )
            entry_obs.pack(fill="x")
            val_det = datos.get(clave, {}).get("detalle", "")
            if val_det:
                entry_obs.insert(0, val_det)

            subform_widgets[clave] = {
                "card": card_outer, "lbl_estado": lbl_est, "lbl_detalle": lbl_obs,
                "combo_estado": combo_est, "entry_obs": entry_obs
            }

    # ROUTER O SWITCH DE RED
    elif tipo_activo in ["Router", "Switch de red"]:
        icono = "📡" if tipo_activo == "Router" else "🔀"
        lbl_titulo_sub.config(text=f"{icono} Especificaciones y Diagnóstico de {tipo_activo}")

        card_outer, card_inner = crear_tarjeta_unificada(frame_dinamico, "Datos de Red y Operatividad")
        card_outer.pack(fill="x", padx=4, pady=2)

        f_top = tk.Frame(card_inner, bg=bg_panel_actual)
        f_top.pack(fill="x", pady=2)
        f_top.columnconfigure(1, weight=1)
        f_top.columnconfigure(3, weight=1)
        f_top.columnconfigure(5, weight=1)

        lbl_marca = tk.Label(f_top, text="Marca:", font=("Segoe UI", 8, "bold"), bg=bg_panel_actual, fg=fg_texto_actual)
        lbl_marca.grid(row=0, column=0, padx=(0, 4), sticky="e")
        entry_marca = tk.Entry(f_top, font=("Segoe UI", 8), relief="solid", bd=1, bg=entry_bg_actual, fg=entry_fg_actual, insertbackground=fg_texto_actual, highlightbackground=pal["entry_border"], highlightthickness=1)
        entry_marca.grid(row=0, column=1, padx=(0, 8), sticky="ew")
        if datos.get("marca"):
            entry_marca.insert(0, datos.get("marca"))

        lbl_modelo = tk.Label(f_top, text="Modelo:", font=("Segoe UI", 8, "bold"), bg=bg_panel_actual, fg=fg_texto_actual)
        lbl_modelo.grid(row=0, column=2, padx=(0, 4), sticky="e")
        entry_modelo = tk.Entry(f_top, font=("Segoe UI", 8), relief="solid", bd=1, bg=entry_bg_actual, fg=entry_fg_actual, insertbackground=fg_texto_actual, highlightbackground=pal["entry_border"], highlightthickness=1)
        entry_modelo.grid(row=0, column=3, padx=(0, 8), sticky="ew")
        if datos.get("modelo"):
            entry_modelo.insert(0, datos.get("modelo"))

        lbl_est = tk.Label(f_top, text="Estado general:", font=("Segoe UI", 8, "bold"), bg=bg_panel_actual, fg=fg_texto_actual)
        lbl_est.grid(row=0, column=4, padx=(0, 4), sticky="e")
        combo_est = ttk.Combobox(f_top, values=["Funcional", "Funcional con fallas", "Dañado"], font=("Segoe UI", 8), state="readonly", width=18, style="TCombobox")
        combo_est.grid(row=0, column=5, sticky="ew")
        
        val_est_gen = datos.get("estado_general", "Funcional")
        combo_est.set(val_est_gen if val_est_gen in ["Funcional", "Funcional con fallas", "Dañado"] else "Funcional")

        frame_condicional = tk.Frame(card_inner, bg=bg_panel_actual)
        lbl_falla = tk.Label(frame_condicional, text="⚠️ Descripción exacta del fallo (Obligatorio):", font=("Segoe UI", 8, "bold"), fg="#dc2626", bg=bg_panel_actual)
        lbl_falla.pack(anchor="w", pady=(4, 1))
        entry_falla = tk.Entry(frame_condicional, font=("Segoe UI", 8), relief="solid", bd=1, bg=entry_bg_actual, fg=entry_fg_actual, insertbackground=fg_texto_actual, highlightbackground=pal["entry_border"], highlightthickness=1)
        entry_falla.pack(fill="x")
        if datos.get("detalle_falla"):
            entry_falla.insert(0, datos.get("detalle_falla"))

        def actualizar_visibilidad_falla(event=None):
            estado_actual = combo_est.get()
            if estado_actual in ["Funcional con fallas", "Dañado"]:
                frame_condicional.pack(fill="x", pady=(4, 2))
            else:
                frame_condicional.pack_forget()

        combo_est.bind("<<ComboboxSelected>>", actualizar_visibilidad_falla)
        actualizar_visibilidad_falla()

        subform_widgets = {
            "tipo_equipo": tipo_activo,
            "card": card_outer,
            "f_top": f_top,
            "frame_condicional": frame_condicional,
            "lbl_marca": lbl_marca,
            "lbl_modelo": lbl_modelo,
            "lbl_estado": lbl_est,
            "lbl_detalle": lbl_falla,
            "entry_marca": entry_marca,
            "entry_modelo": entry_modelo,
            "combo_estado": combo_est,
            "entry_obs": entry_falla
        }

    return subform_widgets


def obtener_datos_tecnicos_subform(subform_widgets, tipo_actual):
    """Extrae los valores seleccionados del subformulario dinámico."""
    resultado = {"tipo": tipo_actual}
    if tipo_actual in ["Router", "Switch de red"]:
        w = subform_widgets
        resultado["marca"] = w["entry_marca"].get().strip() if "entry_marca" in w else ""
        resultado["modelo"] = w["entry_modelo"].get().strip() if "entry_modelo" in w else ""
        resultado["estado_general"] = w["combo_estado"].get() if "combo_estado" in w else "Funcional"
        resultado["detalle_falla"] = w["entry_obs"].get().strip() if "entry_obs" in w else ""
    else:
        for clave, w_item in subform_widgets.items():
            if isinstance(w_item, dict) and "combo_estado" in w_item:
                resultado[clave] = {
                    "estado": w_item["combo_estado"].get(),
                    "detalle": w_item["entry_obs"].get().strip()
                }
    return resultado


def aplicar_preset_operativo_subform(subform_widgets, tipo_actual):
    """Restablece los campos del subformulario a un estado operativo por defecto."""
    if tipo_actual in ["Router", "Switch de red"]:
        if "combo_estado" in subform_widgets:
            subform_widgets["combo_estado"].set("Funcional")
            if "frame_condicional" in subform_widgets:
                subform_widgets["frame_condicional"].pack_forget()
            if "entry_obs" in subform_widgets:
                subform_widgets["entry_obs"].delete(0, tk.END)
    else:
        for clave, w_item in subform_widgets.items():
            if isinstance(w_item, dict) and "combo_estado" in w_item:
                valores = w_item["combo_estado"]["values"]
                if valores:
                    w_item["combo_estado"].set(valores[0])
                if "entry_obs" in w_item:
                    w_item["entry_obs"].delete(0, tk.END)
                    w_item["entry_obs"].insert(0, "En buen estado operativo")


class CustomScrollbar(tk.Canvas):

    def __init__(
        self,
        parent,
        command=None,
        width=12,
        bg_color="#0f172a",
        thumb_color="#88BDFC",
        **kw,
    ):
        super().__init__(
            parent,
            width=width,
            highlightthickness=0,
            bd=0,
            bg=bg_color,
            **kw,
        )
        self.command = command
        self.thumb_color = thumb_color
        self.bg_color = bg_color
        self.width_bar = width

        self.first = 0.0
        self.last = 1.0

        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

    def set(self, first, last):
        self.first = float(first)
        self.last = float(last)
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if h <= 40:
            return

        arrow_size = 14
        margin = 3

        # Flecha Superior
        self.create_polygon(
            w / 2,
            margin,
            margin,
            margin + arrow_size,
            w - margin,
            margin + arrow_size,
            fill=self.thumb_color,
            outline="",
            tags="arrow_up",
        )

        # Flecha Inferior
        self.create_polygon(
            w / 2,
            h - margin,
            margin,
            h - margin - arrow_size,
            w - margin,
            h - margin - arrow_size,
            fill=self.thumb_color,
            outline="",
            tags="arrow_down",
        )

        track_top = arrow_size + margin + 2
        track_bottom = h - arrow_size - margin - 2
        track_height = track_bottom - track_top

        if track_height <= 0:
            return

        top_y = track_top + (self.first * track_height)
        bottom_y = track_top + (self.last * track_height)

        if (bottom_y - top_y) < 20:
            bottom_y = top_y + 20

        r = (w - 4) / 2
        x1, y1, x2, y2 = 2, top_y, w - 2, bottom_y

        self.create_oval(
            x1, y1, x2, y1 + 2 * r, fill=self.thumb_color, outline=""
        )
        self.create_oval(
            x1, y2 - 2 * r, x2, y2, fill=self.thumb_color, outline=""
        )
        self.create_rectangle(
            x1, y1 + r, x2, y2 - r, fill=self.thumb_color, outline=""
        )

    def _on_click(self, event):
        y = event.y
        h = self.winfo_height()
        arrow_size = 14
        if y < arrow_size + 5:
            if self.command:
                self.command("scroll", -1, "units")
        elif y > h - (arrow_size + 5):
            if self.command:
                self.command("scroll", 1, "units")
        else:
            self._on_drag(event)

    def _on_drag(self, event):
        h = self.winfo_height()
        arrow_size = 14
        margin = 3
        track_top = arrow_size + margin + 2
        track_bottom = h - arrow_size - margin - 2
        track_height = track_bottom - track_top

        if track_height > 0:
            fraction = (event.y - track_top) / track_height
            fraction = max(0.0, min(1.0, fraction))
            if self.command:
                self.command("moveto", fraction)