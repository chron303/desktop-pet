"""
day_night.py — Environmental awareness: time, idle, app, window avoidance.

AppWatcher improvements:
  - Scans ALL running processes, not just the foreground window
  - Detects Spotify even when it's in the background (music playing)
  - Detects VS Code / browser even when focus is elsewhere
  - Returns a rich AppContext object with flags for each category
  - Window title scanning for extra signals (e.g. "YouTube" in browser)
  - Debounced with per-category change events so main loop gets notified
    exactly once when app context switches (not every 0.8s)
"""

import sys, time, datetime, ctypes, ctypes.wintypes

_WIN32 = sys.platform == "win32"
try:
    import win32gui, win32process, win32con, psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


# ── Day / Night ──────────────────────────────────────────────────────────

PERIODS = {
    "morning":  (6,  10),
    "day":      (10, 17),
    "evening":  (17, 21),
    "night":    (21, 23),
    "midnight": (23,  6),
}

PERIOD_TINT = {
    "morning":  (255, 235, 180, 18),
    "day":      None,
    "evening":  (255, 170, 100, 22),
    "night":    ( 70,  90, 200, 32),
    "midnight": ( 20,  20,  80, 48),
}

def current_period():
    h = datetime.datetime.now().hour
    for name,(s,e) in PERIODS.items():
        if s < e:
            if s <= h < e: return name
        else:
            if h >= s or h < e: return name
    return "day"

def period_tint():
    return PERIOD_TINT.get(current_period())

def is_night():    return current_period() in ("night","midnight")
def is_morning():  return current_period() == "morning"


# ── Idle detection ───────────────────────────────────────────────────────

class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_seconds():
    if not _WIN32:
        return 0.0
    try:
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        ms = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return ms / 1000.0
    except Exception:
        return 0.0


# ── App context ──────────────────────────────────────────────────────────

SPOTIFY_EXE   = {"spotify.exe", "spotify"}
VSCODE_EXE    = {"code.exe", "code - insiders.exe", "windsurf.exe",
                 "cursor.exe", "vscodium.exe"}
BROWSER_EXE   = {"chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
                 "brave.exe", "chromium.exe", "vivaldi.exe", "waterfox.exe"}
GAME_EXE_HINTS = {"steam.exe", "epicgameslauncher.exe", "gog galaxy.exe"}

# Window title keywords → sub-context
YOUTUBE_TITLES = {"youtube", "youtu.be"}
GITHUB_TITLES  = {"github.com", "github"}
MEET_TITLES    = {"meet.google", "zoom", "teams", "webex"}


class AppContext:
    """Snapshot of what the user is currently doing."""
    __slots__ = ("foreground_exe", "foreground_title", "foreground_cat",
                 "spotify_running", "spotify_playing",
                 "vscode_open", "browser_open",
                 "in_meeting", "on_youtube", "on_github",
                 "category")

    def __init__(self):
        self.foreground_exe   = "unknown"
        self.foreground_title = ""
        self.foreground_cat   = "other"
        self.spotify_running  = False
        self.spotify_playing  = False
        self.vscode_open      = False
        self.browser_open     = False
        self.in_meeting       = False
        self.on_youtube       = False
        self.on_github        = False
        self.category         = "other"   # primary category for pet reactions

    def __eq__(self, other):
        if not isinstance(other, AppContext): return False
        return self.category == other.category and \
               self.spotify_playing == other.spotify_playing and \
               self.in_meeting == other.in_meeting

    def summary(self):
        parts = [f"fg={self.foreground_exe}({self.foreground_cat})"]
        if self.spotify_playing: parts.append("spotify:playing")
        if self.vscode_open:     parts.append("vscode:open")
        if self.in_meeting:      parts.append("meeting!")
        if self.on_youtube:      parts.append("youtube")
        return " | ".join(parts)


class AppWatcher:
    """
    Polls system state every TTL seconds.
    - Foreground window: exe + title
    - Background scan: checks if Spotify / VS Code processes are alive
    - Spotify playing detection: checks Spotify window title (it changes
      when music plays vs paused)
    - Returns AppContext; also exposes `changed` flag when context shifts
    """
    _FOREGROUND_TTL = 0.5    # how often to check foreground window (s)
    _BACKGROUND_TTL = 3.0    # how often to scan all processes (s)

    def __init__(self):
        self._ctx          = AppContext()
        self._prev_ctx     = AppContext()
        self.changed       = False          # True for one tick after change
        self._last_fg      = 0.0
        self._last_bg      = 0.0

    # ── Public ───────────────────────────────────────────────────────────

    def get(self) -> AppContext:
        """Return current AppContext, refresh if stale."""
        now = time.monotonic()
        if now - self._last_fg >= self._FOREGROUND_TTL:
            self._poll_foreground()
            self._last_fg = now
        if now - self._last_bg >= self._BACKGROUND_TTL:
            self._poll_background()
            self._last_bg = now
        self._resolve_category()
        # Detect change
        self.changed = (self._ctx != self._prev_ctx)
        if self.changed:
            self._prev_ctx = AppContext()
            self._prev_ctx.category        = self._ctx.category
            self._prev_ctx.spotify_playing = self._ctx.spotify_playing
            self._prev_ctx.in_meeting      = self._ctx.in_meeting
        return self._ctx

    # ── Foreground poll ──────────────────────────────────────────────────

    def _poll_foreground(self):
        if not _PSUTIL:
            return
        try:
            hwnd  = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).lower()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            exe = psutil.Process(pid).name().lower()

            self._ctx.foreground_exe   = exe
            self._ctx.foreground_title = title

            if exe in SPOTIFY_EXE:
                self._ctx.foreground_cat = "spotify"
            elif exe in VSCODE_EXE:
                self._ctx.foreground_cat = "vscode"
            elif exe in BROWSER_EXE:
                self._ctx.foreground_cat = "browser"
            else:
                self._ctx.foreground_cat = "other"

            # Sub-context from title
            self._ctx.on_youtube = any(k in title for k in YOUTUBE_TITLES)
            self._ctx.on_github  = any(k in title for k in GITHUB_TITLES)
            self._ctx.in_meeting = any(k in title for k in MEET_TITLES) or \
                                   exe in {"zoom.exe","teams.exe","webex.exe"}
        except Exception:
            pass

    # ── Background scan ──────────────────────────────────────────────────

    def _poll_background(self):
        if not _PSUTIL:
            return
        try:
            running_exes = {p.name().lower() for p in psutil.process_iter(["name"])}
        except Exception:
            return

        self._ctx.spotify_running = bool(running_exes & SPOTIFY_EXE)
        self._ctx.vscode_open     = bool(running_exes & VSCODE_EXE)
        self._ctx.browser_open    = bool(running_exes & BROWSER_EXE)

        # Spotify playing detection:
        # When Spotify plays, its window title = "Artist - Song Title"
        # When paused/stopped it's just "Spotify" or "Spotify Premium"
        if self._ctx.spotify_running:
            self._ctx.spotify_playing = self._spotify_is_playing()

    def _spotify_is_playing(self) -> bool:
        """
        Enumerate all windows, find the Spotify one, check its title.
        A title with " - " indicates a track is playing.
        """
        if not _WIN32:
            return False
        playing = [False]
        def cb(hwnd, _):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                exe = psutil.Process(pid).name().lower()
                if exe in SPOTIFY_EXE:
                    title = win32gui.GetWindowText(hwnd)
                    # Playing: "Artist Name - Song Name"
                    # Paused / idle: "Spotify", "Spotify Premium", ""
                    if " - " in title and len(title) > 10:
                        playing[0] = True
            except Exception:
                pass
            return True
        try:
            win32gui.EnumWindows(cb, None)
        except Exception:
            pass
        return playing[0]

    # ── Category resolution ──────────────────────────────────────────────

    def _resolve_category(self):
        """
        Decide the primary category for pet reactions.
        Priority: meeting > spotify_playing > foreground_cat > other
        """
        ctx = self._ctx
        if ctx.in_meeting:
            ctx.category = "meeting"
        elif ctx.spotify_playing:
            ctx.category = "spotify"
        elif ctx.foreground_cat == "vscode":
            ctx.category = "vscode"
        elif ctx.foreground_cat == "browser":
            if ctx.on_youtube:    ctx.category = "youtube"
            elif ctx.on_github:   ctx.category = "github"
            else:                 ctx.category = "browser"
        elif ctx.foreground_cat == "spotify":
            ctx.category = "spotify"
        else:
            ctx.category = "other"


# ── Window avoider ───────────────────────────────────────────────────────

class WindowAvoider:
    _TTL = 3.0

    def __init__(self):
        self._zones     = []
        self._last_scan = 0.0

    def free_zones(self, screen_w, taskbar_top, pet_w=96):
        now = time.monotonic()
        if now - self._last_scan < self._TTL:
            return self._zones or [(0, screen_w-pet_w)]
        self._last_scan = now

        if not _WIN32 or not _PSUTIL:
            self._zones = [(0, screen_w-pet_w)]
            return self._zones

        check_y = taskbar_top - 30
        step    = 20
        busy    = set()

        try:
            def cb(hwnd, _):
                if not win32gui.IsWindowVisible(hwnd): return True
                try:
                    l,t,r,b = win32gui.GetWindowRect(hwnd)
                    if b < check_y-300 or t > check_y+300: return True
                    for cx in range(max(0,l), min(screen_w,r), step):
                        busy.add(cx//step)
                except Exception:
                    pass
                return True
            win32gui.EnumWindows(cb, None)
        except Exception:
            self._zones = [(0, screen_w-pet_w)]; return self._zones

        zones, start = [], None
        total = screen_w // step
        for col in range(total):
            if col not in busy:
                if start is None: start = col*step
            else:
                if start is not None:
                    end = col*step
                    if end-start >= pet_w: zones.append((start, end-pet_w))
                    start = None
        if start is not None and screen_w-start >= pet_w:
            zones.append((start, screen_w-pet_w))

        self._zones = zones if zones else [(0, screen_w-pet_w)]
        return self._zones

    def clamp_x_to_free(self, x, screen_w, taskbar_top, pet_w=96):
        zones = self.free_zones(screen_w, taskbar_top, pet_w)
        for s,e in zones:
            if s <= x <= e: return x
        best = min(zones, key=lambda z: min(abs(x-z[0]), abs(x-z[1])))
        return float(max(best[0], min(best[1], x)))