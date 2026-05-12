<div align="center">

# 🐾 Desktop Pet

**A living AI companion that lives on your Windows desktop.**  
Learns who you are. Reacts to your work. Grows with you.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![GitHub Stars](https://img.shields.io/github/stars/chron303/desktop-pet?style=social)](https://github.com/chron303/desktop-pet)

[**Download v1.0**](https://github.com/chron303/desktop-pet/releases/latest) • [Report Bug](https://github.com/chron303/desktop-pet/issues) • [Request Feature](https://github.com/chron303/desktop-pet/issues)

</div>

---

## What is Desktop Pet?

Desktop Pet is a pixel-art companion that lives in the corner of your screen. It's not a screensaver or a widget — it's something closer to a real pet. It notices what apps you're using, reacts to your music, remembers facts you tell it, gets hungry, levels up, and develops a personality over time.

It runs locally. Your data stays on your machine. No accounts, no cloud, no subscriptions.

---

## Features

### 🐶 🐉 🐱 Three Pets, 24-30 Animations Each
Switch between a Dog, Dragon, or Cat at any time. Each has its own animations, personality system, voice, and fallback responses. The dragon is proud and majestic. The cat is delightfully aloof. The dog just wants to play.

### 🧠 Local AI Brain
Powered by [Ollama](https://ollama.ai) running locally on your PC. No API keys, no internet required. Uses `gemma2:2b` by default — fast enough for an i3 processor. The pet responds to voice commands and typed messages in character, with personality-appropriate replies.

### 💭 Continuous Emotion Engine
The pet's mood isn't a string that gets set and forgotten. It's a live 2D state (valence + arousal) that drifts continuously based on hunger, time of day, music, app context, and how long since you last interacted. Feed it and watch the mood spike. Leave it alone for an hour and it gets bored. Open Spotify and its energy lifts.

### 🎤 Voice Commands
Wake word detection ("hey buddy") + natural language commands:
- `"play lofi"` — controls Spotify
- `"open chrome"` — launches apps
- `"do a backflip"` — triggers trick animations
- `"my name is Alex"` — the pet learns and remembers

### 📖 Memory System
The pet learns facts about you across sessions. Tell it your name, job, or what you like — it remembers and injects this context into every LLM response. After a week, it knows your schedule, top apps, peak hours, and how many late nights you've pulled.

### 🏆 Achievement System
40+ achievements across 7 categories: Caretaker, Performer, Devoted, Bonded, Explorer, Legend, and Secret. Bronze through Legend tier. The pet notifies you when you unlock one. Trophy wall in Settings shows your full progress.

### 📊 HUD Overlay
Compact 130×42px pill above the pet showing mood emoji, pet type emoji, level, hunger bar (color-coded), XP bar, and streak fire. Auto-hides when nothing urgent. Force-shows after feeding or leveling up.

### 🎵 Spotify Integration
The pet reacts to music. Dance animations when a banger drops. Notifies you when tracks change. Reacts with personality — the dragon nods approvingly, the cat's tail sways against its will.

### 🌤️ Weather Awareness
Detects your local weather and reacts. The pet comments on rain, heat, and fog in character. In Delhi at 37°C, the dragon approves of the heat.

### 🌙 Day/Night Awareness
Night tint after 9pm. Different idle animations. Sleepier responses. The pet knows when it's 3am and that you probably shouldn't be awake.

### 🎩 Accessories + Level System
Feed and interact to earn XP. Level up unlocks accessories — hats, glasses, crowns. Accessories are drawn directly onto sprites using Pillow. All level-gated, all unlockable through normal play.

---

## Installation

### Option 1 — Download the .exe (Recommended)

1. Download `DesktopPet.exe` from [Releases](https://github.com/chron303/desktop-pet/releases/latest)
2. Put it anywhere you like
3. Double-click to run
4. Right-click the pet for options

No installer. No admin rights needed. No Python required.

### Option 2 — Run from source

**Requirements:** Python 3.10+, Windows 10/11

```bash
git clone https://github.com/chron303/desktop-pet.git
cd desktop-pet
pip install -r requirements.txt
python main.py
```

**requirements.txt:**
```
pillow
pystray
SpeechRecognition
pyaudio
pywin32
winotify
requests
```

### Option 3 — With Ollama (for AI responses)

1. Install [Ollama](https://ollama.ai)
2. Run: `ollama pull gemma2:2b`
3. Start Ollama, then start Desktop Pet
4. The pet will automatically connect

Without Ollama, the pet uses built-in personality-matched responses — still fun, just not generative.

---

## Usage

| Action | How |
|--------|-----|
| Feed pet | Right-click → Feed, or tray menu |
| Do a trick | Double-click pet, or right-click → Trick |
| Give commands | Right-click → Type Command, or say wake word |
| Settings | Right-click → Settings |
| Switch pet | Settings → Identity → Pet Type |
| View achievements | Settings → 🏆 Achievements |
| View memories | Settings → 🧠 Memory |
| Move pet | Click and drag |
| Quit | Right-click → Quit, or tray menu |

### Voice Commands

Say the wake word first ("hey buddy"), then your command:

```
"play [song/artist]"     — Spotify control
"pause / skip / next"    — Spotify control  
"open [app name]"        — launch applications
"search [query]"         — opens browser search
"do a [trick name]"      — spin, backflip, moonwalk, dance...
"my name is [name]"      — pet learns your name
"set timer [N] minutes"  — break timer
"feed me" / "bone"       — feed the pet
```

---

## Architecture

```
main.py              — DesktopPet class, main loop, event wiring
├── pet_state.py     — hunger, XP, level, mood, persistence
├── emotion_engine.py— 2D valence/arousal continuous mood state
├── llm_brain.py     — Ollama integration, fallback pools, fact extraction
├── memory.py        — persistent facts, exchanges, app time tracking
├── achievements.py  — 40+ achievement definitions and unlock logic
├── behavior.py      — state machine (idle/walk/sleep/trick/follow/curious)
├── hud.py           — transparent HUD overlay
├── speech.py        — speech bubble overlay
├── particles.py     — hearts, stars, zzz, notes, sparkles
├── tray.py          — system tray icon and menu
├── voice.py         — wake word detection, STT, command routing
├── command_handler.py— executes classified commands
├── sprite.py        — dog pixel art, 30 animations
├── dragon_sprite.py — dragon pixel art, 28 animations  
├── cat_sprite.py    — cat pixel art, 26 animations
├── accessories.py   — hat/glasses/crown rendering on sprites
├── settings_window.py— 8-tab Tkinter settings panel
├── memory_dashboard.py— memory viewer/editor UI
├── achievement_ui.py— trophy wall UI
├── screen_time.py   — streak tracking, daily/weekly stats
├── day_night.py     — time awareness, app watching, window detection
├── weather.py       — local weather via wttr.in
├── seasonal.py      — holiday greetings, seasonal accessories
└── config_manager.py— persistent config, works in both source + exe
```

---

## Roadmap

### v1.1 — Pet Evolution
- Level 5 → Form 2 (golden retriever / fire dragon / lynx)
- Level 10 → Form 3 (wolf / ice dragon / panther)  
- Level 20 → Mythic form with unique animations

### v1.2 — Dream Journal
- When pet sleeps (AFK > 10min), LLM generates a dream from your memories
- Shown as speech bubble on wake
- All dreams saved and browsable

### v1.3 — Productivity Guardian
- Tracks focused work vs distraction time
- Pomodoro mode with pet as accountability partner
- Weekly productivity report

### v2.0 — Multiplayer
- LAN discovery — pets on the same network find each other
- Visit, gift, and challenge to mini-games

See [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) for the full vision.

---

## Contributing

Pull requests welcome. The project is structured to make new features easy to add:

- **New pet type:** Create `yourpet_sprite.py` following `cat_sprite.py` as a template. Add to `PET_TYPES` in `main.py`.
- **New achievement:** Add a tuple to `ACHIEVEMENTS` in `achievements.py`. Hook the event in `main.py`.
- **New fallback strings:** Add a context key to `FALLBACK_BY_CONTEXT_[PETTYPE]` in `llm_brain.py`.
- **New voice command:** Add pattern to `classify_command()` in `llm_brain.py`, handler in `command_handler.py`.

---

## Credits

Built with:
- [Pillow](https://python-pillow.org/) — sprite rendering and compositing
- [pystray](https://github.com/moses-palmer/pystray) — system tray
- [Ollama](https://ollama.ai) — local LLM inference
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) — voice STT
- [winotify](https://github.com/versa-syahptr/winotify) — Windows notifications

All pixel art hand-crafted in Python using Pillow's `ImageDraw`.

---

## License

MIT — do whatever you want. Attribution appreciated but not required.

---

<div align="center">

**Made with 🐾 by [chron303](https://github.com/chron303)**

*"The best products don't just solve problems. They become part of people's lives."*

[⭐ Star this repo](https://github.com/chron303/desktop-pet) if your pet made you smile today.

</div>