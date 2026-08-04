# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import hashlib
from datetime import datetime

app = FastAPI(title="SIGAR API - UNELLEZ", version="1.0.0")

DB_NAME = "sigar_cloud.db"

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Tabla Activos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            asignado_a TEXT NOT NULL,
            mantenimiento TEXT NOT NULL,
            fecha_mant TEXT NOT NULL,
            proximo_mant TEXT NOT NULL,
            desc_mant TEXT
        )
    """)
    
    # Tabla Bajas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bajas (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            asignado_a TEXT NOT NULL,
            mantenimiento TEXT NOT NULL,
            fecha_ultimo_mant TEXT NOT NULL,
            desc_mant TEXT,
            motivo_baja TEXT NOT NULL,
            fecha_baja TEXT NOT NULL
        )
    """)
    
    # Usuario Admin por defecto (admin / admin123)
    admin_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?)", ("admin", admin_hash))
    
    conn.commit()
    conn.close()

init_db()

# --- MODELOS PYDANTIC ---
class UserAuth(BaseModel):
    username: str
    password: str

class ActivoSchema(BaseModel):
    id: int
    nombre: str
    asignado_a: str
    mantenimiento: str
    fecha_mant: str
    proximo_mant: str
    desc_mant: Optional[str] = ""

class BajaRequest(BaseModel):
    motivo: str

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "sistema": "SIGAR API Cloud"}

# 1. Autenticación / Registro
@app.post("/api/auth/login")
def login(user: UserAuth):
    pass_hash = hashlib.sha256(user.password.encode('utf-8')).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == pass_hash:
        return {"ok": True, "message": "Acceso concedido"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.post("/api/auth/register")
def register(user: UserAuth):
    pass_hash = hashlib.sha256(user.password.encode('utf-8')).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?)", (user.username, pass_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    conn.close()
    return {"ok": True, "message": "Usuario registrado exitosamente"}

# 2. CRUD Activos
@app.get("/api/activos", response_model=List[ActivoSchema])
def obtener_activos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, asignado_a, mantenimiento, fecha_mant, proximo_mant, desc_mant FROM activos")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "nombre": r[1], "asignado_a": r[2], 
            "mantenimiento": r[3], "fecha_mant": r[4], 
            "proximo_mant": r[5], "desc_mant": r[6]
        } for r in rows
    ]

@app.post("/api/activos", status_code=status.HTTP_201_CREATED)
def crear_activo(activo: ActivoSchema):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO activos VALUES (?, ?, ?, ?, ?, ?, ?)",
            (activo.id, activo.nombre, activo.asignado_a, activo.mantenimiento, activo.fecha_mant, activo.proximo_mant, activo.desc_mant)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"El ID {activo.id} ya existe")
    conn.close()
    return {"ok": True, "message": "Activo registrado en la nube"}

@app.put("/api/activos/{id_bien}")
def actualizar_activo(id_bien: int, activo: ActivoSchema):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE activos SET nombre=?, asignado_a=?, mantenimiento=?, fecha_mant=?, proximo_mant=?, desc_mant=?
           WHERE id=?""",
        (activo.nombre, activo.asignado_a, activo.mantenimiento, activo.fecha_mant, activo.proximo_mant, activo.desc_mant, id_bien)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Activo actualizado"}

@app.post("/api/activos/{id_bien}/baja")
def dar_de_baja(id_bien: int, req: BajaRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Buscar el bien
    cursor.execute("SELECT * FROM activos WHERE id = ?", (id_bien,))
    bien = cursor.fetchone()
    if not bien:
        conn.close()
        raise HTTPException(status_code=404, detail="Activo no encontrado")
        
    fecha_baja = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Mover a la tabla de bajas
    cursor.execute(
        "INSERT INTO bajas VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (bien[0], bien[1], bien[2], bien[3], bien[4], bien[6], req.motivo, fecha_baja)
    )
    
    # Eliminar de activos
    cursor.execute("DELETE FROM activos WHERE id = ?", (id_bien,))
    
    conn.commit()
    conn.close()
    return {"ok": True, "message": f"Activo ID {id_bien} dado de baja exitosamente"}