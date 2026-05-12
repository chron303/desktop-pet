"""
clipboard_watcher.py — Monitors clipboard for changes.

When the user copies text, the pet can:
  • React to code snippets ("Oh you're copying code!")
  • React to URLs ("Ooh a link!")
  • React to long text ("That's a lot to copy!")
  • Offer to help ("Want me to search that?")

Polls every 2 seconds. Throttled to avoid spam.
"""

import threading, time, re, sys

_WIN32 = sys.platform == "win32"

POLL_INTERVAL = 2.0     # seconds between clipboard checks
REACT_COOLDOWN = 30.0   # seconds between reactions

URL_PATTERN  = re.compile(r'https?://\S+')
CODE_HINTS   = ['{', '}', 'def ', 'function ', 'import ', 'class ',
                'const ', 'var ', 'let ', '#include', 'SELECT ', 'FROM ']


def _get_clipboard() -> str:
    """Get current clipboard text. Returns empty string on failure."""
    if not _WIN32:
        return ""
    try:
        import ctypes
        CF_TEXT      = 1
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(0):
            return ""
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            ptr = kernel32.GlobalLock(handle)
            if not ptr:
                return ""
            text = ctypes.wstring_at(ptr)
            kernel32.GlobalUnlock(handle)
            return text or ""
        finally:
            user32.CloseClipboard()
    except Exception:
        return ""


class ClipboardWatcher:
    def __init__(self, on_change=None):
        """on_change: fn(text: str, category: str) called when clipboard changes."""
        self.on_change    = on_change
        self._last_text   = ""
        self._last_react  = 0.0
        self._running     = False
        self._thread      = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                text = _get_clipboard()
                if text and text != self._last_text and len(text.strip()) > 3:
                    self._last_text = text
                    self._react(text.strip())
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    def _react(self, text: str):
        now = time.monotonic()
        if now - self._last_react < REACT_COOLDOWN:
            return
        self._last_react = now

        category = self._classify(text)
        if category and self.on_change:
            self.on_change(text[:200], category)

    def _classify(self, text: str) -> str | None:
        """Classify clipboard content. Returns category or None to ignore."""
        stripped = text.strip()
        n = len(stripped)

        if n < 4:
            return None

        # URL
        if URL_PATTERN.search(stripped):
            return "url"

        # Code
        if any(hint in stripped for hint in CODE_HINTS):
            return "code"

        # Error message
        if any(w in stripped.lower() for w in ["error:", "exception:", "traceback", "syntaxerror"]):
            return "error"

        # Long text (might be article/doc)
        if n > 500:
            return "long_text"

        # Email address
        if re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', stripped):
            return "email"

        # Numbers / data
        if re.match(r'^[\d\s\.,%-]+$', stripped) and n > 5:
            return "data"

        # Short text — ignore (not interesting enough)
        if n < 20:
            return None

        return "text"


CLIPBOARD_QUIPS = {
    "url":       ["Ooh a link! 👀", "Where does that go? 🔗", "Interesting URL!"],
    "code":      ["Copying code? 💻", "Ooh code! Need help? 🐛", "Stack Overflow moment? 😅"],
    "error":     ["That looks like an error... 🐛", "Uh oh, error? 😬", "Bug detected! 🐛"],
    "long_text": ["That's a lot of text! 📄", "Reading something interesting? 📚"],
    "email":     ["An email address! 📧", "Emailing someone? 📬"],
    "data":      ["Numbers! 🔢", "Crunching data? 📊"],
    "text":      [],   # generic text — don't react by default
}

def get_clipboard_quip(category: str) -> str | None:
    import random
    pool = CLIPBOARD_QUIPS.get(category, [])
    return random.choice(pool) if pool else None