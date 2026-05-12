"""
screen_time.py — Tracks daily pet usage and rewards streaks.

Records:
  • Daily session time in minutes
  • Current streak (consecutive days used)
  • Longest streak ever
  • Total lifetime hours
  • Milestones (first week, first month, 100 hours, etc.)

Saves to screen_time.json. Pet celebrates milestones and streaks.
"""

import json, os, time, datetime

SAVE_PATH = os.path.join(os.path.dirname(__file__), "screen_time.json")

MILESTONES = [
    (1,    "First day together! 🎉"),
    (7,    "One week streak! 🔥"),
    (14,   "Two weeks! We're bonding 🐾"),
    (30,   "One whole month!! 🏆"),
    (50,   "50 days! You're amazing 🌟"),
    (100,  "100 DAY STREAK!! LEGENDARY 👑"),
    (365,  "ONE YEAR TOGETHER!! 🎊🎊🎊"),
]

HOUR_MILESTONES = [
    (1,   "1 hour with me!"),
    (10,  "10 hours together 🐾"),
    (24,  "A whole day's worth! ⏰"),
    (100, "100 hours!! Best friends 🌟"),
    (500, "500 hours — we're inseparable 💕"),
]


class ScreenTimeTracker:
    def __init__(self):
        self._data         = self._load()
        self._session_start = time.time()
        self._last_tick     = time.monotonic()

    def _load(self) -> dict:
        today = datetime.date.today().isoformat()
        defaults = {
            "today":          today,
            "today_minutes":  0.0,
            "streak":         0,
            "longest_streak": 0,
            "last_date":      None,
            "total_hours":    0.0,
            "daily_log":      {},       # {date: minutes}
            "milestones_hit": [],
        }
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH) as f:
                    saved = json.load(f)
                defaults.update(saved)
            except Exception:
                pass

        # Update streak on load
        self._update_streak(defaults)
        return defaults

    def _update_streak(self, data: dict):
        today     = datetime.date.today().isoformat()
        last      = data.get("last_date")
        if last is None:
            data["streak"]    = 1
            data["last_date"] = today
            return

        last_dt  = datetime.date.fromisoformat(last)
        today_dt = datetime.date.today()
        delta    = (today_dt - last_dt).days

        if delta == 0:
            pass   # same day — streak unchanged
        elif delta == 1:
            data["streak"] += 1
            data["last_date"] = today
            if data["streak"] > data["longest_streak"]:
                data["longest_streak"] = data["streak"]
        else:
            # Streak broken
            data["streak"]    = 1
            data["last_date"] = today

        # Reset daily counter on new day
        if data.get("today") != today:
            data["today"]         = today
            data["today_minutes"] = 0.0

    def save(self):
        try:
            with open(SAVE_PATH, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def tick(self) -> list[str]:
        """
        Call every game tick. Returns list of milestone messages to show.
        """
        now = time.monotonic()
        dt_minutes = (now - self._last_tick) / 60.0
        self._last_tick = now

        self._data["today_minutes"] += dt_minutes
        self._data["total_hours"]   += dt_minutes / 60.0

        # Update daily log
        today = datetime.date.today().isoformat()
        log = self._data.setdefault("daily_log", {})
        log[today] = log.get(today, 0.0) + dt_minutes

        # Keep only last 90 days of log
        if len(log) > 90:
            oldest = sorted(log.keys())[0]
            del log[oldest]

        return self._check_milestones()

    def _check_milestones(self) -> list[str]:
        messages = []
        hit      = set(self._data.get("milestones_hit", []))

        # Streak milestones
        streak = self._data["streak"]
        for days, msg in MILESTONES:
            key = f"streak_{days}"
            if streak >= days and key not in hit:
                hit.add(key)
                messages.append(msg)

        # Hour milestones
        hours = self._data["total_hours"]
        for h, msg in HOUR_MILESTONES:
            key = f"hours_{h}"
            if hours >= h and key not in hit:
                hit.add(key)
                messages.append(f"{msg} ⏱️")

        self._data["milestones_hit"] = list(hit)
        return messages

    # ── Public getters ────────────────────────────────────────────────────

    @property
    def streak(self) -> int:
        return self._data["streak"]

    @property
    def longest_streak(self) -> int:
        return self._data["longest_streak"]

    @property
    def today_minutes(self) -> float:
        return self._data["today_minutes"]

    @property
    def total_hours(self) -> float:
        return self._data["total_hours"]

    def streak_summary(self) -> str:
        s = self._data["streak"]
        flame = "🔥" * min(s, 5)
        return f"{s} day streak {flame}"

    def today_summary(self) -> str:
        m = int(self._data["today_minutes"])
        if m < 60:
            return f"{m}min today"
        return f"{m//60}h {m%60}min today"

    def weekly_chart(self) -> list[tuple[str, float]]:
        """Last 7 days as [(day_name, minutes)]."""
        result = []
        today  = datetime.date.today()
        log    = self._data.get("daily_log", {})
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            mins = log.get(day.isoformat(), 0.0)
            result.append((day.strftime("%a"), mins))
        return result