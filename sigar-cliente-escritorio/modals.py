# -*- coding: utf-8 -*-
from datetime import date
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from database import (
    URL_RESPALDO_CLOUD,
    cargar_historial_bajas,
    exportar_respaldo_nube_bd,
)
from utils import HAS_REQUESTS


class VentanaDesincorporados(tk.Toplevel):
    """
    Ventana modal emergente para mostrar el historial de activos
    que han sido dados de baja / desincorporados.
    """

    def __init__(self, parent, paleta, modo_oscuro):
        super().__init__(parent)
        self.parent = parent
        self.paleta = paleta
        self.modo_oscuro = modo_oscuro

        t = "oscuro" if self.modo_oscuro else "claro"
        self.pal = self.paleta[t]

        self.title("SIGAR - Historial de Activos Desincorporados")
        self.geometry("800x420")
        self.configure(bg=self.pal["bg_root"])
        self.transient(parent)
        self.grab_set()

        self._centrar_ventana()
        self._construir_ui()

    def _centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        lbl_titulo = tk.Label(
            self,
            text="❌ REGISTRO DE ACTAS DE DESINCORPORACIÓN Y BAJA",
            font=("Segoe UI", 11, "bold"),
            fg="#dc2626",
            bg=self.pal["bg_root"],
            pady=10,
        )
        lbl_titulo.pack()

        frame_tabla_bajas = tk.Frame(self, bg=self.pal["bg_root"])
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
                self,
                text="No hay actas de desincorporación registradas.",
                font=("Segoe UI", 9, "italic"),
                fg=self.pal["fg_subtexto"],
                bg=self.pal["bg_root"],
            )
            lbl_vacio.pack(pady=10)


class VentanaRespaldos(tk.Toplevel):
    """
    Ventana modal emergente para gestionar respaldos locales y sincronización
    con la nube.
    """

    def __init__(self, parent, paleta, modo_oscuro, obtener_bienes_callback):
        super().__init__(parent)
        self.parent = parent
        self.paleta = paleta
        self.modo_oscuro = modo_oscuro
        self.obtener_bienes = obtener_bienes_callback

        t = "oscuro" if self.modo_oscuro else "claro"
        self.pal = self.paleta[t]

        self.title("Gestión y Centro de Respaldos")
        self.geometry("420x280")
        self.resizable(False, False)
        self.configure(bg=self.pal["bg_root"])
        self.transient(parent)
        self.grab_set()

        self._centrar_ventana()
        self._construir_ui()

    def _centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_ui(self):
        lbl_titulo = tk.Label(
            self,
            text="☁️ Sincronización y Respaldos",
            font=("Segoe UI", 12, "bold"),
            fg=self.pal["fg_texto"],
            bg=self.pal["bg_root"],
        )
        lbl_titulo.pack(pady=(15, 5))

        lbl_sub = tk.Label(
            self,
            text="Seleccione la acción de respaldo que desea ejecutar:",
            font=("Segoe UI", 8),
            fg=self.pal["fg_subtexto"],
            bg=self.pal["bg_root"],
        )
        lbl_sub.pack(pady=(0, 15))

        frame_botones = tk.Frame(self, bg=self.pal["bg_root"])
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
            command=self.accion_guardar_nube,
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
            command=self.accion_importar_nube,
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
            command=self.accion_guardar_local,
        )
        btn_local.pack(fill="x", pady=4)

    def accion_guardar_nube(self):
        if not HAS_REQUESTS:
            messagebox.showinfo(
                "Librería Pendiente",
                "Se requiere la librería 'requests' instalada para enviar datos"
                " a la API.",
                parent=self,
            )
            return

        exportar_respaldo_nube_bd(parent_window=self)
        messagebox.showinfo(
            "Conexión Backend",
            "Frontend preparado para enviar datos al servidor"
            f" API:\n\nEndpoint: {URL_RESPALDO_CLOUD}\n\nEstructura JSON lista.",
            parent=self,
        )

    def accion_importar_nube(self):
        if not HAS_REQUESTS:
            messagebox.showinfo(
                "Librería Pendiente",
                "Se requiere la librería 'requests' instalada para recibir"
                " datos de la API.",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Conexión Backend",
            "Frontend preparado para consultar e importar datos desde la"
            f" API:\n\nEndpoint: {URL_RESPALDO_CLOUD}",
            parent=self,
        )

    def accion_guardar_local(self):
        try:
            filename = filedialog.asksaveasfilename(
                parent=self,
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
                bienes = self.obtener_bienes()
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(bienes, f, ensure_ascii=False, indent=4)
                messagebox.showinfo(
                    "Respaldo Guardado",
                    "El respaldo local ha sido guardado exitosamente"
                    f" en:\n{filename}",
                    parent=self,
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo guardar el respaldo local: {e}",
                parent=self,
            )