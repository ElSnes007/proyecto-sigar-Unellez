# -*- coding: utf-8 -*-
import json
import os
import sys
import tkinter as tk

CONFIG_FILE = "config.json"


def obtener_ruta_guardado():
    """Obtiene la ruta física de persistencia evitando la carpeta temporal sys._MEIPASS."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


ARCHIVO_PREFERENCIAS = os.path.join(
    obtener_ruta_guardado(), "config_app.json"
)

# Tipografías globales
FONT_TITLE = ("Segoe UI", 10, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_KPI_VAL = ("Segoe UI", 20, "bold")
FONT_KPI_TIT = ("Segoe UI", 8, "bold")

PALETA = {
    "claro": {
        "bg_root": "#f8fafc",
        "bg_cintillo": "#002B49",
        "fg_cintillo": "#ffffff",
        "bg_panel": "#ffffff",
        "fg_texto": "#1e293b",
        "fg_subtexto": "#64748b",
        "border_panel": "#cbd5e1",
        "entry_bg": "#ffffff",
        "entry_fg": "#0f172a",
        "entry_border": "#94a3b8",
        "tree_bg": "#ffffff",
        "tree_fg": "#0f172a",
        "tree_head_bg": "#002B49",
        "tree_head_fg": "#ffffff",
        "kpis": [
            {
                "bg": "#ffffff",
                "active_bg": "#f1f5f9",
                "border": "#cbd5e1",
                "active_border": "#0284c7",
                "text": "#0369a1",
                "val": "#0f172a",
                "sub": "#64748b",
            },
            {
                "bg": "#ffffff",
                "active_bg": "#f0fdf4",
                "border": "#cbd5e1",
                "active_border": "#16a34a",
                "text": "#15803d",
                "val": "#166534",
                "sub": "#166534",
            },
            {
                "bg": "#ffffff",
                "active_bg": "#f0f9ff",
                "border": "#cbd5e1",
                "active_border": "#0284c7",
                "text": "#0369a1",
                "val": "#075985",
                "sub": "#0369a1",
            },
            {
                "bg": "#ffffff",
                "active_bg": "#fffbeb",
                "border": "#cbd5e1",
                "active_border": "#d97706",
                "text": "#b45309",
                "val": "#92400e",
                "sub": "#b45309",
            },
            {
                "bg": "#ffffff",
                "active_bg": "#fef2f2",
                "border": "#cbd5e1",
                "active_border": "#dc2626",
                "text": "#b91c1c",
                "val": "#991b1b",
                "sub": "#b91c1c",
            },
        ],
    },
    "oscuro": {
        "bg_root": "#0f172a",
        "bg_cintillo": "#001F35",
        "fg_cintillo": "#f8fafc",
        "bg_panel": "#1e293b",
        "fg_texto": "#f8fafc",
        "fg_subtexto": "#94a3b8",
        "border_panel": "#334155",
        "entry_bg": "#090d16",
        "entry_fg": "#f8fafc",
        "entry_border": "#475569",
        "tree_bg": "#1e293b",
        "tree_fg": "#f8fafc",
        "tree_head_bg": "#001f35",
        "tree_head_fg": "#ffffff",
        "kpis": [
            {
                "bg": "#1e293b",
                "active_bg": "#334155",
                "border": "#334155",
                "active_border": "#38bdf8",
                "text": "#cbd5e1",
                "val": "#ffffff",
                "sub": "#94a3b8",
            },
            {
                "bg": "#1e293b",
                "active_bg": "#064e3b",
                "border": "#334155",
                "active_border": "#22c55e",
                "text": "#4ade80",
                "val": "#ffffff",
                "sub": "#86efac",
            },
            {
                "bg": "#1e293b",
                "active_bg": "#0c4a6e",
                "border": "#334155",
                "active_border": "#38bdf8",
                "text": "#38bdf8",
                "val": "#ffffff",
                "sub": "#7dd3fc",
            },
            {
                "bg": "#1e293b",
                "active_bg": "#451a03",
                "border": "#334155",
                "active_border": "#f59e0b",
                "text": "#fbbf24",
                "val": "#ffffff",
                "sub": "#fde047",
            },
            {
                "bg": "#1e293b",
                "active_bg": "#450a0a",
                "border": "#334155",
                "active_border": "#ef4444",
                "text": "#f87171",
                "val": "#ffffff",
                "sub": "#fca5a5",
            },
        ],
    },
}


def obtener_estilo_kpi(modo_oscuro, índice, esta_activa):
    """Retorna las propiedades visuales necesarias para renderizar una tarjeta KPI."""
    t = "oscuro" if modo_oscuro else "claro"
    cfg = PALETA[t]["kpis"][índice]

    bg_tarjeta = cfg["active_bg"] if esta_activa else cfg["bg"]
    borde_color = cfg["active_border"] if esta_activa else cfg["border"]

    return {
        "bg_tarjeta": bg_tarjeta,
        "borde_color": borde_color,
        "grosor_borde": 2 if esta_activa else 1,
        "color_acento": cfg["text"],
        "color_sub": cfg["sub"],
        "color_val": cfg["val"],
        "color_indicador": borde_color if esta_activa else cfg["text"],
    }


def cargar_preferencia_tema():
    if os.path.exists(ARCHIVO_PREFERENCIAS):
        try:
            with open(ARCHIVO_PREFERENCIAS, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("tema", "claro")
        except Exception:
            return "claro"
    return "claro"


def guardar_preferencia_tema(modo):
    try:
        data = {}
        if os.path.exists(ARCHIVO_PREFERENCIAS):
            try:
                with open(ARCHIVO_PREFERENCIAS, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["tema"] = modo
        with open(ARCHIVO_PREFERENCIAS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error guardando preferencia de tema: {e}")


def hex_a_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgb_a_hex(rgb_tuple):
    return "#{:02x}{:02x}{:02x}".format(*rgb_tuple)


class CustomScrollbar(tk.Canvas):

    def __init__(
        self,
        parent,
        command=None,
        width=12,
        bg_color="#0f172a",
        thumb_color="#88BDFC",
        **kw,
    ):
        super().__init__(
            parent,
            width=width,
            highlightthickness=0,
            bd=0,
            bg=bg_color,
            **kw,
        )
        self.command = command
        self.thumb_color = thumb_color
        self.bg_color = bg_color
        self.width_bar = width

        self.first = 0.0
        self.last = 1.0

        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

    def set(self, first, last):
        self.first = float(first)
        self.last = float(last)
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if h <= 40:
            return

        arrow_size = 14
        margin = 3

        # Flecha Superior
        self.create_polygon(
            w / 2,
            margin,
            margin,
            margin + arrow_size,
            w - margin,
            margin + arrow_size,
            fill=self.thumb_color,
            outline="",
            tags="arrow_up",
        )

        # Flecha Inferior
        self.create_polygon(
            w / 2,
            h - margin,
            margin,
            h - margin - arrow_size,
            w - margin,
            h - margin - arrow_size,
            fill=self.thumb_color,
            outline="",
            tags="arrow_down",
        )

        track_top = arrow_size + margin + 2
        track_bottom = h - arrow_size - margin - 2
        track_height = track_bottom - track_top

        if track_height <= 0:
            return

        top_y = track_top + (self.first * track_height)
        bottom_y = track_top + (self.last * track_height)

        if (bottom_y - top_y) < 20:
            bottom_y = top_y + 20

        r = (w - 4) / 2
        x1, y1, x2, y2 = 2, top_y, w - 2, bottom_y

        self.create_oval(
            x1, y1, x2, y1 + 2 * r, fill=self.thumb_color, outline=""
        )
        self.create_oval(
            x1, y2 - 2 * r, x2, y2, fill=self.thumb_color, outline=""
        )
        self.create_rectangle(
            x1, y1 + r, x2, y2 - r, fill=self.thumb_color, outline=""
        )

    def _on_click(self, event):
        y = event.y
        h = self.winfo_height()
        arrow_size = 14
        if y < arrow_size + 5:
            if self.command:
                self.command("scroll", -1, "units")
        elif y > h - (arrow_size + 5):
            if self.command:
                self.command("scroll", 1, "units")
        else:
            self._on_drag(event)

    def _on_drag(self, event):
        h = self.winfo_height()
        arrow_size = 14
        margin = 3
        track_top = arrow_size + margin + 2
        track_bottom = h - arrow_size - margin - 2
        track_height = track_bottom - track_top

        if track_height > 0:
            fraction = (event.y - track_top) / track_height
            fraction = max(0.0, min(1.0, fraction))
            if self.command:
                self.command("moveto", fraction)