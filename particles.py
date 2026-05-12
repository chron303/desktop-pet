"""
particles.py — Particle system rendered as a separate always-on-top
transparent Tkinter window that sits exactly over the pet window.

Particle types:
  heart   — floats up, fades (feeding / petting)
  star    — bursts outward (tricks / level up)
  zzz     — drifts up-right (sleeping)
  paw     — stamp on screen, fades (walking)
  sparkle — quick flash (excited)
  note    — floats up (dancing / spotify)
"""

import tkinter as tk
import math, time, random
from dataclasses import dataclass, field
from typing import List

CHROMA = "#FF00FF"

@dataclass
class Particle:
    kind:   str
    x:      float
    y:      float
    vx:     float = 0.0
    vy:     float = 0.0
    life:   float = 1.0     # 0=dead, 1=fresh
    decay:  float = 0.025
    size:   int   = 14
    text:   str   = ""
    color:  str   = "#FF4466"
    angle:  float = 0.0
    spin:   float = 0.0

SYMBOLS = {
    "heart":   ("♥", "#FF4466"),
    "star":    ("★", "#FFD700"),
    "zzz":     ("z",  "#AABBFF"),
    "note":    ("♪",  "#88DDFF"),
    "sparkle": ("✦",  "#FFFAAA"),
    "paw":     ("🐾", "#CC9966"),
    "bone":    ("🦴", "#F5F0DC"),
    "levelup": ("⬆",  "#FFD700"),
    "exclaim": ("!",  "#FF8800"),
}

class ParticleSystem:
    W = 200    # overlay window is wider to catch particles drifting
    H = 200

    def __init__(self, pet_window_ref):
        self._pet = pet_window_ref
        self._particles: List[Particle] = []
        self._canvas = None
        self._win = None
        self._item_ids = []
        self._build()

    def _build(self):
        self._win = tk.Toplevel(self._pet.root)
        self._win.overrideredirect(True)
        self._win.wm_attributes("-topmost", True)
        self._win.wm_attributes("-transparentcolor", CHROMA)
        self._win.configure(bg=CHROMA)
        self._win.geometry(f"{self.W}x{self.H}+0+0")
        self._win.resizable(False, False)

        self._canvas = tk.Canvas(
            self._win, bg=CHROMA,
            highlightthickness=0,
            width=self.W, height=self.H,
        )
        self._canvas.pack(fill="both", expand=True)

        # Apply layered flag
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self._win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000)
        except Exception:
            pass

    def _reposition(self, pet_x, pet_y):
        """Move particle window to be centred over the pet."""
        wx = pet_x + 48 - self.W//2
        wy = pet_y + 48 - self.H//2
        self._win.geometry(f"+{wx}+{wy}")

    # ── Emitters ─────────────────────────────────────────────────────────

    def emit_hearts(self, count=4):
        cx, cy = self.W//2, self.H//2
        for _ in range(count):
            sym, col = SYMBOLS["heart"]
            self._particles.append(Particle(
                "heart", cx+random.randint(-20,20), cy+random.randint(-10,10),
                vx=random.uniform(-0.6,0.6), vy=random.uniform(-2.0,-1.0),
                decay=0.018, size=random.randint(14,22), text=sym, color=col
            ))

    def emit_stars(self, count=6):
        cx, cy = self.W//2, self.H//2
        for i in range(count):
            angle = (i/count)*math.tau
            spd = random.uniform(1.5, 3.0)
            sym, col = SYMBOLS["star"]
            self._particles.append(Particle(
                "star", cx, cy,
                vx=math.cos(angle)*spd, vy=math.sin(angle)*spd,
                decay=0.022, size=random.randint(12,18), text=sym, color=col
            ))

    def emit_zzz(self):
        cx, cy = self.W//2 + 20, self.H//2 - 10
        sym, col = SYMBOLS["zzz"]
        sz = random.randint(10,16)
        self._particles.append(Particle(
            "zzz", cx+random.randint(-8,8), cy,
            vx=random.uniform(0.2,0.6), vy=random.uniform(-0.8,-0.4),
            decay=0.010, size=sz, text=sym, color=col
        ))

    def emit_notes(self, count=2):
        cx, cy = self.W//2, self.H//2
        for _ in range(count):
            sym, col = SYMBOLS["note"]
            self._particles.append(Particle(
                "note", cx+random.randint(-25,25), cy+random.randint(-10,10),
                vx=random.uniform(-0.5,0.5), vy=random.uniform(-1.5,-0.8),
                decay=0.015, size=random.randint(13,19), text=sym, color=col
            ))

    def emit_sparkles(self, count=5):
        cx, cy = self.W//2, self.H//2
        for _ in range(count):
            sym, col = SYMBOLS["sparkle"]
            self._particles.append(Particle(
                "sparkle", cx+random.randint(-30,30), cy+random.randint(-30,30),
                vx=random.uniform(-1,1), vy=random.uniform(-1,1),
                decay=0.040, size=random.randint(10,16), text=sym, color=col
            ))

    def emit_levelup(self):
        cx, cy = self.W//2, self.H//4
        sym, col = SYMBOLS["levelup"]
        self._particles.append(Particle(
            "levelup", cx, cy, vx=0, vy=-1.0,
            decay=0.012, size=22, text=sym, color=col
        ))
        self.emit_stars(8)

    def emit_bone(self):
        cx, cy = self.W//2 + 30, self.H//2 - 20
        sym, col = SYMBOLS["bone"]
        self._particles.append(Particle(
            "bone", cx, cy, vx=0, vy=-0.5,
            decay=0.010, size=20, text=sym, color=col
        ))

    def emit_exclaim(self):
        cx, cy = self.W//2 + 25, self.H//4
        sym, col = SYMBOLS["exclaim"]
        self._particles.append(Particle(
            "exclaim", cx, cy, vx=0, vy=-0.3,
            decay=0.020, size=20, text=sym, color=col
        ))

    # ── Update + render ──────────────────────────────────────────────────

    def update_and_draw(self, pet_x, pet_y):
        self._reposition(pet_x, pet_y)
        self._canvas.delete("all")

        alive = []
        for p in self._particles:
            p.x    += p.vx
            p.y    += p.vy
            p.vy   += 0.04    # gentle gravity
            p.life -= p.decay
            if p.life <= 0:
                continue
            alive.append(p)

            # Fade by adjusting color brightness (approximate)
            alpha_factor = max(0.1, p.life)
            sz = max(8, int(p.size * alpha_factor**0.3))

            # Draw text particle
            self._canvas.create_text(
                int(p.x), int(p.y),
                text=p.text,
                font=("Segoe UI Emoji", sz),
                fill=p.color,
            )

        self._particles = alive

    def has_particles(self):
        return len(self._particles) > 0