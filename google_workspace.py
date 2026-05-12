"""
google_workspace.py — Read-only Google Workspace integration.

Features:
  • Gmail: unread count in inbox
  • Calendar: next event today / upcoming events
  • OAuth2 flow — browser-based, tokens cached locally

Setup (one-time):
  1. Go to console.cloud.google.com
  2. Create project → Enable Gmail API + Calendar API
  3. Create OAuth2 credentials (Desktop app type)
  4. Download credentials.json → put in ascii-pet/ folder
  5. Run: python google_workspace.py --setup
     → browser opens, authorize, tokens saved to google_token.json

After setup, the pet reads your Gmail/Calendar automatically.
No credentials.json = workspace features silently disabled.
"""

import os, json, datetime, threading, time

CREDS_PATH  = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_PATH  = os.path.join(os.path.dirname(__file__), "google_token.json")
SCOPES      = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

POLL_INTERVAL_GMAIL    = 120   # seconds
POLL_INTERVAL_CALENDAR = 300   # seconds


class WorkspaceData:
    def __init__(self):
        self.unread_count   = 0
        self.unread_senders = []   # last 3 sender names
        self.next_event     = None # {"title": str, "start": datetime, "minutes_away": int}
        self.events_today   = []
        self.last_gmail_check    = 0.0
        self.last_calendar_check = 0.0
        self.available      = False
        self.error          = None


class GoogleWorkspace:
    def __init__(self):
        self._data    = WorkspaceData()
        self._service_gmail    = None
        self._service_calendar = None
        self._thread  = None
        self._running = False

        if os.path.exists(CREDS_PATH) or os.path.exists(TOKEN_PATH):
            threading.Thread(target=self._init_services, daemon=True).start()
        else:
            print("[workspace] No credentials.json — Google integration disabled.")
            print("           See google_workspace.py docstring for setup instructions.")

    def _init_services(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(CREDS_PATH):
                        self._data.error = "credentials.json missing"
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())

            self._service_gmail    = build("gmail",    "v1", credentials=creds)
            self._service_calendar = build("calendar", "v3", credentials=creds)
            self._data.available   = True
            print("[workspace] Google Workspace connected ✅")

            self._running = True
            self._poll_loop()

        except ImportError:
            print("[workspace] google-api-python-client not installed.")
            print("           Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        except Exception as e:
            print(f"[workspace] Init failed: {e}")
            self._data.error = str(e)

    def _poll_loop(self):
        while self._running:
            now = time.monotonic()
            if now - self._data.last_gmail_check > POLL_INTERVAL_GMAIL:
                self._fetch_gmail()
                self._data.last_gmail_check = now
            if now - self._data.last_calendar_check > POLL_INTERVAL_CALENDAR:
                self._fetch_calendar()
                self._data.last_calendar_check = now
            time.sleep(10)

    # ── Gmail ────────────────────────────────────────────────────────────

    def _fetch_gmail(self):
        try:
            result = self._service_gmail.users().messages().list(
                userId="me", labelIds=["INBOX","UNREAD"], maxResults=10
            ).execute()

            messages = result.get("messages", [])
            self._data.unread_count   = result.get("resultSizeEstimate", len(messages))
            self._data.unread_senders = []

            for msg in messages[:3]:
                detail = self._service_gmail.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From"]
                ).execute()
                headers = {h["name"]: h["value"]
                           for h in detail.get("payload",{}).get("headers",[])}
                sender = headers.get("From","Unknown")
                # Extract just the name part
                if "<" in sender:
                    sender = sender.split("<")[0].strip().strip('"')
                self._data.unread_senders.append(sender[:20])

        except Exception as e:
            print(f"[workspace] Gmail error: {e}")

    # ── Calendar ─────────────────────────────────────────────────────────

    def _fetch_calendar(self):
        try:
            now_dt   = datetime.datetime.utcnow()
            end_dt   = now_dt + datetime.timedelta(hours=12)
            now_str  = now_dt.isoformat() + "Z"
            end_str  = end_dt.isoformat() + "Z"

            result = self._service_calendar.events().list(
                calendarId="primary",
                timeMin=now_str,
                timeMax=end_str,
                maxResults=5,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = result.get("items", [])
            self._data.events_today = []

            for ev in events:
                start = ev["start"].get("dateTime", ev["start"].get("date",""))
                if "T" in start:
                    start_dt = datetime.datetime.fromisoformat(start.replace("Z","+00:00"))
                    # Convert to local
                    local_now = datetime.datetime.now(datetime.timezone.utc)
                    mins_away = int((start_dt - local_now).total_seconds() / 60)
                else:
                    mins_away = 9999   # all-day event

                self._data.events_today.append({
                    "title":      ev.get("summary", "Untitled"),
                    "start":      start,
                    "mins_away":  mins_away,
                    "location":   ev.get("location",""),
                })

            if self._data.events_today:
                self._data.next_event = self._data.events_today[0]
            else:
                self._data.next_event = None

        except Exception as e:
            print(f"[workspace] Calendar error: {e}")

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def is_available(self): return self._data.available

    def get_unread_count(self) -> int:
        return self._data.unread_count

    def get_unread_senders(self) -> list:
        return self._data.unread_senders

    def get_next_event(self) -> dict | None:
        return self._data.next_event

    def get_events_today(self) -> list:
        return self._data.events_today

    def get_summary(self) -> str:
        """Returns a short pet-friendly summary of workspace state."""
        parts = []
        if self._data.unread_count > 0:
            n = self._data.unread_count
            parts.append(f"{n} unread email{'s' if n>1 else ''}")
        if self._data.next_event:
            ev = self._data.next_event
            m  = ev["mins_away"]
            if m <= 15:
                parts.append(f"'{ev['title']}' in {m}min!")
            elif m <= 60:
                parts.append(f"'{ev['title']}' in {m//60}h{m%60}m")
        return ", ".join(parts) if parts else ""

    def stop(self):
        self._running = False


# ── CLI setup helper ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--setup", action="store_true", help="Run OAuth2 setup flow")
    args = p.parse_args()

    if args.setup:
        print("Setting up Google Workspace OAuth2...")
        ws = GoogleWorkspace()
        time.sleep(10)   # give it time to complete
        if ws.is_available:
            print("✅ Setup complete! Token saved to google_token.json")
            print(f"   Unread emails: {ws.get_unread_count()}")
            ev = ws.get_next_event()
            if ev:
                print(f"   Next event: {ev['title']} in {ev['mins_away']}min")
        else:
            print(f"❌ Setup failed: {ws._data.error}")