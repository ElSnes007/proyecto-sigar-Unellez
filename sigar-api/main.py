# -*- coding: utf-8 -*-
import json
import os
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

# Archivos de persistencia
DB_FILE = "bienes.json"
DB_BAJAS_FILE = "bienes_bajas.json"

class InventarioBienesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Sistema de Inventario y Gestión de Activos y Recursos")
        self.root.geometry("1100x720")
        self.root.configure(bg="#f4f6f9")
        
        # Cargar datos iniciales
        self.bienes = self.cargar_datos()
        
        # Estilos de Tkinter
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#0b3c5d", foreground="white")
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        
        # --- CINTILLO INSTITUCIONAL SUPERIOR ---
        frame_cintillo = tk.Frame(root, bg="#0b3c5d", height=35)
        frame_cintillo.pack(fill="x", side="top")
        
        lbl_cintillo = tk.Label(
            frame_cintillo, 
            text="UNELLEZ | Universidad Nacional Experimental de los Llanos Occidentales 'Ezequiel Zamora'", 
            font=("Segoe UI", 10, "bold"), 
            fg="#ffffff", 
            bg="#0b3c5d"
        )
        lbl_cintillo.pack(side="left", padx=15, pady=6)
        
        lbl_status = tk.Label(
            frame_cintillo, 
            text="• Conectado a Render Cloud", 
            font=("Segoe UI", 9, "bold"), 
            fg="#2ecc71", 
            bg="#0b3c5d"
        )
        lbl_status.pack(side="right", padx=15, pady=6)

        # --- TARJETAS DE MÉTRICAS (KPIs) ---
        frame_kpis = tk.Frame(root, bg="#f4f6f9")
        frame_kpis.pack(fill="x", padx=15, pady=(10, 5))
        frame_kpis.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="kpi")

        self.card_total = self.crear_tarjeta_kpi(frame_kpis, 0, "TOTAL ACTIVOS", "0", "Bienes registrados", "#0b3c5d")
        self.card_operativos = self.crear_tarjeta_kpi(frame_kpis, 1, "OPERATIVOS", "0", "En servicio activo", "#27ae60")
        self.card_preventivos = self.crear_tarjeta_kpi(frame_kpis, 2, "PREVENTIVOS", "0", "Ciclo regular (+3M)", "#328cc1")
        self.card_correctivos = self.crear_tarjeta_kpi(frame_kpis, 3, "CORRECTIVOS", "0", "Ajuste / Reparación", "#e67e22")
        self.card_bajas = self.crear_tarjeta_kpi(frame_kpis, 4, "DESINCORPORADOS", "0", "Actas emitidas", "#d9534f")

        # --- PANEL CENTRAL: Formulario de Registro e Historial ---
        frame_form = tk.LabelFrame(root, text=" Registrar Activo y Gestión de Mantenimiento ", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0b3c5d", bd=2, relief="groove")
        frame_form.pack(fill="x", padx=15, pady=5)
        
        frame_form.columnconfigure(1, weight=1)
        frame_form.columnconfigure(3, weight=2)
        frame_form.columnconfigure(5, weight=1)
        
        # Fila 0: ID y Asignación
        tk.Label(frame_form, text="ID único:", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="e")
        self.entry_id = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, insertbackground="black")
        self.entry_id.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_form, text="Asignado a:", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=(10, 5), pady=5, sticky="e")
        opciones_asignacion = self.obtener_opciones_asignacion()
        self.combo_asignado = ttk.Combobox(frame_form, values=opciones_asignacion, font=("Segoe UI", 9))
        self.combo_asignado.grid(row=0, column=3, columnspan=3, padx=5, pady=5, sticky="ew")
        if opciones_asignacion:
            self.combo_asignado.current(0)
            
        # Contenedor Lateral de Botones de Formulario
        frame_btn_form = tk.Frame(frame_form, bg="#ffffff")
        frame_btn_form.grid(row=0, column=6, rowspan=4, padx=10, pady=5, sticky="ns")
        
        btn_agregar = tk.Button(frame_btn_form, text="Registrar Nuevo", bg="#328cc1", fg="white", font=("Segoe UI", 9, "bold"), command=self.agregar_bien, bd=0, padx=12, pady=5, cursor="hand2")
        btn_agregar.pack(fill="x", pady=2)
        
        btn_modificar = tk.Button(frame_btn_form, text="Guardar Cambios", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=self.actualizar_bien, bd=0, padx=12, pady=5, cursor="hand2")
        btn_modificar.pack(fill="x", pady=2)
        
        btn_limpiar = tk.Button(frame_btn_form, text="Limpiar Campos", bg="#7f8c8d", fg="white", font=("Segoe UI", 9, "bold"), command=self.limpiar_formulario, bd=0, padx=12, pady=4, cursor="hand2")
        btn_limpiar.pack(fill="x", pady=2)
        
        # Fila 1: Descripción / Nombre
        tk.Label(frame_form, text="Descripción / Nombre:", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, padx=(10, 5), pady=5, sticky="e")
        self.entry_nombre = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, insertbackground="black")
        self.entry_nombre.grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="ew")
        
        # Fila 2: Datos de Mantenimiento
        tk.Label(frame_form, text="¿Mantenimiento?:", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, padx=(10, 5), pady=5, sticky="e")
        self.combo_mant = ttk.Combobox(frame_form, values=["No", "Sí (Preventivo)", "Sí (Correctivo)"], font=("Segoe UI", 9), width=15, state="readonly")
        self.combo_mant.current(0)
        self.combo_mant.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_form, text="Fecha (DD/MM/AAAA):", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=2, column=2, padx=(10, 5), pady=5, sticky="e")
        fecha_hoy = date.today().strftime("%d/%m/%Y")
        self.entry_fecha_mant = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, insertbackground="black")
        self.entry_fecha_mant.insert(0, fecha_hoy)
        self.entry_fecha_mant.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        self.entry_fecha_mant.bind("<KeyRelease>", self.al_cambiar_fecha)
        
        tk.Label(frame_form, text="Próximo (Hábil +3M):", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=2, column=4, padx=(10, 5), pady=5, sticky="e")
        self.entry_proximo = tk.Entry(frame_form, bg="#e9ecef", fg="#000000", font=("Segoe UI", 9, "bold"), relief="solid", bd=1)
        self.entry_proximo.grid(row=2, column=5, padx=5, pady=5, sticky="ew")
        
        # Fila 3: Detalle / Observación
        tk.Label(frame_form, text="Detalle / Observación:", bg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, padx=(10, 5), pady=5, sticky="e")
        self.entry_desc_mant = tk.Entry(frame_form, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, insertbackground="black")
        self.entry_desc_mant.grid(row=3, column=1, columnspan=5, padx=5, pady=5, sticky="ew")
        
        # --- PANEL DE BÚSQUEDA Y FILTRADO ---
        frame_busqueda = tk.Frame(root, bg="#f4f6f9")
        frame_busqueda.pack(fill="x", padx=15, pady=(5, 2))
        
        tk.Label(frame_busqueda, text="🔍 Buscar Activo:", bg="#f4f6f9", font=("Segoe UI", 9, "bold"), fg="#0b3c5d").pack(side="left", padx=(0, 5))
        self.entry_buscar = tk.Entry(frame_busqueda, bg="#ffffff", fg="#000000", font=("Segoe UI", 9), relief="solid", bd=1, width=35)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        
        btn_limpiar_filtro = tk.Button(frame_busqueda, text="Limpiar Filtro", bg="#0b3c5d", fg="white", font=("Segoe UI", 8, "bold"), command=self.limpiar_filtro_busqueda, bd=0, padx=8, pady=2, cursor="hand2")
        btn_limpiar_filtro.pack(side="left", padx=5)
        
        tk.Label(frame_busqueda, text="(Doble clic en un registro para editarlo)", bg="#f4f6f9", font=("Segoe UI", 8, "italic"), fg="#7f8c8d").pack(side="right")
        
        # --- PANEL CENTRAL: Tabla de Visualización ---
        frame_tabla = tk.Frame(root, bg="#f4f6f9")
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)
        
        columnas = ("id", "nombre", "asignado_a", "mantenimiento", "fecha_mant", "proximo_mant")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tabla.heading("id", text="ID Activo")
        self.tabla.heading("nombre", text="Descripción / Detalles del Bien")
        self.tabla.heading("asignado_a", text="Asignado a")
        self.tabla.heading("mantenimiento", text="Mantenimiento")
        self.tabla.heading("fecha_mant", text="Última Fecha")
        self.tabla.heading("proximo_mant", text="Próxima Fecha (Hábil)")
        
        self.tabla.column("id", width=80, anchor="center")
        self.tabla.column("nombre", width=360, anchor="w")
        self.tabla.column("asignado_a", width=180, anchor="w")
        self.tabla.column("mantenimiento", width=120, anchor="center")
        self.tabla.column("fecha_mant", width=110, anchor="center")
        self.tabla.column("proximo_mant", width=130, anchor="center")
        
        self.tabla.bind("<Double-1>", self.cargar_seleccion_para_editar)
        
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- PANEL INFERIOR: Acciones de Control ---
        frame_acciones = tk.Frame(root, bg="#f4f6f9")
        frame_acciones.pack(fill="x", padx=15, pady=10)
        
        btn_cargar = tk.Button(frame_acciones, text="Cargar Seleccionado para Editar", bg="#e67e22", fg="white", font=("Segoe UI", 9, "bold"), command=self.cargar_seleccion_para_editar, bd=0, padx=12, pady=6, cursor="hand2")
        btn_cargar.pack(side="left", padx=(0, 10))
        
        btn_eliminar = tk.Button(frame_acciones, text="Dar de Baja / Generar Acta PDF", bg="#d9534f", fg="white", font=("Segoe UI", 9, "bold"), command=self.dar_de_baja_bien, bd=0, padx=12, pady=6, cursor="hand2")
        btn_eliminar.pack(side="left")
        
        lbl_info = tk.Label(frame_acciones, text="SIGAR V1.0 — Universidad Nacional Experimental de los Llanos Occidentales Ezequiel Zamora", font=("Segoe UI", 8, "italic"), fg="#7f8c8d", bg="#f4f6f9")
        lbl_info.pack(side="right", pady=5)
        
        # Cargar datos iniciales y refrescar interfaz
        self.actualizar_tabla()
        self.calcular_proxima_fecha_mantenimiento()
        self.root.after(200, self.activar_foco_inicial)

    def crear_tarjeta_kpi(self, parent, col, titulo, valor, subtitulo, color):
        frame = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        frame.grid(row=0, column=col, padx=4, sticky="ew")
        
        # Barra lateral de color institucional
        bar = tk.Frame(frame, bg=color, width=4)
        bar.pack(side="left", fill="y")
        
        content = tk.Frame(frame, bg="#ffffff", padx=8, pady=4)
        content.pack(side="left", fill="both", expand=True)
        
        lbl_titulo = tk.Label(content, text=titulo, font=("Segoe UI", 7, "bold"), fg=color, bg="#ffffff", anchor="w")
        lbl_titulo.pack(fill="x")
        
        lbl_valor = tk.Label(content, text=valor, font=("Segoe UI", 14, "bold"), fg="#2c3e50", bg="#ffffff", anchor="w")
        lbl_valor.pack(fill="x")
        
        lbl_sub = tk.Label(content, text=subtitulo, font=("Segoe UI", 7), fg="#7f8c8d", bg="#ffffff", anchor="w")
        lbl_sub.pack(fill="x")
        
        return lbl_valor

    def actualizar_metricas(self):
        total = len(self.bienes)
        operativos = sum(1 for b in self.bienes if b.get("mantenimiento") == "No")
        preventivos = sum(1 for b in self.bienes if "Preventivo" in b.get("mantenimiento", ""))
        correctivos = sum(1 for b in self.bienes if "Correctivo" in b.get("mantenimiento", ""))
        
        bajas_cnt = 0
        if os.path.exists(DB_BAJAS_FILE):
            try:
                with open(DB_BAJAS_FILE, 'r', encoding='utf-8') as f:
                    bajas_cnt = len(json.load(f))
            except Exception:
                bajas_cnt = 0

        self.card_total.config(text=str(total))
        self.card_operativos.config(text=str(operativos))
        self.card_preventivos.config(text=str(preventivos))
        self.card_correctivos.config(text=str(correctivos))
        self.card_bajas.config(text=str(bajas_cnt))

    def activar_foco_inicial(self):
        self.root.focus_force()
        self.entry_id.focus_force()

    # --- PROCESO DE BAJA CON JUSTIFICACIÓN Y GENERACIÓN DE PDF ---
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
            f"Indique la causa / motivo por el cual se da de baja el activo ID {id_bien}:\n({nombre_bien})",
            parent=self.root
        )
        
        if motivo is None:
            return
            
        motivo = motivo.strip()
        if not motivo:
            messagebox.showwarning("Motivo Requerido", "Debe ingresar una explicación válida para procesar la baja del activo.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Desincorporación", 
            f"¿Está seguro de desincorporar el activo ID {id_bien}?\n\nMotivo: {motivo}\n\nEsta acción registrará la baja y generará el acta PDF correspondiente."
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
            
            self.guardar_registro_baja(registro_baja)
            self.bienes = [b for b in self.bienes if b["id"] != id_bien]
            self.guardar_datos(self.bienes)
            
            archivo_generado = self.generar_acta_baja(registro_baja)
            
            self.actualizar_tabla()
            self.limpiar_formulario()
            
            messagebox.showinfo(
                "Baja Procesada con Éxito", 
                f"El activo ID {id_bien} ha sido desincorporado del inventario activo.\n\n"
                f"📄 Registro guardado en histórico.\n"
                f"📁 Documento generado: {archivo_generado}"
            )

    def guardar_registro_baja(self, registro):
        bajas = []
        if os.path.exists(DB_BAJAS_FILE):
            try:
                with open(DB_BAJAS_FILE, 'r', encoding='utf-8') as f:
                    bajas = json.load(f)
            except Exception:
                bajas = []
        bajas.append(registro)
        try:
            with open(DB_BAJAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(bajas, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error de Registro", f"No se pudo guardar la baja en el histórico: {e}")

    def generar_acta_baja(self, registro):
        nombre_base = f"Acta_Baja_ID_{registro['id']}"
        
        if HAS_REPORTLAB:
            archivo_pdf = f"{nombre_base}.pdf"
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 50, "SIGAR - SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS (UNELLEZ)")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 70, "ACTA DE DESINCORPORACIÓN Y BAJA DE ACTIVO")
            c.setLineWidth(1)
            c.line(50, height - 78, width - 50, height - 78)
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, height - 110, f"Fecha de Procesamiento: {registro['fecha_baja']}")
            c.drawString(50, height - 125, f"Código de Activo (ID): {registro['id']}")
            
            y = height - 160
            c.drawString(50, y, "DETALLES DEL EQUIPO:")
            c.setFont("Helvetica", 10)
            c.drawString(70, y - 18, f"• Descripción / Equipo: {registro['nombre']}")
            c.drawString(70, y - 34, f"• Asignación Previa: {registro['asignado_a']}")
            c.drawString(70, y - 50, f"• Registro de Mantenimiento: {registro['mantenimiento']}")
            c.drawString(70, y - 66, f"• Último Mantenimiento: {registro['fecha_ultimo_mant']}")
            if registro['desc_mant']:
                c.drawString(70, y - 82, f"• Detalle Mantenimiento: {registro['desc_mant']}")
                
            y_motivo = y - 120
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
            c.drawCentredString(155, y_firma - 15, "Responsable del Bien / Equipo")
            c.drawCentredString(415, y_firma - 15, "Autorizado por (Bienes y Suministros UNELLEZ)")
            
            c.drawCentredString(width / 2, 40, "Documento oficial generado automáticamente por SIGAR V1.0")
            c.save()
            return archivo_pdf
        else:
            archivo_txt = f"{nombre_base}.txt"
            contenido = f"""======================================================================
SIGAR (UNELLEZ) - SISTEMA DE GESTIÓN DE ACTIVOS Y RECURSOS
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
Responsable del Equipo                  Bienes y Suministros
======================================================================
"""
            with open(archivo_txt, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return archivo_txt

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
            
        bien = next((b for b in self.bienes if b["id"] == id_int), None)
        if not bien:
            messagebox.showerror("No Encontrado", f"No existe ningún activo registrado con el ID {id_int}.")
            return
            
        nombre_val = self.entry_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()
        mant_val = self.combo_mant.get()
        fecha_mant_val = self.entry_fecha_mant.get().strip()
        proximo_val = self.entry_proximo.get().strip()
        desc_mant_val = self.entry_desc_mant.get().strip()
        
        if not nombre_val or not asignado_val:
            messagebox.showwarning("Campos Incompletos", "Por favor, complete la Descripción / Nombre y el campo 'Asignado a'.")
            return
            
        bien["nombre"] = nombre_val
        bien["asignado_a"] = asignado_val
        bien["mantenimiento"] = mant_val
        bien["fecha_mant"] = fecha_mant_val if mant_val != "No" else "N/A"
        bien["proximo_mant"] = proximo_val if mant_val != "No" else "N/A"
        bien["desc_mant"] = desc_mant_val if mant_val != "No" else ""
        
        self.guardar_datos(self.bienes)
        
        opciones_actuales = list(self.combo_asignado["values"])
        if asignado_val not in opciones_actuales:
            opciones_actuales.append(asignado_val)
            self.combo_asignado["values"] = opciones_actuales
            
        self.actualizar_tabla()
        self.limpiar_formulario()
        messagebox.showinfo("Actualización Exitosa", f"Los datos del activo ID {id_int} han sido modificados correctamente.")

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
        opciones_base = ["Almacén / Stock", "Dirección General", "Coordinación de Sistemas", "Recursos Humanos"]
        existentes = list(opciones_base)
        for bien in self.bienes:
            val = bien.get("asignado_a")
            if val and val not in existentes:
                existentes.append(val)
        return existentes

    def cargar_datos(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    for d in datos:
                        if "asignado_a" not in d:
                            d["asignado_a"] = d.pop("estado", "Almacén / Stock")
                        if "mantenimiento" not in d:
                            d["mantenimiento"] = "No"
                        if "fecha_mant" not in d:
                            d["fecha_mant"] = "N/A"
                        if "proximo_mant" not in d:
                            d["proximo_mant"] = "N/A"
                        if "desc_mant" not in d:
                            d["desc_mant"] = ""
                    return datos
            except Exception:
                return []
        else:
            data_inicial = [
                {
                    "id": 1, 
                    "nombre": "Laptop Dell Latitude 3420 Core i7 16GB RAM SSD 512GB", 
                    "asignado_a": "Coordinación de Sistemas",
                    "mantenimiento": "Sí (Preventivo)",
                    "fecha_mant": "15/05/2026",
                    "proximo_mant": "17/08/2026",
                    "desc_mant": "Limpieza de ventiladores y cambio de pasta térmica"
                }
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
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for bien in self.bienes:
            self.tabla.insert("", "end", values=(
                bien["id"], 
                bien["nombre"], 
                bien.get("asignado_a", "N/A"),
                bien.get("mantenimiento", "No"),
                bien.get("fecha_mant", "N/A"),
                bien.get("proximo_mant", "N/A")
            ))
        self.actualizar_metricas()

    def agregar_bien(self):
        id_val = self.entry_id.get().strip()
        nombre_val = self.entry_nombre.get().strip()
        asignado_val = self.combo_asignado.get().strip()
        mant_val = self.combo_mant.get()
        fecha_mant_val = self.entry_fecha_mant.get().strip()
        proximo_val = self.entry_proximo.get().strip()
        desc_mant_val = self.entry_desc_mant.get().strip()
        
        if not id_val or not nombre_val or not asignado_val:
            messagebox.showwarning("Campos Incompletos", "Por favor, complete el ID, la Descripción / Nombre y el campo 'Asignado a'.")
            return
            
        try:
            id_int = int(id_val)
        except ValueError:
            messagebox.showwarning("Tipo Incorrecto", "El ID debe ser un valor numérico entero.")
            return
            
        if any(b["id"] == id_int for b in self.bienes):
            messagebox.showerror("ID Duplicado", f"El ID {id_int} ya existe. Si desea modificar este bien, use el botón 'Guardar Cambios'.")
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
        self.guardar_datos(self.bienes)
        
        opciones_actuales = list(self.combo_asignado["values"])
        if asignado_val not in opciones_actuales:
            opciones_actuales.append(asignado_val)
            self.combo_asignado["values"] = opciones_actuales
        
        self.actualizar_tabla()
        self.limpiar_formulario()
        messagebox.showinfo("Registro Exitoso", "El bien ha sido añadido correctamente.")

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioBienesApp(root)
    root.mainloop()