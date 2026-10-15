# -*- coding: utf-8 -*-
"""
Módulo de Vistas Especializadas - SIGART UNELLEZ VIPI
Implementa el panel para la generación y emisión de Actas de Traslado de Equipos en PDF
con extracción automática de procedencia y actualización del inventario.
"""
from datetime import date, datetime
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk

try:
    from database import registrar_traslado_local, actualizar_asignacion_bienes_trasladados
except ImportError:
    def registrar_traslado_local(registro_traslado):
        return True
    def actualizar_asignacion_bienes_trasladados(ids, destino):
        return True

from utils import generar_acta_traslado


class VistaTraslado(ctk.CTkFrame):
    """Vista principal para la elaboración y exportación de Actas de Traslado de Equipos."""

    def __init__(self, parent, obtener_bienes_callback, modo_oscuro=True, paleta=None, actualizar_inventario_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.obtener_bienes_callback = obtener_bienes_callback
        self.modo_oscuro = modo_oscuro
        self.paleta = paleta or {}
        self.actualizar_inventario_callback = actualizar_inventario_callback

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.crear_encabezado()
        self.crear_cuerpo()
        self.crear_acciones()

    def crear_encabezado(self):
        frame_head = ctk.CTkFrame(self, fg_color="#002B49", corner_radius=8, height=48)
        frame_head.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 8))
        frame_head.pack_propagate(False)

        lbl_tit = ctk.CTkLabel(
            frame_head,
            text="📋 GENERADOR OFICIAL DE ACTAS DE TRASLADO DE EQUIPOS TECNOLÓGICOS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#ffffff",
        )
        lbl_tit.pack(side="left", padx=15, pady=10)

    def crear_cuerpo(self):
        f_mid = ctk.CTkFrame(self, corner_radius=10)
        f_mid.grid(row=1, column=0, sticky="nsew", padx=15, pady=4)
        f_mid.columnconfigure(0, weight=0)  # Panel izquierdo compacto
        f_mid.columnconfigure(1, weight=1)  # Tabla derecha toma todo el ancho
        f_mid.rowconfigure(0, weight=1)

        # Panel izquierdo compacto (340px)
        f_izq = ctk.CTkScrollableFrame(f_mid, label_text="Datos de Traslado y Custodia", corner_radius=8, width=340)
        f_izq.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        f_izq.columnconfigure(1, weight=1)

        r = 0
        # Solo se selecciona la dependencia destino
        ctk.CTkLabel(f_izq, text="Dependencia Destino:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=4, sticky="w")
        self.combo_destino = ctk.CTkOptionMenu(
            f_izq,
            values=[
                "Rectorado", "Departamento de Sistemas", "Laboratorio 1", "Control de Estudios",
                "Servicios Generales", "Planificación y Presupuesto", "Coordinación de Docencia",
                "Comunicaciones y Prensa", "Secretaría Ejecutiva", "Recursos Humanos", "Taller Central CTSI"
            ],
            height=28
        )
        self.combo_destino.grid(row=r, column=1, padx=8, pady=4, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="Fecha de Emisión:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=4, sticky="w")
        self.entry_fecha = ctk.CTkEntry(f_izq, height=28)
        self.entry_fecha.insert(0, date.today().strftime("%d/%m/%Y"))
        self.entry_fecha.grid(row=r, column=1, padx=8, pady=4, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="Motivo del Traslado:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=4, sticky="w")
        self.entry_motivo = ctk.CTkEntry(f_izq, placeholder_text="Ej: Reasignación por requerimiento docente", height=28)
        self.entry_motivo.grid(row=r, column=1, padx=8, pady=4, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="Condiciones / Obs:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=4, sticky="w")
        self.entry_obs = ctk.CTkEntry(f_izq, placeholder_text="Ej: Equipos operativos verificados", height=28)
        self.entry_obs.grid(row=r, column=1, padx=8, pady=4, sticky="ew")

        r += 1
        sep = ctk.CTkFrame(f_izq, height=2, fg_color="#334155")
        sep.grid(row=r, column=0, columnspan=2, sticky="ew", padx=8, pady=10)

        # Firmas institucionales
        r += 1
        ctk.CTkLabel(f_izq, text="Jefe de CTSI (Emisor):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").grid(row=r, column=0, padx=8, pady=2, sticky="w")
        self.entry_jefe_nom = ctk.CTkEntry(f_izq, placeholder_text="Nombre del Jefe de CTSI", height=28)
        self.entry_jefe_nom.insert(0, "Ing. Coordinador de CTSI")
        self.entry_jefe_nom.grid(row=r, column=1, padx=8, pady=2, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="C.I. Jefe CTSI:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=2, sticky="w")
        self.entry_jefe_ci = ctk.CTkEntry(f_izq, placeholder_text="Cédula", height=28)
        self.entry_jefe_ci.insert(0, "V-12345678")
        self.entry_jefe_ci.grid(row=r, column=1, padx=8, pady=2, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="Custodio Receptor:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").grid(row=r, column=0, padx=8, pady=2, sticky="w")
        self.entry_rec_nom = ctk.CTkEntry(f_izq, placeholder_text="Nombre de quien recibe", height=28)
        self.entry_rec_nom.grid(row=r, column=1, padx=8, pady=2, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="C.I. Custodio Receptor:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=2, sticky="w")
        self.entry_rec_ci = ctk.CTkEntry(f_izq, placeholder_text="Cédula del receptor", height=28)
        self.entry_rec_ci.grid(row=r, column=1, padx=8, pady=2, sticky="ew")

        r += 1
        ctk.CTkLabel(f_izq, text="Cargo del Receptor:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=r, column=0, padx=8, pady=2, sticky="w")
        self.entry_rec_cargo = ctk.CTkEntry(f_izq, placeholder_text="Cargo o Función", height=28)
        self.entry_rec_cargo.grid(row=r, column=1, padx=8, pady=2, sticky="ew")

        # Panel derecho: Tabla de activos
        f_der = ctk.CTkFrame(f_mid, corner_radius=8)
        f_der.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        f_der.rowconfigure(1, weight=1)
        f_der.columnconfigure(0, weight=1)

        f_der_top = ctk.CTkFrame(f_der, fg_color="transparent")
        f_der_top.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(f_der_top, text="Seleccione los Activos a Trasladar (Clic en fila para marcar):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkButton(f_der_top, text="Actualizar Lista", width=100, height=24, command=self.cargar_equipos_en_tabla).pack(side="right")

        cols = ("sel", "id", "nombre", "asignado")
        self.tabla_activos = ttk.Treeview(f_der, columns=cols, show="headings", selectmode="extended")
        self.tabla_activos.heading("sel", text="✓", anchor="center")
        self.tabla_activos.heading("id", text="ID", anchor="center")
        self.tabla_activos.heading("nombre", text="Activo / Equipo Tecnológico", anchor="w")
        self.tabla_activos.heading("asignado", text="Asignado a / Área", anchor="w")

        self.tabla_activos.column("sel", width=32, minwidth=32, stretch=False, anchor="center")
        self.tabla_activos.column("id", width=46, minwidth=40, stretch=False, anchor="center")
        self.tabla_activos.column("nombre", width=340, minwidth=240, stretch=True, anchor="w")
        self.tabla_activos.column("asignado", width=175, minwidth=140, stretch=False, anchor="w")

        sc = ctk.CTkScrollbar(f_der, command=self.tabla_activos.yview)
        self.tabla_activos.configure(yscrollcommand=sc.set)

        self.tabla_activos.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=6)
        sc.grid(row=1, column=1, sticky="ns", padx=(0, 6), pady=6)

        self.tabla_activos.bind("<Button-1>", self.al_hacer_clic_fila)
        self.cargar_equipos_en_tabla()

    def al_hacer_clic_fila(self, event):
        item = self.tabla_activos.identify_row(event.y)
        if item:
            val = list(self.tabla_activos.item(item, "values"))
            val[0] = "✔" if val[0] == "" else ""
            self.tabla_activos.item(item, values=val)

    def cargar_equipos_en_tabla(self):
        for item in self.tabla_activos.get_children():
            self.tabla_activos.delete(item)
        bienes = self.obtener_bienes_callback()
        for b in bienes:
            self.tabla_activos.insert(
                "", "end",
                values=("", b.get("id"), b.get("nombre"), b.get("asignado_a", "N/A"))
            )

    def crear_acciones(self):
        f_bot = ctk.CTkFrame(self, fg_color="transparent")
        f_bot.grid(row=2, column=0, sticky="ew", padx=15, pady=(4, 12))

        ctk.CTkButton(
            f_bot,
            text="📄 Generar y Exportar Acta de Traslado (PDF)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=34,
            command=self.procesar_acta_traslado
        ).pack(side="left")

        ctk.CTkButton(
            f_bot,
            text="Limpiar Formulario",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#475569",
            hover_color="#334155",
            height=34,
            command=self.limpiar_campos
        ).pack(side="right")

    def limpiar_campos(self):
        self.entry_motivo.delete(0, tk.END)
        self.entry_obs.delete(0, tk.END)
        self.entry_rec_nom.delete(0, tk.END)
        self.entry_rec_ci.delete(0, tk.END)
        self.entry_rec_cargo.delete(0, tk.END)
        self.cargar_equipos_en_tabla()

    def procesar_acta_traslado(self):
        destino = self.combo_destino.get().strip()
        motivo = self.entry_motivo.get().strip()
        fecha = self.entry_fecha.get().strip()
        jefe_nom = self.entry_jefe_nom.get().strip()
        jefe_ci = self.entry_jefe_ci.get().strip()
        rec_nom = self.entry_rec_nom.get().strip()
        rec_ci = self.entry_rec_ci.get().strip()
        rec_cargo = self.entry_rec_cargo.get().strip()

        if not motivo:
            messagebox.showwarning("Motivo Requerido", "Por favor detalle el motivo formal del traslado.")
            return

        if not rec_nom or not rec_ci:
            messagebox.showwarning("Receptor Requerido", "Debe indicar el nombre y cédula del Custodio Receptor.")
            return

        equipos_sel = []
        for row in self.tabla_activos.get_children():
            vals = self.tabla_activos.item(row, "values")
            if vals[0] == "✔":
                equipos_sel.append({
                    "id": vals[1],
                    "nombre": vals[2],
                    "asignado_a": vals[3],
                    "estado": "Operativo"
                })

        if not equipos_sel:
            messagebox.showwarning("Sin Selección", "Marque al menos un activo de la tabla con clic para trasladar.")
            return

        # Extracción automática de las dependencias de origen desde los activos seleccionados
        origenes_unicos = []
        for eq in equipos_sel:
            orig = eq.get("asignado_a", "N/A")
            if orig and orig not in origenes_unicos:
                origenes_unicos.append(orig)

        origen_str = ", ".join(origenes_unicos) if origenes_unicos else "No especificado"

        # Validación: si todos los equipos seleccionados ya están en la dependencia destino
        if len(origenes_unicos) == 1 and origenes_unicos[0] == destino:
            messagebox.showwarning(
                "Ubicación Idéntica",
                f"Todos los equipos seleccionados ya se encuentran asignados a '{destino}'."
            )
            return

        ref_id = f"TRASLADO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        datos_acta = {
            "referencia": ref_id,
            "fecha": fecha,
            "origen": origen_str,
            "destino": destino,
            "motivo": motivo,
            "observaciones": self.entry_obs.get().strip() or "Sin observaciones adicionales",
            "firma_jefe_nombre": jefe_nom,
            "firma_jefe_ci": jefe_ci,
            "firma_receptor_nombre": rec_nom,
            "firma_receptor_ci": rec_ci,
            "firma_receptor_cargo": rec_cargo,
            "equipos": equipos_sel
        }

        # 1. Generar el documento PDF oficial
        archivo_salida = generar_acta_traslado(datos_acta)
        if archivo_salida:
            # 2. Registrar el traslado en el historial
            registrar_traslado_local(datos_acta)

            # 3. Actualizar la asignación de los activos en bienes.json
            ids_trasladados = [eq["id"] for eq in equipos_sel]
            actualizar_asignacion_bienes_trasladados(ids_trasladados, destino)

            # 4. Refrescar el inventario en tiempo real
            if self.actualizar_inventario_callback:
                self.actualizar_inventario_callback()
            self.cargar_equipos_en_tabla()

            messagebox.showinfo(
                "Acta de Traslado Emitida",
                f"El Acta de Traslado ha sido generada en formato PDF:\n\n{archivo_salida}\n\n"
                f"Los bienes seleccionados han sido reasignados a: '{destino}'."
            )
            self.limpiar_campos()