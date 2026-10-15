# -*- coding: utf-8 -*-
"""
Módulo de Autenticación y Control de Acceso - SIGART UNELLEZ VIPI
Punto de entrada principal para la compilación y ejecución segura del sistema.
"""
import hashlib
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import customtkinter as ctk

# Configuración inicial de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Manejo de rutas dinámicas para desarrollo local y empaquetado PyInstaller (.exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

DB_ACCESO = os.path.join(EXE_DIR, 'acceso.json')

# Soporte para encontrar submódulos si login.py está en la raíz o dentro de sigar-cliente-escritorio
RUTAS_MODULOS = [
    BASE_DIR,
    os.path.join(BASE_DIR, 'sigar-cliente-escritorio'),
    EXE_DIR,
    os.path.join(EXE_DIR, 'sigar-cliente-escritorio')
]
for r in RUTAS_MODULOS:
    if os.path.exists(r) and r not in sys.path:
        sys.path.insert(0, r)


def obtener_ruta_icono_ctsi():
    """Busca dinámicamente el archivo CTSI.png en todas las ubicaciones posibles."""
    posibles_rutas = [
        os.path.join(BASE_DIR, 'iconos', 'CTSI.png'),
        os.path.join(BASE_DIR, 'sigar-cliente-escritorio', 'iconos', 'CTSI.png'),
        os.path.join(EXE_DIR, 'iconos', 'CTSI.png'),
        os.path.join(EXE_DIR, 'sigar-cliente-escritorio', 'iconos', 'CTSI.png'),
        os.path.join(BASE_DIR, 'CTSI.png'),
        os.path.join(BASE_DIR, 'logo.png')
    ]
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            return ruta
    return None


class AuthApp:

    def __init__(self, root):
        self.root = root
        self.root.title('SIGART - Acceso Institucional (UNELLEZ VIPI)')
        self.root.geometry('400x560')
        self.root.minsize(380, 520)
        self.root.resizable(False, False)
        self.root.configure(fg_color='#0b1324')

        # Centrar la ventana en la pantalla
        self.root.update_idletasks()
        ancho = self.root.winfo_width()
        alto = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')

        self.mostrar_clave = False
        self.clave_hash = self.cargar_clave()
        self.construir_interfaz()

    def hash_password(self, password):
        """Genera el hash SHA-256 de la contraseña."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def cargar_clave(self):
        """Carga o genera la clave cifrada de acceso (por defecto: admin123)."""
        if os.path.exists(DB_ACCESO):
            try:
                with open(DB_ACCESO, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('clave', self.hash_password('admin123'))
            except Exception:
                return self.hash_password('admin123')
        else:
            clave_defecto = self.hash_password('admin123')
            self.guardar_clave(clave_defecto)
            return clave_defecto

    def guardar_clave(self, clave_hash):
        try:
            with open(DB_ACCESO, 'w', encoding='utf-8') as f:
                json.dump({'clave': clave_hash}, f, indent=4)
        except Exception as e:
            print(f'Error al guardar clave: {e}')

    def construir_interfaz(self):
        # Tarjeta central con estética SIGART
        self.card = ctk.CTkFrame(
            self.root,
            corner_radius=14,
            fg_color="#101d36",
            border_width=1,
            border_color="#1e293b"
        )
        self.card.pack(expand=True, fill="both", padx=25, pady=25)

        # --- AVATAR CIRCULAR CTSI ---
        self.canvas_avatar = tk.Canvas(
            self.card, width=104, height=104, bg='#101d36', highlightthickness=0
        )
        self.canvas_avatar.pack(pady=(20, 8))

        self.cargar_avatar_circular()

        # --- TITULOS INSTITUCIONALES ---
        f_tit = ctk.CTkFrame(self.card, fg_color="transparent")
        f_tit.pack(fill="x", padx=15, pady=(0, 2))

        ctk.CTkLabel(
            f_tit,
            text='SIGART',
            font=ctk.CTkFont(family="Georgia", size=24, weight="bold"),
            text_color='#FF6600'
        ).pack()

        ctk.CTkLabel(
            self.card,
            text='UNELLEZ — VICERRECTORADO VIPI',
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color='#38bdf8'
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            self.card,
            text='Gestión y Control de Activos Tecnológicos',
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color='#94a3b8'
        ).pack(pady=(0, 12))

        # Línea separadora sutil
        ctk.CTkFrame(self.card, height=1, fg_color="#1e293b").pack(fill="x", padx=25, pady=(0, 12))

        # --- MENSAJE DE ERROR ---
        self.lbl_error = ctk.CTkLabel(
            self.card,
            text='',
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color='#f87171',
            wraplength=280
        )
        self.lbl_error.pack(fill='x', pady=(0, 6))

        # --- CAMPO CONTRASEÑA ---
        f_entry_box = ctk.CTkFrame(self.card, fg_color="transparent")
        f_entry_box.pack(fill="x", padx=25, pady=(0, 16))

        ctk.CTkLabel(
            f_entry_box,
            text='Contraseña de Acceso:',
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color='#cbd5e1'
        ).pack(anchor='w', pady=(0, 4))

        f_input_row = ctk.CTkFrame(f_entry_box, fg_color="transparent")
        f_input_row.pack(fill="x")

        self.entry_pass = ctk.CTkEntry(
            f_input_row,
            font=("Segoe UI", 12),
            show='•',
            height=36,
            corner_radius=8,
            placeholder_text="Ingrese su clave institucional...",
            fg_color="#090d16",
            border_color="#334155"
        )
        self.entry_pass.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_pass.bind('<Return>', lambda e: self.procesar_login())
        self.entry_pass.bind('<Key>', lambda e: self.limpiar_error())

        # Botón para alternar visibilidad de contraseña
        self.btn_ver_clave = ctk.CTkButton(
            f_input_row,
            text="👁",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.toggle_mostrar_clave
        )
        self.btn_ver_clave.pack(side="right")

        # --- BOTÓN INGRESAR ---
        self.btn_ingresar = ctk.CTkButton(
            self.card,
            text='Ingresar al Sistema',
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color='#0284c7',
            hover_color='#0369a1',
            height=38,
            corner_radius=8,
            command=self.procesar_login
        )
        self.btn_ingresar.pack(fill='x', padx=25, pady=(0, 15))

        # Pie informativo
        ctk.CTkLabel(
            self.card,
            text="Coordinación de Tecnología (CTSI)",
            font=ctk.CTkFont(size=9),
            text_color="#64748b"
        ).pack(side="bottom", pady=(0, 10))

        self.root.after(150, lambda: self.entry_pass.focus_force())

    def toggle_mostrar_clave(self):
        """Muestra u oculta los caracteres de la contraseña."""
        self.mostrar_clave = not self.mostrar_clave
        if self.mostrar_clave:
            self.entry_pass.configure(show="")
            self.btn_ver_clave.configure(fg_color="#0284c7")
        else:
            self.entry_pass.configure(show="•")
            self.btn_ver_clave.configure(fg_color="#1e293b")

    def limpiar_error(self):
        self.lbl_error.configure(text='')
        self.entry_pass.configure(border_color="#334155")

    def cargar_avatar_circular(self):
        """Carga CTSI.png perfectamente centrado, eliminando aros artificiales desalineados."""
        diametro = 104
        size = (diametro, diametro)
        ruta_ctsi = obtener_ruta_icono_ctsi()

        if ruta_ctsi:
            try:
                img_raw = Image.open(ruta_ctsi).convert('RGBA')

                # 1. Recortar bordes transparentes sobrantes
                bbox = img_raw.getbbox()
                if bbox:
                    img_raw = img_raw.crop(bbox)

                # 2. Cuadrar el centro exacto para evitar cualquier desfase de píxeles
                w, h = img_raw.size
                lado = max(w, h)
                img_cuadrada = Image.new('RGBA', (lado, lado), (0, 0, 0, 0))
                # Centrado milimétrico
                img_cuadrada.paste(img_raw, ((lado - w) // 2, (lado - h) // 2))

                # 3. Escalar al tamaño completo (100x100) con suavizado de bordes
                target_dim = 100
                metodo_resize = (
                    getattr(Image, "Resampling", Image).LANCZOS
                    if hasattr(Image, "Resampling")
                    else Image.ANTIALIAS
                )
                img_final = img_cuadrada.resize((target_dim, target_dim), metodo_resize)

                # 4. Pegar en el lienzo centrado (sin aros artificiales que choquen con el logo)
                output = Image.new('RGBA', size, (0, 0, 0, 0))
                pos_x = (diametro - target_dim) // 2
                pos_y = (diametro - target_dim) // 2
                output.paste(img_final, (pos_x, pos_y), mask=img_final)

                self.img_tk = ImageTk.PhotoImage(output)
                self.canvas_avatar.create_image(diametro // 2, diametro // 2, image=self.img_tk)
                return
            except Exception as e:
                print(f'Error al cargar avatar CTSI: {e}')

        # Fallback si no encontrara la imagen
        self.canvas_avatar.create_oval(
            4, 4, 100, 100, fill='#0b1324', outline='#0284c7', width=2
        )
        self.canvas_avatar.create_text(
            52, 52, text='CTSI', fill='#38bdf8', font=('Segoe UI', 15, 'bold')
        )

    def procesar_login(self):
        password = self.entry_pass.get().strip()

        if not password:
            self.lbl_error.configure(text='⚠️ Ingrese su contraseña de acceso.')
            self.entry_pass.configure(border_color='#ef4444')
            return

        if self.hash_password(password) == self.clave_hash:
            self.lbl_error.configure(text='')
            self.abrir_sistema_principal()
        else:
            self.lbl_error.configure(text='❌ Contraseña incorrecta.')
            self.entry_pass.configure(border_color='#ef4444')
            self.entry_pass.delete(0, tk.END)

    def abrir_sistema_principal(self):
        """Cierra el Login e inicia la aplicación principal SIGART de forma limpia."""
        try:
            from main import InventarioBienesApp

            self.root.destroy()  # Cierra la ventana de acceso

            main_root = ctk.CTk()
            app = InventarioBienesApp(main_root)
            main_root.mainloop()

        except Exception as e:
            import traceback
            error_detallado = traceback.format_exc()
            err_root = tk.Tk()
            err_root.withdraw()
            messagebox.showerror(
                'Error de Inicio',
                f'No se pudo iniciar el sistema principal:\n\n{e}\n\nDetalle:\n{error_detallado[:400]}...',
            )
            err_root.destroy()


if __name__ == '__main__':
    root = ctk.CTk()
    app = AuthApp(root)
    root.mainloop()