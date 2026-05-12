"""
hud.py — Compact HUD overlay above the pet.

Layout (130 × 42px pill):
  [ PetEmoji  MoodEmoji  Lv.N  🔥streak | hunger▓▓▓░░ | xp▓▓░░░ ]

Behaviour:
  • Auto-hides after 5s of no urgency
  • Force-shows on feed / levelup / hunger spike
  • Colour-coded hunger bar: green → yellow → orange → red
  • XP bar fills left-to-right, resets on levelup
  • Streak fire shown when streak >= 2 days
"""

import tkinter as tk
import time
import sys

if sys.platform == "win32":
    import ctypes

CHROMA = "#FF00FF"

# ── Mood → emoji map ──────────────────────────────────────────────────────────
MOOD_ICON = {
    "happy":    "😊",
    "excited":  "🤩",
    "content":  "😌",
    "bored":    "😑",
    "hungry":   "🍖",
    "sad":      "😢",
    "angry":    "😤",
    "curious":  "🧐",
    "sleepy":   "😴",
    "love":     "🥰",
}

# ── Pet type → emoji ──────────────────────────────────────────────────────────
PET_ICON = {
    "dog":    "🐶",
    "dragon": "🐉",
    "cat":    "🐱",
}

# ── Hunger thresholds → bar colour ────────────────────────────────────────────
HUNGER_COLORS = [
    (0,  30,  "#4CAF50"),   # green   — well fed
    (30, 55,  "#8BC34A"),   # lime    — fine
    (55, 70,  "#FFC107"),   # yellow  — getting hungry
    (70, 85,  "#FF9800"),   # orange  — hungry
    (85, 101, "#F44336"),   # red     — starving
]

# ── XP required per level (simple linear, adjust to match pet_state.py) ───────
XP_PER_LEVEL = 100          # must match whatever pet_state uses


def _hunger_color(h: float) -> str:
    for lo, hi, col in HUNGER_COLORS:
        if lo <= h < hi:
            return col
    return "#F44336"


def _rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a filled rounded rectangle on a Canvas."""
    canvas.create_arc(x1,       y1,       x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,   y1,       x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kw)
    canvas.create_arc(x1,       y2-2*r,   x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,   y2-2*r,   x2,     y2,     start=270, extent=90,  style="pieslice", **kw)
    canvas.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
    canvas.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)


class PetHUD:
    W            = 130          # total width
    H            = 42           # total height
    AUTO_HIDE_SEC = 5.0         # seconds before auto-hide

    # Internal layout constants
    _PAD         = 5            # horizontal edge padding
    _BAR_H       = 5            # hunger / xp bar height
    _BAR_Y_HUN   = 27           # y-top of hunger bar
    _BAR_Y_XP    = 35           # y-top of XP bar

    def __init__(self, pet_root, pet_ref):
        self._root       = pet_root
        self._pet        = pet_ref
        self._visible    = False
        self._enabled    = True
        self._last_shown = 0.0
        self._win        = None
        self._canvas     = None
        self._build()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _build(self):
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.wm_attributes("-topmost", True)
        self._win.wm_attributes("-transparentcolor", CHROMA)
        self._win.configure(bg=CHROMA)
        self._win.geometry(f"{self.W}x{self.H}+0+0")
        self._win.resizable(False, False)

        self._canvas = tk.Canvas(
            self._win, bg=CHROMA, highlightthickness=0,
            width=self.W, height=self.H)
        self._canvas.pack(fill="both", expand=True)

        if sys.platform == "win32":
            self._root.after(200, self._set_layered)

        self._win.withdraw()   # start hidden

    def _set_layered(self):
        """Apply WS_EX_LAYERED so transparency works on Win32."""
        try:
            hwnd  = ctypes.windll.user32.GetParent(self._win.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000)
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def toggle(self):
        """Called from tray to enable/disable the HUD entirely."""
        self._enabled = not self._enabled
        if not self._enabled:
            self._hide()

    def show_now(self, pet_x: int, pet_y: int):
        """Force-show for AUTO_HIDE_SEC seconds (e.g. after feed / levelup)."""
        self._last_shown = time.monotonic()
        self._show(pet_x, pet_y, self._pet.state)

    def update(self, pet_x: int, pet_y: int):
        """
        Called every animation tick.
        Decides whether to show or hide based on urgency and elapsed time.
        """
        if not self._enabled:
            return

        s   = self._pet.state
        h   = s.hunger
        now = time.monotonic()

        # Always show when hungry, sad, or excited
        urgent = h > 55 or s.mood in ("excited", "sad", "hungry", "angry")
        if urgent:
            self._last_shown = now

        if now - self._last_shown < self.AUTO_HIDE_SEC:
            self._show(pet_x, pet_y, s)
        else:
            self._hide()

    # ── Visibility helpers ────────────────────────────────────────────────────

    def _show(self, pet_x: int, pet_y: int, state):
        hud_x = pet_x + (96 - self.W) // 2
        hud_y = max(0, pet_y - self.H - 4)
        self._win.geometry(f"+{hud_x}+{hud_y}")

        if not self._visible:
            self._win.deiconify()
            self._visible = True

        self._draw(state)

    def _hide(self):
        if self._visible:
            self._win.withdraw()
            self._visible = False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self, state):
        c = self._canvas
        c.delete("all")

        hunger     = state.hunger
        level      = state.level
        mood       = state.mood
        pet_type   = getattr(self._pet, "pet_type", "dog")
        xp         = state._data.get("xp", 0)
        streak     = getattr(self._pet, "screen_time",  None)
        streak_days = 0
        if streak is not None:
            try:
                streak_days = streak._data.get("streak", 0)
            except Exception:
                streak_days = 0

        pet_emoji  = PET_ICON.get(pet_type, "🐾")
        mood_emoji = MOOD_ICON.get(mood, "😐")
        hcol       = _hunger_color(hunger)

        W, H = self.W, self.H
        PAD  = self._PAD

        # ── Background pill ───────────────────────────────────────────────
        _rounded_rect(c, 0, 0, W, H, 10, fill="#1A1A2E", outline="")

        # ── Top row: pet icon  mood  level  streak ────────────────────────
        # Pet icon
        c.create_text(PAD + 4, 13, text=pet_emoji,
                      font=("Segoe UI Emoji", 10), anchor="w")

        # Mood icon
        c.create_text(PAD + 20, 13, text=mood_emoji,
                      font=("Segoe UI Emoji", 10), anchor="w")

        # Level badge
        lv_text = f"Lv{level}"
        c.create_text(PAD + 42, 13, text=lv_text,
                      font=("Courier New", 8, "bold"),
                      fill="#C0C0E0", anchor="w")

        # Streak (only show if 2+ days)
        if streak_days >= 2:
            streak_text = f"🔥{streak_days}"
            c.create_text(W - PAD, 13, text=streak_text,
                          font=("Segoe UI Emoji", 8), anchor="e")

        # ── Hunger bar ────────────────────────────────────────────────────
        bar_x0 = PAD
        bar_x1 = W - PAD
        bar_w  = bar_x1 - bar_x0
        by     = self._BAR_Y_HUN

        # Track
        _rounded_rect(c, bar_x0, by, bar_x1, by + self._BAR_H, 2,
                      fill="#2D2D4A", outline="")

        # Fill (hunger fills right-to-left — more hunger = more bar)
        fill_w = int((hunger / 100) * bar_w)
        if fill_w > 0:
            _rounded_rect(c, bar_x0, by, bar_x0 + fill_w, by + self._BAR_H, 2,
                          fill=hcol, outline="")

        # Label inside bar
        if hunger > 75:
            bar_label = "HUNGRY!"
            bar_label_col = "#FFFFFF"
        else:
            bar_label = f"{int(hunger)}% hungry"
            bar_label_col = "#888899"
        c.create_text(W // 2, by + self._BAR_H // 2 + 1,
                      text=bar_label, font=("Courier New", 6),
                      fill=bar_label_col, anchor="center")

        # ── XP bar ────────────────────────────────────────────────────────
        xy     = self._BAR_Y_XP
        xp_frac = min(1.0, (xp % XP_PER_LEVEL) / XP_PER_LEVEL)
        xp_fill = int(xp_frac * bar_w)

        # Track
        _rounded_rect(c, bar_x0, xy, bar_x1, xy + self._BAR_H, 2,
                      fill="#2D2D4A", outline="")

        # Fill (purple-ish for XP)
        if xp_fill > 0:
            _rounded_rect(c, bar_x0, xy, bar_x0 + xp_fill, xy + self._BAR_H, 2,
                          fill="#7C5CBF", outline="")

        # XP label
        xp_label = f"XP {int(xp_frac * 100)}%"
        c.create_text(W // 2, xy + self._BAR_H // 2 + 1,
                      text=xp_label, font=("Courier New", 6),
                      fill="#9988BB", anchor="center")