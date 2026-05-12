"""
Desktop Pet — main.py v9

Updates:
  • Emotion Engine — 2D valence/arousal state machine drives mood continuously
  • Achievement System — 40+ achievements wired in
  • Text command fact extraction — tray dialog learns from typed commands
  • config_manager fix — exe reads/writes config next to .exe
  • Pet type persists across restarts via config.json "pet" key
"""

import sys, os, time, random, argparse
sys.path.insert(0, os.path.dirname(__file__))
import config_manager

from pet_window       import PetWindow
from behavior         import BehaviorMachine, State
from input_tracker    import InputTracker
from tray             import TrayManager
from pet_state        import PetState
from particles        import ParticleSystem
from speech           import SpeechBubble
from day_night        import (current_period, period_tint, is_night, is_morning,
                               get_idle_seconds, AppWatcher, WindowAvoider)
from reminders        import ReminderSystem
from llm_brain        import LLMBrain
from voice            import VoiceListener
from command_handler  import CommandHandler
from accessories      import apply_accessory, unlocked_accessories, ACCESSORIES
from google_workspace import GoogleWorkspace
from notifications    import NotificationManager
from hud              import PetHUD
from updater          import UpdateChecker
from memory           import PetMemory
from weather          import WeatherWatcher
from clipboard_watcher import ClipboardWatcher, get_clipboard_quip
from screen_time      import ScreenTimeTracker
from seasonal         import SeasonalManager
from emotion_engine   import EmotionEngine
from achievements     import AchievementSystem
import sprite as dog_sprite
import dragon_sprite
import cat_sprite

# ── Pet type registry ─────────────────────────────────────────────────────
PET_TYPES = {
    "dog": {
        "module":     dog_sprite,
        "tricks":     dog_sprite.TRICK_ANIMS,
        "icon_fn":    dog_sprite.make_icon,
        "animations": dog_sprite.ANIMATIONS,
        "name":       "Dog 🐶",
    },
    "dragon": {
        "module":     dragon_sprite,
        "tricks":     dragon_sprite.DRAGON_TRICKS,
        "icon_fn":    dragon_sprite.make_dragon_icon,
        "animations": dragon_sprite.DRAGON_ANIMATIONS,
        "name":       "Dragon 🐉",
    },
    "cat": {
        "module":     cat_sprite,
        "tricks":     cat_sprite.CAT_TRICKS,
        "icon_fn":    cat_sprite.make_cat_icon,
        "animations": cat_sprite.CAT_ANIMATIONS,
        "name":       "Cat 🐱",
    },
}

def load_pet(pet_type: str = "dog"):
    pt      = PET_TYPES.get(pet_type, PET_TYPES["dog"])
    mod     = pt["module"]
    anims   = pt.get("animations") or getattr(mod, "ANIMATIONS", {})
    tricks  = pt["tricks"]
    icon_fn = pt["icon_fn"]
    return anims, tricks, icon_fn

PET_W = 96
PET_H = 96

ANIM_FPS = {
    "idle":12, "idle_night":8, "walk_right":12, "walk_left":12,
    "sleep":6, "sleep_night":5, "curious_right":10, "curious_left":10,
    "happy":12, "surprised":12, "jump":12, "spin":14,
    "dance":14, "wiggle":12, "backflip":12, "leg_shake":12,
    "panting":10, "bone_walk":12, "bone_sit":10,
    "sneeze":10, "hiccup":12, "dizzy":10, "love":10,
    "angry":12, "moonwalk":10, "roll_over":10,
    "petting":10, "wag":10, "shake_no":12, "sit_beg":8,
}

TINTS = {
    "default": None,
    "gold":  (200, 160,  40),
    "pink":  (220, 100, 150),
    "blue":  ( 60, 120, 220),
    "green": ( 60, 180,  80),
    "white": (220, 220, 220),
}

TRICK_POOL    = dog_sprite.TRICK_ANIMS
AFK_SLEEP_SEC = 120
ZZZ_INTERVAL  = 3.5
SAVE_INTERVAL = 60.0
CD_APP_SPEECH  = 90
CD_IDLE_SPEECH = 40
CD_MEET_SPEECH = 180
CD_WORKSPACE   = 300

EMOTION_ANIM = {
    "excited":  "happy",
    "love":     "love",
    "angry":    "angry",
    "dizzy":    "dizzy",
    "surprised":"surprised",
    "curious":  "curious_right",
    "sad":      "sleep",
    "happy":    "happy",
}


class DesktopPet:
    def __init__(self, speed=1.0, reminder_min=45, voice_enabled=True, pet_type="dog"):

        # ── Load pet type ─────────────────────────────────────────────────
        self.pet_type    = pet_type
        self._ANIMS, self._TRICKS, self._icon_fn = load_pet(pet_type)
        self._TRICK_POOL = self._TRICKS

        # ── Core modules ──────────────────────────────────────────────────
        self.window    = PetWindow()
        self.state     = PetState()
        self.behavior  = BehaviorMachine(self.state.personality)
        self.tracker   = InputTracker()
        self.app_watch = AppWatcher()
        self.avoider   = WindowAvoider()
        self.particles = ParticleSystem(self.window)
        self.speech    = SpeechBubble(self.window.root)
        self.reminder  = ReminderSystem(self, reminder_min)
        self.brain     = LLMBrain(self.state, self.app_watch)
        self.cmd       = CommandHandler(self)
        self.workspace = GoogleWorkspace()
        self.notify    = NotificationManager(lambda: self.window.root)

        from voice import PET_WAKE_WORDS
        self.voice = VoiceListener(
            wake_words=PET_WAKE_WORDS.get(pet_type, PET_WAKE_WORDS["dog"]),
            command_callback=self._on_voice_command)
        self.voice.on_wake = self._on_wake_word

        # ── HUD + updater ─────────────────────────────────────────────────
        self.hud         = PetHUD(self.window.root, self)
        self.hud_enabled = True
        self.updater     = UpdateChecker(
            owner="yourusername", repo="ascii-pet",
            callback=self._on_update_found)

        # ── Memory, weather, clipboard, seasonal ──────────────────────────
        self.memory      = PetMemory()
        self.weather     = WeatherWatcher()
        self.screen_time = ScreenTimeTracker()
        self.seasonal    = SeasonalManager()
        self.brain.set_memory(self.memory)
        self.brain.set_pet_type(pet_type)

        # ── Emotion engine ────────────────────────────────────────────────
        self.emotion = EmotionEngine(
            self.state,
            personality=self.state.personality,
            pet_type=pet_type,
        )

        # ── Achievement system ────────────────────────────────────────────
        self.achievements = AchievementSystem()
        self.achievements.on_session_start(
            self.memory._data.get("total_sessions", 1),
            self.screen_time._data.get("streak", 0),
        )
        self.achievements.on_pet_named(self.state.name)

        # ── Clipboard ─────────────────────────────────────────────────────
        self.clipboard = ClipboardWatcher(on_change=self._on_clipboard)
        self.clipboard.start()

        self._t_weather_react = 0.0
        self._hover_start     = 0.0
        self._petting_active  = False

        # ── Pet config ────────────────────────────────────────────────────
        self.follow_mode       = False
        self.sit_mode          = False
        self.anim_speed        = speed
        self._color_tint       = None
        self._active_accessory = None
        self._acc_cache        = {}
        self._follow_speed     = 0.15
        self._afk_sleep_sec    = AFK_SLEEP_SEC
        self._feeding          = False
        self._feed_timer       = 0.0
        self._listening_mode   = False
        self._queued_speech    = None

        # ── Animation ─────────────────────────────────────────────────────
        self._anim      = "idle"
        self._frame_idx = 0
        self._frame_t   = time.monotonic()
        self._frames    = self._ANIMS["idle"]

        # ── Cooldowns ─────────────────────────────────────────────────────
        self._t_app_speech   = 0.0
        self._t_idle_speech  = 0.0
        self._t_meet_speech  = 0.0
        self._t_zzz          = 0.0
        self._t_save         = 0.0
        self._t_llm_idle     = 0.0
        self._t_workspace    = 0.0
        self._last_app_cat   = "other"
        self._last_spotify   = False
        self._last_meeting   = False
        self._afk_sleeping   = False
        self._last_unread    = 0
        self._last_track     = ""

        # ── Position ──────────────────────────────────────────────────────
        sw = self.window.screen_w
        sh = self.window.screen_h
        self._taskbar_top = self.tracker.get_taskbar_top(sh)
        floor_y = max(0, min(sh - PET_H - 5, self._taskbar_top - PET_H - 8))

        # ── Restore config ────────────────────────────────────────────────
        _cfg = config_manager.load()
        start_x = _cfg.get("last_x", -1)
        start_y = _cfg.get("last_y", -1)
        self.x = self.tx = float(start_x if start_x > 0 else sw // 3)
        self.y = self.ty = float(start_y if start_y > 0 else floor_y)
        self.x = max(10, min(sw - PET_W - 10, self.x))
        self.y = max(0,  min(sh - PET_H - 5,  self.y))

        saved_color = _cfg.get("color", "default")
        if saved_color != "default":
            self._color_tint = TINTS.get(saved_color)

        self.anim_speed         = _cfg.get("speed",         speed)
        self.hud_enabled        = _cfg.get("hud_enabled",   True)
        self._follow_speed      = _cfg.get("follow_speed",  0.15)
        self._afk_sleep_sec     = _cfg.get("afk_sleep_sec", 120)
        self._restore_accessory = _cfg.get("accessory")

        self.window.move_to(int(self.x), int(self.y))

        print(f"[pet] v9 | {sw}x{sh} | floor={int(floor_y)} | "
              f"{self.state.personality} | "
              f"sessions={self.memory._data.get('total_sessions', 1)}")

        # ── Welcome ───────────────────────────────────────────────────────
        away = self.state.seconds_since_last_seen()
        ctx  = "afk_return" if away > 1800 else ("morning" if is_morning() else "idle")
        self.brain.respond_async("starting up", self._on_llm_response, ctx)

        if self._restore_accessory:
            from accessories import unlocked_accessories
            if self._restore_accessory in unlocked_accessories(self.state.level):
                self._active_accessory = self._restore_accessory

        seasonal_msg = self.seasonal.get_daily_greeting()
        if seasonal_msg:
            self.window.root.after(3000, lambda: self._queue(seasonal_msg))

        acc_hint = self.seasonal.should_suggest_accessory()
        if acc_hint and acc_hint != self._active_accessory:
            from accessories import unlocked_accessories
            if acc_hint in unlocked_accessories(self.state.level):
                self.set_accessory(acc_hint)
                print(f"[pet] seasonal accessory: {acc_hint}")

        milestones = self.screen_time.tick()
        for msg in milestones:
            self.window.root.after(5000, lambda m=msg: (
                self._queue(m),
                self.particles.emit_levelup()
            ))

        # ── Drag state ────────────────────────────────────────────────────
        self._drag_ox  = self._drag_oy = 0
        self._dragging = False
        self._press_x  = self._press_y = 0
        self._bind_events()

        self._set_anim("idle")
        self.window.draw_frame(self._get_frame())

        self._tray = TrayManager(self, self._icon_fn(32))
        self._tray.start()
        if voice_enabled:
            if not self.voice.start():
                print("[pet] Voice disabled.")

    # ── Shadow rendering ──────────────────────────────────────────────────

    def _draw_shadow(self):
        from PIL import Image, ImageDraw
        shadow = Image.new("RGBA", (PET_W, PET_H + 12), (0, 0, 0, 0))
        d  = ImageDraw.Draw(shadow)
        cx = PET_W // 2
        cy = PET_H + 4
        d.ellipse([cx - 28, cy - 7, cx + 28, cy + 7], fill=(0, 0, 0, 55))
        return shadow

    # ── Accessory management ──────────────────────────────────────────────

    def set_accessory(self, name):
        unlocked = unlocked_accessories(self.state.level)
        if name and name not in unlocked:
            self._queue(f"Reach level {ACCESSORIES[name][1]} to unlock that! 🔒")
            return
        self._active_accessory = name
        self._acc_cache.clear()
        if name:
            self.achievements.on_accessory_equipped(name, unlocked)
        print(f"[pet] accessory → {name}")

    def _get_frames_with_acc(self, anim_name: str) -> list:
        if not self._active_accessory:
            return self._ANIMS.get(anim_name, self._ANIMS["idle"])
        cache_key = f"{anim_name}_{self._active_accessory}"
        if cache_key not in self._acc_cache:
            base = self._ANIMS.get(anim_name, self._ANIMS["idle"])
            self._acc_cache[cache_key] = [
                apply_accessory(f, self._active_accessory,
                                pet_type=self.pet_type) for f in base
            ]
        return self._acc_cache[cache_key]

    def _get_frame(self):
        from PIL import Image, ImageDraw
        frames = self._get_frames_with_acc(self._anim)
        base   = frames[self._frame_idx % len(frames)]

        shadow_canvas = Image.new("RGBA", (PET_W, PET_H), (0, 0, 0, 0))
        d  = ImageDraw.Draw(shadow_canvas)
        cx = PET_W // 2
        d.ellipse([cx - 26, PET_H - 10, cx + 26, PET_H - 2], fill=(0, 0, 0, 45))
        result = Image.alpha_composite(shadow_canvas, base)

        to_apply = []
        dt = period_tint()
        if dt: to_apply.append(dt)
        if self._color_tint: to_apply.append((*self._color_tint, 65))
        for t in to_apply:
            ov     = Image.new("RGBA", result.size, t)
            result = Image.alpha_composite(result, ov)
        return result

    # ── Bindings ──────────────────────────────────────────────────────────

    def _bind_events(self):
        self.window.bind("<ButtonPress-1>",   self._on_press)
        self.window.bind("<B1-Motion>",       self._on_drag)
        self.window.bind("<ButtonRelease-1>", self._on_release)
        self.window.bind("<ButtonPress-3>",   self._on_right_click)
        self.window.bind("<Double-Button-1>", self._on_double_click)

    def _on_right_click(self, e):
        import tkinter as tk
        menu = tk.Menu(self.window.root, tearoff=0,
                       bg="#2D2D3A", fg="white",
                       activebackground="#444466",
                       font=("Segoe UI", 9))
        menu.add_command(label="Do a Trick! 🎉", command=self.do_trick)
        menu.add_command(label="Feed 🦴",        command=self.feed)
        menu.add_separator()
        menu.add_command(label="Follow Cursor",  command=self.toggle_follow)
        menu.add_command(label="Sit / Stay",     command=self.toggle_sit)
        menu.add_separator()
        menu.add_command(label="⚙️ Settings",    command=self.open_settings)
        menu.add_command(label="Pet Status",     command=self.show_status_dialog)
        menu.add_separator()
        menu.add_command(label="Quit",           command=self.window.root.destroy)
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _on_double_click(self, e):
        if not self._dragging:
            self.do_trick()

    def _on_press(self, e):
        self._drag_ox  = e.x_root - self.window.root.winfo_x()
        self._drag_oy  = e.y_root - self.window.root.winfo_y()
        self._press_x  = e.x_root
        self._press_y  = e.y_root
        self._dragging = False

    def _on_drag(self, e):
        if abs(e.x_root - self._press_x) > 4 or abs(e.y_root - self._press_y) > 4:
            self._dragging = True
        if self._dragging:
            self.x = self.tx = float(e.x_root - self._drag_ox)
            self.y = self.ty = float(e.y_root - self._drag_oy)
            self.window.move_to(int(self.x), int(self.y))

    def _on_release(self, e):
        if self._dragging:
            self._snap_to_taskbar()
        self._dragging = False

    def _snap_to_taskbar(self):
        floor_y = float(self._taskbar_top - PET_H - 8)
        if abs(self.y - floor_y) < 80:
            self.ty = floor_y
        sw = self.window.screen_w
        self.tx = max(10, min(sw - PET_W - 10, self.tx))

    def _on_update_found(self, version: str, url: str):
        self.window.root.after(0, lambda: self._queue(
            f"New version v{version} available! 🎉"))

    # ── Voice ─────────────────────────────────────────────────────────────

    def _on_wake_word(self):
        self._listening_mode = True
        self.particles.emit_exclaim()
        self._set_anim("curious_right")
        self.emotion.on_wake_word()
        self.achievements.on_voice_command()

    def _on_voice_command(self, text: str):
        print(f"[pet] voice: '{text}'")
        self._listening_mode = False

        import re
        rename = re.search(
            r'(?:your name is|call yourself|rename yourself to|you are now) (\w+)',
            text.lower())
        if rename:
            new_name = rename.group(1).capitalize()
            old_name = self.state.name
            self.state._data["name"] = new_name
            self.state.save()
            self._queue(f"My new name is {new_name}! I love it! 🐾")
            self.achievements.on_pet_rename()
            self.brain.respond_async(
                f"My name was just changed from {old_name} to {new_name}!",
                self._on_llm_response, "excited")
            return

        # Check if user is telling their own name
        import re as _re
        name_match = _re.search(r'my name is (\w+)', text.lower())
        if name_match:
            self.achievements.on_user_name_told()

        classified = self.brain.classify_command(text)
        if classified["action"] == "unknown":
            self.memory.add_exchange(text, "")
            # Track facts learned
            facts_before = len(self.memory._data.get("facts", {}))
            self.memory._extract_facts(text)
            facts_after  = len(self.memory._data.get("facts", {}))
            if facts_after > facts_before:
                self.achievements.on_fact_learned(facts_after)
            self.brain.respond_async(text, self._on_llm_response,
                                     self.app_watch.get().category)
        else:
            response = self.cmd.execute(classified)
            if response: self._queue(response)
            self.brain.respond_async(
                f"just did: {classified['action']} {classified.get('target', '')}",
                self._on_llm_response, classified["action"])

        # Chat count achievement
        chats = len(self.memory._data.get("exchanges", [])) // 2
        self.achievements.on_chat(chats)

    def send_text_command(self, text: str):
        self.voice.send_text_command(text)

    def _on_clipboard(self, text: str, category: str):
        quip = get_clipboard_quip(category)
        if quip:
            self.window.root.after(0, lambda: self._queue(quip))
        if category in ("code", "error", "url"):
            self.window.root.after(0, lambda: self.brain.respond_async(
                f"User just copied some {category}: {text[:80]}",
                self._on_llm_response, category
            ))

    # ── LLM response ──────────────────────────────────────────────────────

    def _on_llm_response(self, text: str, intent: str, emotion: str):
        self.window.root.after(0, lambda: self._apply_llm(text, intent, emotion))

    def _apply_llm(self, text: str, intent: str, emotion: str):
        self._queue(text)
        self.memory.log_emotion(emotion, text[:60])
        self.memory.record_interaction()
        anim = EMOTION_ANIM.get(emotion)
        if anim and anim in self._ANIMS:
            if anim in self._TRICKS:
                self.behavior.current_trick = anim
                self.behavior._queued_trick = anim
            else:
                self._set_anim(anim)

    # ── Tray API ──────────────────────────────────────────────────────────

    def set_color(self, name):
        self._color_tint = TINTS.get(name)
        self.achievements.on_color_tried(name)

    def toggle_follow(self):  self.follow_mode = not self.follow_mode
    def toggle_sit(self):     self.sit_mode    = not self.sit_mode

    def switch_pet(self, pet_type: str):
        if pet_type == self.pet_type:
            return
        self.pet_type    = pet_type
        self._ANIMS, self._TRICKS, self._icon_fn = load_pet(pet_type)
        self._TRICK_POOL = self._TRICKS
        self._acc_cache  = {}
        self.brain.set_pet_type(pet_type)
        self.emotion.set_personality(self.state.personality, pet_type)
        self.achievements.on_pet_switched(pet_type)
        from voice import PET_WAKE_WORDS
        self.voice.wake_words = [w.lower() for w in
                                  PET_WAKE_WORDS.get(pet_type, PET_WAKE_WORDS["dog"])]
        self._set_anim("idle")
        self._queue(f"I'm a {PET_TYPES[pet_type]['name']} now! 🎉")
        try:
            self._tray._icon.icon = self._icon_fn(32)
        except Exception:
            pass
        print(f"[pet] switched to {pet_type} | wake: {self.voice.wake_words}")

    def toggle_hud(self):
        self.hud_enabled = not self.hud_enabled
        if not self.hud_enabled:
            self.hud._hide()

    def set_reminder(self, m):
        self.reminder.set_interval(m)

    def open_settings(self):
        from settings_window import SettingsWindow
        # Always create fresh — ensures latest tabs/changes show up
        if not hasattr(self, "_settings_win") or \
        not self._settings_win._win or \
        not self._settings_win._win.winfo_exists():
            self._settings_win = SettingsWindow(self)
        self._settings_win.open()

    def show_command_dialog(self):
        import tkinter as tk
        dlg = tk.Toplevel(self.window.root)
        dlg.title("💬 Command")
        dlg.geometry("360x140")
        dlg.resizable(False, False)
        dlg.wm_attributes("-topmost", True)
        dlg.configure(bg="#FAFAFA")
        dlg.grab_set()

        tk.Label(dlg,
                 text=f'Tell {self.state.name} what to do:',
                 bg="#FAFAFA", font=("Segoe UI", 10, "bold")).pack(pady=(14, 2))
        tk.Label(dlg,
                 text='"play lofi"  •  "open chrome"  •  "do a backflip"  •  "search cats"',
                 bg="#FAFAFA", fg="#888899", font=("Segoe UI", 8)).pack()

        var   = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, font=("Segoe UI", 11),
                         bg="white", relief="solid", bd=1, width=36)
        entry.pack(pady=8, padx=16)
        entry.focus_set()

        def submit(e=None):
            cmd = var.get().strip()
            dlg.destroy()
            if cmd:
                # Route directly — text commands get full fact extraction + memory
                self.memory._extract_facts(cmd)
                self.memory.record_interaction()
                self._on_voice_command(cmd)

        entry.bind("<Return>", submit)
        tk.Button(dlg, text="Send", command=submit,
                  bg="#2D2D3A", fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=14, pady=4, cursor="hand2").pack()

    def show_status_dialog(self):
        import tkinter as tk
        s         = self.state
        xp_needed = s.level * 100
        bar    = "█" * int(s.xp / xp_needed * 10) + "░" * (10 - int(s.xp / xp_needed * 10))
        hbar   = "█" * int(s.hunger / 10)          + "░" * (10 - int(s.hunger / 10))
        brain  = f"Ollama: {self.brain._model}" if self.brain.is_available else "Built-in"
        ws     = "Connected ✅" if self.workspace.is_available else "Not configured"
        acc    = self._active_accessory or "none"
        wthr   = self.weather.summary() or "unavailable"
        sess   = self.memory.session_summary()
        top    = ", ".join(self.memory.top_apps(3)) or "none tracked"
        streak = self.screen_time.streak_summary()
        today  = self.screen_time.today_summary()
        total  = f"{self.screen_time.total_hours:.1f}h lifetime"
        facts  = self.memory._data.get("facts", {})
        user   = facts.get("user_name", "")
        ach_st = self.achievements.stats()

        dlg = tk.Toplevel(self.window.root)
        dlg.title("🐾 Pet Status")
        dlg.geometry("340x440")
        dlg.resizable(False, False)
        dlg.wm_attributes("-topmost", True)
        dlg.configure(bg="#FAFAFA")

        lines = [
            f"🐶  {s.name}  [{s.personality.upper()}]",
            f"User: {user}" if user else "",
            "",
            f"Level {s.level}   XP [{bar}]  {int(s.xp)}/{xp_needed}",
            f"Hunger [{hbar}]  {int(s.hunger)}%  {'🍖 Hungry!' if s.is_hungry else '😊 Full'}",
            f"Mood: {s.mood}   Age: {s.age_hours:.1f}h",
            f"Emotion: {self.emotion.debug_str()}",
            "",
            f"🏆 {ach_st['unlocked']}/{ach_st['total']} achievements  •  {ach_st['total_xp']:,} XP",
            f"🔥 {streak}   |   {today}   |   {total}",
            f"Tricks: {s._data.get('total_tricks', 0)}   Fed: {s._data.get('total_feeds', 0)}x",
            f"Accessory: {acc}",
            f"Sessions: {self.memory._data.get('total_sessions', 1)}   {sess}",
            f"Top apps: {top}",
            "",
            f"Weather: {wthr}",
            f"LLM: {brain}",
            f"Workspace: {ws}",
        ]
        for line in [l for l in lines if l is not None]:
            bold = line.startswith("🐶")
            tk.Label(dlg, text=line, bg="#FAFAFA",
                     font=("Segoe UI", 10, "bold" if bold else "normal"),
                     fg="#222233" if bold else "#444455",
                     anchor="w").pack(fill="x", padx=20, pady=1)

        tk.Button(dlg, text="Close", command=dlg.destroy,
                  bg="#2D2D3A", fg="white", font=("Segoe UI", 9),
                  relief="flat", padx=14, pady=4, cursor="hand2").pack(pady=10)

    def do_trick(self):
        trick = random.choice(self._TRICK_POOL)
        self.behavior.current_trick = trick
        self.behavior._queued_trick = trick

    def feed(self):
        leveled = self.state.feed()
        self._feeding    = True
        self._feed_timer = time.monotonic()
        self.particles.emit_hearts(5)
        self.particles.emit_bone()
        self.emotion.on_fed()
        self.achievements.on_feed(
            self.state._data.get("total_feeds", 0),
            self.state.hunger)
        self.behavior.current_trick = "love"
        self.behavior._queued_trick = "love"
        self.brain.respond_async("I was just fed a bone!", self._on_llm_response, "fed")
        self.hud.show_now(int(self.x), int(self.y))
        if leveled:
            self.emotion.on_levelup()
            self.achievements.on_level_up(self.state.level)
            self.particles.emit_levelup()
            self.behavior._queued_trick = "dizzy"
            self.notify.level_up(self.state.level)
            new = unlocked_accessories(self.state.level)
            if new:
                self._queue(f"Level {self.state.level}! "
                            f"{new[-1].replace('_', ' ').title()} unlocked! 🎉")

    # ── Animation ─────────────────────────────────────────────────────────

    def _set_anim(self, name: str):
        if name == self._anim: return
        if name not in self._ANIMS: name = "idle"
        self._anim      = name
        self._frames    = self._ANIMS[name]
        self._frame_idx = 0
        self._frame_t   = time.monotonic()

    def _tick_anim(self):
        fps = max(1.0, ANIM_FPS.get(self._anim, 10) * self.anim_speed)
        now = time.monotonic()
        if now - self._frame_t >= 1.0 / fps:
            frames          = self._get_frames_with_acc(self._anim)
            self._frame_idx = (self._frame_idx + 1) % len(frames)
            self._frame_t   = now

    def _anim_for_state(self, state, ctx) -> str:
        if self._feeding:        return "bone_sit"
        if self._petting_active: return "petting"
        if state == State.TRICK: return self.behavior.current_trick or "happy"
        d     = self.behavior.move_dir
        night = is_night()
        base  = {
            State.IDLE:    "idle_night" if night else "idle",
            State.WALK:    f"walk_{d}",
            State.SLEEP:   "sleep_night" if night else "sleep",
            State.CURIOUS: f"curious_{d}",
            State.FOLLOW:  f"walk_{d}",
        }.get(state, "idle")

        if state == State.IDLE:
            if self._listening_mode:   return "curious_right"
            if ctx.spotify_playing:
                t = int(time.monotonic()) % 24
                return ["dance", "moonwalk", "happy"][t // 8]
            if self.state.is_starving: return "angry"
            if ctx.in_meeting:         return "idle"
        if state == State.WALK and ctx.spotify_playing:
            return f"walk_{d}"
        return base

    # ── Position ──────────────────────────────────────────────────────────

    def _get_virtual_screen_bounds(self) -> tuple:
        try:
            import ctypes
            vx = ctypes.windll.user32.GetSystemMetrics(76)
            vy = ctypes.windll.user32.GetSystemMetrics(77)
            vw = ctypes.windll.user32.GetSystemMetrics(78)
            vh = ctypes.windll.user32.GetSystemMetrics(79)
            return (vx, vy, vx + vw, vy + vh)
        except Exception:
            return (0, 0, self.window.screen_w, self.window.screen_h)

    def _update_pos(self, state, cursor):
        if self._dragging or self.sit_mode: return
        sw = self.window.screen_w
        sh = self.window.screen_h
        vx_min, vy_min, vx_max, vy_max = self._get_virtual_screen_bounds()

        if state == State.WALK:
            spd   = 2.2 * self.anim_speed
            self.tx += spd if self.behavior.move_dir == "right" else -spd
            self.tx  = self.avoider.clamp_x_to_free(
                self.tx, sw, self._taskbar_top, PET_W)
            if self.tx < 10:
                self.tx = 10.0; self.behavior._flip()
            elif self.tx > sw - PET_W - 10:
                self.tx = float(sw - PET_W - 10); self.behavior._flip()

        elif state == State.FOLLOW:
            cx, cy = cursor
            gx = max(vx_min, min(vx_max - PET_W, cx - PET_W // 2))
            gy = max(vy_min, min(vy_max - PET_H, cy - PET_H // 2))
            dx, dy = gx - self.x, gy - self.y
            if (dx * dx + dy * dy) ** 0.5 > 20:
                self.tx = self.x + dx * self._follow_speed
                self.ty = self.y + dy * self._follow_speed

        elif state == State.CURIOUS:
            dx = cursor[0] - (self.x + PET_W // 2)
            if abs(dx) > 80:
                self.tx = max(0, min(sw - PET_W, self.tx + dx * 0.025))

        self.x += (self.tx - self.x) * 0.14
        self.y += (self.ty - self.y) * 0.14
        self.x  = max(vx_min - PET_W + 20, min(vx_max - 20, self.x))
        self.y  = max(vy_min, min(vy_max - PET_H, self.y))
        self.window.move_to(int(self.x), int(self.y))

    # ── Speech ────────────────────────────────────────────────────────────

    def _queue(self, msg):
        if msg: self._queued_speech = msg

    def _handle_speech(self, state, ctx):
        now = time.monotonic()

        if self.app_watch.changed:
            cat = ctx.category
            if ctx.spotify_playing and not self._last_spotify:
                self.brain.respond_async("Spotify just started playing",
                                         self._on_llm_response, "spotify")
                self.particles.emit_notes(3)
                self._last_spotify = True
                self.emotion.on_spotify(True)
                self.achievements.on_spotify_played()
            elif not ctx.spotify_playing:
                if self._last_spotify:
                    self.emotion.on_spotify(False)
                self._last_spotify = False

            if ctx.in_meeting and not self._last_meeting:
                self.brain.respond_async("A meeting just started",
                                         self._on_llm_response, "meeting")
                self._last_meeting = True
            elif not ctx.in_meeting:
                self._last_meeting = False

            if cat not in (self._last_app_cat, "other"):
                if now - self._t_app_speech > CD_APP_SPEECH:
                    self.brain.respond_async(f"User just switched to {cat}",
                                             self._on_llm_response, cat)
                    self._t_app_speech = now
            self._last_app_cat = cat

        if self.workspace.is_available and now - self._t_workspace > CD_WORKSPACE:
            unread = self.workspace.get_unread_count()
            ev     = self.workspace.get_next_event()
            if unread > self._last_unread:
                diff    = unread - self._last_unread
                senders = self.workspace.get_unread_senders()
                who     = f" from {senders[0]}" if senders else ""
                self.brain.respond_async(
                    f"There are {diff} new unread emails{who}",
                    self._on_llm_response, "idle")
                self._last_unread = unread
                self.particles.emit_exclaim()
                self.notify.email(diff, senders[0] if senders else "")
            if ev and ev.get("mins_away", 9999) <= 10:
                self.brain.respond_async(
                    f"Meeting '{ev['title']}' starts in {ev['mins_away']} minutes!",
                    self._on_llm_response, "meeting")
                self.particles.emit_exclaim()
                self.notify.meeting(ev["title"], ev["mins_away"])
            self._t_workspace = now

        if state == State.IDLE and now - self._t_llm_idle > random.uniform(60, 90):
            if random.random() < 0.4:
                c = ctx.category if ctx.category != "other" else "idle"
                self.brain.respond_async("just checking in",
                                         self._on_llm_response, c)
                self._t_llm_idle = now

        if self.weather.is_available:
            if self.weather.changed and now - self._t_weather_react > 300:
                self._queue(self.weather.get_reaction())
                self._t_weather_react = now
                self.weather.changed  = False
            elif now - self._t_weather_react > 3600:
                if random.random() < 0.3:
                    self._queue(self.weather.get_reaction())
                    self._t_weather_react = now

        if self.state.is_starving and now - self._t_idle_speech > 25:
            if random.random() < 0.04:
                self.brain.respond_async("I am absolutely starving",
                                         self._on_llm_response, "starving")
                self.particles.emit_exclaim()
                self._t_idle_speech = now
        elif self.state.is_hungry and now - self._t_idle_speech > 40:
            if random.random() < 0.02:
                self.brain.respond_async("getting a bit hungry",
                                         self._on_llm_response, "hungry")
                self._t_idle_speech = now

        msg = self.reminder.check()
        if msg:
            self._queue(msg)
            self.particles.emit_exclaim()

    # ── Achievement notification pump ─────────────────────────────────────

    def _pump_achievements(self):
        """Check for newly unlocked achievements and notify user."""
        from achievements import ACHIEVEMENT_MAP
        for aid in self.achievements.pop_pending():
            if aid not in ACHIEVEMENT_MAP:
                continue
            ach  = ACHIEVEMENT_MAP[aid]
            tier = ach[1]
            name = ach[4]
            emoji= ach[3]
            self._queue(f"{emoji} Achievement: {name}!")
            self.particles.emit_levelup()
            print(f"[achievement] 🏆 {name} ({tier.upper()})")

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self):
        def tick():
            now    = time.monotonic()
            cursor = self.tracker.get_cursor_pos()
            cx_pet = int(self.x) + PET_W // 2
            cy_pet = int(self.y) + PET_H // 2

            self.state.tick()
            milestones = self.screen_time.tick()
            for msg in milestones:
                self._queue(msg)
                self.particles.emit_levelup()
                self.notify.level_up(self.screen_time.streak)

            if now - self._t_save > SAVE_INTERVAL:
                self.state.save()
                self.memory.save()
                self.screen_time.save()
                self.achievements.save()
                self._t_save = now

            # Sync personality
            if self.behavior.personality != self.state.personality:
                self.behavior.set_personality(self.state.personality)
                self.emotion.set_personality(self.state.personality, self.pet_type)

            # App context
            ctx = self.app_watch.get()
            self.state.record_app(ctx.foreground_exe)
            self.memory.record_app_time(ctx.foreground_exe, 0.016)

            # ── Emotion engine tick ───────────────────────────────────────
            mood, intensity = self.emotion.tick(
                app_category    = ctx.category,
                spotify_playing = ctx.spotify_playing,
            )
            self.state._data["mood"] = mood      # ← correct: write to internal dict

            if self._afk_sleeping:
                self.emotion.on_ignored(get_idle_seconds())

            # ── Petting detection ─────────────────────────────────────────
            cursor_dist = ((cursor[0] - cx_pet)**2 + (cursor[1] - cy_pet)**2) ** 0.5
            if cursor_dist < 40 and not self._dragging:
                if self._hover_start == 0.0:
                    self._hover_start = now
                elif now - self._hover_start > 2.0 and not self._petting_active:
                    self._petting_active = True
                    self.particles.emit_hearts(2)
                    self.state.did_trick()
                    self.emotion.on_petted()
            else:
                self._hover_start    = 0.0
                self._petting_active = False

            # AFK detection
            idle = get_idle_seconds()
            if idle > self._afk_sleep_sec and not self._afk_sleeping:
                self._afk_sleeping = True
                self.behavior._set(State.SLEEP)
            elif idle < 3 and self._afk_sleeping:
                self._afk_sleeping = False
                self.behavior._set(State.IDLE)
                self.particles.emit_sparkles(4)
                self.brain.respond_async("user just came back",
                                         self._on_llm_response, "afk_return")

            # Trick queue
            if self.behavior._queued_trick:
                self.behavior.current_trick = self.behavior._queued_trick
                self.behavior._queued_trick = None
                self.behavior._set(State.TRICK)

            self.behavior.follow_mode = self.follow_mode
            state = self.behavior.update(cursor, (cx_pet, cy_pet))
            if self.follow_mode: state = State.FOLLOW

            if self._feeding and now - self._feed_timer > 4.0:
                self._feeding = False

            # Trick completion
            if state == State.TRICK:
                anim   = self.behavior.current_trick or "happy"
                frames = self._ANIMS.get(anim, [])
                self._set_anim(anim)
                if frames and self._frame_idx >= len(frames) - 1:
                    self.state.did_trick()
                    self.emotion.on_trick()
                    self.achievements.on_trick(
                        anim,
                        self.state._data.get("total_tricks", 0),
                        self.state.hunger,
                        self.state.personality,
                    )
                    self.particles.emit_stars(5)
                    self.brain.respond_async("just finished a trick!",
                                             self._on_llm_response, "trick")
                    self.behavior.finish_trick()
                    state = State.IDLE
            else:
                self._set_anim(self._anim_for_state(state, ctx))

            # Particles
            if state == State.SLEEP and now - self._t_zzz > ZZZ_INTERVAL:
                self.particles.emit_zzz()
                self._t_zzz = now
            if ctx.spotify_playing and state in (State.IDLE, State.WALK):
                if random.random() < 0.004:
                    self.particles.emit_notes(2)

            # Spotify track change
            if ctx.spotify_playing and self.cmd._spotify and self.cmd._spotify.is_available:
                track = self.cmd._spotify.get_current_track_name()
                if track and track != self._last_track:
                    self._last_track = track
                    self.notify.track(track)
                    self.brain.respond_async(f"Now playing: {track}",
                                             self._on_llm_response, "spotify")

            self._handle_speech(state, ctx)
            self._pump_achievements()      # ← check + notify new achievements

            if self._queued_speech:
                self.speech.say(self._queued_speech, int(self.x), int(self.y))
                self._queued_speech = None

            self._tick_anim()
            self.window.draw_frame(self._get_frame())
            self.particles.update_and_draw(int(self.x), int(self.y))
            self._update_pos(state, cursor)

            if self.hud_enabled:
                self.hud.update(int(self.x), int(self.y))

            self.updater.tick()
            self.window.root.after(16, tick)

        tick()
        self.window.root.mainloop()

        # ── Shutdown ──────────────────────────────────────────────────────
        self.state.save()
        self.memory.save()
        self.screen_time.save()
        self.achievements.save()
        self.achievements.on_session_end(
            self.memory.session_duration_minutes())
        config_manager.save({
            "pet":           self.pet_type,
            "speed":         self.anim_speed,
            "color":         next((k for k, v in TINTS.items()
                                   if v == self._color_tint), "default"),
            "accessory":     self._active_accessory,
            "last_x":        int(self.x),
            "last_y":        int(self.y),
            "reminder_min":  self.reminder._interval // 60,
            "afk_sleep_sec": self._afk_sleep_sec,
            "hud_enabled":   self.hud_enabled,
            "follow_speed":  self._follow_speed,
        })
        self.voice.stop()
        self.clipboard.stop()
        self.workspace.stop()
        self._tray.stop()


def main():
    p = argparse.ArgumentParser(description="Desktop Pet v9")
    p.add_argument("--speed",    default=1.0,  type=float)
    p.add_argument("--reminder", default=45,   type=int)
    p.add_argument("--no-voice", action="store_true")
    p.add_argument("--pet",      default="dog",
                   choices=["dog", "dragon", "cat"])
    args = p.parse_args()

    saved_pet = config_manager.load().get("pet", args.pet)

    DesktopPet(
        speed         = args.speed,
        reminder_min  = args.reminder,
        voice_enabled = not args.no_voice,
        pet_type      = saved_pet,
    ).run()


if __name__ == "__main__":
    main()