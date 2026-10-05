# -*- coding: utf-8 -*-
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


class VentanaDesincorporados(ctk.CTkToplevel):

    def __init__(self, parent, paleta, modo_oscuro):
        super().__init__(parent)
        self.parent = parent
        self.PALETA = paleta
        self.modo_oscuro = modo_oscuro

        self.title("Histórico de Activos Desincorporados (Bajas)")
        self.geometry("900x520")
        self.minsize(750, 400)

        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Encabezado
        self.rowconfigure(1, weight=1)  # Tabla
        self.rowconfigure(2, weight=0)  # Acciones / Leyenda

        self.bajas_data = []

        self.crear_encabezado()
        self.crear_tabla()
        self.crear_panel_acciones()
        self.aplicar_tema()
        self.cargar_datos()

    def crear_encabezado(self):
        self.frame_head = ctk.CTkFrame(self, fg_color="#002B49", corner_radius=0, height=50)
        self.frame_head.grid(row=0, column=0, sticky="ew")
        self.frame_head.pack_propagate(False)

        lbl_tit = ctk.CTkLabel(
            self.frame_head,
            text="❌ Registro de Bienes Desincorporados",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#ffffff",
        )
        lbl_tit.pack(side="left", padx=15, pady=10)

    def crear_tabla(self):
        self.frame_tabla = ctk.CTkFrame(self, corner_radius=8)
        self.frame_tabla.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        cols = ("id", "nombre", "asignado_a", "motivo", "fecha_baja")
        self.tabla = ttk.Treeview(
            self.frame_tabla, columns=cols, show="headings", selectmode="browse"
        )

        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción del Bien")
        self.tabla.heading("asignado_a", text="Última Asignación")
        self.tabla.heading("motivo", text="Justificación / Motivo de Baja")
        self.tabla.heading("fecha_baja", text="Fecha de Desincorporación")

        self.tabla.column("id", width=70, anchor="center", stretch=False)
        self.tabla.column("nombre", width=200, anchor="w", stretch=True)
        self.tabla.column("asignado_a", width=140, anchor="w", stretch=True)
        self.tabla.column("motivo", width=230, anchor="w", stretch=True)
        self.tabla.column("fecha_baja", width=130, anchor="center", stretch=False)

        scrollbar = ctk.CTkScrollbar(self.frame_tabla, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        self.tabla.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=2)

    def crear_panel_acciones(self):
        self.frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acciones.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

        self.btn_reincorporar = ctk.CTkButton(
            self.frame_acciones,
            text="♻ Restaurar / Reincorporar Activo",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=32,
            command=self.reincorporar_bien,
        )
        self.btn_reincorporar.pack(side="left")

        self.btn_cerrar = ctk.CTkButton(
            self.frame_acciones,
            text="Cerrar",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#475569",
            hover_color="#334155",
            height=32,
            command=self.destroy,
        )
        self.btn_cerrar.pack(side="right")

    def aplicar_tema(self):
        tree_bg = "#1e293b" if self.modo_oscuro else "#ffffff"
        tree_fg = "#f8fafc" if self.modo_oscuro else "#0f172a"
        head_bg = "#0f172a" if self.modo_oscuro else "#e2e8f0"
        head_fg = "#38bdf8" if self.modo_oscuro else "#0284c7"
        tree_bg_odd = "#0f172a" if self.modo_oscuro else "#f8fafc"

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=tree_bg,
            foreground=tree_fg,
            fieldbackground=tree_bg,
            font=("Segoe UI", 9),
            rowheight=28,
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

        self.tabla.tag_configure("par", background=tree_bg, foreground=tree_fg)
        self.tabla.tag_configure("impar", background=tree_bg_odd, foreground=tree_fg)

    def cargar_datos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        self.bajas_data = cargar_bajas_locales()
        for i, b in enumerate(self.bajas_data):
            tag = "par" if i % 2 == 0 else "impar"
            self.tabla.insert(
                "",
                "end",
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
        selection = self.tabla.selection()
        if not selection:
            messagebox.showwarning(
                "Sin Selección",
                "Seleccione un activo desincorporado para restaurar al inventario principal.",
                parent=self,
            )
            return

        item = self.tabla.item(selection[0])
        id_bien = int(item["values"][0])

        confirm = messagebox.askyesno(
            "Confirmar Restauración",
            f"¿Desea reincorporar el activo ID {id_bien} al inventario activo?",
            parent=self,
        )
        if confirm:
            exito, msj = restaurar_baja_local(id_bien)
            if exito:
                messagebox.showinfo("Éxito", msj, parent=self)
                self.cargar_datos()
                if hasattr(self.parent, "bienes"):
                    from database import cargar_datos_locales

                    self.parent.bienes = cargar_datos_locales()
                    if hasattr(self.parent, "actualizar_tabla"):
                        self.parent.actualizar_tabla()
                    if hasattr(self.parent, "actualizar_metricas"):
                        self.parent.actualizar_metricas()
            else:
                messagebox.showerror("Error", msj, parent=self)


class VentanaRespaldos(ctk.CTkToplevel):

    def __init__(self, parent, paleta, modo_oscuro, obtener_bienes_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.PALETA = paleta
        self.modo_oscuro = modo_oscuro
        self.obtener_bienes_callback = obtener_bienes_callback

        self.title("Centro de Respaldos y Migración de Base de Datos")
        self.geometry("520x420")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Cabecera
        self.rowconfigure(1, weight=1)  # Cuerpo de Opciones

        self.crear_encabezado()
        self.crear_cuerpo()

    def crear_encabezado(self):
        self.frame_head = ctk.CTkFrame(self, fg_color="#002B49", corner_radius=0, height=50)
        self.frame_head.grid(row=0, column=0, sticky="ew")
        self.frame_head.pack_propagate(False)

        lbl_tit = ctk.CTkLabel(
            self.frame_head,
            text="☁ Centro de Respaldos de Información",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#ffffff",
        )
        lbl_tit.pack(side="left", padx=15, pady=10)

    def crear_cuerpo(self):
        self.frame_content = ctk.CTkFrame(self, corner_radius=10)
        self.frame_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.frame_content.columnconfigure(0, weight=1)

        lbl_instruccion = ctk.CTkLabel(
            self.frame_content,
            text="Gestione las copias de seguridad locales y en la nube del sistema SIGAR:",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        lbl_instruccion.pack(anchor="w", padx=15, pady=(15, 10))

        # Sección Exportar Local
        frame_exp = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        frame_exp.pack(fill="x", padx=15, pady=4)

        lbl_exp_desc = ctk.CTkLabel(
            frame_exp,
            text="• Generar una copia de respaldo local (JSON):",
            font=ctk.CTkFont(size=10),
        )
        lbl_exp_desc.pack(anchor="w", pady=(0, 2))

        btn_exportar = ctk.CTkButton(
            frame_exp,
            text="📤 Exportar Respaldo Local",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=30,
            command=self.exportar_respaldo,
        )
        btn_exportar.pack(fill="x")

        # Sección Respaldo Nube
        frame_nube = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        frame_nube.pack(fill="x", padx=15, pady=4)

        lbl_nube_desc = ctk.CTkLabel(
            frame_nube,
            text="• Sincronizar respaldo en la nube (Google Sheets):",
            font=ctk.CTkFont(size=10),
        )
        lbl_nube_desc.pack(anchor="w", pady=(0, 2))

        btn_nube = ctk.CTkButton(
            frame_nube,
            text="☁ Respaldo en la Nube",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0d9488",
            hover_color="#0f766e",
            height=30,
            command=lambda: exportar_respaldo_nube_bd(parent_window=self),
        )
        btn_nube.pack(fill="x")

        # Separador
        ctk.CTkFrame(self.frame_content, height=1, fg_color="#334155").pack(
            fill="x", padx=15, pady=8
        )

        # Sección Importar
        frame_imp = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        frame_imp.pack(fill="x", padx=15, pady=4)

        lbl_imp_desc = ctk.CTkLabel(
            frame_imp,
            text="• Importar base de datos desde un archivo JSON externo:",
            font=ctk.CTkFont(size=10),
        )
        lbl_imp_desc.pack(anchor="w", pady=(0, 2))

        btn_importar = ctk.CTkButton(
            frame_imp,
            text="📥 Importar Base de Datos",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=30,
            command=self.importar_respaldo,
        )
        btn_importar.pack(fill="x")

    def exportar_respaldo(self):
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Respaldo de Base de Datos",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            exito, msj = exportar_bd(ruta)
            if exito:
                messagebox.showinfo("Respaldo Exitoso", msj, parent=self)
            else:
                messagebox.showerror("Error al Exportar", msj, parent=self)

    def importar_respaldo(self):
        confirmacion = messagebox.askyesno(
            "Advertencia de Sobrescritura",
            "ADVERTENCIA: Importar un nuevo archivo reemplazará los datos actuales.\n\n¿Desea continuar?",
            parent=self,
        )
        if not confirmacion:
            return

        ruta = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar Archivo de Respaldo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            exito, msj = importar_bd(ruta)
            if exito:
                messagebox.showinfo("Importación Exitosa", msj, parent=self)
                if hasattr(self.parent, "bienes"):
                    from database import cargar_datos_locales

                    self.parent.bienes = cargar_datos_locales()
                    if hasattr(self.parent, "actualizar_tabla"):
                        self.parent.actualizar_tabla()
                    if hasattr(self.parent, "actualizar_metricas"):
                        self.parent.actualizar_metricas()
                self.destroy()
            else:
                messagebox.showerror("Error al Importar", msj, parent=self)