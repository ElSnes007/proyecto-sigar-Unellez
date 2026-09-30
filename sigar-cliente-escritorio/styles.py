# -*- coding: utf-8 -*-
import os
import json
import tkinter as tk

CONFIG_FILE = "config.json"

# Tipografías globales modernas
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
        "border_panel": "#cbd5e1",
        "fg_texto": "#0f172a",
        "fg_subtexto": "#475569",
        "entry_bg": "#ffffff",
        "entry_fg": "#0f172a",
        "entry_border": "#94a3b8",
        "tree_bg": "#ffffff",
        "tree_fg": "#0f172a",
        "tree_head_bg": "#002B49",
        "tree_head_fg": "#ffffff",
        "kpis": [
            {"bg": "#f1f5f9", "border": "#475569", "text": "#334155", "val": "#0f172a", "sub": "#64748b"},
            {"bg": "#ecfdf5", "border": "#10b981", "text": "#047857", "val": "#064e3b", "sub": "#059669"},
            {"bg": "#f0f9ff", "border": "#0284c7", "text": "#0369a1", "val": "#0c4a6e", "sub": "#0284c7"},
            {"bg": "#fffbeb", "border": "#f59e0b", "text": "#b45309", "val": "#78350f", "sub": "#d97706"},
            {"bg": "#fff1f2", "border": "#f43f5e", "text": "#be123c", "val": "#881337", "sub": "#e11d48"}
        ]
    },
    "oscuro": {
        "bg_root": "#0f172a",
        "bg_cintillo": "#020617",
        "fg_cintillo": "#f8fafc",
        "bg_panel": "#1e293b",
        "border_panel": "#334155",
        "fg_texto": "#f8fafc",
        "fg_subtexto": "#cbd5e1",
        "entry_bg": "#334155",
        "entry_fg": "#ffffff",
        "entry_border": "#64748b",
        "tree_bg": "#1e293b",
        "tree_fg": "#f8fafc",
        "tree_head_bg": "#020617",
        "tree_head_fg": "#38bdf8",
        "kpis": [
            {"bg": "#1e293b", "border": "#64748b", "text": "#cbd5e1", "val": "#f8fafc", "sub": "#94a3b8"},
            {"bg": "#064e3b", "border": "#34d399", "text": "#a7f3d0", "val": "#ffffff", "sub": "#6ee7b7"},
            {"bg": "#0c4a6e", "border": "#38bdf8", "text": "#bae6fd", "val": "#ffffff", "sub": "#7dd3fc"},
            {"bg": "#78350f", "border": "#fbbf24", "text": "#fde68a", "val": "#ffffff", "sub": "#fcd34d"},
            {"bg": "#881337", "border": "#fb7185", "text": "#fecdd3", "val": "#ffffff", "sub": "#fda4af"}
        ]
    }
}


def cargar_preferencia_tema():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("tema", "oscuro")
        except Exception:
            return "oscuro"
    return "oscuro"


def guardar_preferencia_tema(modo):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"tema": modo}, f, indent=4)
    except Exception as e:
        print(f"Error al guardar tema: {e}")


def hex_a_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def rgb_a_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


class CustomScrollbar(tk.Canvas):
    def __init__(self, parent, command=None, width=12, bg_color="#0f172a", thumb_color="#88BDFC", **kw):
        super().__init__(parent, width=width, highlightthickness=0, bd=0, bg=bg_color, **kw)
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
            w / 2, margin,
            margin, margin + arrow_size,
            w - margin, margin + arrow_size,
            fill=self.thumb_color, outline="", tags="arrow_up"
        )

        # Flecha Inferior
        self.create_polygon(
            w / 2, h - margin,
            margin, h - margin - arrow_size,
            w - margin, h - margin - arrow_size,
            fill=self.thumb_color, outline="", tags="arrow_down"
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

        self.create_oval(x1, y1, x2, y1 + 2*r, fill=self.thumb_color, outline="")
        self.create_oval(x1, y2 - 2*r, x2, y2, fill=self.thumb_color, outline="")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=self.thumb_color, outline="")

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