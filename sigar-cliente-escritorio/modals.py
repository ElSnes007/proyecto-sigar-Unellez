# -*- coding: utf-8 -*-
"""
Módulo de Ventanas Modales y Popups - SIGART UNELLEZ VIPI
Incluye:
- VentanaDesincorporados: Histórico y reincorporación de bajas.
- VentanaRespaldos: Copias de seguridad locales y en la nube.
- VentanaDiagnosticoTecnico: Evaluación modular previa por componentes.
- VentanaFichaTecnica: Consulta estética y detallada del activo.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from database import (
    cargar_bajas_locales,
    exportar_bd,
    exportar_respaldo_nube_bd,
    importar_bd,
    restaurar_baja_local,
)
from styles import (
    aplicar_preset_operativo_subform,
    construir_subformulario_dinamico,
    obtener_datos_tecnicos_subform,
)
from utils import es_verdadero


# =========================================================================
# MODAL: HISTÓRICO DE DESINCORPORADOS (BAJAS)
# =========================================================================
class VentanaDesincorporados(ctk.CTkToplevel):

    def __init__(self, parent, paleta, modo_oscuro):
        super().__init__(parent)
        self.parent = parent
        self.PALETA = paleta
        self.modo_oscuro = modo_oscuro

        self.title("Histórico de Activos Desincorporados (Bajas)")
        self.geometry("900x520")
        self.minsize(750, 400)

        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.bajas_data = []

        self.crear_encabezado()
        self.crear_tabla()
        self.crear_panel_acciones()
        self.aplicar_tema()
        self.cargar_datos()

    def crear_encabezado(self):
        self.frame_head = ctk.CTkFrame(self, fg_color="#002B49", corner_radius=0, height=48)
        self.frame_head.grid(row=0, column=0, sticky="ew")
        self.frame_head.pack_propagate(False)

        lbl_tit = ctk.CTkLabel(
            self.frame_head,
            text="❌ REGISTRO HISTÓRICO DE ACTIVOS DESINCORPORADOS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ffffff",
        )
        lbl_tit.pack(side="left", padx=15, pady=10)

    def crear_tabla(self):
        self.frame_tabla = ctk.CTkFrame(self, corner_radius=8)
        self.frame_tabla.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        cols = ("id", "nombre", "asignado_a", "motivo", "fecha_baja")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings", selectmode="browse")

        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción del Bien")
        self.tabla.heading("asignado_a", text="Última Asignación")
        self.tabla.heading("motivo", text="Justificación / Motivo de Baja")
        self.tabla.heading("fecha_baja", text="Fecha de Desincorporación")

        self.tabla.column("id", width=70, anchor="center")
        self.tabla.column("nombre", width=180, anchor="w")
        self.tabla.column("asignado_a", width=140, anchor="w")
        self.tabla.column("motivo", width=250, anchor="w")
        self.tabla.column("fecha_baja", width=130, anchor="center")

        sc = ctk.CTkScrollbar(self.frame_tabla, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sc.set)

        self.tabla.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        sc.grid(row=0, column=1, sticky="ns", pady=2)

    def crear_panel_acciones(self):
        f_bot = ctk.CTkFrame(self, fg_color="transparent")
        f_bot.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

        self.btn_reincorporar = ctk.CTkButton(
            f_bot,
            text="♻ Restaurar / Reincorporar Activo",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=32,
            command=self.reincorporar_bien,
        )
        self.btn_reincorporar.pack(side="left")

        ctk.CTkButton(
            f_bot,
            text="Cerrar",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#475569",
            hover_color="#334155",
            height=32,
            command=self.destroy,
        ).pack(side="right")

    def aplicar_tema(self):
        tree_bg = "#1e293b" if self.modo_oscuro else "#ffffff"
        tree_fg = "#f8fafc" if self.modo_oscuro else "#0f172a"
        head_bg = "#0f172a" if self.modo_oscuro else "#002B49"
        head_fg = "#ffffff"

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg, font=("Segoe UI", 9), rowheight=26, borderwidth=0)
        style.map("Treeview", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background=head_bg, foreground=head_fg, font=("Segoe UI", 9, "bold"), relief="flat")

        self.tabla.tag_configure("par", background=tree_bg, foreground=tree_fg)
        self.tabla.tag_configure("impar", background="#0f172a" if self.modo_oscuro else "#f8fafc", foreground=tree_fg)

    def cargar_datos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        self.bajas_data = cargar_bajas_locales()
        for i, b in enumerate(self.bajas_data):
            tag = "par" if i % 2 == 0 else "impar"
            self.tabla.insert(
                "", "end",
                values=(
                    b.get("id", "N/A"),
                    b.get("nombre", "N/A"),
                    b.get("asignado_a", "N/A"),
                    b.get("motivo_baja", "N/A"),
                    b.get("fecha_baja", "N/A"),
                ),
                tags=(tag,),
            )

    def reincorporar_bien(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Sin Selección", "Seleccione un activo desincorporado para reintegrar.", parent=self)
            return

        item = self.tabla.item(sel[0])
        id_bien = int(item["values"][0])

        if messagebox.askyesno("Confirmar", f"¿Desea reincorporar el activo ID {id_bien} al inventario activo?", parent=self):
            exito, msj = restaurar_baja_local(id_bien)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self)
                self.cargar_datos()
                if hasattr(self.parent, "recargar_datos_completos"):
                    self.parent.recargar_datos_completos()
            else:
                messagebox.showerror("Error", msj, parent=self)


# =========================================================================
# MODAL: CENTRO DE RESPALDOS
# =========================================================================
class VentanaRespaldos(ctk.CTkToplevel):

    def __init__(self, parent, paleta, modo_oscuro, obtener_bienes_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.PALETA = paleta
        self.modo_oscuro = modo_oscuro
        self.obtener_bienes_callback = obtener_bienes_callback

        self.title("Centro de Respaldos de Información")
        self.geometry("520x400")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.crear_encabezado()
        self.crear_cuerpo()

    def crear_encabezado(self):
        frame_head = ctk.CTkFrame(self, fg_color="#002B49", corner_radius=0, height=48)
        frame_head.grid(row=0, column=0, sticky="ew")
        frame_head.pack_propagate(False)

        lbl_tit = ctk.CTkLabel(
            frame_head,
            text="☁ CENTRO DE RESPALDOS Y MIGRACIÓN DE DATOS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ffffff",
        )
        lbl_tit.pack(side="left", padx=15, pady=10)

    def crear_cuerpo(self):
        f_mid = ctk.CTkFrame(self, corner_radius=10)
        f_mid.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        f_mid.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            f_mid,
            text="Seleccione la operación de respaldo que desea realizar:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Exportar Local
        ctk.CTkButton(
            f_mid,
            text="📤 Exportar Respaldo Local (JSON)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            command=self.exportar_respaldo,
        ).pack(fill="x", padx=15, pady=5)

        # Respaldo en la Nube
        ctk.CTkButton(
            f_mid,
            text="☁ Sincronizar Respaldo en la Nube (Google Sheets)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0d9488",
            hover_color="#0f766e",
            height=32,
            command=lambda: exportar_respaldo_nube_bd(parent_window=self),
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkFrame(f_mid, height=1, fg_color="#334155").pack(fill="x", padx=15, pady=10)

        # Importar Local
        ctk.CTkButton(
            f_mid,
            text="📥 Importar Base de Datos Externa",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=32,
            command=self.importar_respaldo,
        ).pack(fill="x", padx=15, pady=5)

    def exportar_respaldo(self):
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Respaldo JSON",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")],
        )
        if ruta:
            exito, msj = exportar_bd(ruta)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self)
            else:
                messagebox.showerror("Error", msj, parent=self)

    def importar_respaldo(self):
        if not messagebox.askyesno("Confirmar", "ADVERTENCIA: Importar un respaldo reemplazará los datos actuales.\n¿Desea continuar?", parent=self):
            return
        ruta = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar Respaldo JSON",
            filetypes=[("Archivos JSON", "*.json")],
        )
        if ruta:
            exito, msj = importar_bd(ruta)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self)
                if hasattr(self.parent, "recargar_datos_completos"):
                    self.parent.recargar_datos_completos()
                self.destroy()
            else:
                messagebox.showerror("Error", msj, parent=self)


# =========================================================================
# MODAL: EVALUACIÓN / DIAGNÓSTICO TÉCNICO
# =========================================================================
class VentanaDiagnosticoTecnico:
    """Ventana modal para diagnóstico técnico con flujo de CPU y periféricos."""

    def __init__(self, parent, tipo_activo, paleta, modo_oscuro, datos_previos=None, guardar_callback=None):
        self.parent = parent
        self.tipo_activo = tipo_activo
        self.paleta = paleta
        self.modo_oscuro = modo_oscuro
        self.guardar_callback = guardar_callback
        self.datos_previos = dict(datos_previos) if datos_previos else {}

        t = "oscuro" if modo_oscuro else "claro"
        pal = paleta[t]

        self.modal = tk.Toplevel(parent)
        self.modal.title(f"Diagnóstico Técnico Especializado — {tipo_activo}")
        self.modal.geometry("780x480")
        self.modal.minsize(720, 420)
        self.modal.resizable(True, True)
        self.modal.configure(bg=pal["bg_root"])
        self.modal.transient(parent)
        self.modal.grab_set()

        # Centrar en pantalla
        self.modal.update_idletasks()
        w, h = self.modal.winfo_width(), self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (w // 2)
        y = (self.modal.winfo_screenheight() // 2) - (h // 2)
        self.modal.geometry(f"{w}x{h}+{x}+{y}")

        f_top = tk.Frame(self.modal, bg=pal["bg_root"])
        f_top.pack(fill="x", padx=15, pady=(10, 4))

        self.lbl_titulo_sub = tk.Label(
            f_top, text="", font=("Segoe UI", 10, "bold"),
            fg="#38bdf8" if modo_oscuro else "#0284c7", bg=pal["bg_root"]
        )
        self.lbl_titulo_sub.pack(side="left")

        tk.Button(
            f_top, text="⚡ Todo Operativo al 100%", font=("Segoe UI", 8, "bold"),
            bg="#0284c7", fg="white", bd=0, padx=12, pady=5, cursor="hand2", command=self.aplicar_preset
        ).pack(side="right")

        self.frame_dinamico = tk.Frame(self.modal, bg=pal["bg_panel"], highlightthickness=1, highlightbackground=pal["border_panel"])
        self.frame_dinamico.pack(fill="both", expand=True, padx=15, pady=6)

        self.subform_widgets = construir_subformulario_dinamico(
            self.frame_dinamico,
            tipo_activo,
            modo_oscuro,
            pal,
            self.lbl_titulo_sub,
            self.datos_previos
        )

        f_bot = tk.Frame(self.modal, bg=pal["bg_root"])
        f_bot.pack(fill="x", padx=15, pady=(4, 10))

        tk.Button(
            f_bot, text="Guardar Diagnóstico", bg="#059669", fg="white", font=("Segoe UI", 9, "bold"),
            bd=0, padx=16, pady=6, cursor="hand2", command=self.guardar_y_cerrar
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            f_bot, text="Cancelar", bg="#64748b", fg="white", font=("Segoe UI", 9, "bold"),
            bd=0, padx=12, pady=6, cursor="hand2", command=self.modal.destroy
        ).pack(side="right")

    def aplicar_preset(self):
        aplicar_preset_operativo_subform(self.subform_widgets, self.tipo_activo)

    def guardar_y_cerrar(self):
        datos = obtener_datos_tecnicos_subform(self.subform_widgets, self.tipo_activo)
        if self.guardar_callback:
            self.guardar_callback(datos)
        self.modal.destroy()


# =========================================================================
# MODAL: CONSULTA DE FICHA TÉCNICA
# =========================================================================
class VentanaFichaTecnica:
    """Ventana modal estética para consultar la ficha técnica y diagnóstico del activo."""

    def __init__(self, parent, bien, modo_oscuro, paleta):
        self.parent = parent
        self.bien = bien
        self.modo_oscuro = modo_oscuro
        self.pal = paleta["oscuro" if modo_oscuro else "claro"]

        self.modal = tk.Toplevel(parent)
        self.modal.title(f"Ficha Técnica / Diagnóstico — Activo ID #{bien.get('id', 'N/A')}")
        self.modal.geometry("560x560")
        self.modal.minsize(480, 420)
        self.modal.configure(bg=self.pal["bg_root"])
        self.modal.transient(parent)
        self.modal.grab_set()

        self.modal.update_idletasks()
        w, h = self.modal.winfo_width(), self.modal.winfo_height()
        x = (self.modal.winfo_screenwidth() // 2) - (w // 2)
        y = (self.modal.winfo_screenheight() // 2) - (h // 2)
        self.modal.geometry(f"{w}x{h}+{x}+{y}")

        self.construir_interfaz()

    def construir_interfaz(self):
        pal = self.pal
        tipo = self.bien.get("nombre", "")
        id_bien = self.bien.get("id", "N/A")
        detalles = self.bien.get("detalles_tecnicos") or self.bien.get("perifericos") or {}

        # Cabecera
        f_head = tk.Frame(self.modal, bg=pal["bg_cintillo"], padx=15, pady=10)
        f_head.pack(fill="x")
        tk.Label(
            f_head, text=f"ACTIVO #{id_bien} — {tipo.upper()}",
            font=("Segoe UI", 11, "bold"), fg="#ffffff", bg=pal["bg_cintillo"]
        ).pack(anchor="w")
        tk.Label(
            f_head, text=f"Asignado a: {self.bien.get('asignado_a', 'N/A')} | Mant: {self.bien.get('mantenimiento', 'No')}",
            font=("Segoe UI", 9), fg="#93c5fd", bg=pal["bg_cintillo"]
        ).pack(anchor="w")

        # Contenedor con Scrollbar
        f_body = tk.Frame(self.modal, bg=pal["bg_root"])
        f_body.pack(fill="both", expand=True, padx=15, pady=10)

        canvas = tk.Canvas(f_body, bg=pal["bg_panel"], highlightthickness=1, highlightbackground=pal["border_panel"])
        sc = ttk.Scrollbar(f_body, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=pal["bg_panel"])

        w_id = canvas.create_window((0, 0), window=sf, anchor="nw")

        def on_conf(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(w_id, width=canvas.winfo_width())

        canvas.bind("<Configure>", on_conf)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=sc.set)

        canvas.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        # Observación previa
        obs_gen = self.bien.get("desc_mant", "").strip()
        if obs_gen:
            f_obs = tk.LabelFrame(sf, text=" Observación de Registro ", font=("Segoe UI", 8, "bold"), fg="#38bdf8" if self.modo_oscuro else "#0284c7", bg=pal["bg_panel"], padx=8, pady=6)
            f_obs.pack(fill="x", padx=10, pady=8)
            tk.Label(f_obs, text=obs_gen, font=("Segoe UI", 9, "italic"), bg=pal["bg_panel"], fg=pal["fg_texto"], justify="left", wraplength=460).pack(anchor="w")

        # Desglose Técnico
        if not detalles:
            tk.Label(sf, text="Este activo no posee detalles técnicos registrados.", font=("Segoe UI", 9), bg=pal["bg_panel"], fg=pal["fg_subtexto"]).pack(pady=30)
        else:
            if tipo == "Computadora de escritorio":
                incluye_p = es_verdadero(detalles.get("incluye_perifericos", False))
                
                # Banner de modalidad
                f_mod = tk.Frame(sf, bg="#064e3b" if incluye_p else "#451a03", padx=8, pady=6)
                f_mod.pack(fill="x", padx=10, pady=6)
                txt_mod = "✔ Combo Completo: Incluye Torre/CPU y Periféricos Vinculados" if incluye_p else "ℹ Chasis Individual: Registrado estrictamente como Torre/CPU (Sin Periféricos)"
                col_mod = "#6ee7b7" if incluye_p else "#fde047"
                tk.Label(f_mod, text=txt_mod, font=("Segoe UI", 9, "bold"), fg=col_mod, bg="#064e3b" if incluye_p else "#451a03").pack(anchor="w")

                # CPU y Componentes
                cpu_dat = detalles.get("cpu", {})
                self.crear_item_detalle(sf, "Torre / CPU Principal", cpu_dat.get("estado", "Operativo"), cpu_dat.get("detalle", ""))

                comp_int = cpu_dat.get("componentes_internos", {})
                if comp_int:
                    f_int = tk.Frame(sf, bg=pal["bg_panel"], padx=10, pady=4)
                    f_int.pack(fill="x", padx=10)
                    tk.Label(f_int, text="Componentes Internos:", font=("Segoe UI", 8, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"]).pack(anchor="w")
                    for k_c, v_c in comp_int.items():
                        c_col = "#16a34a" if "Operativ" in v_c else "#dc2626"
                        tk.Label(f_int, text=f"  • {k_c.replace('_', ' ').capitalize()}: {v_c}", font=("Segoe UI", 8), fg=c_col, bg=pal["bg_panel"]).pack(anchor="w")

                if incluye_p:
                    for k_p, lbl_p in [("monitor", "Monitor / Pantalla"), ("teclado", "Teclado"), ("mouse", "Mouse")]:
                        dat_p = detalles.get(k_p, {})
                        self.crear_item_detalle(sf, lbl_p, dat_p.get("estado", "Operativo"), dat_p.get("detalle", ""))

            elif tipo == "Laptop":
                for k_l, lbl_l in [("pantalla", "Pantalla"), ("teclado", "Teclado"), ("mouse_touchpad", "Mouse/Touchpad"), ("carcasa_puertos", "Carcasa y Puertos")]:
                    dat_l = detalles.get(k_l, {})
                    self.crear_item_detalle(sf, lbl_l, dat_l.get("estado", "Operativo"), dat_l.get("detalle", ""))

            elif tipo == "Impresora":
                for k_i, lbl_i in [("impresion", "Impresión Simple"), ("copia", "Función Copiado"), ("scanner", "Función Escáner")]:
                    dat_i = detalles.get(k_i, {})
                    self.crear_item_detalle(sf, lbl_i, dat_i.get("estado", "Operativa"), dat_i.get("detalle", ""))

            elif tipo in ["Router", "Switch de red"]:
                f_r = tk.Frame(sf, bg=pal["bg_panel"], padx=10, pady=8)
                f_r.pack(fill="x", padx=10)
                tk.Label(f_r, text=f"• Marca: {detalles.get('marca', 'N/A')}", font=("Segoe UI", 9, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"]).pack(anchor="w")
                tk.Label(f_r, text=f"• Modelo: {detalles.get('modelo', 'N/A')}", font=("Segoe UI", 9, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"]).pack(anchor="w")
                est_r = detalles.get("estado_general", "Funcional")
                col_r = "#16a34a" if est_r == "Funcional" else ("#ca8a04" if est_r == "Funcional con fallas" else "#dc2626")
                tk.Label(f_r, text=f"• Estado General: {est_r}", font=("Segoe UI", 9, "bold"), fg=col_r, bg=pal["bg_panel"]).pack(anchor="w", pady=2)
                if detalles.get("detalle_falla"):
                    tk.Label(f_r, text=f"• Falla: {detalles.get('detalle_falla')}", font=("Segoe UI", 8, "italic"), fg="#dc2626", bg=pal["bg_panel"]).pack(anchor="w")

        # Botón Cerrar
        f_bot = tk.Frame(self.modal, bg=pal["bg_root"])
        f_bot.pack(fill="x", pady=(0, 10))
        tk.Button(
            f_bot, text="Cerrar", font=("Segoe UI", 9, "bold"), bg="#002B49", fg="white",
            bd=0, padx=20, pady=6, cursor="hand2", command=self.modal.destroy
        ).pack()

    def crear_item_detalle(self, parent, titulo, estado, detalle):
        pal = self.pal
        f = tk.Frame(parent, bg=pal["bg_panel"], padx=10, pady=4)
        f.pack(fill="x", padx=10, pady=2)

        header = tk.Frame(f, bg=pal["bg_panel"])
        header.pack(fill="x")
        tk.Label(header, text=f"• {titulo}:", font=("Segoe UI", 9, "bold"), fg=pal["fg_texto"], bg=pal["bg_panel"]).pack(side="left")

        color_est = "#16a34a" if ("Operativ" in estado or "Sin daños" in estado) else ("#dc2626" if "Dañad" in estado else "#ca8a04")
        tk.Label(header, text=f" [{estado}]", font=("Segoe UI", 9, "bold"), fg=color_est, bg=pal["bg_panel"]).pack(side="left", padx=4)

        if detalle:
            tk.Label(f, text=f"  Obs: {detalle}", font=("Segoe UI", 8, "italic"), fg=pal["fg_subtexto"], bg=pal["bg_panel"]).pack(anchor="w", padx=14)