# -*- coding: utf-8 -*-
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Nombre del archivo para la base de datos local simulada
DB_FILE = "bienes.json"

class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Inventario de Bienes - Mibodeguitaverival")
        self.root.geometry("750x500")
        self.root.configure(bg="#f4f6f9")
        
        # Cargar datos iniciales
        self.bienes = self.cargar_datos()
        
        # Estilos
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#0b3c5d", foreground="white")
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        
        # --- PANEL SUPERIOR: Formulario de Registro ---
        frame_form = tk.LabelFrame(root, text=" Registrar Nuevo Activo / Bien ", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0b3c5d", bd=2, relief="groove")
        frame_form.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_form, text="ID único:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_id = ttk.Entry(frame_form, width=10)
        self.entry_id.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        tk.Label(frame_form, text="Nombre del Bien:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.entry_nombre = ttk.Entry(frame_form, width=30)
        self.entry_nombre.grid(row=0, column=3, padx=5, pady=10, sticky="w")
        
        tk.Label(frame_form, text="Estado Actual:", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=4, padx=10, pady=10, sticky="e")
        self.combo_estado = ttk.Combobox(frame_form, values=["Stock", "Asignado", "En Reparación", "Dado de Baja"], width=15, state="readonly")
        self.combo_estado.current(0)
        self.combo_estado.grid(row=0, column=5, padx=5, pady=10, sticky="w")
        
        btn_agregar = tk.Button(frame_form, text="Registrar Activo", bg="#328cc1", fg="white", font=("Segoe UI", 9, "bold"), command=self.agregar_bien, bd=0, padx=10, pady=4)
        btn_agregar.grid(row=0, column=6, padx=15, pady=10)
        
        # --- PANEL CENTRAL: Tabla de Visualización ---
        frame_tabla = tk.Frame(root, bg="#f4f6f9")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)
        
        columnas = ("id", "nombre", "estado")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción / Nombre del Bien")
        self.tabla.heading("estado", text="Estado Logístico")
        
        self.tabla.column("id", width=100, anchor="center")
        self.tabla.column("nombre", width=400, anchor="w")
        self.tabla.column("estado", width=180, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- PANEL INFERIOR: Acciones de Control ---
        frame_acciones = tk.Frame(root, bg="#f4f6f9")
        frame_acciones.pack(fill="x", padx=15, pady=15)
        
        btn_eliminar = tk.Button(frame_acciones, text="Dar de Baja / Eliminar Seleccionado", bg="#d9534f", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_bien, bd=0, padx=12, pady=6)
        btn_eliminar.pack(side="left")
        
        lbl_info = tk.Label(frame_acciones, text="Mibodeguitaverival V1.0 - Entorno Corporativo", font=("Segoe UI", 9, "italic"), fg="#7f8c8d", bg="#f4f6f9")
        lbl_info.pack(side="right", pady=5)
        
        # Renderizar datos en la tabla
        self.actualizar_tabla()

    def cargar_datos(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        else:
            # Datos semilla iniciales coincidentes con la guía de simulación
            data_inicial = [
                {"id": 1, "nombre": "Laptop Core i7", "estado": "Asignado"},
                {"id": 2, "nombre": "Monitor 24 pulg", "estado": "Stock"}
            ]
            self.guardar_datos(data_inicial)
            return data_inicial

    def guardar_datos(self, datos):
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error de Almacenamiento", f"No se pudo escribir en la base de datos: {e}")

    def actualizar_tabla(self):
        # Limpiar registros existentes en la interfaz
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        # Insertar registros actuales
        for bien in self.bienes:
            self.tabla.insert("", "end", values=(bien["id"], bien["nombre"], bien["estado"]))

    def agregar_bien(self):
        id_val = self.entry_id.get().strip()
        nombre_val = self.entry_nombre.get().strip()
        estado_val = self.combo_estado.get()
        
        if not id_val or not nombre_val:
            messagebox.showwarning("Campos Incompletos", "Por favor, complete los campos de ID y Nombre del Bien.")
            return
            
        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("Tipo Incorrecto", "El ID debe ser un valor numérico entero.")
            return
            
        # Validar duplicados de clave primaria simulada
        if any(b["id"] == id_int for b in self.bienes):
            messagebox.showerror("ID Duplicado", f"El ID {id_int} ya se encuentra asignado a otro bien del sistema.")
            return
            
        nuevo_bien = {"id": id_int, "nombre": nombre_val, "estado": estado_val}
        self.bienes.append(nuevo_bien)
        self.guardar_datos(self.bienes)
        self.actualizar_tabla()
        
        # Limpiar formulario
        self.entry_id.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        messagebox.showinfo("Registro Exitoso", f"El bien '{nombre_val}' ha sido añadido al inventario.")

    def eliminar_bien(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un elemento de la tabla para darlo de baja.")
            return
            
        item = self.tabla.item(seleccion)
        id_bien = int(item["values"][0])
        nombre_bien = item["values"][1]
        
        confirmacion = messagebox.askyesno("Confirmar Baja", f"¿Está seguro de que desea retirar el activo '{nombre_bien}' del inventario activo?")
        if confirmacion:
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            self.guardar_datos(self.bienes)
            self.actualizar_tabla()
            messagebox.showinfo("Baja Procesada", "El registro ha sido eliminado del sistema central.")

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()
