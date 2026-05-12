"""
command_handler.py — Executes classified commands.
Uses Spotify Web API when configured, falls back to media keys.
"""

import subprocess, webbrowser, urllib.parse, sys, os, re

class CommandHandler:
    def __init__(self, pet_ref):
        self._pet    = pet_ref
        self._win32  = sys.platform == "win32"
        self._spotify = None
        # Lazy-load Spotify API
        threading.Thread(target=self._init_spotify, daemon=True).start()

    def _init_spotify(self):
        try:
            from spotify_api import SpotifyAPI
            self._spotify = SpotifyAPI()
        except Exception as e:
            print(f"[cmd] Spotify API init: {e}")

    def execute(self, classified: dict) -> str:
        action  = classified.get("action", "unknown")
        target  = classified.get("target", "")
        params  = classified.get("params", {})
        handler = {
            "music":   self._music,
            "app":     self._open_app,
            "timer":   self._set_timer,
            "search":  self._search,
            "feed":    self._feed,
            "trick":   self._trick,
            "volume":  self._volume,
            "unknown": self._unknown,
        }.get(action, self._unknown)
        try:
            return handler(target, params)
        except Exception as e:
            print(f"[cmd] {action} error: {e}")
            return "Couldn't do that! 😅"

    # ── Music ─────────────────────────────────────────────────────────────

    def _music(self, target: str, params: dict) -> str:
        sp = self._spotify

        # Use Spotify Web API if available
        if sp and sp.is_available:
            if not target or target == "resume":
                return sp.resume()
            elif target == "pause":
                return sp.pause()
            elif target == "next":
                return sp.skip()
            elif target == "prev":
                return sp.previous()
            else:
                return sp.play(target)

        # Fallback: media keys + Spotify URI
        if not target or target == "pause":
            self._media_key("play_pause"); return "Paused! 🎵"
        elif target == "next":
            self._media_key("next_track"); return "Skipped! ⏭️"
        elif target == "prev":
            self._media_key("prev_track"); return "Going back! ⏮️"
        else:
            q = urllib.parse.quote(target)
            try:
                subprocess.Popen(f"start spotify:search:{q}", shell=True)
                return f"Searching: {target} 🎵"
            except Exception:
                webbrowser.open(f"https://open.spotify.com/search/{q}")
                return f"Searching: {target} 🎶"

    def _volume(self, target: str, params: dict) -> str:
        level = int(params.get("level", 50))
        sp    = self._spotify
        if sp and sp.is_available:
            return sp.set_volume(level)
        # Win32 media keys fallback
        if level > 60:
            for _ in range(3): self._media_key("volume_up")
        elif level < 40:
            for _ in range(3): self._media_key("volume_down")
        return f"Volume adjusted! 🔊"

    def _media_key(self, key: str):
        if not self._win32: return
        import ctypes
        vk = {"play_pause":0xB3,"next_track":0xB0,"prev_track":0xB1,
              "stop":0xB2,"volume_up":0xAF,"volume_down":0xAE,"volume_mute":0xAD}.get(key)
        if vk:
            ctypes.windll.user32.keybd_event(vk,0,0,0)
            ctypes.windll.user32.keybd_event(vk,0,2,0)

    # ── Apps ─────────────────────────────────────────────────────────────

    APP_MAP = {
        "spotify":"spotify","chrome":"chrome","firefox":"firefox",
        "edge":"msedge","vs code":"code","vscode":"code",
        "notepad":"notepad","calculator":"calc","explorer":"explorer",
        "task manager":"taskmgr","discord":"discord","slack":"slack",
        "terminal":"cmd","powershell":"powershell","word":"winword",
        "excel":"excel","paint":"mspaint","snipping tool":"snippingtool",
    }

    def _open_app(self, target: str, params: dict) -> str:
        exe = self.APP_MAP.get(target.lower(), target)
        try:
            subprocess.Popen(exe, shell=True)
            return f"Opening {target}! 🚀"
        except Exception:
            return f"Can't find {target} 🤔"

    # ── Timer / search / feed / trick ─────────────────────────────────────

    def _set_timer(self, target: str, params: dict) -> str:
        minutes = int(params.get("minutes", 5))
        self._pet.set_reminder(minutes)
        return f"Reminder in {minutes} min! ⏰"

    def _search(self, target: str, params: dict) -> str:
        if not target: return "Search for what? 🤔"
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(target)}")
        return f"Searching: {target} 🔍"

    def _feed(self, target: str, params: dict) -> str:
        self._pet.feed(); return ""

    def _trick(self, target: str, params: dict) -> str:
        import sprite
        if target and target != "random" and target in sprite.ANIMATIONS:
            self._pet.behavior.current_trick = target
            self._pet.behavior._queued_trick = target
        else:
            self._pet.do_trick()
        return ""

    def _unknown(self, target: str, params: dict) -> str:
        return "I'll try! 🐾"


import threading  # needed for _init_spotify