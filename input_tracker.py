"""
input_tracker.py — Cursor pos + taskbar detection with safe fallbacks.
"""
import sys, time

if sys.platform == "win32":
    import ctypes, ctypes.wintypes
    _WIN32 = True
    try:
        import win32gui, win32process, psutil
        _PSUTIL = True
    except ImportError:
        _PSUTIL = False
else:
    _WIN32 = _PSUTIL = False


class APPBARDATA(ctypes.Structure if _WIN32 else object):
    if _WIN32:
        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("hWnd",   ctypes.c_void_p),
            ("uCallbackMessage", ctypes.c_uint),
            ("uEdge",  ctypes.c_uint),
            ("rc",     ctypes.wintypes.RECT),
            ("lParam", ctypes.c_long),
        ]


class InputTracker:
    _WIN_TTL = 0.5

    def __init__(self):
        self._cached_win   = "unknown"
        self._last_win_t   = 0.0
        self._taskbar_top  = None

    def get_cursor_pos(self):
        if _WIN32:
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return (pt.x, pt.y)
        return (0, 0)

    def get_active_window_name(self):
        now = time.monotonic()
        if now - self._last_win_t < self._WIN_TTL:
            return self._cached_win
        self._last_win_t = now
        if _PSUTIL:
            try:
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                self._cached_win = psutil.Process(pid).name().lower()
            except Exception:
                pass
        return self._cached_win

    def get_taskbar_top(self, screen_h: int) -> int:
        """Return taskbar top y. Falls back to screen_h - 48 safely."""
        if self._taskbar_top is not None:
            return self._taskbar_top

        fallback = screen_h - 48   # standard taskbar height

        if not _WIN32:
            self._taskbar_top = fallback
            return fallback

        try:
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            ret = ctypes.windll.shell32.SHAppBarMessage(5, ctypes.byref(abd))  # ABM_GETTASKBARPOS=5
            top = abd.rc.top
            # Sanity check: must be in lower 40% of screen
            if top > screen_h * 0.5 and top < screen_h:
                self._taskbar_top = top
                print(f"[tracker] taskbar detected at y={top}")
                return top
            else:
                print(f"[tracker] taskbar y={top} looks wrong, using fallback {fallback}")
        except Exception as e:
            print(f"[tracker] taskbar detection failed: {e}")

        self._taskbar_top = fallback
        return fallback

    def get_free_x_zones(self, screen_w, pet_w=240):
        return [(0, screen_w - pet_w)]