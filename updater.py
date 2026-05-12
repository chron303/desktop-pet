"""
updater.py — GitHub release checker.
Checks for new versions on startup and once daily.
Shows a non-intrusive speech bubble if an update is available.
"""
import json, threading, time
import urllib.request, urllib.error

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
CURRENT_VERSION = "1.0.0"
CHECK_INTERVAL  = 86400   # 24 hours


class UpdateChecker:
    def __init__(self, owner: str, repo: str, callback=None):
        """
        owner:    GitHub username
        repo:     repository name
        callback: fn(version: str, url: str) called if update found
        """
        self._owner    = owner
        self._repo     = repo
        self._callback = callback
        self._last_check = 0.0
        self._latest   = None
        # Check immediately in background
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        try:
            url = GITHUB_API.format(owner=self._owner, repo=self._repo)
            req = urllib.request.Request(url,
                headers={"User-Agent": "DesktopPet/1.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=6).read())
            tag  = data.get("tag_name", "").lstrip("v")
            html = data.get("html_url", "")
            self._last_check = time.monotonic()

            if tag and self._is_newer(tag):
                self._latest = (tag, html)
                print(f"[updater] New version available: v{tag}")
                if self._callback:
                    self._callback(tag, html)
            else:
                print(f"[updater] Up to date (v{CURRENT_VERSION})")
        except Exception as e:
            # Network error / no repo set up yet — silent fail
            pass

    def _is_newer(self, tag: str) -> bool:
        try:
            def parse(v):
                return tuple(int(x) for x in v.split("."))
            return parse(tag) > parse(CURRENT_VERSION)
        except Exception:
            return False

    def tick(self):
        """Call periodically — re-checks every 24h."""
        if time.monotonic() - self._last_check > CHECK_INTERVAL:
            threading.Thread(target=self._check, daemon=True).start()

    @property
    def latest(self):
        return self._latest