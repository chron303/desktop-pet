"""
pet_window.py — Renders PIL pixel-art frames on a transparent Tkinter window.
Background: #FF00FF (magenta chroma-key) = fully transparent.
Dog RGBA image is composited onto magenta; only the dog pixels are visible.

Fix: semi-transparent edge pixels are snapped to fully transparent or fully
opaque to prevent magenta fringing on anti-aliased sprite edges.
"""

import tkinter as tk
from PIL import Image, ImageTk
import sys

if sys.platform == "win32":
    import ctypes, ctypes.wintypes

CHROMA    = "#FF00FF"
CHROMA_RGB = (255, 0, 255)   # magenta as RGB tuple


class PetWindow:
    W = 96
    H = 96

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", CHROMA)
        self.root.configure(bg=CHROMA)
        self.root.geometry(f"{self.W}x{self.H}+400+400")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root, bg=CHROMA,
            highlightthickness=0,
            width=self.W, height=self.H,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self._img_ref = None

        if sys.platform == "win32":
            self.root.after(200, self._set_layered)

    def _set_layered(self):
        try:
            hwnd  = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000)
        except Exception as e:
            print(f"[window] layered: {e}")

    def draw_frame(self, pil_image: Image.Image):
        """
        Composite RGBA sprite onto magenta background.

        Key fix: instead of blending semi-transparent edge pixels into magenta
        (which creates a visible pink fringe), we threshold the alpha channel:
          - alpha >= 128  → keep pixel fully opaque
          - alpha <  128  → replace with pure magenta (will be keyed out)

        This gives crisp edges with zero colour fringing.
        """
        # Ensure RGBA
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")

        # Start with a pure magenta background
        bg = Image.new("RGBA", (self.W, self.H), (255, 0, 255, 255))

        # Centre the sprite
        ox = (self.W - pil_image.width)  // 2
        oy = (self.H - pil_image.height) // 2

        # Threshold alpha: snap semi-transparent pixels to fully transparent
        # so they merge cleanly with the magenta key instead of blending
        r, g, b, a = pil_image.split()
        # pixels with alpha < 128 become transparent (will show magenta bg)
        # pixels with alpha >= 128 become fully opaque
        threshold = a.point(lambda p: 255 if p >= 128 else 0)
        clean = Image.merge("RGBA", (r, g, b, threshold))

        bg.paste(clean, (ox, oy), threshold)

        # Convert to RGB for Tkinter (magenta bg will be keyed transparent)
        rgb = bg.convert("RGB")
        self._img_ref = ImageTk.PhotoImage(rgb)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._img_ref)

    def move_to(self, x: int, y: int):
        self.root.geometry(f"+{x}+{y}")

    def bind(self, event: str, fn):
        self.root.bind(event, fn)
        self.canvas.bind(event, fn)

    @property
    def screen_w(self): return self.root.winfo_screenwidth()

    @property
    def screen_h(self): return self.root.winfo_screenheight()