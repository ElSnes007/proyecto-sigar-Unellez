# -*- coding: utf-8 -*-
"""
Módulo de Estilos, Tematización y Subformularios Técnicos - SIGART UNELLEZ VIPI
Soporte completo de modo Claro/Oscuro y lógica de diagnóstico técnico por tarjetas.
"""
import json
import os
import sys
import tkinter as tk
from tkinter import ttk

from utils import es_verdadero


def obtener_ruta_guardado():
    """Obtiene la ruta física del directorio donde corre la aplicación."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_base():
    """Obtiene la ruta base adecuada según modo compilado o script directo."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_icono(nombre_archivo):
    """Busca un ícono en la carpeta 'iconos'."""
    base_dir = obtener_ruta_guardado()
    ruta = os.path.join(base_dir, "iconos", nombre_archivo)
    if not os.path.exists(ruta):
        ruta_alt = os.path.join(obtener_ruta_base(), "iconos", nombre_archivo)
        if os.path.exists(ruta_alt):
            return ruta_alt
    return ruta


ARCHIVO_CONFIG_TEMA = "config_app.json"
ARCHIVO_PREFERENCIAS = os.path.join(obtener_ruta_guardado(), ARCHIVO_CONFIG_TEMA)

# Tipografías estándar
FONT_TITLE = ("Segoe UI", 11, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_KPI_VAL = ("Segoe UI", 26, "bold")
FONT_KPI_TIT = ("Segoe UI", 9, "bold")

PALETA = {
    "claro": {
        "bg_root": "#f8fafc",
        "bg_cintillo": "#1C2F46",
        "fg_cintillo": "#ffffff",
        "bg_panel": "#ffffff",
        "bg_sidebar": "#0f172a",
        "fg_sidebar": "#f8fafc",
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
            {"bg": "#f0fdf4", "active_bg": "#dcfce7", "border": "#86efac", "active_border": "#22c55e", "text": "#166534", "sub": "#15803d", "val": "#14532d"},
            {"bg": "#eff6ff", "active_bg": "#dbeafe", "border": "#93c5fd", "active_border": "#3b82f6", "text": "#1e40af", "sub": "#1d4ed8", "val": "#1e3a8a"},
            {"bg": "#fefce8", "active_bg": "#fef9c3", "border": "#fde047", "active_border": "#eab308", "text": "#a16207", "sub": "#854d0e", "val": "#713f12"},
            {"bg": "#fff7ed", "active_bg": "#ffedd5", "border": "#fdba74", "active_border": "#f97316", "text": "#c2410c", "sub": "#9a3412", "val": "#7c2d12"},
            {"bg": "#fef2f2", "active_bg": "#fee2e2", "border": "#fca5a5", "active_border": "#ef4444", "text": "#991b1b", "sub": "#b91c1c", "val": "#7f1d1d"}
        ]
    },
    "oscuro": {
        "bg_root": "#0f172a",
        "bg_cintillo": "#1C2F46",
        "fg_cintillo": "#f8fafc",
        "bg_panel": "#1e293b",
        "bg_sidebar": "#0b1324",
        "fg_sidebar": "#f8fafc",
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
            {"bg": "#064e3b", "active_bg": "#065f46", "border": "#059669", "active_border": "#34d399", "text": "#6ee7b7", "sub": "#a7f3d0", "val": "#ffffff"},
            {"bg": "#1e3a8a", "active_bg": "#1d4ed8", "border": "#3b82f6", "active_border": "#60a5fa", "text": "#93c5fd", "sub": "#bfdbfe", "val": "#ffffff"},
            {"bg": "#713f12", "active_bg": "#854d0e", "border": "#eab308", "active_border": "#facc15", "text": "#fde047", "sub": "#fef08a", "val": "#ffffff"},
            {"bg": "#7c2d12", "active_bg": "#9a3412", "border": "#ea580c", "active_border": "#fb923c", "text": "#ffedd5", "sub": "#fed7aa", "val": "#ffffff"},
            {"bg": "#7f1d1d", "active_bg": "#991b1b", "border": "#dc2626", "active_border": "#f87171", "text": "#fca5a5", "sub": "#fee2e2", "val": "#ffffff"}
        ]
    }
}


def obtener_estilo_kpi(modo_oscuro, indice, esta_activa):
    t = "oscuro" if modo_oscuro else "claro"
    cfg = PALETA[t]["kpis"][indice]
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
    if os.path.exists(ARCHIVO_PREFERENCIAS):
        try:
            with open(ARCHIVO_PREFERENCIAS, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modo", data.get("tema", "oscuro"))
        except Exception:
            return "oscuro"
    return "oscuro"


def guardar_preferencia_tema(modo):
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
        print(f"Error guardando tema: {e}")


def construir_subformulario_dinamico(frame_dinamico, tipo_activo, modo_oscuro, pal, lbl_titulo_sub, datos_previos=None):
    """
    Construye el subformulario dinámico de diagnóstico técnico.
    Para 'Computadora de escritorio', implementa el flujo de evaluación de CPU y componentes internos
    antes de la selección de periféricos.
    """
    for widget in frame_dinamico.winfo_children():
        widget.destroy()

    subform_widgets = {"_tipo": tipo_activo}
    datos = datos_previos or {}

    bg_p = pal["bg_panel"]
    fg_t = pal["fg_texto"]
    entry_bg = pal["entry_bg"]
    entry_fg = pal["entry_fg"]
    border_c = pal["border_panel"]

    frame_dinamico.config(bg=bg_p)

    def crear_tarjeta(parent, titulo_card):
        outer = tk.Frame(parent, bg=border_c, bd=1, relief="solid")
        inner = tk.Frame(outer, bg=bg_p, padx=8, pady=8)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        lbl_t = tk.Label(
            inner, text=titulo_card, font=("Segoe UI", 9, "bold"),
            fg="#38bdf8" if modo_oscuro else "#0284c7", bg=bg_p, anchor="w"
        )
        lbl_t.pack(fill="x", pady=(0, 6))
        return outer, inner

    # ================= COMPUTADORA DE ESCRITORIO =================
    if tipo_activo == "Computadora de escritorio":
        lbl_titulo_sub.config(text="🖥️ Diagnóstico de Computadora de Escritorio — Evaluación por Módulos")

        # Frame superior: Evaluación obligatoria del CPU
        card_cpu_outer, card_cpu_inner = crear_tarjeta(frame_dinamico, "1. Evaluación Obligatoria de Torre / CPU")
        card_cpu_outer.pack(fill="x", padx=8, pady=(4, 6))

        f_cpu_grid = tk.Frame(card_cpu_inner, bg=bg_p)
        f_cpu_grid.pack(fill="x")
        f_cpu_grid.columnconfigure(1, weight=1)
        f_cpu_grid.columnconfigure(3, weight=1)

        tk.Label(f_cpu_grid, text="Estado General del CPU:", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t).grid(row=0, column=0, sticky="w", padx=(0, 4))
        opciones_cpu = ["Operativo al 100%", "Requiere mantenimiento/limpieza", "Falla de fuente", "Problemas de disco/sistema", "Dañado"]
        combo_cpu = ttk.Combobox(f_cpu_grid, values=opciones_cpu, state="readonly", font=("Segoe UI", 8))
        combo_cpu.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        val_cpu_prev = datos.get("cpu", {}).get("estado", opciones_cpu[0])
        combo_cpu.set(val_cpu_prev if val_cpu_prev in opciones_cpu else opciones_cpu[0])

        tk.Label(f_cpu_grid, text="Detalle CPU / Falla:", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t).grid(row=0, column=2, sticky="w", padx=(0, 4))
        entry_cpu_det = tk.Entry(f_cpu_grid, font=("Segoe UI", 8), bg=entry_bg, fg=entry_fg, relief="solid", bd=1)
        entry_cpu_det.grid(row=0, column=3, sticky="ew")
        entry_cpu_det.insert(0, datos.get("cpu", {}).get("detalle", "En buen estado operativo"))

        # Componentes internos del CPU
        f_internos = tk.LabelFrame(card_cpu_inner, text=" Verificación de Componentes Básicos Internos ", font=("Segoe UI", 8, "bold"), bg=bg_p, fg="#38bdf8" if modo_oscuro else "#0284c7", padx=6, pady=4)
        f_internos.pack(fill="x", pady=(6, 2))
        for col_i in range(5):
            f_internos.columnconfigure(col_i, weight=1)

        componentes = [
            ("Placa Madre", "placa_madre"),
            ("Procesador", "procesador"),
            ("Memoria RAM", "memoria_ram"),
            ("Disco Duro / Almacenamiento", "disco_duro"),
            ("Fuente de Poder", "fuente_poder"),
        ]
        combos_internos = {}
        comp_prev = datos.get("cpu", {}).get("componentes_internos", {})

        for c_idx, (label_c, key_c) in enumerate(componentes):
            f_c = tk.Frame(f_internos, bg=bg_p)
            f_c.grid(row=0, column=c_idx, padx=4, sticky="ew")
            tk.Label(f_c, text=label_c, font=("Segoe UI", 7, "bold"), bg=bg_p, fg=fg_t).pack(anchor="w")
            c_box = ttk.Combobox(f_c, values=["Operativo", "Con fallas", "Dañado"], state="readonly", font=("Segoe UI", 8))
            c_box.pack(fill="x")
            val_actual = comp_prev.get(key_c, "Operativo")
            c_box.set(val_actual if val_actual in ["Operativo", "Con fallas", "Dañado"] else "Operativo")
            combos_internos[key_c] = c_box

        # Modalidad: Solo Case vs Combo Completo
        card_mod_outer, card_mod_inner = crear_tarjeta(frame_dinamico, "2. Modalidad de Entrega y Periféricos")
        card_mod_outer.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        f_switch = tk.Frame(card_mod_inner, bg=bg_p)
        f_switch.pack(fill="x", pady=(0, 6))

        tk.Label(f_switch, text="Seleccione la Modalidad:", font=("Segoe UI", 9, "bold"), bg=bg_p, fg=fg_t).pack(side="left", padx=(0, 10))

        incluye_p_inicial = es_verdadero(datos.get("incluye_perifericos", False))
        var_modalidad = tk.StringVar(value="combo" if incluye_p_inicial else "solo_case")

        frame_perifericos = tk.Frame(card_mod_inner, bg=bg_p)
        banner_solo_case = tk.Frame(card_mod_inner, bg="#064e3b" if modo_oscuro else "#ecfdf5", bd=1, relief="solid")
        lbl_solo_case = tk.Label(
            banner_solo_case,
            text="✔ Modalidad Chasis/Torre Individual: Este bien se registra estrictamente como Torre/CPU sin periféricos vinculados.",
            font=("Segoe UI", 8, "bold"),
            fg="#6ee7b7" if modo_oscuro else "#15803d",
            bg="#064e3b" if modo_oscuro else "#ecfdf5",
            pady=8
        )
        lbl_solo_case.pack(fill="x")

        # Tarjetas de periféricos
        perif_widgets = {}
        for c_idx in range(3):
            frame_perifericos.columnconfigure(c_idx, weight=1)

        lista_perif = [
            ("Monitor / Pantalla", "monitor", ["Operativo", "Rayones visibles", "Parpadeos intermitentes", "Líneas visibles", "Dañado"]),
            ("Teclado", "teclado", ["Operativo", "Falla de teclas", "Teclas trabadas/duras", "Dañado"]),
            ("Mouse", "mouse", ["Operativo", "Falla en sensor", "Falla de clic", "Dañado"]),
        ]

        for p_idx, (p_nom, p_key, p_opc) in enumerate(lista_perif):
            f_p_box = tk.LabelFrame(frame_perifericos, text=f" {p_nom} ", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t, padx=6, pady=4)
            f_p_box.grid(row=0, column=p_idx, sticky="nsew", padx=4)

            tk.Label(f_p_box, text="Estado:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            c_p = ttk.Combobox(f_p_box, values=p_opc, state="readonly", font=("Segoe UI", 8))
            c_p.pack(fill="x", pady=(0, 2))
            val_p = datos.get(p_key, {}).get("estado", p_opc[0])
            c_p.set(val_p if val_p in p_opc else p_opc[0])

            tk.Label(f_p_box, text="Observación:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            e_p = tk.Entry(f_p_box, font=("Segoe UI", 8), bg=entry_bg, fg=entry_fg, relief="solid", bd=1)
            e_p.pack(fill="x")
            e_p.insert(0, datos.get(p_key, {}).get("detalle", "En buen estado operativo"))

            perif_widgets[p_key] = {"combo_estado": c_p, "entry_obs": e_p}

        def actualizar_vista_modalidad():
            if var_modalidad.get() == "combo":
                banner_solo_case.pack_forget()
                frame_perifericos.pack(fill="x", expand=True, pady=4)
            else:
                frame_perifericos.pack_forget()
                banner_solo_case.pack(fill="x", pady=6)

        rb_solo = tk.Radiobutton(
            f_switch, text="Solo Chasis / Torre (Sin Periféricos)", variable=var_modalidad,
            value="solo_case", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t,
            selectcolor=bg_p, command=actualizar_vista_modalidad
        )
        rb_solo.pack(side="left", padx=8)

        rb_combo = tk.Radiobutton(
            f_switch, text="Combo Completo (CPU + Monitor, Teclado, Mouse)", variable=var_modalidad,
            value="combo", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t,
            selectcolor=bg_p, command=actualizar_vista_modalidad
        )
        rb_combo.pack(side="left", padx=8)

        actualizar_vista_modalidad()

        subform_widgets["var_modalidad"] = var_modalidad
        subform_widgets["combo_cpu"] = combo_cpu
        subform_widgets["entry_cpu_det"] = entry_cpu_det
        subform_widgets["combos_internos"] = combos_internos
        subform_widgets["perifericos"] = perif_widgets

    # ================= LAPTOP =================
    elif tipo_activo == "Laptop":
        lbl_titulo_sub.config(text="💻 Diagnóstico Técnico de Laptop — Componentes Integrados")
        componentes_laptop = [
            ("Pantalla", "pantalla", ["Operativa", "Rayones visibles", "Parpadeos intermitentes", "Líneas visibles", "Dañada"]),
            ("Teclado", "teclado", ["Operativo", "Falla de teclas específicas", "Teclas trabadas o duras", "Dañado"]),
            ("Mouse / Touchpad", "mouse_touchpad", ["Operativo", "Falla en el sensor", "Dañado"]),
            ("Carcasa / Puertos", "carcasa_puertos", ["Sin daños", "Puerto USB dañado", "Puerto HDMI dañado", "Puerto de carga dañado", "Bisagra rota"])
        ]
        for idx in range(4):
            frame_dinamico.columnconfigure(idx, weight=1)

        for idx, (label_txt, clave, opciones) in enumerate(componentes_laptop):
            card_outer, card_inner = crear_tarjeta(frame_dinamico, label_txt)
            card_outer.grid(row=0, column=idx, sticky="nsew", padx=4, pady=4)

            tk.Label(card_inner, text="Estado rápido:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            c_est = ttk.Combobox(card_inner, values=opciones, font=("Segoe UI", 8), state="readonly")
            c_est.pack(fill="x", pady=(0, 2))
            val_est = datos.get(clave, {}).get("estado", opciones[0])
            c_est.set(val_est if val_est in opciones else opciones[0])

            tk.Label(card_inner, text="Detalle / Observación:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            e_obs = tk.Entry(card_inner, font=("Segoe UI", 8), relief="solid", bd=1, bg=entry_bg, fg=entry_fg)
            e_obs.pack(fill="x")
            e_obs.insert(0, datos.get(clave, {}).get("detalle", "En buen estado operativo"))

            subform_widgets[clave] = {"combo_estado": c_est, "entry_obs": e_obs}

    # ================= IMPRESORA =================
    elif tipo_activo == "Impresora":
        lbl_titulo_sub.config(text="🖨️ Diagnóstico Funcional de Impresora")
        categorias = [
            ("1. Impresión Simple", "impresion", ["Operativa", "Atasco de papel", "Daño/desgaste de rodillo", "Falta de tinta/tóner", "Problema de drivers", "Desconfigurada"]),
            ("2. Función de Copiado", "copia", ["Operativa", "No copia", "El rodillo se traba", "Desconfigurada"]),
            ("3. Función de Escáner", "scanner", ["Operativa", "Cristal dañado", "Fallas en el sensor del escáner"])
        ]
        for idx in range(3):
            frame_dinamico.columnconfigure(idx, weight=1)

        for idx, (label_txt, clave, opciones) in enumerate(categorias):
            card_outer, card_inner = crear_tarjeta(frame_dinamico, label_txt)
            card_outer.grid(row=0, column=idx, sticky="nsew", padx=4, pady=4)

            tk.Label(card_inner, text="Estado funcional:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            c_est = ttk.Combobox(card_inner, values=opciones, font=("Segoe UI", 8), state="readonly")
            c_est.pack(fill="x", pady=(0, 2))
            val_est = datos.get(clave, {}).get("estado", opciones[0])
            c_est.set(val_est if val_est in opciones else opciones[0])

            tk.Label(card_inner, text="Detalle de anomalía:", font=("Segoe UI", 7), bg=bg_p, fg=fg_t).pack(anchor="w")
            e_obs = tk.Entry(card_inner, font=("Segoe UI", 8), relief="solid", bd=1, bg=entry_bg, fg=entry_fg)
            e_obs.pack(fill="x")
            e_obs.insert(0, datos.get(clave, {}).get("detalle", "En buen estado operativo"))

            subform_widgets[clave] = {"combo_estado": c_est, "entry_obs": e_obs}

    # ================= ROUTER / SWITCH =================
    elif tipo_activo in ["Router", "Switch de red"]:
        icono = "📡" if tipo_activo == "Router" else "🔀"
        lbl_titulo_sub.config(text=f"{icono} Diagnóstico y Conectividad — {tipo_activo}")

        card_outer, card_inner = crear_tarjeta(frame_dinamico, "Datos Técnicos y Estado de Operación")
        card_outer.pack(fill="x", padx=8, pady=4)

        f_grid = tk.Frame(card_inner, bg=bg_p)
        f_grid.pack(fill="x", pady=2)
        f_grid.columnconfigure(1, weight=1)
        f_grid.columnconfigure(3, weight=1)
        f_grid.columnconfigure(5, weight=1)

        tk.Label(f_grid, text="Marca:", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t).grid(row=0, column=0, padx=4, sticky="e")
        e_marca = tk.Entry(f_grid, font=("Segoe UI", 8), bg=entry_bg, fg=entry_fg, relief="solid", bd=1)
        e_marca.grid(row=0, column=1, padx=4, sticky="ew")
        e_marca.insert(0, datos.get("marca", ""))

        tk.Label(f_grid, text="Modelo:", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t).grid(row=0, column=2, padx=4, sticky="e")
        e_modelo = tk.Entry(f_grid, font=("Segoe UI", 8), bg=entry_bg, fg=entry_fg, relief="solid", bd=1)
        e_modelo.grid(row=0, column=3, padx=4, sticky="ew")
        e_modelo.insert(0, datos.get("modelo", ""))

        tk.Label(f_grid, text="Estado General:", font=("Segoe UI", 8, "bold"), bg=bg_p, fg=fg_t).grid(row=0, column=4, padx=4, sticky="e")
        c_est = ttk.Combobox(f_grid, values=["Funcional", "Funcional con fallas", "Dañado"], state="readonly", font=("Segoe UI", 8))
        c_est.grid(row=0, column=5, padx=4, sticky="ew")
        c_est.set(datos.get("estado_general", "Funcional"))

        f_cond = tk.Frame(card_inner, bg=bg_p)
        lbl_falla = tk.Label(f_cond, text="⚠️ Descripción detallada del fallo (Obligatorio en caso de falla):", font=("Segoe UI", 8, "bold"), fg="#dc2626", bg=bg_p)
        lbl_falla.pack(anchor="w", pady=(4, 1))
        e_falla = tk.Entry(f_cond, font=("Segoe UI", 8), bg=entry_bg, fg=entry_fg, relief="solid", bd=1)
        e_falla.pack(fill="x")
        e_falla.insert(0, datos.get("detalle_falla", ""))

        def toggle_falla(event=None):
            if c_est.get() in ["Funcional con fallas", "Dañado"]:
                f_cond.pack(fill="x", pady=4)
            else:
                f_cond.pack_forget()

        c_est.bind("<<ComboboxSelected>>", toggle_falla)
        toggle_falla()

        subform_widgets = {
            "_tipo": tipo_activo,
            "entry_marca": e_marca,
            "entry_modelo": e_modelo,
            "combo_estado": c_est,
            "entry_obs": e_falla,
            "frame_falla": f_cond
        }

    return subform_widgets


def obtener_datos_tecnicos_subform(subform_widgets, tipo_actual):
    """Extrae y estructura los datos técnicos cargados en el subformulario dinámico."""
    resultado = {"tipo": tipo_actual}

    if tipo_actual == "Computadora de escritorio":
        modalidad = subform_widgets["var_modalidad"].get()
        incluye_p = (modalidad == "combo")
        resultado["incluye_perifericos"] = incluye_p

        # CPU y componentes internos
        comp_internos = {}
        for k_comp, c_comp in subform_widgets["combos_internos"].items():
            comp_internos[k_comp] = c_comp.get()

        resultado["cpu"] = {
            "estado": subform_widgets["combo_cpu"].get(),
            "detalle": subform_widgets["entry_cpu_det"].get().strip(),
            "componentes_internos": comp_internos
        }

        # Periféricos si aplica
        if incluye_p:
            for p_k, p_w in subform_widgets["perifericos"].items():
                resultado[p_k] = {
                    "estado": p_w["combo_estado"].get(),
                    "detalle": p_w["entry_obs"].get().strip()
                }
        else:
            # Marcador limpio para modalidad solo case
            for p_k in ["monitor", "teclado", "mouse"]:
                resultado[p_k] = {"estado": "No Asignado (Solo Case)", "detalle": ""}

    elif tipo_actual in ["Router", "Switch de red"]:
        resultado["marca"] = subform_widgets["entry_marca"].get().strip()
        resultado["modelo"] = subform_widgets["entry_modelo"].get().strip()
        resultado["estado_general"] = subform_widgets["combo_estado"].get()
        resultado["detalle_falla"] = subform_widgets["entry_obs"].get().strip()

    else:
        for clave, w_item in subform_widgets.items():
            if isinstance(w_item, dict) and "combo_estado" in w_item:
                resultado[clave] = {
                    "estado": w_item["combo_estado"].get(),
                    "detalle": w_item["entry_obs"].get().strip()
                }
    return resultado


def aplicar_preset_operativo_subform(subform_widgets, tipo_actual):
    """Restablece los campos del subformulario a estado 100% operativo."""
    if tipo_actual == "Computadora de escritorio":
        if "combo_cpu" in subform_widgets:
            subform_widgets["combo_cpu"].set("Operativo al 100%")
        if "entry_cpu_det" in subform_widgets:
            subform_widgets["entry_cpu_det"].delete(0, tk.END)
            subform_widgets["entry_cpu_det"].insert(0, "En buen estado operativo")
        for c_comp in subform_widgets.get("combos_internos", {}).values():
            c_comp.set("Operativo")
        for p_w in subform_widgets.get("perifericos", {}).values():
            p_w["combo_estado"].set("Operativo")
            p_w["entry_obs"].delete(0, tk.END)
            p_w["entry_obs"].insert(0, "En buen estado operativo")

    elif tipo_actual in ["Router", "Switch de red"]:
        if "combo_estado" in subform_widgets:
            subform_widgets["combo_estado"].set("Funcional")
        if "entry_obs" in subform_widgets:
            subform_widgets["entry_obs"].delete(0, tk.END)
        if "frame_falla" in subform_widgets:
            subform_widgets["frame_falla"].pack_forget()
    else:
        for w_item in subform_widgets.values():
            if isinstance(w_item, dict) and "combo_estado" in w_item:
                vals = w_item["combo_estado"]["values"]
                if vals:
                    w_item["combo_estado"].set(vals[0])
                if "entry_obs" in w_item:
                    w_item["entry_obs"].delete(0, tk.END)
                    w_item["entry_obs"].insert(0, "En buen estado operativo")