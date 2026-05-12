"""
emotion_engine.py — 2D continuous emotion state machine for the desktop pet.

Instead of a simple mood string, the pet has two continuous axes:
  • valence  : -1.0 (very negative) → +1.0 (very positive)
  • arousal  : -1.0 (very calm/sleepy) → +1.0 (very excited/frantic)

These drift naturally over time based on:
  - Hunger level
  - Time of day
  - Music playing
  - App context (coding, YouTube, meeting, etc.)
  - Recent interactions (fed, trick, pet, ignored)
  - Pet personality multipliers
  - Random micro-fluctuations (makes it feel alive)

Every tick the engine outputs:
  - mood_name  : human-readable mood string (maps to existing animation system)
  - intensity  : 0.0–1.0 (how strongly the pet feels this)
  - speech_bias: which fallback context to prefer

Usage:
    engine = EmotionEngine(pet_state, personality="hyper")
    engine.tick(context)           # call every ~1 second
    mood = engine.mood_name        # use in animation selection
    engine.on_fed()                # call when pet is fed
    engine.on_trick()              # call when trick completes
    engine.on_ignored(seconds)     # call when pet hasn't been interacted with
"""

import time
import math
import random
from dataclasses import dataclass


# ── Mood map — (valence_min, valence_max, arousal_min, arousal_max) → mood ──
# Regions of the 2D space map to named moods
MOOD_REGIONS = [
    # name          v_min  v_max  a_min  a_max   weight
    ("excited",      0.3,   1.0,   0.4,   1.0,    1.0),
    ("happy",        0.2,   1.0,  -0.2,   0.4,    1.0),
    ("love",         0.6,   1.0,  -0.4,   0.3,    1.0),
    ("content",      0.1,   0.6,  -1.0,  -0.2,    1.0),
    ("curious",     -0.1,   0.5,   0.1,   0.7,    0.9),
    ("bored",       -0.3,   0.1,  -1.0,   0.0,    0.8),
    ("sleepy",      -0.1,   0.3,  -1.0,  -0.5,    0.9),
    ("sad",         -0.6,  -0.1,  -0.5,   0.2,    0.9),
    ("hungry",      -0.4,   0.1,   0.0,   0.6,    1.0),  # mid arousal, negative valence
    ("angry",       -1.0,  -0.3,   0.3,   1.0,    0.9),
    ("surprised",    0.0,   1.0,   0.6,   1.0,    0.8),
]

# ── Personality modifiers ─────────────────────────────────────────────────
# Each personality biases the 2D space differently
PERSONALITY_BIAS = {
    #             valence  arousal  volatility
    "playful":   ( 0.2,    0.3,     0.15),
    "lazy":      ( 0.1,   -0.4,     0.05),
    "curious":   ( 0.1,    0.1,     0.12),
    "loyal":     ( 0.3,    0.0,     0.08),
    "hyper":     ( 0.1,    0.5,     0.25),
    # cat variants
    "cat_aloof":  (-0.1,  -0.2,     0.06),
    "cat_curious":( 0.0,   0.1,     0.10),
    "cat_grumpy": (-0.2,  -0.1,     0.08),
    # dragon variants
    "dragon_proud":( 0.2,  0.1,     0.07),
    "dragon_fire": ( 0.0,  0.3,     0.15),
}

# ── App context influence ─────────────────────────────────────────────────
APP_INFLUENCE = {
    # category   valence  arousal
    "spotify":  ( 0.15,   0.10),
    "youtube":  ( 0.05,   0.05),
    "vscode":   ( 0.00,  -0.05),
    "github":   ( 0.00,  -0.05),
    "meeting":  (-0.05,  -0.10),
    "browser":  ( 0.00,   0.00),
    "other":    ( 0.00,   0.00),
}

# ── Time of day influence ─────────────────────────────────────────────────
def _time_influence() -> tuple:
    """Returns (valence_delta, arousal_delta) based on hour."""
    h = time.localtime().tm_hour
    if 0 <= h <= 5:    return (-0.05, -0.25)   # deep night — sleepy, slight melancholy
    if 6 <= h <= 8:    return ( 0.10,  0.05)   # morning — hopeful, gently waking
    if 9 <= h <= 11:   return ( 0.05,  0.10)   # mid morning — productive, mild energy
    if 12 <= h <= 13:  return ( 0.00,  0.00)   # lunch — neutral
    if 14 <= h <= 16:  return (-0.05, -0.05)   # afternoon slump
    if 17 <= h <= 19:  return ( 0.10,  0.05)   # evening — relaxing, positive
    if 20 <= h <= 22:  return ( 0.05, -0.10)   # late evening — calm
    return (-0.05, -0.15)                        # late night — tired


class EmotionEngine:
    """
    Continuous 2D emotion state machine.
    Call tick() every second. Read mood_name for current mood.
    """

    DECAY_RATE    = 0.02    # how fast valence/arousal drift back to baseline
    MICRO_NOISE   = 0.008   # tiny random fluctuation per tick (feels alive)
    HUNGER_WEIGHT = 0.4     # how much hunger dominates the mood
    MAX_DELTA     = 0.12    # max change per tick (prevents jarring jumps)

    def __init__(self, pet_state, personality: str = "playful", pet_type: str = "dog"):
        self._state       = pet_state
        self._pet_type    = pet_type
        self._personality = personality

        # Get personality key for bias lookup
        self._pers_key = self._resolve_personality_key(personality, pet_type)

        # Start near the personality baseline
        bias = PERSONALITY_BIAS.get(self._pers_key, (0.1, 0.0, 0.10))
        self.valence  = bias[0] + random.uniform(-0.1, 0.1)
        self.arousal  = bias[1] + random.uniform(-0.1, 0.1)
        self.valence  = max(-1.0, min(1.0, self.valence))
        self.arousal  = max(-1.0, min(1.0, self.arousal))

        self._last_tick   = time.monotonic()
        self._last_fed    = 0.0
        self._last_trick  = 0.0
        self._last_pet    = 0.0
        self._last_interact = time.monotonic()

        # Smoothed output (prevents flickering)
        self._smooth_v    = self.valence
        self._smooth_a    = self.arousal

        # Public outputs
        self.mood_name    = "happy"
        self.intensity    = 0.5
        self.speech_bias  = "idle"

    # ── Public API ────────────────────────────────────────────────────────

    def set_personality(self, personality: str, pet_type: str = None):
        if pet_type:
            self._pet_type = pet_type
        self._personality = personality
        self._pers_key    = self._resolve_personality_key(
            personality, self._pet_type)

    def on_fed(self):
        """Call when pet is fed."""
        self._last_fed = time.monotonic()
        self._push(+0.5, +0.3)   # big positive surge, moderate energy

    def on_trick(self):
        """Call when trick completes."""
        self._last_trick = time.monotonic()
        self._push(+0.3, +0.5)   # positive + high energy

    def on_petted(self):
        """Call when user hovers/pets the pet."""
        self._last_pet = time.monotonic()
        self._push(+0.25, -0.1)  # warm positive, slightly calming

    def on_levelup(self):
        """Call on level up."""
        self._push(+0.4, +0.7)   # very excited

    def on_wake_word(self):
        """Call when wake word detected."""
        self._push(+0.1, +0.4)   # alert, engaged

    def on_ignored(self, idle_seconds: float):
        """Call periodically when pet hasn't been interacted with."""
        if idle_seconds > 300:    # 5 minutes
            self._push(-0.02, -0.03)  # slowly gets lonely/bored

    def on_spotify(self, playing: bool):
        """Call when Spotify state changes."""
        if playing:
            self._push(+0.15, +0.10)
        else:
            self._push(-0.05, -0.05)

    def tick(self, app_category: str = "other", spotify_playing: bool = False):
        """
        Update the emotion state. Call every ~1 second.
        Returns (mood_name, intensity).
        """
        now     = time.monotonic()
        dt      = min(now - self._last_tick, 0.5)   # cap at 0.5s to avoid jumps
        self._last_tick = now

        bias        = PERSONALITY_BIAS.get(self._pers_key, (0.1, 0.0, 0.10))
        v_bias      = bias[0]
        a_bias      = bias[1]
        volatility  = bias[2]

        # ── Hunger influence ──────────────────────────────────────────────
        hunger = getattr(self._state, "hunger", 0)
        if hunger > 80:
            h_v = -0.6   # very negative when starving
            h_a =  0.4   # agitated
        elif hunger > 55:
            h_v = -0.25
            h_a =  0.15
        elif hunger < 15:
            h_v =  0.15  # well fed — positive boost
            h_a = -0.05
        else:
            h_v =  0.0
            h_a =  0.0

        # ── Time of day ───────────────────────────────────────────────────
        t_v, t_a = _time_influence()

        # ── App context ───────────────────────────────────────────────────
        app_v, app_a = APP_INFLUENCE.get(app_category, (0.0, 0.0))

        # Spotify bonus
        if spotify_playing:
            app_a += 0.08
            app_v += 0.08

        # ── Target state ──────────────────────────────────────────────────
        target_v = (v_bias
                    + h_v   * self.HUNGER_WEIGHT
                    + t_v   * 0.3
                    + app_v * 0.2)
        target_a = (a_bias
                    + h_a   * self.HUNGER_WEIGHT
                    + t_a   * 0.3
                    + app_a * 0.2)
        target_v = max(-1.0, min(1.0, target_v))
        target_a = max(-1.0, min(1.0, target_a))

        # ── Drift toward target ───────────────────────────────────────────
        drift_v = (target_v - self.valence) * self.DECAY_RATE * dt * 60
        drift_a = (target_a - self.arousal) * self.DECAY_RATE * dt * 60

        # ── Micro-noise (makes it feel alive) ─────────────────────────────
        noise_v = random.gauss(0, volatility * self.MICRO_NOISE * dt * 60)
        noise_a = random.gauss(0, volatility * self.MICRO_NOISE * dt * 60)

        # ── Apply ─────────────────────────────────────────────────────────
        delta_v = max(-self.MAX_DELTA, min(self.MAX_DELTA, drift_v + noise_v))
        delta_a = max(-self.MAX_DELTA, min(self.MAX_DELTA, drift_a + noise_a))

        self.valence = max(-1.0, min(1.0, self.valence + delta_v))
        self.arousal = max(-1.0, min(1.0, self.arousal + delta_a))

        # ── Smooth output (exponential moving average) ────────────────────
        alpha = 0.15
        self._smooth_v = self._smooth_v + alpha * (self.valence - self._smooth_v)
        self._smooth_a = self._smooth_a + alpha * (self.arousal - self._smooth_a)

        # ── Map to mood name ──────────────────────────────────────────────
        self.mood_name   = self._map_mood(self._smooth_v, self._smooth_a)
        self.intensity   = self._calc_intensity()
        self.speech_bias = self._calc_speech_bias(hunger)

        return self.mood_name, self.intensity

    # ── Internal helpers ──────────────────────────────────────────────────

    def _push(self, dv: float, da: float):
        """Instantly push valence/arousal by given amounts."""
        self.valence = max(-1.0, min(1.0, self.valence + dv))
        self.arousal = max(-1.0, min(1.0, self.arousal + da))
        self._last_interact = time.monotonic()

    def _map_mood(self, v: float, a: float) -> str:
        """Find the best matching mood for the given v/a coordinates."""
        best_mood  = "happy"
        best_score = float("inf")

        for name, v_min, v_max, a_min, a_max, w in MOOD_REGIONS:
            # Distance from center of region, weighted
            v_center = (v_min + v_max) / 2
            a_center = (a_min + a_max) / 2
            dist = math.sqrt((v - v_center)**2 + (a - a_center)**2) / w
            if dist < best_score:
                best_score = dist
                best_mood  = name

        return best_mood

    def _calc_intensity(self) -> float:
        """How strongly is the pet feeling this? Distance from neutral (0,0)."""
        return min(1.0, math.sqrt(self._smooth_v**2 + self._smooth_a**2))

    def _calc_speech_bias(self, hunger: float) -> str:
        """Which fallback context should the pet lean toward right now?"""
        if hunger > 80:    return "starving"
        if hunger > 55:    return "hungry"
        now = time.monotonic()
        if now - self._last_fed   < 10: return "fed"
        if now - self._last_trick < 8:  return "trick"
        if now - self._last_pet   < 15: return "idle"
        h = time.localtime().tm_hour
        if h >= 23 or h <= 5:  return "idle_night"
        if 6 <= h <= 8:        return "morning"
        if h >= 22:            return "night"
        return "idle"

    @staticmethod
    def _resolve_personality_key(personality: str, pet_type: str) -> str:
        """Map pet_type + personality to the correct PERSONALITY_BIAS key."""
        if pet_type == "cat":
            mapping = {
                "loyal":   "cat_aloof",
                "hyper":   "cat_curious",
                "playful": "cat_curious",
                "lazy":    "cat_grumpy",
                "curious": "cat_curious",
            }
            return mapping.get(personality, "cat_aloof")
        if pet_type == "dragon":
            mapping = {
                "loyal":   "dragon_proud",
                "hyper":   "dragon_fire",
                "playful": "dragon_proud",
                "lazy":    "dragon_proud",
                "curious": "dragon_proud",
            }
            return mapping.get(personality, "dragon_proud")
        return personality   # dog — use personality directly

    # ── Debug ─────────────────────────────────────────────────────────────

    def debug_str(self) -> str:
        return (f"v={self.valence:+.2f} a={self.arousal:+.2f} "
                f"→ {self.mood_name} ({self.intensity:.2f}) "
                f"[{self.speech_bias}]")