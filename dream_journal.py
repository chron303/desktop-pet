"""
dream_journal.py — Dream Journal for Desktop Pet.

When the pet has been asleep (AFK) for DREAM_THRESHOLD_MIN minutes,
the LLM quietly generates a short dream in the background based on
the user's actual memory facts.

On wake, the speech bubble shows a dream fragment.
All dreams saved to dreams.json and browsable in Memory Dashboard.

Dream personality per pet type:
  Dog    — food, you, running, squirrels, bones, playing
  Dragon — conquest, hoards, kingdoms, fire, ancient power
  Cat    — birds, sunbeams, keyboards, judging humans, boxes
"""

import json, os, sys, time, random, threading, datetime
import urllib.request

# ── Path helper (works in both source + frozen exe) ───────────────────────
def _data_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "dreams.json")

OLLAMA_URL       = "http://localhost:11434/api/chat"
DREAM_THRESHOLD_MIN = 10      # minutes asleep before dream generates
MAX_DREAMS       = 50         # keep last 50 dreams
DREAM_SHOW_MS    = 6000       # show dream bubble for 6 seconds (longer than normal)

# ── Per-pet dream system prompts ──────────────────────────────────────────
DREAM_PROMPTS = {
    "dog": """You are a pixel dog who just woke up from a nap.
Describe ONE short dream you just had in 1-2 sentences.
The dream should feel personal — use any facts given about the user.
Be warm, funny, and dog-like. Include something about food, the user, or playing.
Examples:
- "I dreamed you gave me infinite bones and we ran on a beach forever 🦴"
- "Dreamed I finally caught that squirrel... but it was actually a treat 🐿️"
- "I dreamed about code... and bones... mostly bones."
Keep it under 20 words. Be charming.""",

    "dragon": """You are a pixel dragon who just woke from slumber.
Describe ONE short dream you just had in 1-2 sentences.
The dream should feel ancient and dramatic — use any facts given about the user.
Be proud, majestic, occasionally self-important.
Examples:
- "I dreamed I conquered seventeen kingdoms. You were there. You were adequate."
- "I dreamed my hoard doubled. Then I woke here. Disappointing."  
- "The realm trembled in my dream. As it should."
Keep it under 20 words. Be dramatic.""",

    "cat": """You are a pixel cat who just woke from a nap (one of many today).
Describe ONE short dream you just had in 1-2 sentences.
The dream should feel aloof and cat-like — use any facts given about the user.
Be judgemental, slightly mysterious, occasionally warm by accident.
Examples:
- "I dreamed about birds. Many birds. You were not in it. That was fine."
- "Dreamed I sat in a sunbeam for seventeen hours. Best dream. 10/10."
- "I dreamed your keyboard was mine. It was, actually, a good dream."
Keep it under 20 words. Be a cat about it.""",
}

# ── Offline fallback dreams (when Ollama not available) ───────────────────
FALLBACK_DREAMS = {
    "dog": [
        "I dreamed you gave me ALL the bones 🦴 infinite bones",
        "Dreamed we ran on a beach forever and you didn't leave once 🐾",
        "I dreamed about treats... so many treats... *wags tail*",
        "Dreamed I finally caught that squirrel. It tasted like bacon.",
        "I dreamed you petted me for six hours straight. Perfect dream.",
        "Dreamed about you and me and a really big stick 🌟",
        "I dreamed I was a good boy. I was THE good boy.",
        "Dreamed the food bowl was always full... *wistful sigh*",
        "I dreamed we went for a walk that never ended 🐶",
        "Dreamed about code... and bones... mostly bones.",
    ],
    "dragon": [
        "I dreamed I conquered seventeen kingdoms. You were there. Adequate.",
        "Dreamed my hoard doubled. Then I woke here. Disappointing.",
        "I dreamed the realm trembled at my name. As it should.",
        "Dreamed of ancient fire and great power. Standard Tuesday.",
        "I dreamed I was even more magnificent than usual. Accurate.",
        "Dreamed I breathed fire so magnificently they wrote songs about it.",
        "I dreamed of mountains of gold. I owned all of them. Obviously.",
        "Dreamed the stars bowed. A good dream. A true dream.",
        "I dreamed of conquest. And also a nap. Both were glorious.",
        "Dreamed I was the last dragon. I was also the best dragon.",
    ],
    "cat": [
        "I dreamed about birds. Many birds. You were not in it. Fine.",
        "Dreamed I sat in a sunbeam for seventeen hours. 10/10.",
        "I dreamed your keyboard was entirely mine. It was correct.",
        "Dreamed I knocked everything off every surface. Very satisfying.",
        "I dreamed you finally understood that I am in charge. Progress.",
        "Dreamed about a very large cardboard box. Perfect dream.",
        "I dreamed of birds again. Always the birds.",
        "Dreamed I judged seventeen humans and found them all wanting.",
        "I dreamed the whole house was warm and quiet. It was enough.",
        "Dreamed you fed me on time for once. Wild concept.",
    ],
}


class DreamJournal:
    def __init__(self, memory_ref, ollama_available: bool = False):
        self._memory          = memory_ref
        self._ollama_available = ollama_available
        self._ollama_model    = None
        self._path            = _data_path()
        self._dreams          = self._load()
        self._generating      = False
        self._pending_dream   = None   # dream text ready to show on wake
        self._sleep_start     = 0.0   # when pet fell asleep
        self._dream_shown     = False  # whether this sleep's dream was shown

    # ── Persistence ───────────────────────────────────────────────────────

    def _load(self) -> list:
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._dreams[-MAX_DREAMS:], f, indent=2)
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────

    def set_ollama(self, available: bool, model: str = None):
        self._ollama_available = available
        self._ollama_model     = model

    def on_sleep(self):
        """Call when pet falls asleep (AFK detected)."""
        self._sleep_start  = time.monotonic()
        self._dream_shown  = False
        self._pending_dream = None

    def on_wake(self) -> str | None:
        """
        Call when pet wakes up.
        Returns dream text to show in speech bubble, or None.
        """
        if self._dream_shown:
            return None

        dream = self._pending_dream
        self._pending_dream = None
        self._dream_shown   = True
        return dream

    def tick(self, pet_type: str, is_sleeping: bool):
        """
        Call every few seconds from main loop.
        Triggers dream generation after threshold.
        """
        if not is_sleeping:
            return

        if self._dream_shown or self._generating or self._pending_dream:
            return

        # Check if slept long enough
        sleep_minutes = (time.monotonic() - self._sleep_start) / 60
        if sleep_minutes < DREAM_THRESHOLD_MIN:
            return

        # Generate dream in background
        self._generating = True
        threading.Thread(
            target=self._generate,
            args=(pet_type,),
            daemon=True
        ).start()

    # ── Dream generation ──────────────────────────────────────────────────

    def _generate(self, pet_type: str):
        try:
            if self._ollama_available and self._ollama_model:
                dream = self._generate_llm(pet_type)
            else:
                dream = self._generate_fallback(pet_type)

            if dream:
                # Save to journal
                self._dreams.append({
                    "text":     dream,
                    "pet_type": pet_type,
                    "ts":       time.time(),
                    "date":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                self.save()
                self._pending_dream = f"💤 {dream}"
                print(f"[dream] Generated: {dream}")
        except Exception as e:
            print(f"[dream] Generation failed: {e}")
            self._pending_dream = f"💤 {self._generate_fallback(pet_type)}"
        finally:
            self._generating = False

    def _generate_llm(self, pet_type: str) -> str:
        """Generate dream via Ollama LLM."""
        system = DREAM_PROMPTS.get(pet_type, DREAM_PROMPTS["dog"])

        # Build context from memory
        mem_ctx = self._memory.build_context_block()
        facts   = self._memory._data.get("facts", {})

        context_parts = []
        if facts.get("user_name"):
            context_parts.append(f"The user's name is {facts['user_name']}.")
        if facts.get("job"):
            context_parts.append(f"They are a {facts['job']}.")
        if facts.get("likes"):
            context_parts.append(f"They like {facts['likes']}.")

        top_apps = self._memory.top_apps(2)
        if top_apps:
            context_parts.append(f"They mostly use {', '.join(top_apps)}.")

        nights = self._memory._data.get("late_nights", 0)
        if nights > 3:
            context_parts.append(f"They often work late at night.")

        if context_parts:
            system += f"\n\nFacts about the user to weave into the dream: {' '.join(context_parts)}"

        payload = json.dumps({
            "model":   self._ollama_model,
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": "What did you just dream about?"},
            ],
            "stream":  False,
            "options": {
                "temperature":  1.1,    # higher temp = more creative dreams
                "num_predict":  50,
                "top_p":        0.95,
            },
        }).encode()

        req  = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=15)
        raw  = json.loads(resp.read())
        text = raw["message"]["content"].strip()

        # Clean up
        import re
        text = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', text)  # remove markdown
        text = re.sub(r'^(I dreamed?|Dream:|Pet:)\s*', '', text, flags=re.IGNORECASE)

        # Truncate if too long
        if len(text) > 100:
            sentences = text.split(".")
            text = sentences[0].strip() + ("." if not sentences[0].endswith(".") else "")

        return text if len(text) > 10 else self._generate_fallback(pet_type)

    def _generate_fallback(self, pet_type: str) -> str:
        """Return a random pre-written dream."""
        pool = FALLBACK_DREAMS.get(pet_type, FALLBACK_DREAMS["dog"])

        # Try to personalise with user name if available
        facts     = self._memory._data.get("facts", {})
        user_name = facts.get("user_name", "")

        dream = random.choice(pool)

        # Occasionally inject user name for personal touch
        if user_name and random.random() < 0.3:
            personal = [
                f"I dreamed about you, {user_name}. It was nice 🐾",
                f"Dreamed {user_name} gave me infinite treats. Best dream.",
                f"I dreamed {user_name} never left. Ever. Perfect.",
            ] if pet_type == "dog" else [
                f"I dreamed {user_name} finally acknowledged my greatness.",
                f"Dreamed {user_name} brought tribute. As is correct.",
            ] if pet_type == "dragon" else [
                f"I dreamed {user_name} was adequately attentive. For once.",
                f"Dreamed {user_name} gave me the good treats. Acceptable.",
            ]
            dream = random.choice(personal)

        return dream

    # ── Stats + browsing ──────────────────────────────────────────────────

    def all_dreams(self) -> list:
        """Return all dreams sorted newest first."""
        return sorted(self._dreams, key=lambda d: d.get("ts", 0), reverse=True)

    def recent_dreams(self, n: int = 5) -> list:
        return self.all_dreams()[:n]

    def total_dreams(self) -> int:
        return len(self._dreams)

    def dreams_by_pet(self, pet_type: str) -> list:
        return [d for d in self.all_dreams() if d.get("pet_type") == pet_type]

    def clear(self):
        self._dreams = []
        self.save()