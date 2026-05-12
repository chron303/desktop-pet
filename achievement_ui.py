"""
achievement_ui.py — Trophy wall UI for the achievement system.

Opened from Settings → 🏆 Achievements tab.

Layout:
  - Header: total XP, completion %, tier breakdown
  - Filter bar: All / Bronze / Silver / Gold / Secret / Legend
  - Scrollable grid of achievement cards
  - Locked achievements shown as dim cards (secret ones fully hidden)
  - Click any unlocked card to see unlock date
"""

import tkinter as tk
from tkinter import ttk
import datetime, time
from achievements import ACHIEVEMENT_MAP, TIER_COLORS, TIER_XP

BG       = "#0F0F1A"
BG2      = "#1A1A2E"
BG3      = "#22223A"
TEXT     = "#E0E0F0"
TEXT2    = "#9090AA"
TEXT3    = "#555566"
BORDER   = "#2D2D4A"
ACCENT   = "#7C5CBF"
GREEN    = "#1D9E75"


def _ts(ts: float) -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%b %d, %Y")
    except Exception:
        return "?"


class AchievementUI:
    def __init__(self, root, achievement_ref):
        self._root = root
        self._ach  = achievement_ref
        self._win  = None
        self._filter = tk.StringVar(value="all")

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return
        self._build()

    def _build(self):
        win = tk.Toplevel(self._root)
        self._win = win
        win.title("🏆 Achievements")
        win.geometry("580x680")
        win.resizable(True, True)
        win.configure(bg=BG)
        win.wm_attributes("-topmost", True)
        win.minsize(480, 500)

        self._draw_header(win)
        self._draw_filter_bar(win)
        self._draw_grid(win)
        self._draw_footer(win)

    def _draw_header(self, win):
        stats = self._ach.stats()
        hdr   = tk.Frame(win, bg="#1A0A2E", height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Left: title
        tk.Label(hdr, text="🏆  Achievements",
                 bg="#1A0A2E", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=(14,2))

        # Right: stats
        right = tk.Frame(hdr, bg="#1A0A2E")
        right.pack(side="right", padx=16, pady=8)

        tk.Label(right,
                 text=f"✨ {stats['total_xp']:,} XP",
                 bg="#1A0A2E", fg="#FFD700",
                 font=("Segoe UI", 11, "bold")).pack(anchor="e")
        tk.Label(right,
                 text=f"{stats['unlocked']}/{stats['total']}  ({stats['pct']}% complete)",
                 bg="#1A0A2E", fg=TEXT2,
                 font=("Segoe UI", 8)).pack(anchor="e")

        # Progress bar
        bar_frame = tk.Frame(win, bg=BG3, height=4)
        bar_frame.pack(fill="x")
        pct = stats["pct"] / 100
        if pct > 0:
            bar_fill = tk.Frame(win, bg=ACCENT, height=4)
            bar_fill.place(relx=0, rely=0, relwidth=pct, height=4,
                           in_=bar_frame)

        # Tier summary row
        tier_row = tk.Frame(win, bg=BG2, height=32)
        tier_row.pack(fill="x")
        tier_row.pack_propagate(False)
        for tier in ["bronze","silver","gold","secret","legend"]:
            td = stats["by_tier"].get(tier, {"unlocked":0,"total":0})
            color = TIER_COLORS[tier]
            tk.Label(tier_row,
                     text=f"{td['unlocked']}/{td['total']} {tier}",
                     bg=BG2, fg=color,
                     font=("Segoe UI", 8, "bold")).pack(
                     side="left", padx=10, pady=6)

    def _draw_filter_bar(self, win):
        bar = tk.Frame(win, bg=BG, height=36)
        bar.pack(fill="x", padx=8, pady=(4,0))

        filters = [("All","all"),("🥉","bronze"),("🥈","silver"),
                   ("🥇","gold"),("🔮","secret"),("👑","legend")]
        for label, val in filters:
            btn = tk.Radiobutton(bar, text=label,
                                 variable=self._filter, value=val,
                                 bg=BG, fg=TEXT2,
                                 selectcolor=ACCENT,
                                 activebackground=BG,
                                 font=("Segoe UI", 9),
                                 indicatoron=False,
                                 relief="flat",
                                 padx=10, pady=4,
                                 cursor="hand2",
                                 command=self._refresh)
            btn.pack(side="left", padx=2)

    def _draw_grid(self, win):
        # Scrollable canvas
        container = tk.Frame(win, bg=BG)
        container.pack(fill="both", expand=True, padx=8, pady=4)

        self._canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical",
                           command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._grid_frame = tk.Frame(self._canvas, bg=BG)
        self._canvas_win = self._canvas.create_window(
            (0,0), window=self._grid_frame, anchor="nw")

        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._grid_frame.bind("<Configure>", self._on_frame_resize)
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(
                int(-1*(e.delta/120)), "units"))

        self._populate_grid()

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._canvas_win, width=e.width)

    def _on_frame_resize(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _refresh(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._populate_grid()

    def _populate_grid(self):
        f      = self._filter.get()
        unlocked_ids = set(self._ach._data.get("unlocked", {}).keys())
        unlocked_ts  = self._ach._data.get("unlocked", {})

        # Separate unlocked and locked
        unlocked_achs = []
        locked_achs   = []

        for aid, ach in ACHIEVEMENT_MAP.items():
            tier = ach[1]
            if f != "all" and tier != f:
                continue
            if aid in unlocked_ids:
                unlocked_achs.append((aid, ach, unlocked_ts.get(aid, 0)))
            else:
                locked_achs.append((aid, ach))

        # Sort unlocked by most recent first
        unlocked_achs.sort(key=lambda x: x[2], reverse=True)

        row = 0
        col = 0
        COLS = 2

        # Section header — unlocked
        if unlocked_achs:
            lbl = tk.Label(self._grid_frame,
                           text=f"✅  Unlocked ({len(unlocked_achs)})",
                           bg=BG, fg=GREEN,
                           font=("Segoe UI", 9, "bold"))
            lbl.grid(row=row, column=0, columnspan=COLS,
                     sticky="w", padx=8, pady=(8,4))
            row += 1

            for aid, ach, ts in unlocked_achs:
                card = self._make_card(aid, ach, True, ts)
                card.grid(row=row, column=col,
                          padx=4, pady=3, sticky="ew")
                self._grid_frame.columnconfigure(col, weight=1)
                col += 1
                if col >= COLS:
                    col = 0
                    row += 1
            if col != 0:
                row += 1
                col  = 0

        # Section header — locked
        visible_locked = [(aid, ach) for aid, ach in locked_achs
                          if not ach[6]]   # exclude secret
        secret_locked  = [(aid, ach) for aid, ach in locked_achs
                          if ach[6]]

        if visible_locked:
            lbl = tk.Label(self._grid_frame,
                           text=f"🔒  Locked ({len(visible_locked)})",
                           bg=BG, fg=TEXT2,
                           font=("Segoe UI", 9, "bold"))
            lbl.grid(row=row, column=0, columnspan=COLS,
                     sticky="w", padx=8, pady=(12,4))
            row += 1

            for aid, ach in visible_locked:
                card = self._make_card(aid, ach, False, 0)
                card.grid(row=row, column=col,
                          padx=4, pady=3, sticky="ew")
                self._grid_frame.columnconfigure(col, weight=1)
                col += 1
                if col >= COLS:
                    col = 0
                    row += 1
            if col != 0:
                row += 1
                col  = 0

        # Secret locked — show count but not details
        if secret_locked and f in ("all", "secret"):
            lbl = tk.Label(self._grid_frame,
                           text=f"🔮  Secret ({len(secret_locked)} hidden)",
                           bg=BG, fg=TIER_COLORS["secret"],
                           font=("Segoe UI", 9, "bold"))
            lbl.grid(row=row, column=0, columnspan=COLS,
                     sticky="w", padx=8, pady=(12,4))
            row += 1
            hint = tk.Label(self._grid_frame,
                            text="Keep playing to discover secret achievements...",
                            bg=BG, fg=TEXT3,
                            font=("Segoe UI", 8, "italic"))
            hint.grid(row=row, column=0, columnspan=COLS,
                      sticky="w", padx=8, pady=2)

    def _make_card(self, aid, ach, is_unlocked: bool, ts: float):
        _, tier, cat, emoji, name, desc, secret = ach
        color  = TIER_COLORS[tier]
        bg_col = BG2 if is_unlocked else BG3
        fg_col = TEXT if is_unlocked else TEXT3
        xp     = TIER_XP[tier]

        card = tk.Frame(self._grid_frame, bg=bg_col,
                        relief="flat", bd=0)

        # Left color stripe
        stripe = tk.Frame(card, bg=color if is_unlocked else BORDER, width=4)
        stripe.pack(side="left", fill="y")

        # Content
        content = tk.Frame(card, bg=bg_col)
        content.pack(side="left", fill="both", expand=True, padx=(8,4), pady=6)

        # Top row: emoji + name + tier badge
        top = tk.Frame(content, bg=bg_col)
        top.pack(fill="x")

        tk.Label(top, text=emoji if is_unlocked else "🔒",
                 bg=bg_col,
                 font=("Segoe UI Emoji", 16)).pack(side="left")

        info = tk.Frame(top, bg=bg_col)
        info.pack(side="left", fill="x", expand=True, padx=(6,0))

        name_row = tk.Frame(info, bg=bg_col)
        name_row.pack(fill="x")
        tk.Label(name_row, text=name,
                 bg=bg_col, fg=fg_col,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(side="left")
        tk.Label(name_row,
                 text=f" +{xp}XP",
                 bg=bg_col,
                 fg=color if is_unlocked else TEXT3,
                 font=("Segoe UI", 7, "bold")).pack(side="left")

        tk.Label(info, text=desc,
                 bg=bg_col, fg=TEXT2 if is_unlocked else TEXT3,
                 font=("Segoe UI", 8),
                 anchor="w", wraplength=220,
                 justify="left").pack(fill="x")

        if is_unlocked and ts:
            tk.Label(content,
                     text=f"✅ Unlocked {_ts(ts)}",
                     bg=bg_col, fg=GREEN,
                     font=("Segoe UI", 7)).pack(anchor="w")

        # Tier label top-right
        tk.Label(card, text=tier.upper(),
                 bg=bg_col,
                 fg=color if is_unlocked else BORDER,
                 font=("Segoe UI", 7, "bold")).pack(
                 side="right", anchor="n", padx=6, pady=6)

        return card

    def _draw_footer(self, win):
        footer = tk.Frame(win, bg=BG2, height=36)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        stats = self._ach.stats()
        tk.Label(footer,
                 text=f"Total achievement XP: {stats['total_xp']:,}  •  "
                      f"{stats['unlocked']}/{stats['total']} unlocked  •  "
                      f"{stats['pct']}% complete",
                 bg=BG2, fg=TEXT2,
                 font=("Segoe UI", 8)).pack(side="left", padx=12, pady=8)
        tk.Button(footer, text="Close",
                  command=win.destroy,
                  bg=BG3, fg=TEXT,
                  font=("Segoe UI", 8),
                  relief="flat", padx=10, pady=2,
                  cursor="hand2").pack(side="right", padx=8, pady=6)