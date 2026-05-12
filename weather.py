"""
weather.py — Real-time local weather awareness.

Uses wttr.in JSON API — completely free, no API key, no account.
Detects location from IP automatically.

Updates every 30 minutes. Pet reacts to weather:
  • Rain   → "It's raining outside! Stay cozy ☔"
  • Snow   → "IT'S SNOWING!! 🌨️"
  • Hot    → "It's so hot today 🥵 stay cool"
  • Storm  → "*hides under desk* 🌩️"
  • Sunny  → "Beautiful day outside! 🌞"
"""

import urllib.request, json, time, threading

WTTR_URL     = "https://wttr.in/?format=j1"
POLL_MINUTES = 30


WEATHER_CONDITIONS = {
    # WMO code ranges → (emoji, category, description)
    113: ("☀️",  "sunny",   "sunny"),
    116: ("⛅",  "cloudy",  "partly cloudy"),
    119: ("☁️",  "cloudy",  "cloudy"),
    122: ("🌫️", "cloudy",  "overcast"),
    143: ("🌫️", "fog",     "foggy"),
    176: ("🌦️", "rain",    "light showers"),
    179: ("🌨️", "snow",    "light snow"),
    182: ("🌧️", "rain",    "sleet"),
    185: ("🌨️", "snow",    "freezing drizzle"),
    200: ("⛈️",  "storm",   "thundery outbreaks"),
    227: ("🌨️", "snow",    "blowing snow"),
    230: ("❄️",  "snow",    "blizzard"),
    248: ("🌫️", "fog",     "fog"),
    260: ("🌫️", "fog",     "freezing fog"),
    263: ("🌦️", "rain",    "light drizzle"),
    266: ("🌧️", "rain",    "drizzle"),
    281: ("🌨️", "snow",    "freezing drizzle"),
    284: ("🌨️", "snow",    "heavy freezing drizzle"),
    293: ("🌦️", "rain",    "light rain"),
    296: ("🌧️", "rain",    "light rain"),
    299: ("🌧️", "rain",    "moderate rain"),
    302: ("🌧️", "rain",    "heavy rain"),
    305: ("🌧️", "rain",    "heavy rain"),
    308: ("🌧️", "rain",    "very heavy rain"),
    311: ("🌧️", "rain",    "light freezing rain"),
    314: ("🌧️", "rain",    "moderate freezing rain"),
    317: ("🌨️", "snow",    "light sleet"),
    320: ("🌨️", "snow",    "moderate sleet"),
    323: ("🌨️", "snow",    "light snow"),
    326: ("🌨️", "snow",    "moderate snow"),
    329: ("❄️",  "snow",    "heavy snow"),
    332: ("❄️",  "snow",    "heavy snow"),
    335: ("❄️",  "snow",    "heavy snow showers"),
    338: ("❄️",  "snow",    "heavy snow"),
    350: ("🌨️", "snow",    "ice pellets"),
    353: ("🌦️", "rain",    "light rain shower"),
    356: ("🌧️", "rain",    "moderate rain"),
    359: ("🌧️", "rain",    "torrential rain"),
    362: ("🌨️", "snow",    "light sleet showers"),
    365: ("🌨️", "snow",    "moderate sleet"),
    368: ("🌨️", "snow",    "light snow showers"),
    371: ("❄️",  "snow",    "moderate snow showers"),
    374: ("🌨️", "snow",    "light ice pellet showers"),
    377: ("🌨️", "snow",    "moderate ice pellets"),
    386: ("⛈️",  "storm",   "thunderstorm with light rain"),
    389: ("⛈️",  "storm",   "thunderstorm with heavy rain"),
    392: ("⛈️",  "storm",   "thunderstorm with light snow"),
    395: ("⛈️",  "storm",   "thunderstorm with heavy snow"),
}

PET_REACTIONS = {
    "sunny": [
        "Beautiful day outside! 🌞",
        "It's sunny out there! 🌤️",
        "Nice weather today! 🌞",
    ],
    "rain": [
        "It's raining outside ☔ stay cozy!",
        "Rainy day... perfect for staying in 🌧️",
        "Don't forget an umbrella! ☔",
    ],
    "snow": [
        "IT'S SNOWING!! 🌨️ OMG",
        "Snow!! Can we go play?? ❄️",
        "Everything is white outside! ❄️",
    ],
    "storm": [
        "*hides* Is that thunder? 🌩️",
        "Scary storm outside! 🌩️",
        "I don't like storms... 😨",
    ],
    "fog": [
        "It's super foggy out 🌫️",
        "Can't see anything in this fog! 🌫️",
    ],
    "cloudy": [
        "Cloudy today ☁️",
        "Grey skies... but we're warm inside!",
    ],
    "hot": [
        "It's so HOT out! 🥵 Stay cool!",
        "Phew! {temp}°C outside 🌡️",
    ],
    "cold": [
        "Brrr! {temp}°C outside! 🥶",
        "It's freezing! {temp}°C 🥶 stay warm!",
    ],
}


class WeatherData:
    def __init__(self):
        self.temp_c      = None
        self.feels_like  = None
        self.condition   = "unknown"
        self.category    = "unknown"
        self.emoji       = "🌡️"
        self.description = ""
        self.city        = ""
        self.humidity    = None
        self.last_update = 0.0
        self.available   = False


class WeatherWatcher:
    def __init__(self):
        self._data    = WeatherData()
        self._prev_cat = ""
        self.changed  = False
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _fetch(self):
        try:
            req  = urllib.request.Request(WTTR_URL,
                   headers={"User-Agent": "DesktopPet/1.0"})
            raw  = json.loads(urllib.request.urlopen(req, timeout=8).read())
            curr = raw["current_condition"][0]
            area = raw.get("nearest_area", [{}])[0]

            code = int(curr.get("weatherCode", 113))
            temp = int(curr.get("temp_C", 20))
            feel = int(curr.get("FeelsLikeC", 20))
            hum  = int(curr.get("humidity", 50))
            city = area.get("areaName", [{}])[0].get("value", "")

            # Find closest code
            best_code = min(WEATHER_CONDITIONS.keys(),
                           key=lambda c: abs(c - code))
            emoji, cat, desc = WEATHER_CONDITIONS.get(
                best_code, ("🌡️", "unknown", "unknown"))

            # Override category for extreme temps
            if temp >= 35:  cat = "hot"
            elif temp <= 0: cat = "cold"

            self._prev_cat        = self._data.category
            self._data.temp_c     = temp
            self._data.feels_like = feel
            self._data.condition  = str(code)
            self._data.category   = cat
            self._data.emoji      = emoji
            self._data.description = desc
            self._data.city       = city
            self._data.humidity   = hum
            self._data.last_update = time.monotonic()
            self._data.available  = True
            self.changed = (cat != self._prev_cat)

            print(f"[weather] {city}: {temp}°C, {desc} {emoji}")
        except Exception as e:
            print(f"[weather] fetch failed: {e}")

    def _poll_loop(self):
        while True:
            self._fetch()
            time.sleep(POLL_MINUTES * 60)

    @property
    def is_available(self): return self._data.available

    @property
    def data(self): return self._data

    def get_reaction(self) -> str:
        """Get a random pet reaction for current weather."""
        import random
        cat  = self._data.category
        temp = self._data.temp_c or 20
        pool = PET_REACTIONS.get(cat, PET_REACTIONS.get("cloudy", ["Weather's weird today 🌡️"]))
        msg  = random.choice(pool)
        return msg.format(temp=temp, city=self._data.city, emoji=self._data.emoji)

    def summary(self) -> str:
        d = self._data
        if not d.available: return ""
        city = f"{d.city}: " if d.city else ""
        return f"{city}{d.temp_c}°C, {d.description} {d.emoji}"