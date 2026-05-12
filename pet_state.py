"""
pet_state.py — Persistent pet state saved to pet_save.json.
Hunger, mood, XP/level, personality, memory of user habits.
"""
import json, os, time, random, datetime

SAVE_PATH = os.path.join(os.path.dirname(__file__), "pet_save.json")

PERSONALITIES = {
    "playful":  {"trick_bias":2.0, "sleep_bias":0.5, "curious_bias":1.5},
    "lazy":     {"trick_bias":0.3, "sleep_bias":3.0, "curious_bias":0.6},
    "curious":  {"trick_bias":0.8, "sleep_bias":0.8, "curious_bias":3.0},
    "loyal":    {"trick_bias":1.0, "sleep_bias":1.0, "curious_bias":0.7},
    "hyper":    {"trick_bias":3.5, "sleep_bias":0.1, "curious_bias":2.5},
}

class PetState:
    HUNGER_RATE  = 12.0   # points per hour
    XP_PER_TRICK = 10
    XP_PER_FEED  = 5
    XP_PER_HOUR  = 3

    def __init__(self):
        self._data = self._load()
        self._last_tick = time.monotonic()

    def _load(self):
        defaults = {
            "name": "Buddy",
            "personality": random.choice(list(PERSONALITIES)),
            "hunger": 20.0, "mood": "happy",
            "xp": 0, "level": 1,
            "total_tricks": 0, "total_feeds": 0,
            "interaction_count": 0,
            "born_ts": time.time(), "last_seen_ts": time.time(),
            "late_night_sessions": 0, "fav_app": None,
        }
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH) as f:
                    defaults.update(json.load(f))
            except Exception:
                pass
        return defaults

    def save(self):
        self._data["last_seen_ts"] = time.time()
        try:
            with open(SAVE_PATH,"w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    # Properties
    @property
    def name(self):        return self._data["name"]
    @property
    def personality(self): return self._data["personality"]
    @property
    def traits(self):      return PERSONALITIES[self.personality]
    @property
    def hunger(self):      return self._data["hunger"]
    @property
    def mood(self):        return self._data["mood"]
    @property
    def level(self):       return self._data["level"]
    @property
    def xp(self):          return self._data["xp"]
    @property
    def is_hungry(self):   return self._data["hunger"] > 55
    @property
    def is_starving(self): return self._data["hunger"] > 80
    @property
    def age_hours(self):   return (time.time()-self._data["born_ts"])/3600

    def seconds_since_last_seen(self):
        return time.time() - self._data["last_seen_ts"]

    def tick(self):
        now = time.monotonic()
        dt_h = (now - self._last_tick) / 3600.0
        self._last_tick = now
        self._data["hunger"] = min(100.0, self._data["hunger"] + self.HUNGER_RATE*dt_h)
        self._add_xp(self.XP_PER_HOUR * dt_h)
        if datetime.datetime.now().hour >= 23 or datetime.datetime.now().hour <= 4:
            self._data["late_night_sessions"] = self._data.get("late_night_sessions",0) + 1
        self._update_mood()

    def _update_mood(self):
        h = self._data["hunger"]
        if h > 80:   self._data["mood"] = "sad"
        elif h > 55: self._data["mood"] = "hungry"
        elif h < 15: self._data["mood"] = "happy"

    def _add_xp(self, amt):
        self._data["xp"] += amt
        needed = self._data["level"] * 100
        if self._data["xp"] >= needed:
            self._data["xp"] -= needed
            self._data["level"] += 1
            return True
        return False

    def feed(self):
        self._data["hunger"]      = max(0.0, self._data["hunger"] - 45.0)
        self._data["total_feeds"] = self._data.get("total_feeds",0)+1
        self._data["mood"] = "happy"
        leveled = self._add_xp(self.XP_PER_FEED)
        self.save(); return leveled

    def did_trick(self):
        self._data["total_tricks"] = self._data.get("total_tricks",0)+1
        self._data["interaction_count"] += 1
        self._data["mood"] = "excited"
        leveled = self._add_xp(self.XP_PER_TRICK)
        self.save(); return leveled

    def record_app(self, app):
        if app and app != "unknown":
            self._data["fav_app"] = app