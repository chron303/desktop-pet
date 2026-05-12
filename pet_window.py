"""
pet_window.py — Renders PIL pixel-art frames on a transparent Tkinter window.
Background: #FF00FF (magenta chroma-key) = fully transparent.
Dog RGBA image is composited onto magenta; only the dog pixels are visible.
"""

import tkinter as tk
from PIL import Image, ImageTk
import sys

if sys.platform == "win32":
    import ctypes, ctypes.wintypes

CHROMA = "#FF00FF"


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

    def draw_frame(self, pil_image):
        """Composite RGBA sprite onto magenta bg, display on canvas."""
        bg = Image.new("RGBA", (self.W, self.H), (255, 0, 255, 255))
        ox = (self.W - pil_image.width)  // 2
        oy = (self.H - pil_image.height) // 2
        bg.paste(pil_image, (ox, oy), pil_image)
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