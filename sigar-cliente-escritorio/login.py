# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Importar el módulo principal de la aplicación
try:
    from app_inventario import InventarioBienesApp
    HAS_APP_INVENTARIO = True
except ImportError:
    HAS_APP_INVENTARIO = False

# --- CONFIGURACIÓN DE CONEXIÓN A LA API EN RENDER (UNELLEZ) ---
BASE_URL = "https://sigar-unellez.onrender.com"

API_LOGIN_URL = f"{BASE_URL}/api/auth/login"
API_REGISTER_URL = f"{BASE_URL}/api/auth/register"


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGAR (UNELLEZ) - Inicio de Sesión")
        self.root.geometry("400x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#0b3c5d")  # Azul corporativo SIGAR
        
        # Centrar ventana en la pantalla
        self.centrar_ventana(self.root, 400, 520)
        
        # --- CONTENEDOR PRINCIPAL ---
        frame_card = tk.Frame(root, bg="#ffffff", bd=0, relief="flat")
        frame_card.pack(expand=True, fill="both", padx=25, pady=25)
        
        # Título y Encabezado
        lbl_titulo = tk.Label(
            frame_card, 
            text="SIGAR", 
            font=("Segoe UI", 24, "bold"), 
            fg="#0b3c5d", 
            bg="#ffffff"
        )
        lbl_titulo.pack(pady=(20, 2))
        
        lbl_subtitulo = tk.Label(
            frame_card, 
            text="Gestión de Activos y Recursos", 
            font=("Segoe UI", 9, "italic"), 
            fg="#7f8c8d", 
            bg="#ffffff"
        )
        lbl_subtitulo.pack(pady=(0, 15))
        
        # --- CAMPOS DE ENTRADA ---
        frame_inputs = tk.Frame(frame_card, bg="#ffffff")
        frame_inputs.pack(fill="x", padx=20)
        
        # Campo: Usuario
        tk.Label(
            frame_inputs, 
            text="Usuario:", 
            font=("Segoe UI", 9, "bold"), 
            fg="#2c3e50", 
            bg="#ffffff", 
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.entry_usuario = tk.Entry(
            frame_inputs, 
            font=("Segoe UI", 10), 
            bg="#f8f9fa", 
            fg="#000000", 
            relief="solid", 
            bd=1, 
            insertbackground="black"
        )
        self.entry_usuario.pack(fill="x", ipady=5, pady=(0, 10))
        self.entry_usuario.focus_set()
        
        # Campo: Contraseña
        tk.Label(
            frame_inputs, 
            text="Contraseña:", 
            font=("Segoe UI", 9, "bold"), 
            fg="#2c3e50", 
            bg="#ffffff", 
            anchor="w"
        ).pack(fill="x", pady=(5, 2))
        
        self.entry_password = tk.Entry(
            frame_inputs, 
            font=("Segoe UI", 10), 
            bg="#f8f9fa", 
            fg="#000000", 
            show="•", 
            relief="solid", 
            bd=1, 
            insertbackground="black"
        )
        self.entry_password.pack(fill="x", ipady=5, pady=(0, 12))
        
        # Enlazar la tecla Enter para iniciar sesión
        self.root.bind('<Return>', lambda event: self.validar_login())
        
        # --- BOTONES DE ACCIÓN ---
        self.btn_ingresar = tk.Button(
            frame_card, 
            text="INICIAR SESIÓN", 
            font=("Segoe UI", 10, "bold"), 
            bg="#328cc1", 
            fg="#ffffff", 
            activebackground="#0b3c5d", 
            activeforeground="#ffffff", 
            bd=0, 
            cursor="hand2", 
            command=self.validar_login
        )
        self.btn_ingresar.pack(fill="x", padx=20, ipady=7, pady=(5, 8))

        self.btn_registrar = tk.Button(
            frame_card, 
            text="Crear Nueva Cuenta", 
            font=("Segoe UI", 9, "bold"), 
            bg="#e9ecef", 
            fg="#0b3c5d", 
            activebackground="#d6d8db", 
            bd=0, 
            cursor="hand2", 
            command=self.abrir_ventana_registro
        )
        self.btn_registrar.pack(fill="x", padx=20, ipady=5, pady=(0, 10))
        
        # Indicador de estado de conexión
        self.lbl_status = tk.Label(
            frame_card, 
            text="🌐 Sincronizado con UNELLEZ Cloud", 
            font=("Segoe UI", 8), 
            fg="#95a5a6", 
            bg="#ffffff"
        )
        self.lbl_status.pack(side="bottom", pady=5)

    def centrar_ventana(self, vent, ancho, alto):
        vent.update_idletasks()
        pantalla_ancho = vent.winfo_screenwidth()
        pantalla_alto = vent.winfo_screenheight()
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)
        vent.geometry(f"{ancho}x{alto}+{x}+{y}")

    def validar_login(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()
        
        if not usuario or not password:
            messagebox.showwarning("Campos Incompletos", "Por favor, ingrese su usuario y contraseña.")
            return
            
        # Feedback visual inmediato
        self.btn_ingresar.config(state="disabled", text="CONECTANDO A LA NUBE...")
        self.lbl_status.config(text="⏳ Despertando servidor en Render (puede tardar ~30s)...", fg="#d35400")
        self.root.update_idletasks()
        
        payload = {"username": usuario, "password": password}
        
        try:
            # Timeout de 45s para contemplar el inicio en frío de Render
            respuesta = requests.post(API_LOGIN_URL, json=payload, timeout=45)
            
            if respuesta.status_code == 200:
                self.abrir_sistema_principal()
            elif respuesta.status_code == 401:
                messagebox.showerror("Acceso Denegado", "Usuario o contraseña incorrectos.")
                self.entry_password.delete(0, tk.END)
                self.entry_password.focus_set()
            else:
                err_msg = respuesta.json().get("detail", "Error en el servidor.")
                messagebox.showerror("Error de Autenticación", f"Respuesta del servidor: {err_msg}")
                
        except requests.exceptions.Timeout:
            messagebox.showerror("Tiempo Agotado", "El servidor tardó más de 45 segundos en responder.\nPor favor, intenta hacer clic en INICIAR SESIÓN una vez más.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar con el servidor:\n{e}")
        finally:
            self.btn_ingresar.config(state="normal", text="INICIAR SESIÓN")
            self.lbl_status.config(text="🌐 Sincronizado con UNELLEZ Cloud", fg="#95a5a6")

    def abrir_ventana_registro(self):
        """Ventana modal para registrar un nuevo usuario en la API de Render."""
        win_reg = tk.Toplevel(self.root)
        win_reg.title("SIGAR - Registrar Usuario")
        win_reg.geometry("350x420")
        win_reg.resizable(False, False)
        win_reg.configure(bg="#f4f6f9")
        win_reg.grab_set()  # Bloquea la ventana principal mientras está abierta
        
        self.centrar_ventana(win_reg, 350, 420)
        
        frame_reg = tk.Frame(win_reg, bg="#ffffff", bd=1, relief="solid")
        frame_reg.pack(fill="both", expand=True, padx=15, pady=15)
        
        tk.Label(frame_reg, text="Nuevo Usuario", font=("Segoe UI", 14, "bold"), fg="#0b3c5d", bg="#ffffff").pack(pady=(15, 10))
        
        # Campo Usuario
        tk.Label(frame_reg, text="Nombre de Usuario:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", padx=15, pady=(5, 2))
        ent_usr = tk.Entry(frame_reg, font=("Segoe UI", 10), bg="#f8f9fa", relief="solid", bd=1)
        ent_usr.pack(fill="x", padx=15, ipady=4, pady=(0, 10))
        ent_usr.focus_set()
        
        # Campo Contraseña
        tk.Label(frame_reg, text="Contraseña:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", padx=15, pady=(5, 2))
        ent_pass1 = tk.Entry(frame_reg, font=("Segoe UI", 10), bg="#f8f9fa", show="•", relief="solid", bd=1)
        ent_pass1.pack(fill="x", padx=15, ipady=4, pady=(0, 10))
        
        # Campo Confirmar Contraseña
        tk.Label(frame_reg, text="Confirmar Contraseña:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", padx=15, pady=(5, 2))
        ent_pass2 = tk.Entry(frame_reg, font=("Segoe UI", 10), bg="#f8f9fa", show="•", relief="solid", bd=1)
        ent_pass2.pack(fill="x", padx=15, ipady=4, pady=(0, 15))
        
        def enviar_registro():
            u = ent_usr.get().strip()
            p1 = ent_pass1.get().strip()
            p2 = ent_pass2.get().strip()
            
            if not u or not p1 or not p2:
                messagebox.showwarning("Campos Incompletos", "Por favor complete todos los campos.", parent=win_reg)
                return
                
            if p1 != p2:
                messagebox.showerror("Contraseñas no coinciden", "Las contraseñas ingresadas no son iguales.", parent=win_reg)
                return
                
            payload = {"username": u, "password": p1}
            try:
                r = requests.post(API_REGISTER_URL, json=payload, timeout=12)
                if r.status_code == 200:
                    messagebox.showinfo("Registro Exitoso", f"El usuario '{u}' ha sido creado correctamente en la nube.", parent=win_reg)
                    win_reg.destroy()
                    self.entry_usuario.delete(0, tk.END)
                    self.entry_usuario.insert(0, u)
                    self.entry_password.focus_set()
                else:
                    err = r.json().get("detail", "Error al registrar el usuario.")
                    messagebox.showerror("Error de Registro", err, parent=win_reg)
            except Exception as e:
                messagebox.showerror("Error de Conexión", f"No se pudo conectar con Render: {e}", parent=win_reg)

        btn_confirmar = tk.Button(
            frame_reg, 
            text="REGISTRAR CUENTA", 
            font=("Segoe UI", 9, "bold"), 
            bg="#27ae60", 
            fg="#ffffff", 
            bd=0, 
            cursor="hand2", 
            command=enviar_registro
        )
        btn_confirmar.pack(fill="x", padx=15, ipady=6, pady=(5, 10))

    def abrir_sistema_principal(self):
        if not HAS_APP_INVENTARIO:
            messagebox.showerror("Error de Archivos", "No se encontró el módulo 'app_inventario.py' en la misma carpeta.")
            return

        self.root.destroy()
        
        root_inventario = tk.Tk()
        app = InventarioBienesApp(root_inventario)
        root_inventario.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()