"""
tray.py — System tray with full menu.
All Tkinter calls go through root.after() — never called directly from pystray thread.
"""
import threading

def _startup_enabled():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.QueryValueEx(k, "DesktopPet"); winreg.CloseKey(k)
        return True
    except:
        return False

def _set_startup(enabled):
    try:
        import winreg, sys, os
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        if enabled:
            path = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
            winreg.SetValueEx(k, "DesktopPet", 0, winreg.REG_SZ, path)
        else:
            try: winreg.DeleteValue(k, "DesktopPet")
            except: pass
        winreg.CloseKey(k)
    except Exception as e:
        print(f"[tray] startup: {e}")

def _build_icon(pet, img):
    import pystray
    from pystray import MenuItem as Item, Menu
    from accessories import ACCESSORIES, unlocked_accessories

    # ── All callbacks — Tkinter calls must go through after() ────────────

    def open_settings(i, it):
        pet.window.root.after(0, pet.open_settings)

    def type_command(i, it):
        pet.window.root.after(0, pet.show_command_dialog)

    def show_status(i, it):
        pet.window.root.after(0, pet.show_status_dialog)

    def toggle_follow(i, it):   pet.toggle_follow()
    def toggle_sit(i, it):      pet.toggle_sit()
    def toggle_hud(i, it):      pet.toggle_hud()
    def toggle_startup(i, it):  _set_startup(not _startup_enabled())
    def switch_dog(i, it):      pet.window.root.after(0, lambda: pet.switch_pet("dog"))
    def switch_dragon(i, it):   pet.window.root.after(0, lambda: pet.switch_pet("dragon"))
    def switch_cat(i, it):      pet.window.root.after(0, lambda: pet.switch_pet("cat"))
    def do_trick(i, it):        pet.do_trick()
    def do_feed(i, it):         pet.feed()

    def set_accessory(name):
        def fn(i, it): pet.set_accessory(name if name != "none" else None)
        return fn

    def set_color(n):
        def fn(i, it): pet.set_color(n)
        return fn

    def set_speed(s):
        def fn(i, it): pet.anim_speed = s
        return fn

    def set_reminder(m):
        def fn(i, it): pet.set_reminder(m)
        return fn

    def quit_app(i, it):
        i.stop()
        pet.window.root.after(0, pet.window.root.destroy)

    # ── Accessory submenu ────────────────────────────────────────────────
    unlocked  = unlocked_accessories(pet.state.level)
    acc_items = [Item("None", set_accessory("none"),
                       checked=lambda i: pet._active_accessory is None)]
    for name in ACCESSORIES:
        _, min_lvl = ACCESSORIES[name]
        label = name.replace("_", " ").title()
        if name in unlocked:
            acc_items.append(Item(
                label, set_accessory(name),
                checked=lambda i, n=name: pet._active_accessory == n))
        else:
            acc_items.append(Item(
                f"{label} (Lv{min_lvl} 🔒)",
                lambda i, it: None, enabled=False))

    # ── Full menu ────────────────────────────────────────────────────────
    menu = Menu(
        Item("Desktop Pet 🐾",    None,           enabled=False),
        Menu.SEPARATOR,
        Item("⚙️  Settings...",    open_settings),
        Menu.SEPARATOR,
        Item("Pet Type", Menu(
            Item("Dog 🐶",    switch_dog,    checked=lambda i: pet.pet_type=="dog"),
            Item("Dragon 🐉", switch_dragon, checked=lambda i: pet.pet_type=="dragon"),
            Item("Cat 🐱",    switch_cat,    checked=lambda i: pet.pet_type=="cat"),
        )),
        Menu.SEPARATOR,
        Item("Follow Cursor",     toggle_follow,  checked=lambda i: pet.follow_mode),
        Item("Sit / Stay",        toggle_sit,     checked=lambda i: pet.sit_mode),
        Item("Show HUD",          toggle_hud,     checked=lambda i: pet.hud_enabled),
        Item("Launch at Startup", toggle_startup, checked=lambda i: _startup_enabled()),
        Menu.SEPARATOR,
        Item("Do a Trick! 🎉",    do_trick),
        Item("Feed 🦴",           do_feed),
        Item("💬 Type a Command", type_command),
        Item("Pet Status...",     show_status),
        Menu.SEPARATOR,
        Item("Accessory 🎩", Menu(*acc_items)),
        Item("Color", Menu(
            Item("Default",   set_color("default")),
            Item("Gold ✨",   set_color("gold")),
            Item("Pink 🌸",   set_color("pink")),
            Item("Blue 💙",   set_color("blue")),
            Item("Green 🌿",  set_color("green")),
            Item("White ☁️",  set_color("white")),
        )),
        Item("Speed", Menu(
            Item("Slow   0.5x", set_speed(0.5)),
            Item("Normal 1.0x", set_speed(1.0)),
            Item("Fast   1.8x", set_speed(1.8)),
            Item("Turbo  3.0x", set_speed(3.0)),
        )),
        Item("Break Reminders", Menu(
            Item("Off",     set_reminder(0)),
            Item("20 min",  set_reminder(20)),
            Item("45 min",  set_reminder(45)),
            Item("60 min",  set_reminder(60)),
            Item("90 min",  set_reminder(90)),
        )),
        Menu.SEPARATOR,
        Item("Quit", quit_app),
    )
    return pystray.Icon("desktop-pet", img, "Desktop Pet 🐾", menu)


class TrayManager:
    def __init__(self, pet, img):
        self._pet  = pet
        self._img  = img
        self._icon = None

    def start(self):
        try:
            import pystray  # noqa
            self._icon = _build_icon(self._pet, self._img)
            threading.Thread(target=self._icon.run, daemon=True).start()
            print("[tray] Right-click the paw icon for options.")
        except ImportError:
            print("[tray] pystray not found — pip install pystray")
        except Exception as e:
            print(f"[tray] Failed to start: {e}")

    def stop(self):
        try:
            if self._icon: self._icon.stop()
        except: pass