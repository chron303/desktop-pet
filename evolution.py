"""
evolution.py — Pet Evolution System

Tracks evolution state and triggers transformations at level thresholds.

Evolution paths:
  Dog:    Level 1-4  → Puppy (sprite.py)
          Level 5-9  → Husky (husky_sprite.py)
          Level 10+  → Wolf  (wolf_sprite.py)

  Dragon: Level 1-4  → Drake      (dragon_sprite.py)
          Level 5-9  → Fire Dragon (fire_dragon_sprite.py)
          Level 10+  → Ice Dragon  (ice_dragon_sprite.py)

  Cat:    Level 1-4  → Kitten (cat_sprite.py)
          Level 5-9  → Lynx   (lynx_sprite.py)
          Level 10+  → Panther(panther_sprite.py)

Evolution fires a 3-second transformation animation then switches sprite.
"""

import time
from dataclasses import dataclass
from typing import Optional

# ── Evolution thresholds ──────────────────────────────────────────────────
EVOLUTIONS = {
    "dog": [
        {"level": 1,  "name": "Puppy",       "module": "sprite",              "emoji": "🐶"},
        {"level": 5,  "name": "Husky",        "module": "husky_sprite",        "emoji": "🐕"},
        {"level": 10, "name": "Wolf",         "module": "wolf_sprite",         "emoji": "🐺"},
    ],
    "dragon": [
        {"level": 1,  "name": "Drake",        "module": "dragon_sprite",       "emoji": "🐉"},
        {"level": 5,  "name": "Fire Dragon",  "module": "fire_dragon_sprite",  "emoji": "🔥"},
        {"level": 10, "name": "Ice Dragon",   "module": "ice_dragon_sprite",   "emoji": "❄️"},
    ],
    "cat": [
        {"level": 1,  "name": "Kitten",       "module": "cat_sprite",          "emoji": "🐱"},
        {"level": 5,  "name": "Lynx",         "module": "lynx_sprite",         "emoji": "🦁"},
        {"level": 10, "name": "Panther",      "module": "panther_sprite",      "emoji": "🐆"},
    ],
}

# Module function names per pet type
SPRITE_FN_MAP = {
    "dog":    {"animations": "ANIMATIONS", "tricks": "TRICK_ANIMS",
               "icon": "make_icon"},
    "dragon": {"animations": "DRAGON_ANIMATIONS", "tricks": "DRAGON_TRICKS",
               "icon": "make_dragon_icon"},
    "cat":    {"animations": "CAT_ANIMATIONS", "tricks": "CAT_TRICKS",
               "icon": "make_cat_icon"},
}

# Evolution messages per pet type and form
EVOLUTION_MESSAGES = {
    "dog": {
        "Husky":  "I'm evolving!! I'm a Husky now! 🐕✨",
        "Wolf":   "ULTIMATE FORM. I am the WOLF. 🐺👑",
    },
    "dragon": {
        "Fire Dragon": "THE FLAMES GROW STRONGER! 🔥🐉",
        "Ice Dragon":  "I have become the Ice Dragon. Fear the cold. ❄️",
    },
    "cat": {
        "Lynx":    "I have ascended. I am Lynx now. 🦁",
        "Panther": "Darkness. Power. I am Panther. 🐆",
    },
}


@dataclass
class EvolutionState:
    pet_type:    str
    form_index:  int   # 0 = base, 1 = form2, 2 = form3
    form_name:   str
    module_name: str
    emoji:       str


class EvolutionSystem:
    def __init__(self, pet_type: str, current_level: int):
        self._pet_type = pet_type
        self._evolving = False
        self._evolve_start = 0.0
        self._pending_form = None   # EvolutionState waiting to apply

        # Determine current form from level
        self._current = self._form_for_level(pet_type, current_level)

    # ── Public API ────────────────────────────────────────────────────────

    def check_evolution(self, new_level: int) -> Optional[EvolutionState]:
        """
        Call when pet levels up.
        Returns new EvolutionState if an evolution should trigger, else None.
        """
        new_form = self._form_for_level(self._pet_type, new_level)

        if new_form.form_index > self._current.form_index:
            self._pending_form = new_form
            self._evolving     = True
            self._evolve_start = time.monotonic()
            print(f"[evolution] {self._current.form_name} → {new_form.form_name}!")
            return new_form

        return None

    def apply_pending(self) -> Optional[EvolutionState]:
        """
        Call after transformation animation plays.
        Returns the new form to switch to, or None.
        """
        if self._pending_form:
            self._current      = self._pending_form
            self._pending_form = None
            self._evolving     = False
            return self._current
        return None

    def get_evolution_message(self) -> str:
        if self._pending_form:
            msgs = EVOLUTION_MESSAGES.get(self._pet_type, {})
            return msgs.get(self._pending_form.form_name,
                           f"Evolving into {self._pending_form.form_name}! ✨")
        return ""

    @property
    def current_form(self) -> EvolutionState:
        return self._current

    @property
    def is_evolving(self) -> bool:
        return self._evolving

    def set_pet_type(self, pet_type: str, level: int):
        self._pet_type = pet_type
        self._current  = self._form_for_level(pet_type, level)
        self._evolving = False
        self._pending_form = None

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _form_for_level(pet_type: str, level: int) -> EvolutionState:
        forms = EVOLUTIONS.get(pet_type, EVOLUTIONS["dog"])
        chosen = forms[0]
        for form in forms:
            if level >= form["level"]:
                chosen = form
        idx = forms.index(chosen)
        return EvolutionState(
            pet_type   = pet_type,
            form_index = idx,
            form_name  = chosen["name"],
            module_name= chosen["module"],
            emoji      = chosen["emoji"],
        )

    def load_form_sprites(self, form: EvolutionState):
        """
        Dynamically import the sprite module for the given form.
        Returns (ANIMATIONS, TRICKS, icon_fn) or None if module missing.
        """
        fn_map = SPRITE_FN_MAP.get(self._pet_type, SPRITE_FN_MAP["dog"])
        try:
            import importlib
            mod        = importlib.import_module(form.module_name)
            animations = getattr(mod, fn_map["animations"])
            tricks     = getattr(mod, fn_map["tricks"])
            icon_fn    = getattr(mod, fn_map["icon"])
            return animations, tricks, icon_fn
        except (ImportError, AttributeError) as e:
            print(f"[evolution] Module {form.module_name} not found: {e}")
            print(f"[evolution] Falling back to base sprite")
            return None   # caller should fall back to base sprite

    def next_evolution_info(self, current_level: int) -> Optional[dict]:
        """Return info about the next evolution, or None if at max form."""
        forms = EVOLUTIONS.get(self._pet_type, EVOLUTIONS["dog"])
        for form in forms:
            if form["level"] > current_level:
                return {
                    "name":       form["name"],
                    "level":      form["level"],
                    "levels_away": form["level"] - current_level,
                    "emoji":      form["emoji"],
                }
        return None   # already at max evolution
