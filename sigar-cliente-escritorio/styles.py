# -*- coding: utf-8 -*-
import os
import json

# Ruta para almacenar la preferencia de tema localmente
ARCHIVO_CONFIG_TEMA = "config_app.json"

# Tipografías estándar del sistema SIGAR
FONT_LABEL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_KPI_VAL = ("Segoe UI", 16, "bold")
FONT_KPI_TIT = ("Segoe UI", 8, "bold")

# Paleta de colores integral para Modo Claro y Modo Oscuro
PALETA = {
    "claro": {
        "bg_root": "#f8fafc",
        "bg_panel": "#ffffff",
        "fg_texto": "#0f172a",
        "fg_subtexto": "#64748b",
        "border_panel": "#cbd5e1",
        "entry_bg": "#ffffff",
        "entry_fg": "#0f172a",
        "entry_border": "#94a3b8",
        "tree_bg": "#ffffff",
        "tree_fg": "#1e293b",
        "tree_head_bg": "#e2e8f0",
        "tree_head_fg": "#0f172a",
        "kpis": [
            {
                "bg": "#f0fdf4", "active_bg": "#dcfce7", "border": "#86efac", "active_border": "#22c55e",
                "text": "#166534", "sub": "#15803d", "val": "#14532d"
            },
            {
                "bg": "#eff6ff", "active_bg": "#dbeafe", "border": "#93c5fd", "active_border": "#3b82f6",
                "text": "#1e40af", "sub": "#1d4ed8", "val": "#1e3a8a"
            },
            {
                "bg": "#fefce8", "active_bg": "#fef9c3", "border": "#fde047", "active_border": "#eab308",
                "text": "#854d0e", "sub": "#a16207", "val": "#713f12"
            },
            {
                "bg": "#fffbeb", "active_bg": "#fef3c7", "border": "#fcd34d", "active_border": "#f59e0b",
                "text": "#92400e", "sub": "#b45309", "val": "#78350f"
            },
            {
                "bg": "#fef2f2", "active_bg": "#fee2e2", "border": "#fca5a5", "active_border": "#ef4444",
                "text": "#991b1b", "sub": "#b91c1c", "val": "#7f1d1d"
            }
        ]
    },
    "oscuro": {
        "bg_root": "#0f172a",
        "bg_panel": "#1e293b",
        "fg_texto": "#f8fafc",
        "fg_subtexto": "#94a3b8",
        "border_panel": "#334155",
        "entry_bg": "#0f172a",
        "entry_fg": "#f8fafc",
        "entry_border": "#475569",
        "tree_bg": "#1e293b",
        "tree_fg": "#f8fafc",
        "tree_head_bg": "#334155",
        "tree_head_fg": "#f8fafc",
        "kpis": [
            {
                "bg": "#064e3b", "active_bg": "#065f46", "border": "#059669", "active_border": "#34d399",
                "text": "#6ee7b7", "sub": "#a7f3d0", "val": "#ffffff"
            },
            {
                "bg": "#1e3a8a", "active_bg": "#1d4ed8", "border": "#3b82f6", "active_border": "#60a5fa",
                "text": "#93c5fd", "sub": "#bfdbfe", "val": "#ffffff"
            },
            {
                "bg": "#713f12", "active_bg": "#854d0e", "border": "#ca8a04", "active_border": "#facc15",
                "text": "#fde047", "sub": "#fef08a", "val": "#ffffff"
            },
            {
                "bg": "#78350f", "active_bg": "#92400e", "border": "#d97706", "active_border": "#fbbf24",
                "text": "#fcd34d", "sub": "#fef3c7", "val": "#ffffff"
            },
            {
                "bg": "#7f1d1d", "active_bg": "#991b1b", "border": "#dc2626", "active_border": "#f87171",
                "text": "#fca5a5", "sub": "#fee2e2", "val": "#ffffff"
            }
        ]
    }
}


def cargar_preferencia_tema():
    """Carga el último tema seleccionado por el usuario desde el archivo de configuración local."""
    if os.path.exists(ARCHIVO_CONFIG_TEMA):
        try:
            with open(ARCHIVO_CONFIG_TEMA, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("modo", "claro")
        except Exception:
            pass
    return "claro"


def guardar_preferencia_tema(modo):
    """Guarda la preferencia de tema actual en el archivo de configuración."""
    try:
        with open(ARCHIVO_CONFIG_TEMA, 'w', encoding='utf-8') as f:
            json.dump({"modo": modo}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error al guardar preferencia de tema: {e}")


def hex_a_rgb(hex_str):
    """Convierte un color en formato hexadecimal (ej. '#0f172a') a una tupla RGB."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def rgb_a_hex(rgb_tuple):
    """Convierte una tupla RGB a un string en formato hexadecimal."""
    return '#{:02x}{:02x}{:02x}'.format(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])