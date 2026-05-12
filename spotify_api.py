"""
spotify_api.py — Spotify Web API integration.

Gives the pet REAL Spotify control:
  • Play any song/artist/playlist by name
  • Pause / resume / skip / previous
  • Get current track info (for display + quips)
  • Set volume
  • Queue songs

Setup (one-time, 2 minutes):
  1. Go to developer.spotify.com/dashboard
  2. Create app → set Redirect URI to http://localhost:8888/callback
  3. Copy Client ID + Secret into config.json:
       "spotify_client_id": "your_id",
       "spotify_client_secret": "your_secret"
  4. Run: python spotify_api.py --setup
     → browser opens, authorize, tokens saved

After setup the pet uses this automatically when Spotify is running.
Falls back to media keys if not configured.
"""

import json, os, time, threading, urllib.request, urllib.parse, urllib.error
import base64, http.server, webbrowser, secrets

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
TOKEN_PATH  = os.path.join(os.path.dirname(__file__), "spotify_token.json")

REDIRECT_URI   = "http://localhost:8888/callback"
SCOPE          = ("user-read-playback-state user-modify-playback-state "
                  "user-read-currently-playing playlist-read-private")
AUTH_URL       = "https://accounts.spotify.com/authorize"
TOKEN_URL      = "https://accounts.spotify.com/api/token"
API_BASE       = "https://api.spotify.com/v1"


def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


class SpotifyAPI:
    def __init__(self):
        self._access_token  = None
        self._refresh_token = None
        self._token_expiry  = 0
        self._client_id     = None
        self._client_secret = None
        self._available     = False
        self._current_track = None
        self._track_poll_t  = 0
        self._lock          = threading.Lock()

        cfg = _load_config()
        self._client_id     = cfg.get("spotify_client_id", "")
        self._client_secret = cfg.get("spotify_client_secret", "")

        if self._client_id and self._client_secret:
            threading.Thread(target=self._init, daemon=True).start()
        else:
            print("[spotify] No credentials in config.json — using media keys fallback.")
            print("          See spotify_api.py docstring for setup.")

    def _init(self):
        if self._load_tokens():
            self._refresh_access_token()
            self._available = True
            print(f"[spotify] Connected ✅ — {self.get_current_track_name()}")
        else:
            print("[spotify] No token — run: python spotify_api.py --setup")

    # ── Token management ─────────────────────────────────────────────────

    def _load_tokens(self) -> bool:
        if not os.path.exists(TOKEN_PATH):
            return False
        try:
            with open(TOKEN_PATH) as f:
                data = json.load(f)
            self._access_token  = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            self._token_expiry  = data.get("expiry", 0)
            return bool(self._refresh_token)
        except Exception:
            return False

    def _save_tokens(self):
        with open(TOKEN_PATH, "w") as f:
            json.dump({
                "access_token":  self._access_token,
                "refresh_token": self._refresh_token,
                "expiry":        self._token_expiry,
            }, f)

    def _refresh_access_token(self):
        if not self._refresh_token:
            return False
        try:
            creds  = base64.b64encode(
                f"{self._client_id}:{self._client_secret}".encode()).decode()
            data   = urllib.parse.urlencode({
                "grant_type":    "refresh_token",
                "refresh_token": self._refresh_token,
            }).encode()
            req    = urllib.request.Request(TOKEN_URL, data=data,
                headers={"Authorization": f"Basic {creds}",
                         "Content-Type": "application/x-www-form-urlencoded"})
            resp   = json.loads(urllib.request.urlopen(req, timeout=8).read())
            self._access_token = resp["access_token"]
            self._token_expiry = time.time() + resp.get("expires_in", 3600) - 60
            if "refresh_token" in resp:
                self._refresh_token = resp["refresh_token"]
            self._save_tokens()
            return True
        except Exception as e:
            print(f"[spotify] Token refresh failed: {e}")
            return False

    def _ensure_token(self):
        if time.time() > self._token_expiry:
            self._refresh_access_token()

    # ── API calls ────────────────────────────────────────────────────────

    def _api(self, method: str, endpoint: str, body: dict = None,
             params: dict = None) -> dict | None:
        self._ensure_token()
        if not self._access_token:
            return None
        url = f"{API_BASE}/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            data = json.dumps(body).encode() if body else None
            req  = urllib.request.Request(url,
                data=data, method=method,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type":  "application/json",
                })
            resp = urllib.request.urlopen(req, timeout=6)
            content = resp.read()
            return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._refresh_access_token()
            elif e.code == 404:
                pass   # no active device
            else:
                print(f"[spotify] API {method} {endpoint}: {e.code}")
            return None
        except Exception as e:
            print(f"[spotify] API error: {e}")
            return None

    # ── Public controls ──────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        return self._available

    def play(self, query: str = "") -> str:
        """Play by search query — finds best match and plays it."""
        if not query:
            self._api("PUT", "me/player/play")
            return "Playing! 🎵"

        # Search for track
        results = self._api("GET", "search", params={
            "q": query, "type": "track,artist,playlist", "limit": 1
        })
        if not results:
            return f"Couldn't find '{query}' 🤔"

        # Try track first, then artist, then playlist
        uri = None
        name = query
        if results.get("tracks", {}).get("items"):
            item = results["tracks"]["items"][0]
            uri  = item["uri"]
            name = f"{item['name']} by {item['artists'][0]['name']}"
        elif results.get("artists", {}).get("items"):
            item = results["artists"]["items"][0]
            uri  = item["uri"]
            name = item["name"]
        elif results.get("playlists", {}).get("items"):
            item = results["playlists"]["items"][0]
            uri  = item["uri"]
            name = item["name"]

        if uri:
            if "track" in uri:
                self._api("PUT", "me/player/play", body={"uris": [uri]})
            else:
                self._api("PUT", "me/player/play", body={"context_uri": uri})
            return f"Playing {name}! 🎵"
        return f"Nothing found for '{query}' 🤔"

    def pause(self) -> str:
        self._api("PUT", "me/player/pause")
        return "Paused ⏸️"

    def resume(self) -> str:
        self._api("PUT", "me/player/play")
        return "Resumed! ▶️"

    def skip(self) -> str:
        self._api("POST", "me/player/next")
        return "Skipped! ⏭️"

    def previous(self) -> str:
        self._api("POST", "me/player/previous")
        return "Going back! ⏮️"

    def set_volume(self, percent: int) -> str:
        pct = max(0, min(100, percent))
        self._api("PUT", "me/player/volume", params={"volume_percent": pct})
        return f"Volume: {pct}% 🔊"

    def get_current_track_name(self) -> str:
        """Returns 'Artist - Track' or empty string."""
        now = time.monotonic()
        if now - self._track_poll_t < 5:
            return self._current_track or ""
        self._track_poll_t = now
        data = self._api("GET", "me/player/currently-playing")
        if data and data.get("item"):
            item = data["item"]
            artist = item["artists"][0]["name"]
            track  = item["name"]
            self._current_track = f"{artist} - {track}"
        else:
            self._current_track = ""
        return self._current_track or ""

    def is_playing(self) -> bool:
        data = self._api("GET", "me/player")
        return bool(data and data.get("is_playing"))

    # ── OAuth setup flow ─────────────────────────────────────────────────

    def run_auth_flow(self):
        """Open browser for OAuth, capture callback, save tokens."""
        state   = secrets.token_urlsafe(16)
        params  = urllib.parse.urlencode({
            "client_id":     self._client_id,
            "response_type": "code",
            "redirect_uri":  REDIRECT_URI,
            "scope":         SCOPE,
            "state":         state,
        })
        auth_url = f"{AUTH_URL}?{params}"
        print(f"[spotify] Opening browser for authorization...")
        webbrowser.open(auth_url)

        # Local server to catch callback
        code_holder = [None]
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                qp     = urllib.parse.parse_qs(parsed.query)
                if "code" in qp:
                    code_holder[0] = qp["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h2>Authorized! You can close this tab.</h2>")
            def log_message(self, *a): pass

        server = http.server.HTTPServer(("localhost", 8888), Handler)
        server.timeout = 60
        server.handle_request()

        if not code_holder[0]:
            print("[spotify] Authorization failed — no code received.")
            return False

        # Exchange code for tokens
        creds = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()).decode()
        data  = urllib.parse.urlencode({
            "grant_type":   "authorization_code",
            "code":         code_holder[0],
            "redirect_uri": REDIRECT_URI,
        }).encode()
        req   = urllib.request.Request(TOKEN_URL, data=data,
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"})
        resp  = json.loads(urllib.request.urlopen(req, timeout=8).read())
        self._access_token  = resp["access_token"]
        self._refresh_token = resp["refresh_token"]
        self._token_expiry  = time.time() + resp.get("expires_in", 3600) - 60
        self._save_tokens()
        self._available = True
        print("[spotify] ✅ Setup complete! Tokens saved.")
        return True


# ── CLI setup ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--setup", action="store_true")
    args = p.parse_args()

    if args.setup:
        cfg = _load_config()
        if not cfg.get("spotify_client_id"):
            cid = input("Paste your Spotify Client ID: ").strip()
            sec = input("Paste your Spotify Client Secret: ").strip()
            cfg["spotify_client_id"]     = cid
            cfg["spotify_client_secret"] = sec
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            print("[spotify] Credentials saved to config.json")

        api = SpotifyAPI()
        if api.run_auth_flow():
            print(f"[spotify] Current track: {api.get_current_track_name()}")
        else:
            print("[spotify] Setup failed.")