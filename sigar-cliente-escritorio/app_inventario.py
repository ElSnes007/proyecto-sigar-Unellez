# -*- coding: utf-8 -*-
import os
import json
import calendar
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

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
URL_RESPALDO_CLOUD = "https://sigar-unellez.onrender.com/api/respaldo"  # Reservado para integración futura

class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Sistema de Inventario Local y Gestión de Activos")
        self.root.geometry("1120x720")
        self.root.minsize(1000, 650)
        self.root.configure(bg="#f4f6f9")
        
        # Estilos globales de Tkinter
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#002B49", foreground="white")
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
        
        # Lista local en memoria
        self.bienes = []

        # Construcción de componentes gráficos
        self.crear_cintillo_institucional()
        self.crear_panel_metricas()
        self.crear_formulario()
        self.crear_panel_busqueda()
        self.crear_tabla()
        self.crear_panel_acciones()
        
        # Cargar datos locales e inicializar
        self.bienes = self.cargar_datos_locales()
        
        opciones_asignacion = self.obtener_opciones_asignacion()
        self.combo_asignado["values"] = opciones_asignacion
        if opciones_asignacion:
            self.combo_asignado.current(0)
            
        self.actualizar_tabla()
        self.actualizar_metricas()
        self.calcular_proxima_fecha_mantenimiento()
        self.root.after(200, self.activar_foco_inicial)

    def activar_foco_inicial(self):
        self.root.focus_force()
        self.entry_id.focus_force()

    # --- 1. CINTILLO INSTITUCIONAL ---
    def crear_cintillo_institucional(self):
        frame_cintillo = tk.Frame(self.root, bg="#002B49", height=36)
        frame_cintillo.pack(fill="x", side="top")
        
        lbl_unellez = tk.Label(
            frame_cintillo, 
            text="  UNELLEZ  |  Universidad Nacional Experimental de los Llanos Occidentales 'Ezequiel Zamora'",
            font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#002B49"
        )
        lbl_unellez.pack(side="left", padx=10, pady=6)

        self.lbl_estado_local = tk.Label(
            frame_cintillo, 
            text="● Modo Local (bienes.json)  ", 
            font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#002B49"
        )
        self.lbl_estado_local.pack(side="right", padx=10)

    # --- 2. TARJETAS DE MÉTRICAS (KPIs) ---
    def crear_panel_metricas(self):
        frame_kpis = tk.Frame(self.root, bg="#f4f6f9")
        frame_kpis.pack(fill="x", padx=15, pady=(10, 5))

        for i in range(5):
            frame_kpis.columnconfigure(i, weight=1, uniform="kpi")

        self.lbl_val_total = self.crear_tarjeta(frame_kpis, 0, "TOTAL ACTIVOS", "0", "Bienes registrados", "#002B49", "#ffffff", "#002B49")
        self.lbl_val_operativos = self.crear_tarjeta(frame_kpis, 1, "OPERATIVOS", "0", "En servicio activo", "#059669", "#ffffff", "#059669")
        self.lbl_val_preventivos = self.crear_tarjeta(frame_kpis, 2, "PREVENTIVOS", "0", "Ciclo regular (+3M)", "#0284C7", "#ffffff", "#0284C7")
        self.lbl_val_correctivos = self.crear_tarjeta(frame_kpis, 3, "CORRECTIVOS", "0", "Ajuste / Reparación", "#D97706", "#ffffff", "#D97706")
        self.lbl_val_desincorporados = self.crear_tarjeta(frame_kpis, 4, "DESINCORPORADOS", "0", "Actas emitidas", "#DC2626", "#ffffff", "#DC2626")

    def crear_tarjeta(self, parent, col, titulo, valor_inic, subtitulo, color_borde, color_bg, color_texto):
        card = tk.Frame(parent, bg=color_bg, highlightbackground=color_borde, highlightthickness=1, bd=0)
        card.grid(row=0, column=col, sticky="nsew", padx=3)

        left_strip = tk.Frame(card, bg=color_borde, width=4)
        left_strip.pack(side="left", fill="y")

        content = tk.Frame(card, bg=color_bg, padx=8, pady=4)
        content.pack(side="left", fill="both", expand=True)

        lbl_tit = tk.Label(content, text=titulo, font=("Segoe UI", 7, "bold"), fg=color_texto, bg=color_bg)
        lbl_tit.pack(anchor="w")

        lbl_val = tk.Label(content, text=valor_inic, font=("Segoe UI", 14, "bold"), fg="#1f2937", bg=color_bg)
        lbl_val.pack(anchor="w")

        lbl_sub = tk.Label(content, text=subtitulo, font=("Segoe UI", 7), fg="#6b7280", bg=color_bg)
        lbl_sub.pack(anchor="w")

        return lbl_val

    def actualizar_metricas(self):
        total = len(self.bienes)
        operativos = 0
        preventivos = 0
        correctivos = 0
        
        # Contar desincorporados registrados en el archivo de bajas
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
        frame_form = tk.LabelFrame(self.root, text=" Registrar Activo y Gestión de Mantenimiento ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#002B49", bd=1, relief="solid")
        frame_form.pack(fill="x", padx=15, pady=5)
        
        frame_form.columnconfigure(1, weight=1)
        frame_form.columnconfigure(3, weight=2)
        frame_form.columnconfigure(5, weight=1)
        
        # Fila 0
        tk.Label(frame_form, text="ID único:", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_id = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_id.grid(row=0, column=1, padx=5, pady=4, sticky="ew")
        
        tk.Label(frame_form, text="Asignado a:", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=0, column=2, padx=(10, 5), pady=4, sticky="e")
        self.combo_asignado = ttk.Combobox(frame_form, font=("Segoe UI", 9))
        self.combo_asignado.grid(row=0, column=3, columnspan=3, padx=5, pady=4, sticky="ew")
            
        # Botones de Formulario
        frame_btn_form = tk.Frame(frame_form, bg="#ffffff")
        frame_btn_form.grid(row=0, column=6, rowspan=4, padx=10, pady=4, sticky="ns")
        
        btn_agregar = tk.Button(frame_btn_form, text="Registrar Nuevo", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.agregar_bien, bd=0, padx=10, pady=4, cursor="hand2")
        btn_agregar.pack(fill="x", pady=2)
        
        btn_modificar = tk.Button(frame_btn_form, text="Guardar Cambios", bg="#059669", fg="white", font=("Segoe UI", 8, "bold"), command=self.actualizar_bien, bd=0, padx=10, pady=4, cursor="hand2")
        btn_modificar.pack(fill="x", pady=2)
        
        btn_limpiar = tk.Button(frame_btn_form, text="Limpiar Campos", bg="#6b7280", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_formulario, bd=0, padx=10, pady=3, cursor="hand2")
        btn_limpiar.pack(fill="x", pady=2)
        
        # Fila 1
        tk.Label(frame_form, text="Descripción / Nombre:", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=1, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_nombre = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_nombre.grid(row=1, column=1, columnspan=5, padx=5, pady=4, sticky="ew")
        
        # Fila 2
        tk.Label(frame_form, text="¿Mantenimiento?:", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=2, column=0, padx=(10, 5), pady=4, sticky="e")
        self.combo_mant = ttk.Combobox(frame_form, values=["No", "Sí (Preventivo)", "Sí (Correctivo)"], font=("Segoe UI", 9), width=15, state="readonly")
        self.combo_mant.current(0)
        self.combo_mant.grid(row=2, column=1, padx=5, pady=4, sticky="w")
        
        tk.Label(frame_form, text="Fecha (DD/MM/AAAA):", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=2, column=2, padx=(10, 5), pady=4, sticky="e")
        fecha_hoy = date.today().strftime("%d/%m/%Y")
        self.entry_fecha_mant = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_fecha_mant.insert(0, fecha_hoy)
        self.entry_fecha_mant.grid(row=2, column=3, padx=5, pady=4, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.al_cambiar_fecha)
        
        tk.Label(frame_form, text="Próximo (Hábil +3M):", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=2, column=4, padx=(10, 5), pady=4, sticky="e")
        self.entry_proximo = tk.Entry(frame_form, bg="#f3f4f6", fg="#000000", font=("Segoe UI", 9, "bold"), relief="solid", bd=1)
        self.entry_proximo.grid(row=2, column=5, padx=5, pady=4, sticky="ew")
        
        # Fila 3
        tk.Label(frame_form, text="Detalle / Observación:", bg="#ffffff", font=("Segoe UI", 8, "bold")).grid(row=3, column=0, padx=(10, 5), pady=4, sticky="e")
        self.entry_desc_mant = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1)
        self.entry_desc_mant.grid(row=3, column=1, columnspan=5, padx=5, pady=4, sticky="ew")

    # --- 4. PANEL DE BÚSQUEDA Y FILTRADO ---
    def crear_panel_busqueda(self):
        frame_busqueda = tk.Frame(self.root, bg="#f4f6f9")
        frame_busqueda.pack(fill="x", padx=15, pady=(4, 2))
        
        tk.Label(frame_busqueda, text="🔍 Buscar Activo:", bg="#f4f6f9", font=("Segoe UI", 8, "bold"), fg="#002B49").pack(side="left", padx=(0, 5))
        self.entry_buscar = tk.Entry(frame_busqueda, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, width=35)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        
        btn_limpiar_filtro = tk.Button(frame_busqueda, text="Limpiar Filtro", bg="#002B49", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_filtro_busqueda, bd=0, padx=8, pady=2, cursor="hand2")
        btn_limpiar_filtro.pack(side="left", padx=5)
        
        tk.Label(frame_busqueda, text="(Doble clic en un registro para editar)", bg="#f4f6f9", font=("Segoe UI", 8, "italic"), fg="#6b7280").pack(side="right")

    # --- 5. TABLA DE VISUALIZACIÓN ---
    def crear_tabla(self):
        frame_tabla = tk.Frame(self.root, bg="#f4f6f9")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=4)
        
        columnas = ("id", "nombre", "asignado_a", "mantenimiento", "fecha_mant", "proximo_mant")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
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
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --- 6. BARRA DE ACCIONES INFERIOR ---
    def crear_panel_acciones(self):
        frame_acciones = tk.Frame(self.root, bg="#f4f6f9")
        frame_acciones.pack(fill="x", padx=15, pady=(4, 10))
        
        btn_cargar = tk.Button(frame_acciones, text="Cargar Seleccionado para Editar", bg="#D97706", fg="white", font=("Segoe UI", 8, "bold"), command=self.cargar_seleccion_para_editar, bd=0, padx=12, pady=5, cursor="hand2")
        btn_cargar.pack(side="left", padx=(0, 10))
        
        btn_eliminar = tk.Button(frame_acciones, text="Dar de Baja / Generar Acta PDF", bg="#DC2626", fg="white", font=("Segoe UI", 8, "bold"), command=self.dar_de_baja_bien, bd=0, padx=12, pady=5, cursor="hand2")
        btn_eliminar.pack(side="left", padx=(0, 10))

        # Botón para futura función de respaldo en la nube
        btn_respaldo = tk.Button(frame_acciones, text="☁️ Respaldo en Nube (Próximamente)", bg="#0284C7", fg="white", font=("Segoe UI", 8, "bold"), command=self.respaldar_en_nube_placeholder, bd=0, padx=12, pady=5, cursor="hand2")
        btn_respaldo.pack(side="left")
        
        lbl_info = tk.Label(frame_acciones, text="SIGAR V1.0 (Modo Local) — UNELLEZ", font=("Segoe UI", 8, "italic"), fg="#6b7280", bg="#f4f6f9")
        lbl_info.pack(side="right", pady=3)

    # --- MANEJO DE PERSISTENCIA LOCAL (JSON) ---
    def cargar_datos_locales(self):
        """Carga la lista de activos desde bienes.json localmente."""
        if not os.path.exists(ARCHIVO_BIENES):
            return []
        try:
            with open(ARCHIVO_BIENES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudieron cargar los datos de {ARCHIVO_BIENES}:\n{e}")
            return []

    def guardar_datos_locales(self):
        """Guarda la lista actual de activos en bienes.json."""
        try:
            with open(ARCHIVO_BIENES, "w", encoding="utf-8") as f:
                json.dump(self.bienes, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error de Escritura", f"No se pudo guardar la información en {ARCHIVO_BIENES}:\n{e}")
            return False

    def guardar_baja_local(self, registro_baja):
        """Guarda un historial acumulativo de las bajas en bienes_bajas.json."""
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

        # Verificar si el ID ya existe en el archivo local
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
            opciones_actuales = list(self.combo_asignado["values"])
            if asignado_val not in opciones_actuales:
                opciones_actuales.append(asignado_val)
                self.combo_asignado["values"] = opciones_actuales
            
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
            opciones_actuales = list(self.combo_asignado["values"])
            if asignado_val not in opciones_actuales:
                opciones_actuales.append(asignado_val)
                self.combo_asignado["values"] = opciones_actuales
                
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
            
            # Remover de activos vigentes y registrar en bajas
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

    # --- APARTADO RESERVADO PARA FUTURA SINCRONIZACIÓN EN LA NUBE ---
    def respaldar_en_nube_placeholder(self):
        """Estructura preparada para implementar la subida/sincronización del archivo bienes.json hacia Render en el futuro."""
        if not HAS_REQUESTS:
            messagebox.showinfo(
                "Respaldo en Nube (Próximamente)",
                "Para activar el respaldo en la nube en el futuro, asegúrate de instalar la librería 'requests' (pip install requests)."
            )
            return

        messagebox.showinfo(
            "Módulo de Respaldo en la Nube (Reservado)",
            "Esta función enviará una copia del archivo local 'bienes.json' "
            f"hacia el servidor remoto ({URL_RESPALDO_CLOUD}) cuando decidas activarlo."
        )

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

    def obtener_opciones_asignacion(self):
        opciones_base = ["Almacén / Stock", "Servicio Médico", "Coordinación de Sistemas", "Unidad de Bienes", "Recursos Humanos"]
        existentes = list(opciones_base)
        for bien in getattr(self, 'bienes', []):
            val = bien.get("asignado_a")
            if val and val not in existentes:
                existentes.append(val)
        return existentes

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