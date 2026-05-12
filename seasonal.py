"""
seasonal.py — Seasonal events and holiday awareness.

Detects current date and returns:
  • Active holiday/season
  • Seasonal greeting messages
  • Recommended accessory for the season
  • Special particle effects (snowflakes, hearts, etc.)

Seasons and events:
  Jan 1       New Year
  Feb 14      Valentine's Day
  Mar 17      St. Patrick's Day
  Apr 1       April Fool's
  Oct 31      Halloween
  Dec 24-25   Christmas
  Dec 31      New Year's Eve
  + seasonal: Winter/Spring/Summer/Autumn
"""

import datetime, random


# (month, day_start, day_end, name, emoji, accessory_hint, greetings)
EVENTS = [
    (1,  1,  2,  "new_year",       "🎊", "party_hat",
     ["HAPPY NEW YEAR!!! 🎊🎉", "New year new adventures! 🌟",
      "365 new days together! 🎊"]),

    (2,  14, 15, "valentines",     "❤️", "bow_tie",
     ["Happy Valentine's Day! ❤️", "You're my favourite human 💕",
      "Love is in the air! 🐾❤️", "Be my valentine? 🥺"]),

    (3,  17, 18, "st_patricks",    "🍀", "bandana",
     ["Happy St. Patrick's Day! 🍀", "Feeling lucky! 🍀",
      "Wear green or I'll bark! 🍀"]),

    (4,  1,  2,  "april_fools",    "🃏", "party_hat",
     ["April Fool's!! I'm actually a DRAGON 🐉 ...jk",
      "Your shoelace is untied! ...you're not wearing shoes 🃏",
      "I learned to talk! ...I always could 😏"]),

    (10, 31, 32, "halloween",      "🎃", "pirate_hat",
     ["Happy Halloween!! 🎃👻", "Trick or TREAT! 🦴",
      "WOOOOOO spooky!! 👻", "I'm going as a WOLF 🐺"]),

    (12, 24, 26, "christmas",      "🎄", "santa_hat",
     ["MERRY CHRISTMAS!! 🎄🎁", "HO HO HO!! 🎅",
      "Santa brought TREATS! 🦴🎁", "It's the most wonderful time!! 🎄"]),

    (12, 31, 32, "new_year_eve",   "🥂", "party_hat",
     ["New Year's Eve!! 🥂🎊", "Almost midnight!! 🕛",
      "One more day then PARTY 🎊"]),
]

SEASONS = {
    "winter": {
        "months": [12, 1, 2],
        "msgs": ["Brr it's cold! 🥶", "Winter cuddles? 🐾", "Stay warm out there! ❄️"]
    },
    "spring": {
        "months": [3, 4, 5],
        "msgs": ["Spring is here! 🌸", "Everything's blooming! 🌷", "Love spring walks! 🐾"]
    },
    "summer": {
        "months": [6, 7, 8],
        "msgs": ["It's so HOT! 🌞🥵", "Summer zoomies! 💨", "Pool time? 🏊 ...I can't swim"]
    },
    "autumn": {
        "months": [9, 10, 11],
        "msgs": ["Autumn leaves! 🍂", "Cozy season! 🍂☕", "The leaves are falling! 🍁"]
    },
}

SEASONAL_PARTICLES = {
    "christmas":   "sparkle",    # snowflakes / sparkles
    "halloween":   "exclaim",    # spooky effect
    "valentines":  "hearts",
    "new_year":    "stars",
    "new_year_eve":"stars",
    "april_fools": "exclaim",
}


class SeasonalManager:
    def __init__(self):
        self._greeted_today = set()
        self._last_check_date = None

    def get_current_event(self) -> dict | None:
        """Return active event dict or None."""
        now   = datetime.datetime.now()
        month = now.month
        day   = now.day

        for (m, d_start, d_end, name, emoji, acc, greetings) in EVENTS:
            if month == m and d_start <= day < d_end:
                return {
                    "name":       name,
                    "emoji":      emoji,
                    "accessory":  acc,
                    "greetings":  greetings,
                }
        return None

    def get_season(self) -> str:
        month = datetime.datetime.now().month
        if month in (12, 1, 2):  return "winter"
        if month in (3, 4, 5):   return "spring"
        if month in (6, 7, 8):   return "summer"
        return "autumn"

    def get_daily_greeting(self) -> str | None:
        """
        Returns a seasonal/holiday greeting once per day.
        Call on startup or first IDLE of the day.
        """
        today = datetime.date.today().isoformat()
        if today in self._greeted_today:
            return None
        self._greeted_today.add(today)

        event = self.get_current_event()
        if event:
            return random.choice(event["greetings"])

        # Seasonal greeting (25% chance on non-holiday days)
        if random.random() < 0.25:
            season = self.get_season()
            season_data = SEASONS.get(season, {})
            msgs = season_data.get("msgs", [])
            if msgs:
                return random.choice(msgs)

        return None

    def should_suggest_accessory(self) -> str | None:
        """Return accessory name if a holiday suggests one."""
        event = self.get_current_event()
        return event["accessory"] if event else None

    def get_particle_type(self) -> str | None:
        """Return particle type for current event."""
        event = self.get_current_event()
        if event:
            return SEASONAL_PARTICLES.get(event["name"])
        return None

    def is_holiday(self) -> bool:
        return self.get_current_event() is not None

    def holiday_name(self) -> str:
        event = self.get_current_event()
        return event["name"] if event else self.get_season()