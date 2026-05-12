"""
notifications.py — Windows toast notifications.
Tries winotify, then win10toast, then falls back to Tk popup.
"""
import sys, threading

_WIN32   = sys.platform == "win32"
_toast_fn = None

def _try_winotify():
    global _toast_fn
    try:
        from winotify import Notification, audio
        def _show(title, msg, icon_path=None):
            n = Notification(app_id="Desktop Pet 🐾",
                             title=title, msg=msg, duration="short")
            n.set_audio(audio.Default, loop=False)
            n.show()
        _toast_fn = _show
        return True
    except ImportError:
        return False

def _try_win10toast():
    global _toast_fn
    try:
        from win10toast import ToastNotifier
        _t = ToastNotifier()
        def _show(title, msg, icon_path=None):
            threading.Thread(
                target=_t.show_toast,
                args=(title, msg),
                kwargs={"duration":4,"threaded":True},
                daemon=True).start()
        _toast_fn = _show
        return True
    except ImportError:
        return False

def _tk_fallback(root_getter):
    global _toast_fn
    def _show(title, msg, icon_path=None):
        root = root_getter()
        if root:
            root.after(0, lambda: _tk_popup(root, title, msg))
    _toast_fn = _show

def _tk_popup(root, title, msg):
    import tkinter as tk
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.wm_attributes("-topmost", True)
    win.wm_attributes("-alpha", 0.93)
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    win.geometry(f"280x68+{sw-292}+{sh-108}")
    win.configure(bg="#2D2D3A")
    tk.Label(win, text=f"🐾 {title}", bg="#2D2D3A", fg="white",
             font=("Segoe UI",10,"bold"), anchor="w").pack(fill="x",padx=12,pady=(8,1))
    tk.Label(win, text=msg, bg="#2D2D3A", fg="#CCCCDD",
             font=("Segoe UI",9), anchor="w", wraplength=256).pack(fill="x",padx=12)
    root.after(4000, lambda: (win.winfo_exists() and win.destroy()))
    win.bind("<Button-1>", lambda e: win.destroy())


class NotificationManager:
    def __init__(self, root_getter=None):
        self._enabled = _WIN32
        if not _WIN32:
            return
        if not _try_winotify():
            if not _try_win10toast():
                if root_getter:
                    _tk_fallback(root_getter)
                    print("[notify] Tk popup fallback  (pip install winotify for toasts)")
                else:
                    self._enabled = False
            else:
                print("[notify] win10toast active")
        else:
            print("[notify] winotify active")

    def show(self, title, message, icon=None):
        if self._enabled and _toast_fn:
            threading.Thread(target=_toast_fn,
                             args=(title, message, icon),
                             daemon=True).start()

    def email(self, count, sender=""):
        f = f" from {sender}" if sender else ""
        self.show("New Email 📧", f"{count} unread{f}")

    def meeting(self, title, minutes):
        self.show("Meeting Soon 📅", f"'{title}' in {minutes} min")

    def level_up(self, level):
        self.show("Level Up! 🎉", f"Pet reached level {level}!")

    def reminder(self, msg):
        self.show("Break Time 🧘", msg)

    def track(self, name):
        self.show("Now Playing 🎵", name)