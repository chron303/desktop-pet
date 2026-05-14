"""
settings_window.py — Settings panel launched from tray.
"""

import tkinter as tk
from tkinter import ttk
import os, sys
import config_manager
from memory_dashboard import MemoryDashboard
from achievement_ui   import AchievementUI

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

PERSONALITIES = ["playful", "lazy", "curious", "loyal", "hyper"]
PERSONALITY_DESC = {
    "playful": "Loves tricks, very bouncy and excitable 🎾",
    "lazy":    "Low energy, prefers napping, occasional grump 😴",
    "curious": "Asks questions, fascinated by everything 👀",
    "loyal":   "Devoted and warm, always supportive ❤️",
    "hyper":   "MAXIMUM ENERGY, ALL CAPS, runs in circles 💨",
}

COLORS = {
    "Default": None,
    "Gold ✨": (200, 160,  40),
    "Pink 🌸": (220, 100, 150),
    "Blue 💙": ( 60, 120, 220),
    "Green 🌿":( 60, 180,  80),
    "White ☁️":(220, 220, 220),
}


class SettingsWindow:
    VERSION = "v6.0"

    def __init__(self, pet_ref):
        self._pet      = pet_ref
        self._win      = None
        self._mem_dash = None
        self._ach_ui   = None

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return
        self._build()

    def _build(self):
        win = tk.Toplevel(self._pet.window.root)
        self._win = win
        win.title("🐾 Desktop Pet Settings")
        win.geometry("460x540")
        win.resizable(False, False)
        win.configure(bg="#FAFAFA")
        win.wm_attributes("-topmost", True)

        # Header
        hdr = tk.Frame(win, bg="#2D2D3A", height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🐾  Desktop Pet Settings",
                 bg="#2D2D3A", fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=14)
        tk.Label(hdr, text=self.VERSION,
                 bg="#2D2D3A", fg="#888899",
                 font=("Segoe UI", 9)).pack(side="right", padx=16)

        # Notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",     background="#FAFAFA", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[10, 6], font=("Segoe UI", 9))
        style.configure("TFrame",        background="#FAFAFA")

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        self._build_identity(nb)
        self._build_appearance(nb)
        self._build_behaviour(nb)
        self._build_voice(nb)
        self._build_reminders(nb)
        self._build_memory(nb)
        self._build_achievements(nb)   # ← inside _build, correct order
        self._build_about(nb)

        # Footer
        footer = tk.Frame(win, bg="#FAFAFA")
        footer.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(footer, text="Save & Close", command=self._save_and_close,
                  bg="#2D2D3A", fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=16, pady=6,
                  cursor="hand2").pack(side="right")
        tk.Button(footer, text="Reset to Defaults", command=self._reset,
                  bg="#FAFAFA", fg="#666677", font=("Segoe UI", 9),
                  relief="flat", padx=12, pady=6,
                  cursor="hand2").pack(side="right", padx=6)

    # ── Identity ──────────────────────────────────────────────────────────

    def _build_identity(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="🐶 Identity")

        self._section(f, "Pet Type")
        self._pet_type_var = tk.StringVar(value=self._pet.pet_type)
        pet_row = tk.Frame(f, bg="#FAFAFA")
        pet_row.pack(fill="x", padx=16, pady=(0, 10))
        for pt_key, emoji, label in [("dog","🐶","Dog"),("dragon","🐉","Dragon"),("cat","🐱","Cat")]:
            tk.Radiobutton(pet_row, text=f"{emoji} {label}",
                           variable=self._pet_type_var, value=pt_key,
                           bg="#FAFAFA", font=("Segoe UI", 10),
                           command=lambda k=pt_key: self._pet.switch_pet(k),
                           activebackground="#FAFAFA",
                           cursor="hand2").pack(side="left", padx=8)

        self._section(f, "Pet Name")
        self._name_var = tk.StringVar(value=self._pet.state.name)
        tk.Entry(f, textvariable=self._name_var, font=("Segoe UI", 11),
                 bg="white", relief="solid", bd=1).pack(
                 fill="x", padx=16, pady=(0, 12))

        self._section(f, "Personality")
        self._personality_var = tk.StringVar(value=self._pet.state.personality)
        for p in PERSONALITIES:
            row = tk.Frame(f, bg="#FAFAFA"); row.pack(fill="x", padx=16, pady=2)
            tk.Radiobutton(row, text=p.capitalize(),
                           variable=self._personality_var, value=p,
                           bg="#FAFAFA", font=("Segoe UI", 10, "bold"),
                           command=self._on_personality_change,
                           activebackground="#FAFAFA",
                           cursor="hand2").pack(side="left")
            tk.Label(row, text=PERSONALITY_DESC[p],
                     bg="#FAFAFA", fg="#666677",
                     font=("Segoe UI", 9)).pack(side="left", padx=6)

        self._section(f, "Stats")
        s = self._pet.state
        tk.Label(f,
                 text=(f"Level {s.level}  •  Age {s.age_hours:.1f}h  •  "
                       f"Tricks: {s._data.get('total_tricks', 0)}  •  "
                       f"Fed: {s._data.get('total_feeds', 0)}x"),
                 bg="#FAFAFA", fg="#444455",
                 font=("Segoe UI", 9)).pack(padx=16, anchor="w")

    # ── Appearance ────────────────────────────────────────────────────────

    def _build_appearance(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="🎨 Appearance")

        self._section(f, "Colour Tint")
        self._color_var = tk.StringVar(value="Default")
        row = tk.Frame(f, bg="#FAFAFA"); row.pack(fill="x", padx=16, pady=(0, 8))
        for i, (name, val) in enumerate(COLORS.items()):
            tk.Radiobutton(row, text=name,
                           variable=self._color_var, value=name,
                           bg="#FAFAFA", font=("Segoe UI", 9),
                           command=lambda n=name, v=val: self._set_color(n, v),
                           activebackground="#FAFAFA",
                           cursor="hand2").grid(row=i//3, column=i%3,
                                                sticky="w", padx=4, pady=1)

        self._section(f, "Accessory")
        from accessories import unlocked_accessories, ACCESSORIES
        unlocked  = unlocked_accessories(self._pet.state.level)
        self._acc_var = tk.StringVar(value=self._pet._active_accessory or "none")
        acc_frame = tk.Frame(f, bg="#FAFAFA")
        acc_frame.pack(fill="x", padx=16, pady=(0, 8))
        tk.Radiobutton(acc_frame, text="None",
                       variable=self._acc_var, value="none",
                       bg="#FAFAFA", font=("Segoe UI", 9),
                       cursor="hand2").grid(row=0, column=0, sticky="w", padx=4)
        for i, name in enumerate(ACCESSORIES):
            _, min_lvl = ACCESSORIES[name]
            locked = name not in unlocked
            tk.Radiobutton(acc_frame,
                           text=name.replace("_", " ").title() +
                                (f" (Lv{min_lvl})" if locked else ""),
                           variable=self._acc_var, value=name,
                           bg="#FAFAFA",
                           fg="#BBBBCC" if locked else "#222233",
                           font=("Segoe UI", 9),
                           state="disabled" if locked else "normal",
                           cursor="hand2").grid(row=(i+1)//3, column=(i+1)%3,
                                                sticky="w", padx=4, pady=1)
        tk.Button(f, text="Apply Accessory", command=self._apply_accessory,
                  bg="#2D2D3A", fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=10, pady=4,
                  cursor="hand2").pack(padx=16, anchor="w")

    # ── Behaviour ─────────────────────────────────────────────────────────

    def _build_behaviour(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="⚙️ Behaviour")

        self._section(f, "Animation Speed")
        self._speed_var = tk.DoubleVar(value=self._pet.anim_speed)
        spd_row = tk.Frame(f, bg="#FAFAFA")
        spd_row.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(spd_row, text="Slow", bg="#FAFAFA", fg="#666677",
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Scale(spd_row, from_=0.3, to=3.0, resolution=0.1,
                 variable=self._speed_var, orient="horizontal",
                 bg="#FAFAFA", highlightthickness=0, showvalue=True,
                 command=lambda v: setattr(self._pet, "anim_speed", float(v))
                 ).pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(spd_row, text="Turbo", bg="#FAFAFA", fg="#666677",
                 font=("Segoe UI", 8)).pack(side="left")

        self._section(f, "Follow Sensitivity")
        self._follow_var = tk.DoubleVar(value=self._pet._follow_speed)
        tk.Scale(f, from_=0.05, to=0.4, resolution=0.01,
                 variable=self._follow_var, orient="horizontal",
                 bg="#FAFAFA", highlightthickness=0, showvalue=True,
                 label="Cursor follow speed").pack(fill="x", padx=16, pady=(0, 12))

        self._section(f, "AFK Sleep Threshold")
        self._afk_var = tk.IntVar(value=self._pet._afk_sleep_sec)
        tk.Scale(f, from_=30, to=600, resolution=10,
                 variable=self._afk_var, orient="horizontal",
                 bg="#FAFAFA", highlightthickness=0, showvalue=True,
                 label="Seconds idle before sleeping").pack(
                 fill="x", padx=16, pady=(0, 12))

        self._section(f, "Behaviour Toggles")
        self._window_avoid_var = tk.BooleanVar(value=True)
        self._night_mode_var   = tk.BooleanVar(value=True)
        for text, var in [("Avoid open windows while walking", self._window_avoid_var),
                          ("Night mode tint after 9pm",        self._night_mode_var)]:
            tk.Checkbutton(f, text=text, variable=var,
                           bg="#FAFAFA", font=("Segoe UI", 9),
                           activebackground="#FAFAFA",
                           cursor="hand2").pack(anchor="w", padx=16, pady=2)

    # ── Voice ─────────────────────────────────────────────────────────────

    def _build_voice(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="🎤 Voice")

        self._section(f, "Wake Words")
        tk.Label(f, text="Comma-separated. Default: hey buddy, okay dog",
                 bg="#FAFAFA", fg="#666677", font=("Segoe UI", 8),
                 wraplength=380).pack(anchor="w", padx=16, pady=(0, 4))
        current = ", ".join(getattr(self._pet.voice, "wake_words", ["hey buddy"]))
        self._wake_var = tk.StringVar(value=current)
        tk.Entry(f, textvariable=self._wake_var, font=("Segoe UI", 10),
                 bg="white", relief="solid", bd=1).pack(
                 fill="x", padx=16, pady=(0, 12))

        self._section(f, "Voice Engine")
        self._voice_engine_var = tk.StringVar(value="google")
        for engine, desc in [
                ("google",  "Google Web Speech — fast, needs internet"),
                ("sphinx",  "CMU Sphinx — offline, less accurate"),
                ("whisper", "Whisper tiny — offline, accurate, slower")]:
            row = tk.Frame(f, bg="#FAFAFA"); row.pack(fill="x", padx=16, pady=1)
            tk.Radiobutton(row, text=engine.capitalize(),
                           variable=self._voice_engine_var, value=engine,
                           bg="#FAFAFA", font=("Segoe UI", 9, "bold"),
                           cursor="hand2").pack(side="left")
            tk.Label(row, text=desc, bg="#FAFAFA", fg="#666677",
                     font=("Segoe UI", 8)).pack(side="left", padx=6)

        self._section(f, "Voice Status")
        vl = self._pet.voice
        ok = vl.is_available
        tk.Label(f,
                 text="✅ Microphone active" if ok else "❌ No microphone / STT library",
                 bg="#FAFAFA", fg="#228855" if ok else "#CC3333",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(0, 4))
        tk.Label(f, text="Install: pip install SpeechRecognition pyaudio",
                 bg="#FAFAFA", fg="#888899",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=16)

    # ── Reminders ─────────────────────────────────────────────────────────

    def _build_reminders(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="⏰ Reminders")

        self._section(f, "Break Reminder Interval")
        self._reminder_var = tk.IntVar(value=self._pet.reminder._interval // 60)
        for text, val in [("Off", 0), ("20 min", 20), ("30 min", 30),
                          ("45 min", 45), ("60 min", 60), ("90 min", 90)]:
            tk.Radiobutton(f, text=text,
                           variable=self._reminder_var, value=val,
                           bg="#FAFAFA", font=("Segoe UI", 9),
                           cursor="hand2",
                           command=lambda v=val: self._pet.set_reminder(v),
                           activebackground="#FAFAFA").pack(
                           anchor="w", padx=16, pady=2)

        self._section(f, "Reminder Style")
        self._remind_style_var = tk.StringVar(value="friendly")
        for style, desc in [("friendly", "Warm and encouraging"),
                             ("stern",   "More direct, no-nonsense"),
                             ("silly",   "Funny and weird")]:
            row = tk.Frame(f, bg="#FAFAFA"); row.pack(fill="x", padx=16, pady=1)
            tk.Radiobutton(row, text=style.capitalize(),
                           variable=self._remind_style_var, value=style,
                           bg="#FAFAFA", font=("Segoe UI", 9),
                           cursor="hand2").pack(side="left")
            tk.Label(row, text=f"— {desc}",
                     bg="#FAFAFA", fg="#666677",
                     font=("Segoe UI", 8)).pack(side="left")

    # ── Memory ────────────────────────────────────────────────────────────

    def _build_memory(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="🧠 Memory")

        tk.Label(f, text="🧠", font=("Segoe UI Emoji", 36),
                 bg="#FAFAFA").pack(pady=(24, 4))
        tk.Label(f, text="Pet Memory Dashboard",
                 font=("Segoe UI", 13, "bold"), bg="#FAFAFA").pack()

        mem      = self._pet.memory
        facts    = len(mem._data.get("facts", {}))
        chats    = len(mem._data.get("exchanges", [])) // 2
        sessions = mem._data.get("total_sessions", 1)
        nights   = mem._data.get("late_nights", 0)

        tk.Label(f,
                 text=(f"{facts} facts  •  {chats} conversations  •  "
                       f"{sessions} sessions  •  {nights} late nights"),
                 bg="#FAFAFA", fg="#666677",
                 font=("Segoe UI", 9)).pack(pady=(4, 20))

        tk.Button(f, text="  Open Memory Dashboard  🧠  ",
                  command=self._open_memory_dashboard,
                  bg="#2D2D3A", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=10,
                  cursor="hand2").pack()

        tk.Label(f,
                 text="View facts, edit memories, see emotion history\n"
                      "and everything your pet knows about you.",
                 bg="#FAFAFA", fg="#888899",
                 font=("Segoe UI", 9),
                 justify="center").pack(pady=(12, 0))

        facts_data = mem._data.get("facts", {})
        if facts_data:
            self._section(f, "Quick preview")
            for k, v in list(facts_data.items())[:4]:
                tk.Label(f,
                         text=f"  {k.replace('_', ' ').title()}: {v}",
                         bg="#FAFAFA", fg="#444455",
                         font=("Segoe UI", 9),
                         anchor="w").pack(fill="x", padx=16)

    def _open_memory_dashboard(self):
        if not self._mem_dash or not hasattr(self._mem_dash, "_win"):
            self._mem_dash = MemoryDashboard(
                self._pet.window.root,
                self._pet.memory,
                self._pet.dreams)   # ← add this
        self._mem_dash.open()

    # ── Achievements ──────────────────────────────────────────────────────

    def _build_achievements(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="🏆 Achievements")

        ach   = self._pet.achievements
        stats = ach.stats()

        tk.Label(f, text="🏆", font=("Segoe UI Emoji", 36),
                 bg="#FAFAFA").pack(pady=(24, 4))
        tk.Label(f, text="Achievement Trophy Wall",
                 font=("Segoe UI", 13, "bold"), bg="#FAFAFA").pack()
        tk.Label(f,
                 text=(f"{stats['unlocked']}/{stats['total']} unlocked  •  "
                       f"{stats['total_xp']:,} XP  •  "
                       f"{stats['pct']}% complete"),
                 bg="#FAFAFA", fg="#666677",
                 font=("Segoe UI", 9)).pack(pady=(4, 6))

        # Tier progress bars
        tier_frame = tk.Frame(f, bg="#FAFAFA")
        tier_frame.pack(padx=20, fill="x", pady=(0, 12))
        tier_colors = {
            "bronze": "#CD7F32",
            "silver": "#C0C0C0",
            "gold":   "#FFD700",
            "secret": "#9B59B6",
            "legend": "#E74C3C",
        }
        for tier, color in tier_colors.items():
            td  = stats["by_tier"].get(tier, {"unlocked": 0, "total": 1})
            row = tk.Frame(tier_frame, bg="#FAFAFA")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=tier.capitalize(),
                     bg="#FAFAFA", fg=color,
                     font=("Segoe UI", 8, "bold"),
                     width=8, anchor="w").pack(side="left")
            bar_bg = tk.Frame(row, bg="#DDDDDD", height=8)
            bar_bg.pack(side="left", fill="x", expand=True, pady=3)
            pct = td["unlocked"] / max(td["total"], 1)
            if pct > 0:
                tk.Frame(bar_bg, bg=color, height=8).place(
                    relx=0, rely=0, relwidth=pct, relheight=1)
            tk.Label(row,
                     text=f"{td['unlocked']}/{td['total']}",
                     bg="#FAFAFA", fg="#888899",
                     font=("Segoe UI", 8), width=6).pack(side="right")

        # Recent unlocks preview
        recent = ach.recent_unlocks(3)
        if recent:
            from achievements import ACHIEVEMENT_MAP
            self._section(f, "Recent unlocks")
            for aid in recent:
                if aid in ACHIEVEMENT_MAP:
                    a = ACHIEVEMENT_MAP[aid]
                    tk.Label(f,
                             text=f"  {a[3]} {a[4]}  ({a[1]})",
                             bg="#FAFAFA", fg="#444455",
                             font=("Segoe UI", 9)).pack(anchor="w", padx=20)

        tk.Button(f, text="  Open Trophy Wall  🏆  ",
                  command=self._open_achievement_ui,
                  bg="#2D2D3A", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", padx=20, pady=10,
                  cursor="hand2").pack(pady=(16, 0))

    def _open_achievement_ui(self):
        if not self._ach_ui or not hasattr(self._ach_ui, "_win"):
            self._ach_ui = AchievementUI(
                self._pet.window.root, self._pet.achievements)
        self._ach_ui.open()

    # ── About ─────────────────────────────────────────────────────────────

    def _build_about(self, nb):
        f = ttk.Frame(nb); nb.add(f, text="ℹ️ About")

        tk.Label(f, text="🐾", font=("Segoe UI Emoji", 40),
                 bg="#FAFAFA").pack(pady=(20, 4))
        tk.Label(f, text="Desktop Pet",
                 font=("Segoe UI", 14, "bold"), bg="#FAFAFA").pack()
        tk.Label(f, text=self.VERSION,
                 font=("Segoe UI", 9), fg="#888899", bg="#FAFAFA").pack()

        self._section(f, "Current LLM")
        brain = self._pet.brain
        ok    = brain.is_available
        tk.Label(f,
                 text=(f"✅ Ollama — {brain._model}" if ok
                       else "⚠️ Ollama not running — using built-in responses"),
                 bg="#FAFAFA", fg="#228855" if ok else "#AA6600",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16)

        self._section(f, "Pet Memory")
        s = self._pet.state
        tk.Label(f,
                 text=(f"Name: {s.name}  |  Personality: {s.personality}\n"
                       f"Born: {s.age_hours:.1f}h ago  |  Level {s.level}\n"
                       f"Tricks: {s._data.get('total_tricks', 0)}  |  "
                       f"Fed: {s._data.get('total_feeds', 0)}x"),
                 bg="#FAFAFA", fg="#444455",
                 font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=16)

        if hasattr(self._pet, "screen_time"):
            self._section(f, "Streak & Usage")
            st = self._pet.screen_time
            tk.Label(f,
                     text=(f"🔥 {st.streak_summary()}   |   "
                           f"{st.today_summary()}   |   "
                           f"{st.total_hours:.1f}h total"),
                     bg="#FAFAFA", fg="#444455",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=16)

            cf    = tk.Frame(f, bg="#FAFAFA")
            cf.pack(padx=16, pady=(4, 0), anchor="w")
            chart = st.weekly_chart()
            max_m = max((m for _, m in chart), default=1) or 1
            for day, mins in chart:
                col = tk.Frame(cf, bg="#FAFAFA"); col.pack(side="left", padx=2)
                bh  = max(2, int(mins / max_m * 28))
                tk.Frame(col, bg="#FAFAFA",
                         height=28 - bh, width=18).pack()
                tk.Frame(col,
                         bg="#1D9E75" if mins > 0 else "#DDDDDD",
                         height=bh, width=18).pack()
                tk.Label(col, text=day[:1],
                         bg="#FAFAFA", fg="#888899",
                         font=("Segoe UI", 7)).pack()

        tk.Button(f, text="Open save file (pet_save.json)",
                  command=lambda: os.startfile(
                      os.path.join(os.path.dirname(__file__), "pet_save.json")),
                  bg="#FAFAFA", fg="#3355AA",
                  font=("Segoe UI", 9, "underline"),
                  relief="flat", cursor="hand2").pack(anchor="w", padx=14, pady=8)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _section(self, parent, title):
        tk.Label(parent, text=title,
                 bg="#FAFAFA", fg="#222233",
                 font=("Segoe UI", 10, "bold")).pack(
                 anchor="w", padx=16, pady=(10, 3))

    def _set_color(self, name, val):
        self._color_var.set(name)
        from main import TINTS
        key_map = {
            "Default":  "default", "Gold ✨":  "gold",
            "Pink 🌸":  "pink",    "Blue 💙":  "blue",
            "Green 🌿": "green",   "White ☁️": "white",
        }
        self._pet.set_color(key_map.get(name, "default"))

    def _apply_accessory(self):
        name = self._acc_var.get()
        self._pet.set_accessory(name if name != "none" else None)

    def _on_personality_change(self):
        self._pet.state._data["personality"] = self._personality_var.get()

    def _save_and_close(self):
        # Pet type
        chosen_pet = self._pet_type_var.get()
        self._pet.pet_type = chosen_pet
        _cfg = config_manager.load()
        _cfg["pet"] = chosen_pet
        config_manager.save(_cfg)

        # Name
        new_name = self._name_var.get().strip()
        if new_name:
            self._pet.state._data["name"] = new_name

        # Personality
        self._pet.state._data["personality"] = self._personality_var.get()

        # Behaviour
        self._pet.anim_speed     = self._speed_var.get()
        self._pet._follow_speed  = self._follow_var.get()
        self._pet._afk_sleep_sec = self._afk_var.get()

        # Voice
        words = [w.strip() for w in self._wake_var.get().split(",") if w.strip()]
        if words:
            self._pet.voice.wake_words = words

        self._pet.state.save()
        self._win.destroy()

    def _reset(self):
        self._name_var.set("Buddy")
        self._personality_var.set("playful")
        self._speed_var.set(1.0)
        self._color_var.set("Default")
        self._reminder_var.set(45)
        self._follow_var.set(0.15)
        self._afk_var.set(120)