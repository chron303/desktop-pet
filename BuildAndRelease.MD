# Desktop Pet — Build & Release Guide

## Step-by-step: from code to shipped .exe

---

### 1. Pre-build: generate icon.ico

Run this ONCE before every build. It pulls your actual pet sprite into a proper
multi-resolution .ico file that Windows and PyInstaller need.

```
python make_icon.py
```

Expected output:
```
[icon] Using sprite.make_icon()
[icon] Saved icon.ico (42 KB) with sizes: [16, 32, 48, 64, 128, 256]
```

---

### 2. Run the build

```
build.bat
```

Expected flow:
```
[1/5] Cleaning previous build...  Done.
[2/5] Locating assets...          Done.
[3/5] Running PyInstaller...      (takes 30-90 seconds)
[4/5] Copying runtime data files... Done.
[5/5] Verifying output...

  BUILD SUCCESSFUL!
  Output: dist\DesktopPet.exe
  Size:   ~35 MB
```

---

### 3. Test before releasing

- Launch `dist\DesktopPet.exe` — pet should appear on screen
- Switch pet type in Settings, Save, close, relaunch — should restore
- Try a voice command if mic is available
- Check tray icon appears correctly

---

### 4. Create GitHub repo

```bash
# In your project folder (PowerShell or Git Bash)
git init
git add .
git commit -m "feat: Desktop Pet v1.0.0 — dog, dragon, cat with LLM brain"
git branch -M main

# Create repo on github.com first, then:
git remote add origin https://github.com/YOURUSERNAME/desktop-pet.git
git push -u origin main
```

---

### 5. Tag the release

```bash
git tag -a v1.0.0 -m "v1.0.0 — Initial release: dog, dragon, cat, Ollama LLM, voice, HUD"
git push origin v1.0.0
```

---

### 6. Create GitHub Release with the .exe

Go to: `github.com/YOURUSERNAME/desktop-pet/releases/new`

- Tag: `v1.0.0`
- Title: `Desktop Pet v1.0.0 🐾`
- Description (copy-paste):

```
## Desktop Pet v1.0.0

A living pixel pet that lives on your Windows desktop.

### Features
- 🐶 Dog / 🐉 Dragon / 🐱 Cat — each with 24-30 animations
- 🧠 Local LLM brain via Ollama (gemma2:2b) — personality-aware responses
- 🎤 Voice commands — feed, trick, play music, open apps
- 🎵 Spotify integration — reacts to your music
- 📊 HUD overlay — hunger, XP, mood, streak
- 💾 Memory system — remembers facts about you across sessions
- 🏆 XP, leveling, accessories
- ☀️ Day/night tints, weather reactions, seasonal events

### Requirements
- Windows 10/11
- [Ollama](https://ollama.ai) (optional, for LLM responses): `ollama pull gemma2:2b`

### Install
Download `DesktopPet.exe` below and run it. No installer needed.
```

- Attach: `dist\DesktopPet.exe`
- Click **Publish release**

---

### Common build errors & fixes

| Error | Fix |
|-------|-----|
| `icon.ico not found` | Run `python make_icon.py` first |
| `ModuleNotFoundError: pystray` | `pip install pystray` |
| `ModuleNotFoundError: PIL` | `pip install pillow` |
| `Failed to execute script main` | Run `dist\DesktopPet.exe` from cmd to see the real error |
| Exe is 200MB+ | Add `--exclude-module torch` to build.bat |
| Tray icon missing | Copy `icon.ico` next to the .exe in dist\ |
| Pet window doesn't appear | Check `config.json` exists next to .exe |

---

### After v1.0.0 — what's next (Phase 2)

- [ ] Memory dashboard UI (view & delete learned facts)
- [ ] Tray text command extracts facts to memory.json
- [ ] Pet-specific accessories (dragon flame crown, cat bow)
- [ ] Spotify OAuth setup wizard
- [ ] Emotion engine (2D valence/arousal state machine)
- [ ] Mini-games (click-to-play fetch with XP rewards)
- [ ] Achievement system (trophy wall in Settings)
- [ ] Pet evolution (level 5 → new form, level 10 → mythic)