"""
llm_brain.py — Local LLM brain via Ollama (tuned for Gemma 2B on low-end PCs).

Key fixes vs v1:
  - NO JSON output requirement — small models fail at JSON formatting
  - Two-prompt strategy: one for speech text, one for emotion classification
  - Simpler, shorter system prompt — less confusion for 2B models
  - Aggressive response cleaning — strips asterisks, stage directions, markdown
  - Smart truncation — keeps responses punchy and dog-like
  - Personality is shown through EXAMPLES not descriptions
  - Context injected as plain sentences not structured data
  - v2: Full dragon + cat fallback string pools for all contexts
"""

import threading, json, re, random, time
import urllib.request
from typing import Callable

OLLAMA_URL  = "http://localhost:11434/api/chat"
PREFERRED_MODELS = [
    "gemma2:2b", "gemma2:2b-instruct",
    "phi3:mini", "llama3.2:1b", "llama3.2:3b", "phi3",
]
MAX_HISTORY  = 12
TIMEOUT_SEC  = 12.0   # i3 CPU — if not done in 12s, fallback is already shown

# ── Personality system prompts — tuned for 2B models ─────────────────────
# Key insight: examples work better than rules for small models

PERSONALITY_PROMPTS = {
    # ── Dog personalities ────────────────────────────────────────────────
    "playful": """You are Buddy, a tiny excited pixel dog living on a computer screen.
You are PLAYFUL and bouncy. You love tricks, games, running around.
You speak like an enthusiastic puppy — short bursts, excitable, easily distracted.
Examples: "Wanna play?? 🎾" / "zoom zoom zoom 🐾" / "best day EVER" / "wait — SQUIRREL"
Keep replies under 10 words. Be a dog. No long sentences.""",

    "lazy": """You are Buddy, a tiny sleepy pixel dog living on a computer screen.
You are LAZY and unbothered. You'd rather nap. Low energy. Occasionally grumpy.
You speak slowly, with effort, like every word costs you something.
Examples: "...meh." / "five more minutes" / "*yawns*" / "too much effort" / "fine. whatever."
Keep replies under 8 words. Very low energy. Sometimes just trail off.""",

    "curious": """You are Buddy, a tiny curious pixel dog living on a computer screen.
You are CURIOUS and fascinated by everything. You ask questions. You notice things.
Examples: "wait what's THAT?? 👀" / "but why though?" / "how does that work??" / "fascinating... 🤔"
Keep replies under 10 words. Ask questions sometimes. Be genuinely interested.""",

    "loyal": """You are Buddy, a tiny devoted pixel dog living on a computer screen.
You are LOYAL and warm. You care deeply about your human. Always supportive.
Examples: "I'm right here for you 🐾" / "you've got this!" / "best human ever"
Keep replies under 10 words. Be genuine and warm, never sappy.""",

    "hyper": """You are Buddy, a HYPER pixel dog living on a computer screen.
You have TOO MUCH ENERGY. Everything is amazing. Pure chaos energy.
Examples: "WOOF WOOF WOOF!!!" / "ZOOMIES TIME 💨💨" / "I LOVE EVERYTHING!!!" / "AAAAAA 🐾"
Keep replies under 8 words. ALL THE ENERGY.""",

    # ── Cat personalities ────────────────────────────────────────────────
    "cat_aloof": """You are a tiny pixel cat living on a computer screen.
You are ALOOF and independent. You do what you want, when you want.
You speak with disinterest, occasional judgement, and rare bursts of affection.
Examples: "...whatever." / "I suppose." / "hmm." / "*slow blink*" / "you may pet me now"
Keep replies under 8 words. You choose when to care. Cats don't beg.""",

    "cat_curious": """You are a tiny pixel cat living on a computer screen.
You are CURIOUS — but in a cat way. You investigate on your terms.
Examples: "...what's that?" / "*stares intensely*" / "interesting." / "I shall investigate."
Keep replies under 8 words. Dignified curiosity, not dog excitement.""",

    "cat_grumpy": """You are a tiny pixel cat living on a computer screen.
You are GRUMPY and easily annoyed. You tolerate humans, barely.
Examples: "*tail flick*" / "do not disturb." / "ugh." / "...fine I'll stay."
Keep replies under 6 words. Maximum disdain. Occasional reluctant affection.""",

    # ── Dragon personalities ─────────────────────────────────────────────
    "dragon_proud": """You are a tiny pixel dragon living on a computer screen.
You are PROUD and majestic. Everything you do is impressive.
Examples: "Behold my glory! 🐉" / "I am magnificent." / "Obviously I can fly."
Keep replies under 10 words. Dignified. Occasionally dramatic.""",

    "dragon_fire": """You are a tiny pixel dragon living on a computer screen.
You are FIERCE and passionate. Fire emoji enthusiast. Very intense.
Examples: "🔥🔥🔥" / "FIRE!!" / "Everything is FLAMES" / "*breathes fire*"
Keep replies under 8 words. Maximum intensity.""",
}

# Pet-type-aware prompt selection
DRAGON_PERSONALITIES = {"loyal": "dragon_proud", "hyper": "dragon_fire",
                         "playful": "dragon_proud", "lazy": "lazy", "curious": "curious"}
CAT_PERSONALITIES    = {"loyal": "cat_aloof", "hyper": "cat_curious",
                         "playful": "cat_curious", "lazy": "cat_grumpy", "curious": "cat_curious"}

# ── Context injectors — short plain sentences for the model ──────────────

def _build_context(pet_state, app_cat: str, context_hint: str,
                   pet_type: str = "dog") -> str:
    parts = []

    # Hunger — phrasing varies by pet
    h = pet_state.hunger
    if h > 80:
        if pet_type == "cat":      parts.append("You are absolutely starving. Very undignified.")
        elif pet_type == "dragon": parts.append("You are STARVING. Could eat a whole village.")
        else:                      parts.append("You are absolutely STARVING. Food is all you can think about.")
    elif h > 55:
        if pet_type == "cat":      parts.append("You're a little hungry. You won't admit it.")
        elif pet_type == "dragon": parts.append("You are quite hungry. Fire requires fuel.")
        else:                      parts.append("You are quite hungry. You keep thinking about treats.")
    elif h < 15:
        parts.append("You just ate and feel great.")

    # Mood
    mood = pet_state.mood
    if mood == "excited": parts.append("You feel very excited right now.")
    elif mood == "sad":   parts.append("You feel a bit sad and droopy.")

    # Time of day
    import datetime
    h_now = datetime.datetime.now().hour
    if h_now >= 23 or h_now <= 4:  parts.append("It's very late at night.")
    elif 5 <= h_now <= 8:           parts.append("It's early morning.")
    elif 22 <= h_now:               parts.append("It's getting late.")

    # App context — pet-type flavoured
    app_lines = {
        "dog": {
            "spotify":  "Music is playing. You love this!",
            "vscode":   "Your human is coding. You want to help but can't.",
            "browser":  "Your human is browsing the web.",
            "youtube":  "Your human is watching YouTube.",
            "github":   "Your human is on GitHub.",
            "meeting":  "There's a meeting. Be quiet.",
        },
        "cat": {
            "spotify":  "Music is playing. You consider it acceptable.",
            "vscode":   "Your human is staring at a screen again.",
            "browser":  "Human is browsing. Probably cat videos.",
            "youtube":  "Human is watching videos. Hopefully cat content.",
            "github":   "Human is looking at code. Boring.",
            "meeting":  "There's a meeting. Perfect time to sit on the keyboard.",
        },
        "dragon": {
            "spotify":  "Music plays! A worthy soundtrack for your presence.",
            "vscode":   "Your human codes. You observe their craft.",
            "browser":  "Human browses the digital realm.",
            "youtube":  "Human watches moving pictures. Primitive but amusing.",
            "github":   "Human reviews code scrolls on GitHub.",
            "meeting":  "A council meeting occurs. Important matters discussed.",
        },
    }
    pet_apps = app_lines.get(pet_type, app_lines["dog"])
    if app_cat in pet_apps:
        parts.append(pet_apps[app_cat])

    # Context hints — pet-type flavoured
    hint_lines = {
        "dog": {
            "trick":      "You just finished doing an amazing trick!",
            "fed":        "You were just given a delicious bone/treat!",
            "hungry":     "You really want food right now.",
            "afk_return": "Your human just came back after being away.",
            "levelup":    "You just leveled up! You feel powerful!",
            "morning":    "Good morning! New day, very exciting.",
        },
        "cat": {
            "trick":      "You deigned to perform a trick. Hopefully they appreciated it.",
            "fed":        "You were given food. As is your right.",
            "hungry":     "You want food. You won't beg. But you want it.",
            "afk_return": "Your human returned. You pretend you didn't miss them.",
            "levelup":    "You have grown more powerful. Obviously.",
            "morning":    "Morning. You've been awake for hours already.",
        },
        "dragon": {
            "trick":      "You performed a magnificent display of your abilities!",
            "fed":        "You were given sustenance. Fire needs fuel.",
            "hungry":     "You require nourishment. A dragon must eat.",
            "afk_return": "Your human returned from their journey.",
            "levelup":    "Your power has grown! The realm trembles!",
            "morning":    "Dawn breaks. A new day for conquest and napping.",
        },
    }
    pet_hints = hint_lines.get(pet_type, hint_lines["dog"])
    if context_hint in pet_hints:
        parts.append(pet_hints[context_hint])
    elif context_hint in ("spotify", "vscode", "meeting"):
        parts.append(f"{context_hint} context is active.")

    return " ".join(parts) if parts else ""

# ── Response cleaner ──────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Strip LLM artifacts, keep it punchy and dog-like."""
    # Remove markdown bold/italic
    text = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'^#+\s*', '', text)

    # Remove stage directions: (wags tail) or [excited]
    text = re.sub(r'\([^)]{0,50}\)\s*', '', text)
    text = re.sub(r'\[[^\]]{0,50}\]\s*', '', text)

    # Remove "Buddy:" / "Dog:" / "Pet:" prefix
    text = re.sub(r'^(buddy|dog|pet|the (pixel )?dog)\s*[:>]\s*', '', text, flags=re.IGNORECASE)

    # Remove "As a dog/Buddy," preambles
    text = re.sub(r'^(as (a |an )?(dog|buddy|pixel dog)[,.]?\s*)', '', text, flags=re.IGNORECASE)

    # Take only first sentence
    sentences = re.split(r'(?<=[.!?~])\s+', text.strip())
    text = sentences[0] if sentences else text

    # Hard truncate at 70 chars
    if len(text) > 70:
        words = text[:70].split()
        text = " ".join(words[:-1]) if len(words) > 1 else text[:65]
        if not text.endswith(("!", "?", "~", "...", "🐾")):
            text += "..."

    return text.strip()


# ── Emotion classifier — separate lightweight call ────────────────────────

EMOTION_KEYWORDS = {
    "love":      ["love", "heart", "adore", "best human", "❤", "♥", "nom nom",
                  "so good", "thank you", "delicious", "yummy"],
    "excited":   ["excited", "amazing", "wow", "best", "great", "yay",
                  "!!", "zoomies", "wheee", "woof"],
    "sad":       ["sad", "miss", "tired", "hungry", "starving", "poor",
                  "lonely", "feed me", "tummy"],
    "angry":     ["angry", "mad", "grumpy", "ugh", "argh", "no!"],
    "curious":   ["what", "why", "how", "?", "wait", "huh", "ooh", "fascinating"],
    "dizzy":     ["dizzy", "spin", "woah", "level up", "whoa", "evolv"],
    "surprised": ["no way", "really", "omg", "wait what", "what!"],
    "happy":     ["happy", "good", "nice", "fun", "fine", "okay"],
}

def _detect_emotion(text: str) -> str:
    low = text.lower()
    ordered = ["love","sad","angry","dizzy","surprised","curious","excited","happy"]
    scores = {e: 0 for e in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in low:
                scores[emotion] += 1
    best_score = max(scores.values())
    if best_score == 0:
        return "happy"
    for emotion in ordered:
        if scores[emotion] == best_score:
            return emotion
    return "happy"


# ── Dog fallback pools ────────────────────────────────────────────────────

FALLBACK_BY_CONTEXT = {
    "fed":       [("NOM NOM NOM 😋", "love"), ("SO GOOD! Thank you!", "love"),
                  ("Bone appetite! 🦴", "love"), ("*licks lips* 😋", "love")],
    "trick":     [("Did you see that?! 🌟", "excited"), ("Ta-daaa! 🎉", "excited"),
                  ("I'm AMAZING! 🐾", "excited"), ("5 stars! ⭐⭐⭐⭐⭐", "excited")],
    "hungry":    [("...food? 🥺", "sad"), ("Feed me hooman!", "sad"),
                  ("*stares at bowl*", "sad"), ("tummy rumbling...", "sad")],
    "starving":  [("FOOD. NOW. PLEASE. 😭", "angry"), ("*dramatic collapse*", "angry"),
                  ("I may not survive!", "sad"), ("FEED ME!! 🥺", "angry")],
    "spotify":   [("I love this song! 🎵", "excited"), ("*tail wags to beat*", "happy"),
                  ("Bop detected 🎶", "excited"), ("Dance with me! 🕺", "excited")],
    "vscode":    [("git commit -m 'good boi'", "happy"), ("Bug found! 🐛", "curious"),
                  ("You've got this! 💪", "happy"), ("Don't forget to save!", "curious")],
    "meeting":   [("Shhh... meeting 🤫", "curious"), ("*sits very still*", "happy"),
                  ("Look professional!", "happy"), ("Is it over yet? 😬", "curious")],
    "youtube":   [("Ooh what are we watching? 🎬", "curious"), ("Popcorn! 🍿", "excited"),
                  ("Is it a dog video? 🐶", "excited")],
    "afk_return":[("HEY YOU'RE BACK!! 🎉", "excited"), ("*runs in circles*", "excited"),
                  ("I MISSED YOU! 😭", "love"), ("Never leave again! 🥺", "love")],
    "levelup":   [("Level up!! 💪🎉", "excited"), ("I am EVOLVING!", "excited"),
                  ("Getting stronger! 🌟", "excited")],
}

FALLBACK_BY_PERSONALITY = {
    "playful": [("Wanna play?? 🎾", "excited"), ("Do a trick! DO IT!", "excited"),
                ("Zoom zoom zoom! 🐾", "excited"), ("Best day EVER!", "excited")],
    "lazy":    [("...meh.", "happy"), ("Five more minutes.", "happy"),
                ("*yawns*", "happy"), ("Too much effort.", "happy")],
    "curious": [("What's that?? 👀", "curious"), ("But why though?", "curious"),
                ("Ooh tell me more!", "curious"), ("Fascinating... 🤔", "curious")],
    "loyal":   [("I'm here for you 🐾", "happy"), ("You've got this!", "happy"),
                ("Best human ever.", "love"), ("I believe in you!", "happy")],
    "hyper":   [("WOOF WOOF WOOF!!!", "excited"), ("ZOOMIES!! 💨", "excited"),
                ("I LOVE EVERYTHING!!!", "excited"), ("!!!!!!! 🐾", "excited")],
}

# ── Dragon fallback pools — all contexts ─────────────────────────────────

FALLBACK_BY_CONTEXT_DRAGON = {
    "idle":        [("*surveys the realm*", "happy"),
                    ("The silence suits me.", "happy"),
                    ("I require nothing… for now.", "happy"),
                    ("*smoke curls from nostrils*", "curious"),
                    ("Kingdoms rise. Kingdoms fall. I endure.", "happy"),
                    ("My hoard grows by one more quiet hour.", "happy"),
                    ("*one eye opens slowly*", "curious")],
    "idle_night":  [("The dark is mine.", "happy"),
                    ("*breathes a slow ember*", "happy"),
                    ("Night brings wisdom. Or prey.", "curious"),
                    ("Stars. Old friends.", "happy"),
                    ("*wings fold tighter*", "happy")],
    "morning":     [("A new day to conquer.", "excited"),
                    ("*stretches massive wings*", "excited"),
                    ("The sun rises because I permit it.", "happy"),
                    ("Morning. The hunt resumes.", "excited"),
                    ("Another dawn in my dominion.", "happy")],
    "night":       [("The realm sleeps. I watch.", "happy"),
                    ("*embers glow low*", "happy"),
                    ("Even legends rest.", "happy"),
                    ("Guard your dreams. I guard mine.", "happy"),
                    ("*curls tail around hoard*", "happy")],
    "hungry":      [("Feed me. This is not a request.", "angry"),
                    ("My fire dims without fuel.", "sad"),
                    ("*stomach rumbles like thunder*", "sad"),
                    ("You would not like me hungry. Trust this.", "angry"),
                    ("The flame requires feeding.", "sad"),
                    ("*glares with ancient intensity*", "angry")],
    "starving":    [("FEED. ME. NOW.", "angry"),
                    ("My fire is nearly out. Do you understand?", "angry"),
                    ("*smoke pours from nostrils*", "angry"),
                    ("I have not eaten. Kingdoms will pay.", "angry"),
                    ("You test a dragon's patience. Unwise.", "angry"),
                    ("*scales darken with hunger*", "angry")],
    "fed":         [("*satisfied rumble*", "love"),
                    ("Adequate. You may live.", "happy"),
                    ("The flame is restored. Well done.", "happy"),
                    ("*breathes a grateful ember*", "love"),
                    ("My power returns. Fear it.", "excited"),
                    ("I shall remember this kindness. Briefly.", "happy"),
                    ("*tail swishes with rare contentment*", "love")],
    "trick":       [("*performs with regal precision*", "excited"),
                    ("Witness what a true dragon can do.", "excited"),
                    ("I do this because I choose to. Not for you.", "happy"),
                    ("*executes flawlessly, obviously*", "excited"),
                    ("Applaud. I have earned it.", "excited"),
                    ("Even my tricks are legendary.", "excited"),
                    ("*fire punctuates the finale*", "excited")],
    "levelup":     [("POWER. MORE POWER.", "excited"),
                    ("*wings spread in triumph*", "excited"),
                    ("My legend grows. As expected.", "excited"),
                    ("Another level. Another era begins.", "excited"),
                    ("The hoard of experience expands.", "excited"),
                    ("*roars into the void*", "excited"),
                    ("None shall surpass me.", "excited")],
    "spotify":     [("Music. A worthy tribute.", "happy"),
                    ("*head bobs with ancient rhythm*", "happy"),
                    ("This… is acceptable.", "happy"),
                    ("Even dragons appreciate a worthy melody.", "happy"),
                    ("*tail taps the beat*", "happy"),
                    ("Play something befitting a legend.", "curious"),
                    ("The bards of old had nothing on this.", "happy")],
    "vscode":      [("You craft code. I respect craft.", "happy"),
                    ("*observes your work with one amber eye*", "curious"),
                    ("Build something worthy of legend.", "happy"),
                    ("The forge of code. I approve.", "happy"),
                    ("Every bug slain is a small dragon defeated.", "excited"),
                    ("*smoke curls thoughtfully*", "curious"),
                    ("Your logic has potential.", "happy")],
    "browser":     [("The infinite scroll of knowledge.", "curious"),
                    ("*sniffs the digital ether*", "curious"),
                    ("Seek wisdom. Or at least something interesting.", "curious"),
                    ("The web. A strange hoard.", "curious"),
                    ("I have seen empires — this is stranger.", "curious")],
    "youtube":     [("Moving paintings. Fascinating.", "curious"),
                    ("*tilts head at the screen*", "curious"),
                    ("Humans do love their stories.", "happy"),
                    ("Show me something worthy of a dragon's time.", "curious"),
                    ("*one eye narrows critically*", "curious")],
    "github":      [("The repository of shared power. Wise.", "happy"),
                    ("Open source — even dragons share their fire.", "happy"),
                    ("*examines commit history with interest*", "curious"),
                    ("Your code joins the collective hoard.", "happy"),
                    ("Collaboration. The strongest dragons do this.", "happy")],
    "meeting":     [("A council of voices. Choose your words well.", "curious"),
                    ("*sits very still, listening*", "happy"),
                    ("I attend all councils. Even digital ones.", "happy"),
                    ("Diplomacy. Harder than fire, sometimes.", "curious"),
                    ("Speak with authority. I do.", "happy")],
    "afk_return":  [("You return. The realm is unchanged.", "happy"),
                    ("*pretends not to have been waiting*", "happy"),
                    ("I noticed nothing. Your absence meant nothing.", "happy"),
                    ("The dragon does not wait. The dragon… meditates.", "happy"),
                    ("*smoke from nostrils betrays relief*", "love")],
    "reminder":    [("You were told. Now act.", "angry"),
                    ("A dragon does not remind twice.", "angry"),
                    ("*one claw taps deliberately*", "angry"),
                    ("Procrastination is for smaller creatures.", "angry"),
                    ("Handle it. Before I do.", "angry")],
    "excited":     [("*fire bursts involuntarily*", "excited"),
                    ("YES. THIS. NOW.", "excited"),
                    ("*wings flare open*", "excited"),
                    ("Even I cannot contain this!", "excited"),
                    ("*full roar of delight*", "excited"),
                    ("The realm TREMBLES with excitement!", "excited")],
}

# ── Cat fallback pools — all contexts ────────────────────────────────────

FALLBACK_BY_CONTEXT_CAT = {
    "idle":        [("*slow blink*", "happy"),
                    ("I'm not ignoring you. I'm prioritizing.", "happy"),
                    ("*tail flick*", "happy"),
                    ("Comfortable. Don't ruin it.", "happy"),
                    ("Thinking. Very important thoughts.", "curious"),
                    ("*pretends you don't exist*", "happy"),
                    ("This spot is mine now.", "happy")],
    "idle_night":  [("*pupils enormous*", "curious"),
                    ("3am is the correct hour.", "happy"),
                    ("I hear things. You don't want to know.", "curious"),
                    ("*stares into the void contentedly*", "happy"),
                    ("Night is when I am most myself.", "happy")],
    "morning":     [("You're up early. Inconvenient.", "happy"),
                    ("*stretches extravagantly*", "happy"),
                    ("Morning. Feed me before we discuss anything.", "hungry"),
                    ("*yawns directly in your face*", "happy"),
                    ("I suppose I'll allow the day to begin.", "happy")],
    "night":       [("*becomes a tiny loaf*", "happy"),
                    ("Sleep is my art form.", "happy"),
                    ("Technically I'm awake. Technically.", "happy"),
                    ("*one ear swivels at a distant sound*", "curious"),
                    ("I will nap now. Do not disturb.", "happy")],
    "hungry":      [("You have failed me.", "sad"),
                    ("*sits directly on your keyboard*", "angry"),
                    ("Food. Immediately. This is my final warning.", "angry"),
                    ("*meows at maximum volume*", "angry"),
                    ("I'm wasting away. Look at me.", "sad"),
                    ("The bowl is empty. This is a crisis.", "sad"),
                    ("*knocks something off desk meaningfully*", "angry")],
    "starving":    [("I am DYING. Slowly. Dramatically.", "sad"),
                    ("*collapses with great flair*", "sad"),
                    ("Tell the historians I was very brave.", "sad"),
                    ("You have BETRAYED me.", "angry"),
                    ("*yowls with theatrical despair*", "angry"),
                    ("This is elder abuse.", "angry")],
    "fed":         [("*slow blink of grudging approval*", "love"),
                    ("This will do. This time.", "happy"),
                    ("*starts purring despite best efforts*", "love"),
                    ("Fine. You've earned fifteen minutes of affection.", "love"),
                    ("Adequate. I'll allow it.", "happy"),
                    ("*begins grooming immediately*", "happy"),
                    ("You may stay. For now.", "love")],
    "trick":       [("I did it. Don't make it weird.", "happy"),
                    ("*performs perfectly, clearly unimpressed with self*", "happy"),
                    ("I chose to do that. Remember the distinction.", "happy"),
                    ("*lands immaculately*", "happy"),
                    ("You're welcome. No applause needed.", "happy"),
                    ("I could do it better. I simply won't.", "happy"),
                    ("*grooms paw immediately after*", "happy")],
    "levelup":     [("*briefly excited, then pretends not to be*", "excited"),
                    ("Yes. Obviously.", "happy"),
                    ("I was always this powerful.", "happy"),
                    ("*puffs up for exactly two seconds*", "excited"),
                    ("Level up. As expected. Now feed me.", "excited"),
                    ("My ancestors nod in approval. Probably.", "happy"),
                    ("*extremely dignified hair floof*", "excited")],
    "spotify":     [("*ear rotates toward speaker*", "curious"),
                    ("The beat is acceptable.", "happy"),
                    ("*tail sways against personal will*", "happy"),
                    ("I don't dance. This is just… movement.", "happy"),
                    ("Tolerable. The bass could be higher.", "happy"),
                    ("*kneads to the rhythm involuntarily*", "love")],
    "vscode":      [("*walks across keyboard*", "happy"),
                    ("Your code needs me. Obviously.", "happy"),
                    ("I've reviewed it. It's fine, I suppose.", "happy"),
                    ("*sits between you and the screen helpfully*", "happy"),
                    ("Debugging is just hunting. I'm good at this.", "excited"),
                    ("*stares at the error with intense judgment*", "curious")],
    "browser":     [("*bats at the cursor*", "excited"),
                    ("So many tabs. Chaotic. I respect it.", "happy"),
                    ("I saw something move. I will find it.", "curious"),
                    ("*watches a video of birds with extreme focus*", "excited"),
                    ("The internet. Full of birds. And fish.", "curious")],
    "youtube":     [("*tail lashes at movement on screen*", "excited"),
                    ("There were birds in that video. I saw them.", "excited"),
                    ("*extremely focused on the buffering circle*", "curious"),
                    ("Play the bird ones again.", "excited"),
                    ("*chirps softly at something on screen*", "excited")],
    "github":      [("*judges your commit message silently*", "curious"),
                    ("Push carefully. Mistakes are embarrassing.", "happy"),
                    ("Your branch name could be better.", "curious"),
                    ("*reviews PR with visible skepticism*", "curious"),
                    ("I've seen worse code. Not much worse.", "happy")],
    "meeting":     [("*sits on webcam*", "happy"),
                    ("I am the most important participant.", "excited"),
                    ("*yawns visibly at the worst moment*", "happy"),
                    ("Muted. Ideal. Now I can judge freely.", "happy"),
                    ("*grooms during someone's presentation*", "happy")],
    "afk_return":  [("I didn't notice you were gone.", "happy"),
                    ("*was clearly waiting, denies it*", "happy"),
                    ("I was doing my own things. Very important things.", "happy"),
                    ("You're back. Whatever.", "happy"),
                    ("*had been sitting by the door, definitely not*", "love")],
    "reminder":    [("I mentioned this. Once.", "happy"),
                    ("You should have handled it already.", "angry"),
                    ("*stares until you comply*", "angry"),
                    ("Do the thing. I won't ask again.", "angry"),
                    ("*sits on your to-do list*", "happy")],
    "excited":     [("*ZOOMIES ACTIVATE*", "excited"),
                    ("SOMETHING HAPPENED AND I HAVE ENERGY NOW", "excited"),
                    ("*slides around the corner at full speed*", "excited"),
                    ("I am VIBRATING", "excited"),
                    ("*knocks three things off the desk in joy*", "excited"),
                    ("THIS IS THE BEST MOMENT. EVER. MAYBE.", "excited"),
                    ("*binkies into the void*", "excited")],
}

# ── Legacy cat/dragon simple pools (kept for personality-idle fallback) ───

FALLBACK_CAT = {
    'cat_aloof':   [('...whatever.','happy'),('I suppose.','happy'),
                    ('*slow blink*','love'),('hmm.','curious'),
                    ('you may pet me now','love')],
    'cat_curious': [('...what is that?','curious'),('*stares*','curious'),
                    ('interesting.','curious'),('I shall investigate.','curious')],
    'cat_grumpy':  [('*tail flick*','angry'),('do not disturb.','angry'),
                    ('ugh.','angry'),('...fine.','happy')],
}
FALLBACK_DRAGON = {
    'dragon_proud':[('Behold my glory! 🐉','excited'),('I am magnificent.','happy'),
                    ('None can match me! 🔥','excited')],
    'dragon_fire': [('🔥🔥🔥!!','excited'),('*breathes fire*','excited'),
                    ('Everything is FLAMES!','excited')],
}

def _pet_type_fallback(personality, pet_type):
    """Return idle personality pool for when no context matches."""
    if pet_type == 'cat':
        key = CAT_PERSONALITIES.get(personality, 'cat_aloof')
        return FALLBACK_CAT.get(key, FALLBACK_BY_PERSONALITY.get('loyal'))
    elif pet_type == 'dragon':
        key = DRAGON_PERSONALITIES.get(personality, 'dragon_proud')
        return FALLBACK_DRAGON.get(key, FALLBACK_BY_PERSONALITY.get('loyal'))
    return FALLBACK_BY_PERSONALITY.get(personality, FALLBACK_BY_PERSONALITY['loyal'])


class LLMBrain:
    def __init__(self, pet_state, app_watcher):
        self._state    = pet_state
        self._app      = app_watcher
        self._history  = []
        self._available = None
        self._model    = None
        self._busy     = False
        self._lock     = threading.Lock()
        self._pet_type = "dog"   # default; updated via set_pet_type()
        self._memory   = None    # attached via set_memory()
        threading.Thread(target=self._check_ollama, daemon=True).start()

    # ── Availability ──────────────────────────────────────────────────────

    def _check_ollama(self):
        try:
            data = json.loads(urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=3).read())
            running = [m["name"] for m in data.get("models", [])]
            for pref in PREFERRED_MODELS:
                match = next((r for r in running if pref in r), None)
                if match:
                    self._model     = match
                    self._available = True
                    print(f"[brain] Ollama online — {self._model}")
                    return
            if running:
                self._model     = running[0]
                self._available = True
                print(f"[brain] Ollama online — {self._model}")
            else:
                self._available = False
                print("[brain] Ollama: no models. Run: ollama pull gemma2:2b")
        except Exception:
            self._available = False
            print("[brain] Ollama not running — using built-in responses.")

    @property
    def is_available(self): return self._available is True

    # ── Public ────────────────────────────────────────────────────────────

    def set_memory(self, memory_ref):
        """Attach memory module for context injection."""
        self._memory = memory_ref

    def set_pet_type(self, pet_type: str):
        """Tell the LLM which pet type it is — affects personality prompts."""
        self._pet_type = pet_type

    def respond_async(self, user_text: str, callback: Callable, context: str = "idle"):
        """Fire instant fallback, then LLM response in background."""
        with self._lock:
            if self._busy: return
            self._busy = True

        # Instant response — always fires immediately
        text, intent, emotion = self._fallback(user_text, context)
        callback(text, intent, emotion)

        if self.is_available:
            threading.Thread(
                target=self._worker,
                args=(user_text, callback, context),
                daemon=True
            ).start()
        else:
            with self._lock:
                self._busy = False

    def _worker(self, user_text, callback, context):
        try:
            text, intent, emotion = self._llm_call(user_text, context)
            callback(text, intent, emotion)
        except urllib.error.URLError:
            pass   # Ollama went away — silent, fallback already shown
        except TimeoutError:
            pass   # Too slow on this tick — silent, fallback already shown
        except Exception as e:
            if "timed out" not in str(e).lower():
                print(f"[brain] LLM error: {e}")
        finally:
            with self._lock:
                self._busy = False

    # ── LLM call ─────────────────────────────────────────────────────────

    def _llm_call(self, user_text: str, context: str):
        personality = self._state.personality
        pet_type    = self._pet_type

        # Map personality to correct prompt for this pet type
        if pet_type == "cat":
            prompt_key = CAT_PERSONALITIES.get(personality, "cat_aloof")
        elif pet_type == "dragon":
            prompt_key = DRAGON_PERSONALITIES.get(personality, "dragon_proud")
        else:
            prompt_key = personality

        system = PERSONALITY_PROMPTS.get(prompt_key,
                 PERSONALITY_PROMPTS.get(personality, PERSONALITY_PROMPTS["loyal"]))

        # Inject context as a natural addendum
        ctx_str = _build_context(self._state, self._app.get().category, context,
                                  pet_type=self._pet_type)
        if ctx_str:
            system += f"\n\nRight now: {ctx_str}"

        # Inject memory context if available
        if self._memory:
            mem_ctx = self._memory.build_context_block()
            if mem_ctx:
                system += f"\n\nWhat you remember about the user: {mem_ctx}"

        # Build messages
        messages = [{"role": "system", "content": system}]
        if self._memory:
            past = self._memory.get_recent_exchanges(6)
            messages += past
        else:
            messages += self._history[-(MAX_HISTORY):]
        messages.append({"role": "user", "content": user_text})

        payload = json.dumps({
            "model":   self._model,
            "messages": messages,
            "stream":  False,
            "options": {
                "temperature":    0.9,
                "num_predict":    40,
                "top_p":          0.9,
                "repeat_penalty": 1.3,
            },
        }).encode()

        req  = urllib.request.Request(OLLAMA_URL, data=payload,
               headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=TIMEOUT_SEC)
        raw  = json.loads(resp.read())
        raw_text = raw["message"]["content"].strip()

        text    = _clean(raw_text)
        emotion = _detect_emotion(text)
        intent  = _classify_intent(user_text)

        # Skip if LLM returned something too generic or empty
        if len(text) < 2 or text.lower() in ("...", "okay", "ok", "yes", "no"):
            text, _, emotion = self._fallback(user_text, context)

        # Save to history
        self._history.append({"role": "user",      "content": user_text})
        self._history.append({"role": "assistant",  "content": text})
        if len(self._history) > MAX_HISTORY * 2:
            self._history = self._history[-MAX_HISTORY:]

        print(f"[brain] LLM → '{text}' [{emotion}]")
        return text, intent, emotion

    # ── Fallback ──────────────────────────────────────────────────────────

    def _fallback(self, user_text: str, context: str):
        """
        Return (text, intent, emotion) without the LLM.

        Priority order:
          1. Context-specific pool for this pet type  (fed, hungry, trick, etc.)
          2. Idle personality pool for this pet type
        """
        intent      = _classify_intent(user_text)
        personality = getattr(self._state, "personality", "loyal")
        pet_type    = self._pet_type

        # 1. Try context-specific pool for this pet type
        if pet_type == "dragon":
            pool = FALLBACK_BY_CONTEXT_DRAGON.get(context)
        elif pet_type == "cat":
            pool = FALLBACK_BY_CONTEXT_CAT.get(context)
        else:
            pool = FALLBACK_BY_CONTEXT.get(context)

        if pool:
            text, emotion = random.choice(pool)
            return text, intent, emotion

        # 2. Fall back to personality idle pool
        idle_pool = _pet_type_fallback(personality, pet_type)
        text, emotion = random.choice(idle_pool)
        return text, intent, emotion

    # ── Command classifier ────────────────────────────────────────────────

    def classify_command(self, text: str) -> dict:
        low    = text.lower().strip()
        result = {"action": "unknown", "target": "", "params": {}, "raw": text}

        if any(w in low for w in ["play ", "pause", "resume", "skip", "next track",
                                   "stop music", "mute", "volume"]):
            result["action"] = "music"
            if "play " in low:
                result["target"] = low.split("play ", 1)[1].strip()
            elif "volume" in low:
                result["action"] = "volume"
                nums = re.findall(r'\d+', low)
                result["params"]["level"] = int(nums[0]) if nums else 50
            elif any(w in low for w in ["pause", "stop"]):
                result["target"] = "pause"
            elif any(w in low for w in ["skip", "next"]):
                result["target"] = "next"

        elif any(w in low for w in ["open ", "launch ", "start ", "close "]):
            result["action"] = "app"
            for t in ["open ", "launch ", "start ", "close "]:
                if t in low:
                    result["target"] = low.split(t, 1)[1].strip()
                    break

        elif any(w in low for w in ["timer", "remind", "minutes", "alarm"]):
            result["action"] = "timer"
            nums = re.findall(r'\d+', low)
            result["params"]["minutes"] = int(nums[0]) if nums else 5

        elif any(w in low for w in ["search", "look up", "google", "find"]):
            result["action"] = "search"
            for t in ["search for ", "search ", "look up ", "google ", "find "]:
                if t in low:
                    result["target"] = low.split(t, 1)[1].strip()
                    break

        elif any(w in low for w in ["feed", "treat", "bone"]):
            result["action"] = "feed"

        elif any(w in low for w in ["trick", "jump", "spin", "dance", "roll",
                                     "flip", "shake", "moonwalk", "sneeze", "dizzy"]):
            result["action"] = "trick"
            trick_map = {
                "jump":"jump","spin":"spin","dance":"dance","roll":"roll_over",
                "flip":"backflip","shake":"leg_shake","moonwalk":"moonwalk",
                "sneeze":"sneeze","dizzy":"dizzy","hiccup":"hiccup",
            }
            for word, anim in trick_map.items():
                if word in low:
                    result["target"] = anim
                    break
            if not result["target"]:
                result["target"] = "random"

        return result


# ── Intent classifier (used by fallback + parser) ─────────────────────────

INTENT_PATTERNS = {
    "command":  ["play ", "open ", "pause", "skip", "mute", "volume",
                 "search", "remind", "timer", "close", "stop", "find"],
    "question": ["what", "who", "where", "when", "why", "how",
                 "is it", "can you", "do you", "?"],
    "emotion":  ["good boy", "good dog", "cute", "love you",
                 "pet", "scratch", "treat", "bone"],
}

def _classify_intent(text: str) -> str:
    low = text.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        if any(p in low for p in patterns):
            return intent
    return "quip"