"""
startup_chooser.py — Pet selection dialog shown on first launch
or when no pet is configured.

Shows dog, dragon, cat with animated preview sprites.
Returns the chosen pet_type string, or None if user closes.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import sys, os, time

# Add project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


BG      = "#0F0F1A"
BG2     = "#1A1A2E"
BG3     = "#2A2A42"
ACCENT  = "#7C5CBF"
TEXT    = "#E0E0F0"
TEXT2   = "#9090AA"
GOLD    = "#FFD700"

PET_INFO = {
    "dog": {
        "emoji":       "🐶",
        "name":        "Dog",
        "subtitle":    "Loyal companion",
        "description": "Playful, energetic, and always happy to see you.\nLoves tricks and belly rubs.",
        "evolutions":  "→ Husky (Lv5) → Wolf (Lv10)",
        "color":       "#4A90D9",
        "module":      "sprite",
        "icon_fn":     "make_icon",
    },
    "dragon": {
        "emoji":       "🐉",
        "name":        "Dragon",
        "subtitle":    "Proud and majestic",
        "description": "Ancient and wise, with a flair for the dramatic.\nFire is its love language.",
        "evolutions":  "→ Fire Dragon (Lv5) → Ice Dragon (Lv10)",
        "color":       "#E05555",
        "module":      "dragon_sprite",
        "icon_fn":     "make_dragon_icon",
    },
    "cat": {
        "emoji":       "🐱",
        "name":        "Cat",
        "subtitle":    "Aloof and mysterious",
        "description": "Judges you silently but loves you deeply.\nOn its own terms, obviously.",
        "evolutions":  "→ Lynx (Lv5) → Panther (Lv10)",
        "color":       "#9B59B6",
        "module":      "cat_sprite",
        "icon_fn":     "make_cat_icon",
    },
}


def _load_sprite(pet_type: str, size: int = 72) -> ImageTk.PhotoImage | None:
    """Load the pet sprite as a PhotoImage for display."""
    try:
        info = PET_INFO[pet_type]
        mod  = __import__(info["module"])
        fn   = getattr(mod, info["icon_fn"])
        img  = fn(size)

        # Composite onto dark background for display
        bg   = Image.new("RGBA", (size, size), (26, 26, 46, 255))
        bg.paste(img, (0, 0), img)
        return ImageTk.PhotoImage(bg)
    except Exception as e:
        print(f"[chooser] sprite load failed for {pet_type}: {e}")
        return None


def show_chooser(current_pet: str = "dog") -> str | None:
    """
    Show the pet selection dialog.
    Returns chosen pet_type string, or None if cancelled.
    Blocks until user makes a choice.
    """
    result = [None]

    root = tk.Tk()
    root.title("🐾 Choose Your Pet")
    root.configure(bg=BG)
    root.resizable(False, False)
    root.wm_attributes("-topmost", True)

    # Center on screen
    w, h = 560, 480
    sw   = root.winfo_screenwidth()
    sh   = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── Header ────────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=ACCENT, height=64)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="🐾  Choose Your Desktop Pet",
             bg=ACCENT, fg="white",
             font=("Segoe UI", 14, "bold")).pack(pady=18)

    # ── Subtitle ──────────────────────────────────────────────────────────
    tk.Label(root,
             text="Each pet has a unique personality and evolves as you level up.",
             bg=BG, fg=TEXT2,
             font=("Segoe UI", 9)).pack(pady=(12, 4))

    # ── Pet cards ─────────────────────────────────────────────────────────
    cards_frame = tk.Frame(root, bg=BG)
    cards_frame.pack(fill="x", padx=20, pady=8)

    selected_var = tk.StringVar(value=current_pet)
    sprite_refs  = {}   # keep refs to prevent GC

    def make_card(parent, pet_type: str, col: int):
        info    = PET_INFO[pet_type]
        color   = info["color"]
        is_curr = pet_type == current_pet

        # Card frame
        card = tk.Frame(parent, bg=BG2, cursor="hand2",
                        highlightthickness=2,
                        highlightbackground=color if is_curr else BG3)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        def select(pt=pet_type, c=card):
            selected_var.set(pt)
            # Update all card borders
            for pt2, c2 in card_refs.items():
                c2.configure(
                    highlightbackground=PET_INFO[pt2]["color"] if pt2 == pt else BG3)

        card.bind("<Button-1>", lambda e, pt=pet_type: select(pt))

        # Sprite
        sprite = _load_sprite(pet_type, 72)
        if sprite:
            sprite_refs[pet_type] = sprite
            lbl = tk.Label(card, image=sprite, bg=BG2, cursor="hand2")
            lbl.pack(pady=(12, 4))
            lbl.bind("<Button-1>", lambda e, pt=pet_type: select(pt))
        else:
            tk.Label(card, text=info["emoji"],
                     font=("Segoe UI Emoji", 32), bg=BG2).pack(pady=(12, 4))

        # Name
        tk.Label(card, text=info["name"],
                 bg=BG2, fg=color,
                 font=("Segoe UI", 12, "bold"),
                 cursor="hand2").pack()
        for w in card.winfo_children():
            w.bind("<Button-1>", lambda e, pt=pet_type: select(pt))

        # Subtitle
        tk.Label(card, text=info["subtitle"],
                 bg=BG2, fg=TEXT2,
                 font=("Segoe UI", 8, "italic")).pack()

        # Description
        tk.Label(card, text=info["description"],
                 bg=BG2, fg=TEXT,
                 font=("Segoe UI", 8),
                 wraplength=148, justify="center").pack(pady=(6, 2))

        # Evolution path
        tk.Label(card, text=info["evolutions"],
                 bg=BG2, fg=GOLD,
                 font=("Segoe UI", 7)).pack(pady=(0, 10))

        # Radio button (hidden but functional)
        rb = tk.Radiobutton(card, variable=selected_var, value=pet_type,
                            bg=BG2, activebackground=BG2,
                            command=lambda pt=pet_type: select(pt))
        rb.pack(pady=(0, 6))

        return card

    card_refs = {}
    for i, pt in enumerate(["dog", "dragon", "cat"]):
        card_refs[pt] = make_card(cards_frame, pt, i)

    # ── Also show current pet label if returning user ─────────────────────
    if current_pet:
        tk.Label(root,
                 text=f"Currently: {PET_INFO[current_pet]['emoji']} {PET_INFO[current_pet]['name']}  —  you can change anytime in Settings",
                 bg=BG, fg=TEXT2,
                 font=("Segoe UI", 8)).pack(pady=(0, 4))

    # ── Buttons ───────────────────────────────────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(pady=12)

    def confirm():
        result[0] = selected_var.get()
        root.destroy()

    def cancel():
        result[0] = current_pet   # keep existing pet if cancelled
        root.destroy()

    tk.Button(btn_frame, text=f"  Start with {PET_INFO[current_pet]['name']}  ",
              command=confirm,
              bg=ACCENT, fg="white",
              font=("Segoe UI", 11, "bold"),
              relief="flat", padx=20, pady=8,
              cursor="hand2").pack(side="left", padx=6)

    # Update button text when selection changes
    def update_btn(*args):
        chosen = selected_var.get()
        btn.configure(
            text=f"  Start with {PET_INFO[chosen]['name']} {PET_INFO[chosen]['emoji']}  ",
            bg=PET_INFO[chosen]["color"])

    selected_var.trace_add("write", update_btn)

    btn = tk.Button(btn_frame,
                    text=f"  Start with {PET_INFO[current_pet]['name']} {PET_INFO[current_pet]['emoji']}  ",
                    command=confirm,
                    bg=PET_INFO[current_pet]["color"], fg="white",
                    font=("Segoe UI", 11, "bold"),
                    relief="flat", padx=20, pady=8,
                    cursor="hand2")
    btn.pack(side="left", padx=6)

    tk.Button(btn_frame, text="Cancel",
              command=cancel,
              bg=BG3, fg=TEXT2,
              font=("Segoe UI", 9),
              relief="flat", padx=12, pady=8,
              cursor="hand2").pack(side="left", padx=6)

    # ── Footer note ───────────────────────────────────────────────────────
    tk.Label(root,
             text="Each pet evolves into 2 additional forms as you level up 🌟",
             bg=BG, fg=TEXT2,
             font=("Segoe UI", 8)).pack(pady=(0, 8))

    root.mainloop()
    return result[0]


if __name__ == "__main__":
    chosen = show_chooser()
    print(f"Chosen: {chosen}")