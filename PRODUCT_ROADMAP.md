# Desktop Pet — Product Roadmap to 1,000,000 Users
## Vision: The world's most personal AI companion for PC users

---

## WHERE WE ARE NOW (v1.0 — Shipped)
- 3 pets (dog, dragon, cat) with 24-30 animations each
- Local LLM brain (Ollama/gemma2:2b) — personality-aware
- Voice commands, Spotify, app awareness, weather
- HUD overlay, accessories, XP/leveling
- Memory system — learns facts about the user
- Emotion engine — 2D continuous mood state
- Achievement system — 40+ achievements, trophy wall
- Settings panel, memory dashboard
- PyInstaller .exe — single file, no install needed

---

## PHASE 3 — Depth & Delight (Month 1-2) — TARGET: 10,000 users

### 3.1 — Pet Evolution System ⭐ HIGHEST IMPACT
**Why:** Transformation is the single most shareable moment in any pet game.
The screenshot that goes viral is always "my pet evolved."

- Level 5  → Form 2 (dog: golden retriever | dragon: fire dragon | cat: lynx)
- Level 10 → Form 3 (dog: wolf | dragon: ice dragon | cat: panther)
- Level 20 → Mythic form — entirely new sprite style, unique personality shift
- Evolution animation: 3-second cinematic with particles + sound
- New forms unlock new animations, new LLM personality tone
- Form stored in pet_save.json, shown in HUD

**Files needed:** `evolution.py`, updated sprite modules, evolution animations

### 3.2 — Mini-Games
**Why:** Gives users a reason to interact beyond feeding/tricks.
Active engagement = daily retention.

- **Fetch** — pet drops a ball, click within 3 seconds for XP
- **Catch** — pet throws treat, click to catch it
- **Whack-a-mole** — pet pops up from different screen positions
- All games drop to screen as transparent overlays
- XP rewards, high score tracking, achievement integration
- "Game Night" mode — chains 3 mini-games back to back

**Files needed:** `mini_game.py`, `fetch_game.py`

### 3.3 — Dream Journal
**Why:** Delightful, personal, shareable. Something NO other desktop app does.

- When pet sleeps (AFK > 10 min), LLM generates a short dream
- Dream is based on recent memory facts ("dreamed about code and pizza")
- On wake: speech bubble shows dream fragment + particle sparkles
- Dreams saved to `dreams.json` — browsable in memory dashboard
- Monthly "dream report" — "kutta dreamed 12 times this month"

**Files needed:** `dream_journal.py`, updated `memory_dashboard.py`

### 3.4 — Productivity Guardian Mode
**Why:** This is what makes the app USEFUL at work, not just cute.
"My pet keeps me accountable" = the story users tell their colleagues.

- Tracks focused work time (active window = code/docs/spreadsheet)
- Tracks distraction time (YouTube, Reddit, Twitter)
- Pet reacts in real time: encourages during focus, gentle nudge on distraction
- Pomodoro mode: 25 min focus → 5 min break, pet enforces it with personality
- Weekly productivity report shown in settings
- "Focus streak" — how many Pomodoros completed today
- Dragon personality: "You have been distracted for 8 minutes. Unacceptable."
- Cat personality: "*sits on your browser tab*"

**Files needed:** `productivity.py`, updated `day_night.py`

---

## PHASE 4 — Virality & Community (Month 2-4) — TARGET: 100,000 users

### 4.1 — Pet Export & Share (.petfile)
**Why:** The #1 growth mechanic. Every shared pet is a free acquisition.

- Export: saves pet_type, name, personality, level, XP, memories, evolution form
  as a signed .petfile (JSON + checksum)
- Import: load a friend's pet — it arrives with its history intact
- "Visiting pet" mode: imported pet walks around for 60 seconds then leaves a gift
- Share button in Settings → copies a shareable link (encodes pet state as base64 URL)
- Discord/Reddit integration: one-click share card (pet sprite + stats as PNG)

**Files needed:** `pet_export.py`, `share_card.py`

### 4.2 — LAN Friendship Network
**Why:** The feature that turns a solo app into a community app.
Two people in the same office, their pets discover each other.

- UDP broadcast every 30s: "I'm [pet_name] at [IP]"
- Pets on same LAN appear in tray: "🐶 Buddy is nearby!"
- Actions: Visit (pet walks to corner, shows greeting), Gift (drops XP bone),
  Challenge (mini-game duel), Trade accessories
- All interactions are opt-in — privacy first
- "Friends met" achievement category

**Files needed:** `lan_network.py`, `pet_visitor.py`

### 4.3 — Web Companion Dashboard
**Why:** Lets users obsess over their pet data from any browser.
Also makes the app feel premium and serious.

- Flask server runs on localhost:7777 when app is open
- Beautiful HTML dashboard:
  - Pet stats, mood history chart (recharts-style)
  - Memory timeline — every fact with date learned
  - Achievement wall with progress bars
  - Weekly screen time chart
  - Emotion heatmap (valence/arousal over 7 days)
  - Export pet data as JSON
- QR code in Settings to open on phone

**Files needed:** `web_dashboard.py`, `templates/dashboard.html`

### 4.4 — Daily Challenges
**Why:** Gives users a reason to open the app every single day.

- 3 challenges reset at midnight: "Feed pet before 9am", "Do 5 tricks",
  "Stay in focus mode for 1 hour"
- Bonus challenge once per week (harder, better reward)
- Challenge XP feeds into both pet level and achievement system
- Streak bonus: completing challenges 7 days in a row = golden day

**Files needed:** `daily_challenges.py`

---

## PHASE 5 — Platform & Monetization (Month 4-8) — TARGET: 500,000 users

### 5.1 — Premium Sprite Packs (Revenue stream #1)
- Community-created sprite packs (fox, bunny, robot, alien, ghost)
- $2.99 per pack or $9.99 lifetime all-access
- Revenue share with sprite artists (70/30)
- Distribution via in-app store + itch.io

### 5.2 — Cloud Sync (Revenue stream #2)
- $1.99/month — sync pet across multiple PCs
- Backup pet state to cloud — never lose your pet
- Cross-device: desktop pet can "visit" your phone as a widget (iOS/Android)

### 5.3 — Desktop Pet SDK
- Public API for third-party integrations
- GitHub Actions integration: pet reacts to CI build results
- Slack/Discord bot: pet posts daily status updates to your team channel
- VS Code extension: pet lives in the sidebar, reacts to your code

### 5.4 — Mac & Linux ports
- Mac: NSWindow-based transparent overlay (Swift wrapper around Python core)
- Linux: X11/Wayland compositor overlay
- Cross-platform core is already Python — just needs window backend swap

---

## PHASE 6 — 1 Million Users (Month 8-18)

### 6.1 — Mobile Companion App
- iOS/Android widget: mini version of the pet on your home screen
- Syncs with desktop via cloud: same pet, same memories
- Mobile-only interactions: tap to feed, accelerometer tricks
- Push notifications from your pet: "Miss you! Come back to your PC 🐾"

### 6.2 — Enterprise / Team Edition
- "Office Pet" — shared pet for a whole team
- Team members all feed/interact with same pet
- Pet tracks team productivity, celebrates deploys, mourns outages
- Slack-native version for remote teams
- $5/user/month for teams of 10+

### 6.3 — AI Upgrade — GPT-4o / Claude Integration
- Optional cloud LLM upgrade for users who want smarter responses
- Pet remembers 1 year of interactions, not just 50 exchanges
- Emotional continuity: pet remembers "last Tuesday you were stressed about a deadline"
- Voice synthesis: pet actually speaks in a consistent character voice

---

## GROWTH STRATEGY

### Acquisition
1. **Product Hunt launch** — target #1 Product of the Day
   "Your AI pet lives on your desktop and actually knows you"
2. **Reddit** — r/sysadmin, r/ProgrammerHumor, r/productivity, r/gaming
   Post "My desktop pet learned my name and work hours after 3 days" with gif
3. **TikTok/YouTube Shorts** — evolution moments, pet reactions to code errors,
   late-night sessions — these are natively viral
4. **Dev communities** — GitHub trending, Hacker News Show HN
5. **Discord servers** — drop the .exe in programming/productivity servers

### Retention
1. **Daily challenges** — reason to open every day
2. **Evolution milestones** — reason to keep leveling
3. **Streak system** — loss aversion keeps people coming back
4. **Dream journal** — delightful surprise every morning

### Monetization Timeline
- Month 1-3:  Free, build audience
- Month 4:    Premium sprite packs ($2.99)
- Month 6:    Cloud sync subscription ($1.99/mo)
- Month 12:   Enterprise edition ($5/user/mo)
- Month 18:   Mobile app (freemium)

### Target Users
Primary:   Developers, designers, remote workers (PC power users)
Secondary: Students, gamers, content creators
Tertiary:  Anyone who works on a Windows PC 4+ hours/day

### KPIs to track
- DAU/MAU ratio (target: >40% — great for desktop apps)
- Session length (target: >2 hours/day average)
- D1/D7/D30 retention (target: 60%/35%/20%)
- Streak length distribution (target: >30% users with 7+ day streaks)
- Viral coefficient (target: >0.3 — 1 in 3 users refers someone)

---

## IMMEDIATE NEXT STEPS (This Week)

1. ✅ Fix `state.mood` setter → `state._data["mood"]`
2. ✅ Test emotion engine debug output in Pet Status
3. 🔲 Wire achievement hooks into main.py (15 min)
4. 🔲 Add 🏆 Achievements tab to settings_window.py
5. 🔲 Rebuild .exe and test achievement unlock notifications
6. 🔲 Create GitHub repo with proper README, screenshots, demo gif
7. 🔲 Post to r/Python and r/sysadmin for first feedback
8. 🔲 Start evolution system sprites

---

*"The best products don't just solve problems. They become part of people's lives."*
*This pet should feel like a real companion — one that grows with you, remembers you,*
*and makes your work day a little less lonely.*
