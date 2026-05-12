"""
config_manager.py — Loads and saves user config from config.json.
Persists: pet type, speed, color tint, accessory, last position,
          reminder interval, AFK threshold, wake words, HUD visibility.

Path logic:
  - Running from source  → config.json sits next to config_manager.py  (os.path.dirname(__file__))
  - Running as .exe      → config.json sits next to DesktopPet.exe     (os.path.dirname(sys.executable))

  PyInstaller extracts __file__ into a temp _MEIPASS folder that gets
  deleted on exit — so we must NEVER write config there.
  sys.executable always points to the real .exe location, which is
  writable and persistent.
"""

import json, os, sys


def _config_path() -> str:
    """
    Return the correct path to config.json whether running from source or as exe.
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle — write next to the .exe
        base = os.path.dirname(sys.executable)
    else:
        # Running from source — write next to config_manager.py
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "config.json")


_DEFAULTS = {
    "pet":              "dog",
    "speed":            1.0,
    "color":            "default",
    "accessory":        None,
    "last_x":           -1,       # -1 = auto-position
    "last_y":           -1,
    "reminder_min":     45,
    "afk_sleep_sec":    120,
    "hud_enabled":      True,
    "wake_words":       ["hey buddy", "okay dog", "hey dog"],
    "follow_speed":     0.15,
}


def load() -> dict:
    path = _config_path()
    if not os.path.exists(path):
        return dict(_DEFAULTS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


def save(cfg: dict):
    path = _config_path()
    # Ensure the directory exists (safety net for weird install locations)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    merged = {**_DEFAULTS, **cfg}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)