"""
reminders.py — Break reminder system.
Pet taps / barks at configurable intervals.
Config stored in config.json under "reminders" key.
"""
import time, datetime

class ReminderSystem:
    def __init__(self, pet_ref, interval_minutes: int = 45):
        self._pet       = pet_ref
        self._interval  = interval_minutes * 60   # seconds
        self._last_remind = time.monotonic()
        self._enabled   = interval_minutes > 0

    def set_interval(self, minutes: int):
        self._interval = minutes * 60
        self._enabled  = minutes > 0
        self._last_remind = time.monotonic()

    def check(self):
        """Call every tick. Returns reminder message or None."""
        if not self._enabled:
            return None
        now = time.monotonic()
        if now - self._last_remind >= self._interval:
            self._last_remind = now
            h = datetime.datetime.now().hour
            if 9 <= h <= 22:          # only remind during working hours
                return self._pick_message()
        return None

    def _pick_message(self):
        import random
        messages = [
            "Break time! Stretch! 🧘",
            "Stand up for a minute!",
            "Water break? 💧",
            "Rest your eyes! 👀",
            "Take a deep breath! 🌿",
            "Quick walk? I'll join! 🐾",
        ]
        return random.choice(messages)