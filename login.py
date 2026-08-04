# -*- coding: utf-8 -*-
import json
import os
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox

# Importar la aplicación principal del inventario
from app_inventario import InventarioBienesApp

# Archivo de persistencia de usuarios
DB_USUARIOS = "usuarios.json"

class AuthApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR - Acceso al Sistema")
        self.root.geometry("400x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#f4f6f9")
        
        self.usuarios = self.cargar_usuarios()
        
        # Estilos
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # --- ENCABEZADO ---
        frame_header = tk.Frame(root, bg="#0b3c5d", height=80)
        frame_header.pack(fill="x")
        
        lbl_titulo = tk.Label(frame_header, text="SIGAR", font=("Segoe UI", 20, "bold"), fg="white", bg="#0b3c5d")
        lbl_titulo.pack(pady=(15, 0))
        lbl_subtitulo = tk.Label(frame_header, text="Gestión de Activos y Recursos", font=("Segoe UI", 9), fg="#e0e0e0", bg="#0b3c5d")
        lbl_subtitulo.pack(pady=(0, 15))

        # --- CONTENEDOR PRINCIPAL ---
        self.frame_cuerpo = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
        self.frame_cuerpo.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Estado inicial (Modo 'login' o 'registro')
        self.modo_registro = False
        self.construir_formulario()

    def hash_password(self, password):
        """Encripta la contraseña usando SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def cargar_usuarios(self):
        """Carga la lista de usuarios. Si no existe, crea un usuario por defecto admin/admin123."""
        if os.path.exists(DB_USUARIOS):
            try:
                with open(DB_USUARIOS, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        else:
            # Usuario inicial por defecto
            admin_defecto = {
                "admin": self.hash_password("admin123")
            }
            self.guardar_usuarios(admin_defecto)
            return admin_defecto

    def guardar_usuarios(self, usuarios):
        try:
            with open(DB_USUARIOS, 'w', encoding='utf-8') as f:
                json.dump(usuarios, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de usuarios: {e}")

    def construir_formulario(self):
        # Limpiar widgets existentes en el frame
        for widget in self.frame_cuerpo.winfo_children():
            widget.destroy()

        if not self.modo_registro:
            # --- FORMULARIO DE INICIO DE SESIÓN ---
            tk.Label(self.frame_cuerpo, text="Iniciar Sesión", font=("Segoe UI", 14, "bold"), fg="#0b3c5d", bg="#ffffff").pack(pady=(15, 15))

            tk.Label(self.frame_cuerpo, text="Usuario:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
            self.entry_user = tk.Entry(self.frame_cuerpo, font=("Segoe UI", 10), bg="#f9f9f9", relief="solid", bd=1)
            self.entry_user.pack(fill="x", padx=20, pady=(2, 12))

            tk.Label(self.frame_cuerpo, text="Contraseña:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
            self.entry_pass = tk.Entry(self.frame_cuerpo, font=("Segoe UI", 10), show="*", bg="#f9f9f9", relief="solid", bd=1)
            self.entry_pass.pack(fill="x", padx=20, pady=(2, 20))
            self.entry_pass.bind("<Return>", lambda e: self.procesar_login())

            btn_ingresar = tk.Button(self.frame_cuerpo, text="Ingresar al Sistema", bg="#328cc1", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=8, cursor="hand2", command=self.procesar_login)
            btn_ingresar.pack(fill="x", padx=20, pady=(0, 15))

            lbl_toggle = tk.Label(self.frame_cuerpo, text="¿No tienes cuenta? Regístrate aquí", font=("Segoe UI", 9, "underline"), fg="#0b3c5d", bg="#ffffff", cursor="hand2")
            lbl_toggle.pack()
            lbl_toggle.bind("<Button-1>", lambda e: self.toggle_modo())
            
        else:
            # --- FORMULARIO DE REGISTRO ---
            tk.Label(self.frame_cuerpo, text="Crear Nueva Cuenta", font=("Segoe UI", 14, "bold"), fg="#0b3c5d", bg="#ffffff").pack(pady=(10, 10))

            tk.Label(self.frame_cuerpo, text="Nuevo Usuario:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
            self.entry_user = tk.Entry(self.frame_cuerpo, font=("Segoe UI", 10), bg="#f9f9f9", relief="solid", bd=1)
            self.entry_user.pack(fill="x", padx=20, pady=(2, 8))

            tk.Label(self.frame_cuerpo, text="Contraseña:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
            self.entry_pass = tk.Entry(self.frame_cuerpo, font=("Segoe UI", 10), show="*", bg="#f9f9f9", relief="solid", bd=1)
            self.entry_pass.pack(fill="x", padx=20, pady=(2, 8))

            tk.Label(self.frame_cuerpo, text="Confirmar Contraseña:", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)
            self.entry_pass_confirm = tk.Entry(self.frame_cuerpo, font=("Segoe UI", 10), show="*", bg="#f9f9f9", relief="solid", bd=1)
            self.entry_pass_confirm.pack(fill="x", padx=20, pady=(2, 15))

            btn_registrar = tk.Button(self.frame_cuerpo, text="Registrar Usuario", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), bd=0, pady=8, cursor="hand2", command=self.procesar_registro)
            btn_registrar.pack(fill="x", padx=20, pady=(0, 10))

            lbl_toggle = tk.Label(self.frame_cuerpo, text="¿Ya tienes cuenta? Inicia sesión", font=("Segoe UI", 9, "underline"), fg="#0b3c5d", bg="#ffffff", cursor="hand2")
            lbl_toggle.pack()
            lbl_toggle.bind("<Button-1>", lambda e: self.toggle_modo())

        self.root.after(100, lambda: self.entry_user.focus_force())

    def toggle_modo(self):
        self.modo_registro = not self.modo_registro
        self.construir_formulario()

    def procesar_login(self):
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not user or not password:
            messagebox.showwarning("Campos Incompletos", "Por favor, ingrese usuario y contraseña.")
            return

        pass_hash = self.hash_password(password)

        if user in self.usuarios and self.usuarios[user] == pass_hash:
            messagebox.showinfo("Acceso Concedido", f"Bienvenido al sistema SIGAR, {user}.")
            self.abrir_sistema_principal()
        else:
            messagebox.showerror("Acceso Denegado", "Usuario o contraseña incorrectos.")

    def procesar_registro(self):
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        confirm = self.entry_pass_confirm.get().strip()

        if not user or not password or not confirm:
            messagebox.showwarning("Campos Incompletos", "Todos los campos son obligatorios.")
            return

        if password != confirm:
            messagebox.showerror("Error de Contraseña", "Las contraseñas no coinciden.")
            return

        if len(password) < 4:
            messagebox.showwarning("Seguridad Debil", "La contraseña debe tener al menos 4 caracteres.")
            return

        if user in self.usuarios:
            messagebox.showerror("Usuario Existente", "El nombre de usuario ya está registrado.")
            return

        # Guardar nuevo usuario
        self.usuarios[user] = self.hash_password(password)
        self.guardar_usuarios(self.usuarios)
        
        messagebox.showinfo("Registro Exitoso", "La cuenta se ha creado correctamente. Ya puedes iniciar sesión.")
        self.toggle_modo()

    def abrir_sistema_principal(self):
        """Cierra la ventana de login y abre la ventana principal SIGAR."""
        self.root.destroy()  # Destruye la ventana de Login
        
        main_root = tk.Tk()
        app = InventarioBienesApp(main_root)
        main_root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = AuthApp(root)
    root.mainloop()