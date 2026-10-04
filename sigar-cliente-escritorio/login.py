# -*- coding: utf-8 -*-
import hashlib
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk

# Manejo de rutas dinámicas para PyInstaller y entorno local
if getattr(sys, 'frozen', False):
  BASE_DIR = sys._MEIPASS
  EXE_DIR = os.path.dirname(sys.executable)
else:
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  EXE_DIR = BASE_DIR

DB_ACCESO = os.path.join(EXE_DIR, 'acceso.json')
CLIENTE_DIR = os.path.join(BASE_DIR, 'sigar-cliente-escritorio')

# Añadir el directorio del cliente al PATH de Python para importar main.py y sus submódulos
if CLIENTE_DIR not in sys.path:
  sys.path.insert(0, CLIENTE_DIR)


class AuthApp:

  def __init__(self, root):
    self.root = root
    self.root.title('SIGAR - Acceso Local')
    self.root.geometry('380x500')
    self.root.resizable(False, False)
    self.root.configure(bg='#0b1329')

    # Centrar la ventana en pantalla
    self.root.update_idletasks()
    width = self.root.winfo_width()
    height = self.root.winfo_height()
    x = (self.root.winfo_screenwidth() // 2) - (width // 2)
    y = (self.root.winfo_screenheight() // 2) - (height // 2)
    self.root.geometry(f'{width}x{height}+{x}+{y}')

    self.clave_hash = self.cargar_clave()
    self.construir_interfaz()

  def hash_password(self, password):
    """Encripta la contraseña con SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

  def cargar_clave(self):
    """Carga o genera acceso.json junto al ejecutable."""
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
    main_frame = tk.Frame(self.root, bg='#0b1329')
    main_frame.pack(expand=True, fill='both', padx=30, pady=25)

    # --- AVATAR CIRCULAR ---
    self.canvas_avatar = tk.Canvas(
        main_frame, width=120, height=120, bg='#0b1329', highlightthickness=0
    )
    self.canvas_avatar.pack(pady=(0, 10))

    self.cargar_avatar_circular()

    # --- TITULOS ---
    lbl_titulo = tk.Label(
        main_frame,
        text='SIGAR',
        font=('Segoe UI', 22, 'bold'),
        fg='#ffffff',
        bg='#0b1329',
    )
    lbl_titulo.pack(pady=(0, 2))

    lbl_subtitulo = tk.Label(
        main_frame,
        text='Gestión e Inventario Local',
        font=('Segoe UI', 9),
        fg='#94a3b8',
        bg='#0b1329',
    )
    lbl_subtitulo.pack(pady=(0, 15))

    # --- ERROR ---
    self.lbl_error = tk.Label(
        main_frame,
        text='',
        font=('Segoe UI', 9, 'bold'),
        fg='#f87171',
        bg='#0b1329',
        wraplength=310,
        justify='center',
    )
    self.lbl_error.pack(fill='x', pady=(0, 8))

    # --- CONTRASEÑA ---
    lbl_pass = tk.Label(
        main_frame,
        text='Contraseña de Acceso:',
        font=('Segoe UI', 9, 'bold'),
        fg='#cbd5e1',
        bg='#0b1329',
    )
    lbl_pass.pack(anchor='w', pady=(0, 5))

    self.entry_pass = tk.Entry(
        main_frame,
        font=('Segoe UI', 11),
        show='•',
        bg='#18243b',
        fg='#ffffff',
        insertbackground='#ffffff',
        bd=0,
        relief='flat',
        highlightthickness=1,
        highlightbackground='#2b3e63',
        highlightcolor='#38bdf8',
    )
    self.entry_pass.pack(fill='x', ipady=4, pady=(0, 18))
    self.entry_pass.bind('<Return>', lambda e: self.procesar_login())
    self.entry_pass.bind('<Key>', lambda e: self.limpiar_error())

    # --- BOTON INGRESAR ---
    btn_ingresar = tk.Button(
        main_frame,
        text='Ingresar',
        bg='#0284c7',
        fg='white',
        activebackground='#0369a1',
        activeforeground='white',
        font=('Segoe UI', 10, 'bold'),
        bd=0,
        pady=9,
        cursor='hand2',
        command=self.procesar_login,
    )
    btn_ingresar.pack(fill='x')

    self.root.after(100, lambda: self.entry_pass.focus_force())

  def limpiar_error(self):
    self.lbl_error.config(text='')
    self.entry_pass.config(highlightbackground='#2b3e63')

  def cargar_avatar_circular(self):
    size = (110, 110)
    posibles_rutas = [
        os.path.join(BASE_DIR, 'logo.png'),
        os.path.join(BASE_DIR, 'upscalemedia-transformed.jpeg'),
        os.path.join(BASE_DIR, 'foto_perfil.png'),
    ]

    ruta_encontrada = next((r for r in posibles_rutas if os.path.exists(r)), None)

    if ruta_encontrada:
      try:
        img_raw = Image.open(ruta_encontrada).convert('RGBA')
        img_raw = img_raw.resize(size, Image.Resampling.LANCZOS)

        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)

        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(img_raw, (0, 0), mask=mask)

        self.img_tk = ImageTk.PhotoImage(output)
        self.canvas_avatar.create_image(60, 60, image=self.img_tk)
        return
      except Exception as e:
        print(f'Error al cargar imagen de avatar: {e}')

    self.canvas_avatar.create_oval(
        5, 5, 115, 115, fill='#1e293b', outline='#0284c7', width=3
    )
    self.canvas_avatar.create_text(
        60, 60, text='SIGAR', fill='#38bdf8', font=('Segoe UI', 16, 'bold')
    )

  def procesar_login(self):
    password = self.entry_pass.get().strip()

    if not password:
      self.lbl_error.config(
          text='⚠️ Por favor, ingrese la contraseña de acceso.'
      )
      self.entry_pass.config(highlightbackground='#ef4444')
      return

    if self.hash_password(password) == self.clave_hash:
      self.lbl_error.config(text='')
      self.abrir_sistema_principal()
    else:
      self.lbl_error.config(text='❌ Contraseña incorrecta. Intente de nuevo.')
      self.entry_pass.config(highlightbackground='#ef4444')
      self.entry_pass.delete(0, tk.END)

  def abrir_sistema_principal(self):
    """Destruye el Login e invoca la app principal InventarioBienesApp directamente."""
    try:
        from main import InventarioBienesApp

        self.root.destroy()  # Cierra la ventana de login

        main_root = tk.Tk()
        app = InventarioBienesApp(main_root)
        main_root.mainloop()

    except Exception as e:
        import traceback

        error_detallado = traceback.format_exc()
        err_root = tk.Tk()
        err_root.withdraw()
        messagebox.showerror(
            'Error de Inicio',
            f'No se pudo iniciar el sistema principal:\n\n{e}\n\nDetalle:\n{error_detallado[:300]}...',
        )
        err_root.destroy()


if __name__ == '__main__':
  root = tk.Tk()
  app = AuthApp(root)
  root.mainloop()