"""
memory_dashboard.py — Standalone Memory Dashboard window.

Tabs:
  📋 Facts      — learned facts, editable + deletable
  💬 Chats      — conversation history
  📊 Apps       — app time bar charts
  💭 Emotions   — emotion history timeline
  💤 Dreams     — dream journal (new)
  📈 Stats      — full summary + LLM context preview
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime, time, os, json


BG        = "#0F0F1A"
BG2       = "#1A1A2E"
BG3       = "#22223A"
ACCENT    = "#7C5CBF"
ACCENT2   = "#1D9E75"
RED       = "#E05555"
DREAM_COL = "#2A1A3E"
DREAM_ACC = "#9B59B6"
TEXT      = "#E0E0F0"
TEXT2     = "#9090AA"
TEXT3     = "#555566"
BORDER    = "#2D2D4A"

EMOTION_EMOJI = {
    "love":      "🥰", "excited": "🤩", "happy":    "😊",
    "curious":   "🧐", "sad":     "😢", "angry":    "😤",
    "dizzy":     "😵", "surprised":"😲","content":  "😌",
}

FACT_LABELS = {
    "user_name": "Your name",
    "job":       "Your job",
    "workplace": "Where you work",
    "location":  "Where you live",
    "likes":     "Things you like",
    "age":       "Your age",
    "favorite":  "Your favourite",
}

PET_DREAM_EMOJI = {
    "dog":    "🐶",
    "dragon": "🐉",
    "cat":    "🐱",
}


def _ts_to_str(ts: float) -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%b %d  %H:%M")
    except Exception:
        return "?"


class MemoryDashboard:
    def __init__(self, root, memory_ref, dream_ref=None):
        self._root   = root
        self._memory = memory_ref
        self._dreams = dream_ref   # DreamJournal instance (optional)
        self._win    = None

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return
        self._build()

    def _build(self):
        win = tk.Toplevel(self._root)
        self._win = win
        win.title("🧠 Pet Memory Dashboard")
        win.geometry("540x660")
        win.resizable(True, True)
        win.configure(bg=BG)
        win.wm_attributes("-topmost", True)
        win.minsize(480, 500)

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=ACCENT, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🧠  Pet Memory",
                 bg=ACCENT, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=12)
        sessions = self._memory._data.get("total_sessions", 1)
        dream_count = self._dreams.total_dreams() if self._dreams else 0
        tk.Label(hdr,
                 text=f"{sessions} sessions  •  {dream_count} dreams",
                 bg=ACCENT, fg="#D0C0FF",
                 font=("Segoe UI", 9)).pack(side="right", padx=16)

        # ── Notebook ──────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Mem.TNotebook",     background=BG,  borderwidth=0)
        style.configure("Mem.TNotebook.Tab", padding=[12, 6],
                        font=("Segoe UI", 9),
                        background=BG2, foreground=TEXT2)
        style.map("Mem.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        style.configure("Mem.TFrame", background=BG)

        nb = ttk.Notebook(win, style="Mem.TNotebook")
        nb.pack(fill="both", expand=True)

        self._build_facts(nb)
        self._build_exchanges(nb)
        self._build_apps(nb)
        self._build_emotions(nb)
        self._build_dreams(nb)     # ← NEW
        self._build_stats(nb)

        # ── Footer ────────────────────────────────────────────────────────
        footer = tk.Frame(win, bg=BG2, height=44)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Button(footer, text="🗑  Forget Everything",
                  command=self._forget_all,
                  bg=RED, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=4,
                  cursor="hand2").pack(side="left", padx=12, pady=8)

        tk.Button(footer, text="Close",
                  command=win.destroy,
                  bg=BG3, fg=TEXT,
                  font=("Segoe UI", 9),
                  relief="flat", padx=14, pady=4,
                  cursor="hand2").pack(side="right", padx=12, pady=8)

        tk.Button(footer, text="💾  Save",
                  command=self._save_and_refresh,
                  bg=ACCENT2, fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=4,
                  cursor="hand2").pack(side="right", padx=4, pady=8)

    # ── Facts tab ─────────────────────────────────────────────────────────

    def _build_facts(self, nb):
        outer = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(outer, text="📋 Facts")

        tk.Label(outer, text="What your pet knows about you",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 9)).pack(
                 anchor="w", padx=16, pady=(10, 4))

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=(8, 0))

        inner = tk.Frame(canvas, bg=BG)
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_resize(e): canvas.itemconfig(canvas_win, width=e.width)
        canvas.bind("<Configure>", on_resize)
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        self._fact_vars = {}
        facts = self._memory._data.get("facts", {})

        if not facts:
            tk.Label(inner,
                     text="No facts learned yet.\nTell your pet your name, job, or what you like!",
                     bg=BG, fg=TEXT2, font=("Segoe UI", 10),
                     justify="center").pack(pady=40)
        else:
            for key, value in facts.items():
                self._add_fact_row(inner, key, value)

        self._add_new_fact_section(outer)

    def _add_fact_row(self, parent, key, value):
        label = FACT_LABELS.get(key, key.replace("_", " ").title())
        row   = tk.Frame(parent, bg=BG2, pady=2)
        row.pack(fill="x", padx=8, pady=3)

        tk.Label(row, text=label, bg=BG2, fg=TEXT2,
                 font=("Segoe UI", 8), width=16,
                 anchor="w").pack(side="left", padx=(10, 4), pady=6)

        var = tk.StringVar(value=value)
        self._fact_vars[key] = var
        tk.Entry(row, textvariable=var, bg=BG3, fg=TEXT,
                 font=("Segoe UI", 10), relief="flat",
                 insertbackground=TEXT).pack(
                 side="left", fill="x", expand=True, padx=4, pady=4)

        tk.Button(row, text="🗑",
                  command=lambda k=key, r=row: self._delete_fact(k, r),
                  bg=BG2, fg=RED, font=("Segoe UI", 10),
                  relief="flat", cursor="hand2",
                  activebackground=BG3).pack(side="right", padx=6)

    def _add_new_fact_section(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(parent, text="Add a fact manually:",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 8)).pack(anchor="w", padx=16)

        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=8, pady=4)

        self._new_key_var = tk.StringVar()
        self._new_val_var = tk.StringVar()

        tk.Entry(row, textvariable=self._new_key_var,
                 bg=BG3, fg=TEXT2, font=("Segoe UI", 9),
                 relief="flat", width=14,
                 insertbackground=TEXT).pack(side="left", padx=(4, 2), pady=4)
        tk.Label(row, text="=", bg=BG, fg=TEXT2,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(row, textvariable=self._new_val_var,
                 bg=BG3, fg=TEXT, font=("Segoe UI", 9),
                 relief="flat", insertbackground=TEXT).pack(
                 side="left", fill="x", expand=True, padx=(2, 4), pady=4)
        tk.Button(row, text="Add",
                  command=self._add_custom_fact,
                  bg=ACCENT, fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=10, cursor="hand2").pack(side="right", padx=4)

    def _delete_fact(self, key, row_frame):
        self._memory._data["facts"].pop(key, None)
        self._fact_vars.pop(key, None)
        row_frame.destroy()

    def _add_custom_fact(self):
        key = self._new_key_var.get().strip().lower().replace(" ", "_")
        val = self._new_val_var.get().strip()
        if key and val:
            self._memory._data["facts"][key] = val
            self._new_key_var.set("")
            self._new_val_var.set("")
            self._win.destroy()
            self._build()

    # ── Exchanges tab ─────────────────────────────────────────────────────

    def _build_exchanges(self, nb):
        f = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(f, text="💬 Chats")

        exchanges = self._memory._data.get("exchanges", [])

        header_row = tk.Frame(f, bg=BG)
        header_row.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(header_row,
                 text=f"Last {len(exchanges)//2} conversations",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 9)).pack(side="left")
        tk.Button(header_row, text="Clear all",
                  command=self._clear_exchanges,
                  bg=BG2, fg=RED, font=("Segoe UI", 8),
                  relief="flat", cursor="hand2").pack(side="right")

        frame = tk.Frame(f, bg=BG)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        txt = tk.Text(frame, bg=BG2, fg=TEXT, font=("Segoe UI", 9),
                      relief="flat", wrap="word", state="disabled",
                      selectbackground=ACCENT, padx=8, pady=4)
        sb  = ttk.Scrollbar(frame, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        txt.tag_config("user", foreground="#88CCFF", font=("Segoe UI", 9, "bold"))
        txt.tag_config("pet",  foreground=TEXT,      font=("Segoe UI", 9))
        txt.tag_config("ts",   foreground=TEXT2,     font=("Segoe UI", 7))

        txt.configure(state="normal")
        if not exchanges:
            txt.insert("end", "No conversations recorded yet.\nTalk to your pet! 🐾")
        else:
            for ex in reversed(exchanges[-40:]):
                role   = ex.get("role", "?")
                text   = ex.get("text", "")
                ts     = ex.get("ts", 0)
                tag    = "user" if role == "user" else "pet"
                prefix = "You:  " if role == "user" else "Pet:  "
                txt.insert("end", f"{_ts_to_str(ts)}\n", "ts")
                txt.insert("end", f"{prefix}{text}\n\n", tag)
        txt.configure(state="disabled")
        txt.see("end")

    def _clear_exchanges(self):
        if messagebox.askyesno("Clear Chats",
                               "Delete all conversation history?\nThis can't be undone.",
                               parent=self._win):
            self._memory._data["exchanges"] = []
            self._win.destroy(); self._build()

    # ── Apps tab ──────────────────────────────────────────────────────────

    def _build_apps(self, nb):
        f = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(f, text="📊 Apps")

        tk.Label(f, text="Time spent per app (minutes)",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 9)).pack(
                 anchor="w", padx=16, pady=(10, 6))

        app_time    = self._memory._data.get("app_time", {})
        sorted_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)
        max_mins    = sorted_apps[0][1] if sorted_apps else 1

        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        sb     = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=8)

        inner  = tk.Frame(canvas, bg=BG)
        cw     = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        if not sorted_apps or max_mins == 0:
            tk.Label(inner, text="No app time recorded yet.",
                     bg=BG, fg=TEXT2, font=("Segoe UI", 10)).pack(pady=40)
        else:
            for app, mins in sorted_apps[:20]:
                row = tk.Frame(inner, bg=BG)
                row.pack(fill="x", padx=4, pady=2)
                tk.Label(row, text=app.replace(".exe", ""),
                         bg=BG, fg=TEXT, font=("Segoe UI", 9),
                         width=16, anchor="w").pack(side="left", padx=(4, 6))
                bar_frame = tk.Frame(row, bg=BG3, height=14)
                bar_frame.pack(side="left", fill="x", expand=True, pady=2)
                bar_frame.pack_propagate(False)
                pct = max(0.01, mins / max_mins)
                tk.Frame(bar_frame, bg=ACCENT, height=14).place(
                    relx=0, rely=0, relwidth=pct, relheight=1)
                tk.Label(row, text=f"{mins:.0f}m",
                         bg=BG, fg=TEXT2,
                         font=("Segoe UI", 8), width=6).pack(side="right", padx=4)

        tk.Button(f, text="Reset app stats",
                  command=self._clear_apps,
                  bg=BG2, fg=RED, font=("Segoe UI", 8),
                  relief="flat", cursor="hand2").pack(anchor="e", padx=12, pady=6)

    def _clear_apps(self):
        if messagebox.askyesno("Reset App Stats", "Clear all app time data?",
                               parent=self._win):
            self._memory._data["app_time"] = {}
            self._win.destroy(); self._build()

    # ── Emotions tab ──────────────────────────────────────────────────────

    def _build_emotions(self, nb):
        f = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(f, text="💭 Emotions")

        tk.Label(f, text="Recent emotional history",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 9)).pack(
                 anchor="w", padx=16, pady=(10, 6))

        emotions = self._memory._data.get("emotions", [])

        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        sb     = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=8)

        inner = tk.Frame(canvas, bg=BG)
        cw    = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        if not emotions:
            tk.Label(inner, text="No emotions logged yet.",
                     bg=BG, fg=TEXT2, font=("Segoe UI", 10)).pack(pady=40)
        else:
            for em in reversed(emotions):
                emotion = em.get("emotion", "happy")
                cause   = em.get("cause", "")
                ts      = em.get("ts", 0)
                emoji   = EMOTION_EMOJI.get(emotion, "😐")

                row = tk.Frame(inner, bg=BG2)
                row.pack(fill="x", padx=4, pady=2)
                tk.Label(row, text=emoji,
                         bg=BG2, font=("Segoe UI Emoji", 14)).pack(
                         side="left", padx=(8, 4), pady=4)
                info = tk.Frame(row, bg=BG2)
                info.pack(side="left", fill="x", expand=True, pady=4)
                tk.Label(info, text=emotion.capitalize(),
                         bg=BG2, fg=TEXT,
                         font=("Segoe UI", 9, "bold"),
                         anchor="w").pack(fill="x")
                tk.Label(info, text=cause,
                         bg=BG2, fg=TEXT2,
                         font=("Segoe UI", 8),
                         anchor="w").pack(fill="x")
                tk.Label(row, text=_ts_to_str(ts),
                         bg=BG2, fg=TEXT2,
                         font=("Segoe UI", 7)).pack(side="right", padx=8)

    # ── Dreams tab ────────────────────────────────────────────────────────

    def _build_dreams(self, nb):
        f = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(f, text="💤 Dreams")

        if not self._dreams:
            tk.Label(f,
                     text="💤",
                     font=("Segoe UI Emoji", 36), bg=BG).pack(pady=(40, 8))
            tk.Label(f, text="No dreams yet",
                     bg=BG, fg=TEXT,
                     font=("Segoe UI", 13, "bold")).pack()
            tk.Label(f,
                     text="Leave your pet sleeping for 10+ minutes\nand it will dream based on your memories.",
                     bg=BG, fg=TEXT2,
                     font=("Segoe UI", 9),
                     justify="center").pack(pady=(8, 0))
            return

        all_dreams = self._dreams.all_dreams()

        # Header row
        header = tk.Frame(f, bg=BG)
        header.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(header,
                 text=f"💤 {len(all_dreams)} dreams recorded",
                 bg=BG, fg=TEXT2,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Button(header, text="Clear dreams",
                  command=self._clear_dreams,
                  bg=BG2, fg=RED, font=("Segoe UI", 8),
                  relief="flat", cursor="hand2").pack(side="right")

        # Scrollable dream cards
        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        sb     = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        inner = tk.Frame(canvas, bg=BG)
        cw    = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        for dream in all_dreams:
            text     = dream.get("text", "").lstrip("💤 ")
            pet_type = dream.get("pet_type", "dog")
            ts       = dream.get("ts", 0)
            date_str = dream.get("date", _ts_to_str(ts))
            pet_emoji = PET_DREAM_EMOJI.get(pet_type, "🐾")

            card = tk.Frame(inner, bg=DREAM_COL)
            card.pack(fill="x", padx=4, pady=3)

            # Left accent stripe
            tk.Frame(card, bg=DREAM_ACC, width=4).pack(side="left", fill="y")

            content = tk.Frame(card, bg=DREAM_COL)
            content.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            top_row = tk.Frame(content, bg=DREAM_COL)
            top_row.pack(fill="x")
            tk.Label(top_row, text=f"{pet_emoji} 💤",
                     bg=DREAM_COL,
                     font=("Segoe UI Emoji", 12)).pack(side="left")
            tk.Label(top_row, text=date_str,
                     bg=DREAM_COL, fg=TEXT3,
                     font=("Segoe UI", 7)).pack(side="right")

            tk.Label(content, text=text,
                     bg=DREAM_COL, fg=TEXT,
                     font=("Segoe UI", 9),
                     anchor="w", wraplength=400,
                     justify="left").pack(fill="x", pady=(4, 0))

    def _clear_dreams(self):
        if self._dreams and messagebox.askyesno(
                "Clear Dreams", "Delete all dream history?", parent=self._win):
            self._dreams.clear()
            self._win.destroy(); self._build()

    # ── Stats tab ─────────────────────────────────────────────────────────

    def _build_stats(self, nb):
        f = ttk.Frame(nb, style="Mem.TFrame")
        nb.add(f, text="📈 Stats")

        d        = self._memory._data
        peak     = d.get("peak_hours", [])
        peak_str = ", ".join(f"{h}:00" for h in peak) if peak else "Not tracked yet"
        nights   = d.get("late_nights", 0)
        sessions = d.get("total_sessions", 1)
        chats    = len(d.get("exchanges", [])) // 2
        facts_n  = len(d.get("facts", {}))
        top_apps = self._memory.top_apps(5)
        dreams_n = self._dreams.total_dreams() if self._dreams else 0

        rows = [
            ("🗓  Sessions together",  str(sessions)),
            ("💬  Conversations",       str(chats)),
            ("📋  Facts learned",       str(facts_n)),
            ("💤  Dreams recorded",     str(dreams_n)),
            ("🌙  Late night sessions", str(nights)),
            ("⏰  Most active hours",   peak_str),
            ("📱  Top apps",            ", ".join(top_apps) if top_apps else "None yet"),
            ("🎭  Recent moods",        ", ".join(self._memory.recent_emotions()) or "None yet"),
        ]

        for label, value in rows:
            row = tk.Frame(f, bg=BG2)
            row.pack(fill="x", padx=8, pady=3)
            tk.Label(row, text=label,
                     bg=BG2, fg=TEXT2,
                     font=("Segoe UI", 9), width=22,
                     anchor="w").pack(side="left", padx=10, pady=6)
            tk.Label(row, text=value,
                     bg=BG2, fg=TEXT,
                     font=("Segoe UI", 9, "bold"),
                     anchor="w").pack(side="left", padx=4)

        tk.Label(f, text="LLM context block:",
                 bg=BG, fg=TEXT2,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(12, 2))
        ctx = self._memory.build_context_block()
        txt = tk.Text(f, bg=BG2, fg=TEXT2, font=("Segoe UI", 8),
                      relief="flat", height=5, wrap="word",
                      state="normal", padx=8, pady=6)
        txt.insert("end", ctx or "(empty — talk to your pet more!)")
        txt.configure(state="disabled")
        txt.pack(fill="x", padx=8, pady=(0, 8))

    # ── Actions ───────────────────────────────────────────────────────────

    def _save_and_refresh(self):
        for key, var in self._fact_vars.items():
            val = var.get().strip()
            if val:
                self._memory._data["facts"][key] = val
            else:
                self._memory._data["facts"].pop(key, None)
        self._memory.save()
        try:
            for w in self._win.winfo_children():
                if isinstance(w, tk.Frame) and w.cget("bg") == ACCENT:
                    w.configure(bg=ACCENT2)
                    self._win.after(600, lambda: w.configure(bg=ACCENT))
                    break
        except Exception:
            pass

    def _forget_all(self):
        if messagebox.askyesno(
            "⚠️ Forget Everything",
            f"This will erase:\n"
            f"• All {len(self._memory._data.get('facts', {}))} learned facts\n"
            f"• All {len(self._memory._data.get('exchanges', []))//2} conversations\n"
            f"• All emotion history\n"
            f"• All app time data\n"
            f"• All {self._dreams.total_dreams() if self._dreams else 0} dreams\n\n"
            f"This CANNOT be undone.\n\nAre you sure?",
            parent=self._win
        ):
            self._memory._data["facts"]     = {}
            self._memory._data["exchanges"] = []
            self._memory._data["emotions"]  = []
            self._memory._data["app_time"]  = {}
            self._memory._data["topics"]    = []
            self._memory.save()
            if self._dreams:
                self._dreams.clear()
            self._win.destroy(); self._build()