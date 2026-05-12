"""
achievements.py — Achievement + badge system for Desktop Pet.

Design philosophy:
  - Achievements should feel EARNED not farmed
  - Every achievement tells a story about the user's relationship with their pet
  - Tiered (bronze/silver/gold) so there's always something to work toward
  - Secret achievements for delightful surprises
  - All data stored in achievements.json next to the exe

Categories:
  🍖 Caretaker  — feeding, hunger management
  🎭 Performer  — tricks, animations
  🔥 Devoted    — streaks, sessions, time
  🧠 Bonded     — memory, facts, naming
  🌍 Explorer   — pet types, accessories, features
  ⚡ Legend     — high level, rare combos
  🌙 Secret     — hidden until unlocked
"""

import json, os, sys, time, datetime
from dataclasses import dataclass, field
from typing import Optional

def _data_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "achievements.json")


TIER_COLORS = {
    "bronze": "#CD7F32",
    "silver": "#C0C0C0",
    "gold":   "#FFD700",
    "secret": "#9B59B6",
    "legend": "#E74C3C",
}

TIER_XP = {
    "bronze": 50,
    "silver": 150,
    "gold":   400,
    "secret": 200,
    "legend": 1000,
}

# ── Achievement definitions ────────────────────────────────────────────────
# (id, tier, category, emoji, name, description, secret)

ACHIEVEMENTS = [
    # ── Caretaker ─────────────────────────────────────────────────────────
    ("first_feed",      "bronze", "caretaker", "🍖", "First Meal",
     "Feed your pet for the first time.", False),
    ("fed_10",          "bronze", "caretaker", "🦴", "Regular Feeder",
     "Feed your pet 10 times.", False),
    ("fed_50",          "silver", "caretaker", "🍗", "Dedicated Carer",
     "Feed your pet 50 times.", False),
    ("fed_100",         "gold",   "caretaker", "👨‍🍳", "Master Chef",
     "Feed your pet 100 times. They trust you completely.", False),
    ("never_starved",   "silver", "caretaker", "💚", "Responsible Owner",
     "Keep hunger below 80% for 7 consecutive days.", False),
    ("rescue",          "bronze", "caretaker", "🚨", "Last Minute!",
     "Feed your pet when hunger is above 90%.", False),

    # ── Performer ─────────────────────────────────────────────────────────
    ("first_trick",     "bronze", "performer", "🎪", "Show Off",
     "Perform your first trick.", False),
    ("tricks_10",       "bronze", "performer", "🎭", "Entertainer",
     "Perform 10 tricks.", False),
    ("tricks_50",       "silver", "performer", "🌟", "Star Performer",
     "Perform 50 tricks.", False),
    ("tricks_100",      "gold",   "performer", "🏆", "Trick Master",
     "Perform 100 tricks. You two are in sync.", False),
    ("all_tricks",      "gold",   "performer", "🎯", "Full Repertoire",
     "Perform every single trick animation at least once.", False),
    ("double_trick",    "silver", "performer", "⚡", "Encore!",
     "Perform 3 tricks in under 60 seconds.", False),

    # ── Devoted ───────────────────────────────────────────────────────────
    ("day_1",           "bronze", "devoted",   "📅", "Day One",
     "Use the app for the first day.", False),
    ("streak_3",        "bronze", "devoted",   "🔥", "On a Roll",
     "3-day usage streak.", False),
    ("streak_7",        "silver", "devoted",   "🔥", "Week Warrior",
     "7-day usage streak.", False),
    ("streak_30",       "gold",   "devoted",   "🔥", "Monthly Legend",
     "30-day usage streak. Truly devoted.", False),
    ("streak_100",      "legend", "devoted",   "👑", "Centurion",
     "100-day usage streak. Legendary.", False),
    ("sessions_10",     "bronze", "devoted",   "💼", "Regular",
     "10 sessions with your pet.", False),
    ("sessions_50",     "silver", "devoted",   "🏠", "Home Base",
     "50 sessions. This pet is part of your routine.", False),
    ("sessions_100",    "gold",   "devoted",   "❤️", "Inseparable",
     "100 sessions together.", False),
    ("long_session",    "silver", "devoted",   "⏰", "Marathon",
     "Single session lasting over 4 hours.", False),

    # ── Bonded ────────────────────────────────────────────────────────────
    ("named_pet",       "bronze", "bonded",    "📛", "Named",
     "Give your pet a custom name.", False),
    ("first_fact",      "bronze", "bonded",    "🧠", "Getting Personal",
     "Your pet learned its first fact about you.", False),
    ("facts_5",         "silver", "bonded",    "📖", "Open Book",
     "Your pet knows 5 facts about you.", False),
    ("facts_10",        "gold",   "bonded",    "💬", "Best Friends",
     "Your pet knows 10 facts about you.", False),
    ("told_name",       "silver", "bonded",    "🤝", "Introductions",
     "Tell your pet your name.", False),
    ("chats_50",        "silver", "bonded",    "💭", "Conversationalist",
     "50 conversations with your pet.", False),
    ("chats_200",       "gold",   "bonded",    "🗣️", "Soulmates",
     "200 conversations. Your pet knows you well.", False),

    # ── Explorer ──────────────────────────────────────────────────────────
    ("tried_dragon",    "bronze", "explorer",  "🐉", "Here Be Dragons",
     "Switch to the dragon pet.", False),
    ("tried_cat",       "bronze", "explorer",  "🐱", "Cat Person",
     "Switch to the cat pet.", False),
    ("all_pets",        "gold",   "explorer",  "🦁", "Zookeeper",
     "Try all three pet types.", False),
    ("first_accessory", "bronze", "explorer",  "🎩", "Dressed Up",
     "Equip your first accessory.", False),
    ("all_accessories", "gold",   "explorer",  "👗", "Fashion Icon",
     "Unlock and equip every accessory.", False),
    ("spotify_connect", "silver", "explorer",  "🎵", "Music Lover",
     "Connect Spotify and play a song.", False),
    ("voice_command",   "bronze", "explorer",  "🎤", "Talking to Pets",
     "Use a voice command.", False),
    ("night_owl",       "silver", "explorer",  "🌙", "Night Owl",
     "Use the app after midnight 10 times.", False),
    ("early_bird",      "silver", "explorer",  "🌅", "Early Bird",
     "Use the app before 7am 5 times.", False),
    ("settings_opened", "bronze", "explorer",  "⚙️", "Curious",
     "Open the settings panel.", False),
    ("memory_opened",   "bronze", "explorer",  "🧠", "Introspective",
     "Open the memory dashboard.", False),

    # ── Legend ────────────────────────────────────────────────────────────
    ("level_5",         "bronze", "legend",    "⬆️", "Growing Up",
     "Reach level 5.", False),
    ("level_10",        "silver", "legend",    "💪", "Veteran",
     "Reach level 10.", False),
    ("level_20",        "gold",   "legend",    "🌟", "Elite",
     "Reach level 20.", False),
    ("level_50",        "legend", "legend",    "👑", "Mythic",
     "Reach level 50. You are a legend.", False),

    # ── Secret ────────────────────────────────────────────────────────────
    ("late_night_50",   "secret", "secret",    "🦇", "Creature of the Night",
     "50 late night sessions. Do you ever sleep?", True),
    ("renamed_3",       "secret", "secret",    "🎭", "Identity Crisis",
     "Rename your pet 3 times.", True),
    ("fed_hungry_self", "secret", "secret",    "🤝", "We're the Same",
     "Feed your pet while YOUR hunger timer is also critical... somehow.", True),
    ("trick_while_hungry", "secret", "secret", "🎪", "Suffering Artist",
     "Perform a trick while pet is starving.", True),
    ("all_colors",      "secret", "secret",    "🌈", "True Colors",
     "Try every colour tint.", True),
    ("midnight_feed",   "secret", "secret",    "🌚", "Midnight Snack",
     "Feed your pet between 00:00 and 01:00.", True),
    ("hyper_100_tricks","secret", "secret",    "💥", "Chaos Agent",
     "Perform 100 tricks with the hyper personality.", True),
    ("pet_5_types",     "secret", "secret",    "🔄", "Indecisive",
     "Switch pet type 5+ times in one session.", True),
]

# Build lookup dict
ACHIEVEMENT_MAP = {a[0]: a for a in ACHIEVEMENTS}


class AchievementSystem:
    def __init__(self):
        self._path    = _data_path()
        self._data    = self._load()
        self._pending = []   # [(achievement_id, timestamp)] unlocked this session
        self._session_tricks = 0
        self._session_pet_switches = 0
        self._last_trick_times = []
        self._colors_tried = set(self._data.get("colors_tried", []))
        self._tricks_seen  = set(self._data.get("tricks_seen",  []))

    # ── Persistence ───────────────────────────────────────────────────────

    def _load(self) -> dict:
        defaults = {
            "unlocked":       {},   # {id: timestamp}
            "progress":       {},   # {id: current_value}
            "total_xp":       0,
            "colors_tried":   [],
            "tricks_seen":    [],
            "pet_types_tried":[],
            "renames":        0,
        }
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    saved = json.load(f)
                defaults.update(saved)
            except Exception:
                pass
        return defaults

    def save(self):
        self._data["colors_tried"] = list(self._colors_tried)
        self._data["tricks_seen"]  = list(self._tricks_seen)
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    # ── Core unlock ───────────────────────────────────────────────────────

    def unlock(self, achievement_id: str) -> bool:
        """
        Attempt to unlock an achievement.
        Returns True if newly unlocked (caller should show notification).
        """
        if achievement_id not in ACHIEVEMENT_MAP:
            return False
        if achievement_id in self._data["unlocked"]:
            return False   # already unlocked

        self._data["unlocked"][achievement_id] = time.time()
        a = ACHIEVEMENT_MAP[achievement_id]
        xp = TIER_XP[a[1]]
        self._data["total_xp"] = self._data.get("total_xp", 0) + xp
        self._pending.append(achievement_id)
        print(f"[achievement] 🏆 UNLOCKED: {a[4]} ({a[1].upper()}) +{xp}XP")
        self.save()
        return True

    def is_unlocked(self, achievement_id: str) -> bool:
        return achievement_id in self._data["unlocked"]

    def pop_pending(self) -> list:
        """Return and clear pending notifications."""
        p = list(self._pending)
        self._pending.clear()
        return p

    # ── Progress tracking ─────────────────────────────────────────────────

    def _prog(self, key: str, default=0):
        return self._data["progress"].get(key, default)

    def _set_prog(self, key: str, value):
        self._data["progress"][key] = value

    # ── Event hooks — call these from main.py ─────────────────────────────

    def on_feed(self, total_feeds: int, hunger: float):
        if total_feeds == 1:          self.unlock("first_feed")
        if total_feeds >= 10:         self.unlock("fed_10")
        if total_feeds >= 50:         self.unlock("fed_50")
        if total_feeds >= 100:        self.unlock("fed_100")
        if hunger >= 90:              self.unlock("rescue")

        h = time.localtime().tm_hour
        if h == 0 or h == 1:          self.unlock("midnight_feed")

    def on_trick(self, trick_name: str, total_tricks: int, hunger: float,
                 personality: str):
        if total_tricks == 1:         self.unlock("first_trick")
        if total_tricks >= 10:        self.unlock("tricks_10")
        if total_tricks >= 50:        self.unlock("tricks_50")
        if total_tricks >= 100:       self.unlock("tricks_100")
        if hunger >= 80:              self.unlock("trick_while_hungry")
        if personality == "hyper" and total_tricks >= 100:
            self.unlock("hyper_100_tricks")

        # Track seen tricks for all_tricks achievement
        self._tricks_seen.add(trick_name)
        self._set_prog("tricks_seen_count", len(self._tricks_seen))

        # Rapid tricks (3 in 60 seconds)
        now = time.monotonic()
        self._last_trick_times.append(now)
        self._last_trick_times = [t for t in self._last_trick_times
                                   if now - t < 60]
        if len(self._last_trick_times) >= 3:
            self.unlock("double_trick")

    def on_session_start(self, total_sessions: int, streak: int):
        if total_sessions >= 1:       self.unlock("day_1")
        if total_sessions >= 10:      self.unlock("sessions_10")
        if total_sessions >= 50:      self.unlock("sessions_50")
        if total_sessions >= 100:     self.unlock("sessions_100")
        if streak >= 3:               self.unlock("streak_3")
        if streak >= 7:               self.unlock("streak_7")
        if streak >= 30:              self.unlock("streak_30")
        if streak >= 100:             self.unlock("streak_100")

        h = time.localtime().tm_hour
        if h >= 23 or h <= 3:
            nights = self._prog("late_nights", 0) + 1
            self._set_prog("late_nights", nights)
            if nights >= 10:          self.unlock("night_owl")
            if nights >= 50:          self.unlock("late_night_50")
        if 5 <= h <= 6:
            early = self._prog("early_birds", 0) + 1
            self._set_prog("early_birds", early)
            if early >= 5:            self.unlock("early_bird")

    def on_session_end(self, duration_minutes: float):
        if duration_minutes >= 240:   self.unlock("long_session")

    def on_level_up(self, level: int):
        if level >= 5:                self.unlock("level_5")
        if level >= 10:               self.unlock("level_10")
        if level >= 20:               self.unlock("level_20")
        if level >= 50:               self.unlock("level_50")

    def on_pet_named(self, name: str, default_names=("Buddy","kutta","Pet")):
        if name not in default_names:
            self.unlock("named_pet")

    def on_pet_rename(self):
        renames = self._data.get("renames", 0) + 1
        self._data["renames"] = renames
        if renames >= 3:              self.unlock("renamed_3")

    def on_fact_learned(self, total_facts: int):
        if total_facts >= 1:          self.unlock("first_fact")
        if total_facts >= 5:          self.unlock("facts_5")
        if total_facts >= 10:         self.unlock("facts_10")

    def on_user_name_told(self):
        self.unlock("told_name")

    def on_chat(self, total_chats: int):
        if total_chats >= 50:         self.unlock("chats_50")
        if total_chats >= 200:        self.unlock("chats_200")

    def on_pet_switched(self, pet_type: str):
        tried = set(self._data.get("pet_types_tried", []))
        tried.add(pet_type)
        self._data["pet_types_tried"] = list(tried)

        if "dragon" in tried:         self.unlock("tried_dragon")
        if "cat" in tried:            self.unlock("tried_cat")
        if tried >= {"dog","dragon","cat"}: self.unlock("all_pets")

        self._session_pet_switches += 1
        if self._session_pet_switches >= 5: self.unlock("pet_5_types")

    def on_accessory_equipped(self, accessory_name: str, all_unlocked: list):
        self.unlock("first_accessory")
        equipped = set(self._data.get("accessories_equipped", []))
        equipped.add(accessory_name)
        self._data["accessories_equipped"] = list(equipped)
        if set(all_unlocked) <= equipped:
            self.unlock("all_accessories")

    def on_spotify_played(self):
        self.unlock("spotify_connect")

    def on_voice_command(self):
        self.unlock("voice_command")

    def on_color_tried(self, color_name: str):
        self._colors_tried.add(color_name)
        if len(self._colors_tried) >= 6:
            self.unlock("all_colors")

    def on_settings_opened(self):
        self.unlock("settings_opened")

    def on_memory_opened(self):
        self.unlock("memory_opened")

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        total   = len(ACHIEVEMENTS)
        unlocked = len(self._data["unlocked"])
        pct     = int(unlocked / total * 100)
        by_tier = {}
        for aid, ach in ACHIEVEMENT_MAP.items():
            tier = ach[1]
            if tier not in by_tier:
                by_tier[tier] = {"total": 0, "unlocked": 0}
            by_tier[tier]["total"] += 1
            if aid in self._data["unlocked"]:
                by_tier[tier]["unlocked"] += 1
        return {
            "total":     total,
            "unlocked":  unlocked,
            "pct":       pct,
            "total_xp":  self._data.get("total_xp", 0),
            "by_tier":   by_tier,
        }

    def recent_unlocks(self, n: int = 5) -> list:
        """Return N most recently unlocked achievement ids."""
        unlocked = self._data.get("unlocked", {})
        sorted_ids = sorted(unlocked.items(), key=lambda x: x[1], reverse=True)
        return [aid for aid, _ in sorted_ids[:n]]

    def get_unlocked_data(self) -> list:
        """Return list of (achievement_def, unlock_timestamp) sorted by time."""
        result = []
        for aid, ts in self._data["unlocked"].items():
            if aid in ACHIEVEMENT_MAP:
                result.append((ACHIEVEMENT_MAP[aid], ts))
        return sorted(result, key=lambda x: x[1], reverse=True)

    def get_locked_data(self) -> list:
        """Return list of achievement_defs not yet unlocked."""
        result = []
        for aid, ach in ACHIEVEMENT_MAP.items():
            if aid not in self._data["unlocked"]:
                result.append(ach)
        return result