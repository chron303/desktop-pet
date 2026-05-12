# Desktop Pet — Launch Checklist

## GitHub Setup (30 min)

- [ ] Create repo: `github.com/chron303/desktop-pet`
- [ ] Set description: "A living AI desktop companion that learns who you are 🐾"
- [ ] Add topics: `desktop-pet`, `tamagotchi`, `ai`, `python`, `windows`, `tkinter`, `ollama`, `pixel-art`
- [ ] Upload `README.md`, `requirements.txt`, `.gitignore`, all `.py` files
- [ ] Create `v1.0.0` release with `DesktopPet.exe` attached
- [ ] Add screenshots to README (pet on desktop, settings panel, trophy wall, memory dashboard)

## Screenshots to capture (critical for virality)

1. **Hero shot** — pet on a real desktop with VS Code open in background
2. **Three pets** — dog, dragon, cat side by side
3. **Settings panel** — all 8 tabs visible
4. **Trophy wall** — achievement UI with a few unlocked
5. **Memory dashboard** — facts tab with some learned facts
6. **HUD overlay** — the compact pill above the pet
7. **Achievement unlock** — speech bubble saying achievement name
8. **Evolution teaser** — placeholder "coming soon" shot

## Reddit Posts (Day 1)

### r/Python
Title: "I built a pixel-art desktop pet with a local LLM brain that learns your name and work habits [OC]"

Body:
> After a few months of evenings, I shipped Desktop Pet v1.0 — a Python app that puts a living pixel-art companion on your Windows desktop.
>
> What makes it different from Shimeji or similar:
> - Local LLM via Ollama (gemma2:2b) — responds with personality, no API key needed
> - Continuous emotion engine — 2D valence/arousal state that drifts based on hunger, music, time of day
> - Persistent memory — learns your name, job, habits across sessions
> - 40+ achievements — unlocks as you actually use it
> - Three pets (dog, dragon, cat) with 24-30 animations each
>
> Built with: Pillow, pystray, SpeechRecognition, Tkinter, Ollama
>
> GitHub: github.com/chron303/desktop-pet
> Download: [direct exe link]
>
> Happy to answer questions about the architecture — the emotion engine and sprite rendering were the most interesting parts to build.

### r/sysadmin  
Title: "My desktop pet now reminds me to take breaks and reacts when I open Teams 😂"

### r/ProgrammerHumor
Title: "My pixel dog has been watching me code for 3 days and just said 'bug found 🐛' [OC]"

### r/learnpython
Title: "6-month project complete: pixel art desktop pet with local AI brain — here's the architecture"

## Product Hunt Launch

**Tagline:** "Your AI desktop pet that actually knows you"

**Description:**
Desktop Pet is a pixel-art companion that lives on your Windows desktop. Unlike screensavers or widgets, it's a real pet — it gets hungry, levels up, reacts to your music, notices what apps you use, and remembers facts you tell it across sessions.

What makes it special:
🧠 Local AI brain (Ollama) — responds in character, no cloud needed
💭 Emotion engine — mood drifts continuously, not just a string
📖 Memory system — learns your name, job, habits
🏆 40+ achievements — Day One to 100-day streak legends
🎤 Voice commands — feed, trick, play music, open apps
🐉 Three pets — dog, dragon, cat with 24-30 animations each

Free. Open source. Your data stays on your machine.

**First comment (post immediately after launch):**
> Hey PH! Made this because I wanted a desktop pet that actually felt alive rather than just cute. The hardest part was the emotion engine — instead of setting mood = "happy", the pet has a continuous 2D state (valence + arousal) that drifts based on a dozen inputs. Feed it and you can literally watch it go from bored to excited in the Pet Status dialog.
>
> If you try it, tell your pet your name and watch it remember across restarts 🐾

## Week 1 Goals
- [ ] 100 GitHub stars
- [ ] 500 downloads
- [ ] 50 Reddit upvotes on at least one post
- [ ] First issue filed (engagement signal)
- [ ] First fork

## Week 4 Goals  
- [ ] 1,000 GitHub stars
- [ ] 5,000 downloads
- [ ] Featured in a Python newsletter (Python Weekly, Real Python)
- [ ] First YouTube video from someone else showing it off
- [ ] v1.1 release with pet evolution
