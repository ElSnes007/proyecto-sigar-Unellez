# -*- coding: utf-8 -*-
import json
import os
import hashlib
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

# Importar la aplicación principal del inventario
try:
    from app_inventario import InventarioBienesApp
except ImportError:
    InventarioBienesApp = None

DB_ACCESO = "acceso.json"

class AuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR - Acceso al Sistema")
        self.root.geometry("380x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#0b1329")

        self.clave_hash = self.cargar_clave()

        # Construcción de la interfaz
        self.construir_interfaz()

    def hash_password(self, password):
        """Encripta la contraseña usando SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def cargar_clave(self):
        """Carga el hash de la contraseña. Si no existe, establece 'admin123' por defecto."""
        if os.path.exists(DB_ACCESO):
            try:
                with open(DB_ACCESO, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("clave", self.hash_password("admin123"))
            except Exception:
                return self.hash_password("admin123")
        else:
            clave_defecto = self.hash_password("admin123")
            self.guardar_clave(clave_defecto)
            return clave_defecto

    def guardar_clave(self, clave_hash):
        try:
            with open(DB_ACCESO, 'w', encoding='utf-8') as f:
                json.dump({"clave": clave_hash}, f, indent=4)
        except Exception as e:
            print(f"Error al guardar clave: {e}")

    def construir_interfaz(self):
        main_frame = tk.Frame(self.root, bg="#0b1329")
        main_frame.pack(expand=True, fill="both", padx=30, pady=25)

        # --- LOGO / AVATAR CIRCULAR ---
        self.canvas_avatar = tk.Canvas(main_frame, width=120, height=120, bg="#0b1329", highlightthickness=0)
        self.canvas_avatar.pack(pady=(5, 10))

        self.cargar_avatar_circular()

        # --- TÍTULOS ---
        lbl_titulo = tk.Label(main_frame, text="SIGAR", font=("Segoe UI", 22, "bold"), fg="#ffffff", bg="#0b1329")
        lbl_titulo.pack(pady=(0, 2))

        lbl_subtitulo = tk.Label(
            main_frame, 
            text="Sistema de Inventario Local y Gestión", 
            font=("Segoe UI", 9), 
            fg="#94a3b8", 
            bg="#0b1329"
        )
        lbl_subtitulo.pack(pady=(0, 15))

        # --- LABEL PARA MENSAJES DE ERROR/ALERTA INTEGRADOS ---
        # Inicialmente vacío; usa un tono rojo/coral suave (#f87171)
        self.lbl_error = tk.Label(
            main_frame, 
            text="", 
            font=("Segoe UI", 9, "bold"), 
            fg="#f87171", 
            bg="#0b1329",
            wraplength=310,
            justify="center"
        )
        self.lbl_error.pack(fill="x", pady=(0, 8))

        # --- CAMPO DE CONTRASEÑA ---
        lbl_pass = tk.Label(main_frame, text="Contraseña de Acceso:", font=("Segoe UI", 9, "bold"), fg="#cbd5e1", bg="#0b1329")
        lbl_pass.pack(anchor="w", pady=(0, 5))

        self.entry_pass = tk.Entry(
            main_frame, 
            font=("Segoe UI", 11), 
            show="•", 
            bg="#18243b", 
            fg="#ffffff", 
            insertbackground="#ffffff", 
            bd=0, 
            relief="flat",
            highlightthickness=1,
            highlightbackground="#2b3e63",
            highlightcolor="#38bdf8"
        )
        self.entry_pass.pack(fill="x", ipady=7, pady=(0, 18))
        self.entry_pass.bind("<Return>", lambda e: self.procesar_login())
        # Limpia el mensaje de error cuando el usuario empieza a escribir nuevamente
        self.entry_pass.bind("<Key>", lambda e: self.lbl_error.config(text=""))

        # --- BOTÓN DE INGRESO ---
        btn_ingresar = tk.Button(
            main_frame, 
            text="Ingresar al Sistema", 
            bg="#0284c7", 
            fg="white", 
            activebackground="#0369a1", 
            activeforeground="white",
            font=("Segoe UI", 10, "bold"), 
            bd=0, 
            pady=9, 
            cursor="hand2", 
            command=self.procesar_login
        )
        btn_ingresar.pack(fill="x")

        # Foco automático en la caja de contraseña
        self.root.after(100, lambda: self.entry_pass.focus_force())

    def cargar_avatar_circular(self):
        """Busca una imagen del logo y la recorta en círculo; de lo contrario crea un emblema."""
        size = (110, 110)
        posibles_rutas = ["logo.png", "icon.png", "unellez_logo.png", "assets/logo.png"]
        ruta_encontrada = None

        for r in posibles_rutas:
            if os.path.exists(r):
                ruta_encontrada = r
                break

        if ruta_encontrada:
            try:
                img_raw = Image.open(ruta_encontrada).convert("RGBA")
                img_raw = img_raw.resize(size, Image.Resampling.LANCZOS)
                
                mask = Image.new("L", size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, size[0], size[1]), fill=255)
                
                output = Image.new("RGBA", size, (0, 0, 0, 0))
                output.paste(img_raw, (0, 0), mask=mask)
                
                self.img_tk = ImageTk.PhotoImage(output)
                self.canvas_avatar.create_image(60, 60, image=self.img_tk)
                return
            except Exception:
                pass

        # Avatar circular por defecto
        self.canvas_avatar.create_oval(5, 5, 115, 115, fill="#1e293b", outline="#0284c7", width=3)
        self.canvas_avatar.create_text(60, 60, text="SIGAR", fill="#38bdf8", font=("Segoe UI", 16, "bold"))

    def procesar_login(self):
        password = self.entry_pass.get().strip()

        if not password:
            self.lbl_error.config(text="⚠️ Por favor, ingrese la contraseña de acceso.")
            self.entry_pass.config(highlightbackground="#ef4444")  # Resalta la casilla en rojo suave
            return

        if self.hash_password(password) == self.clave_hash:
            self.lbl_error.config(text="")
            self.abrir_sistema_principal()
        else:
            self.lbl_error.config(text="❌ Contraseña incorrecta. Intente de nuevo.")
            self.entry_pass.config(highlightbackground="#ef4444")
            self.entry_pass.delete(0, tk.END)

    def abrir_sistema_principal(self):
        """Cierra la ventana de login e inicia la pantalla principal."""
        self.root.destroy()
        main_root = tk.Tk()
        if InventarioBienesApp:
            app = InventarioBienesApp(main_root)
        main_root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = AuthApp(root)
    root.mainloop()