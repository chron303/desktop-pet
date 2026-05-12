"""
speech.py — Speech bubble + full context-aware quip library.
Covers: idle, night, morning, hungry, fed, trick, levelup,
        spotify, vscode, browser, youtube, github, meeting,
        afk_return, reminder, excited, starving.
"""
import tkinter as tk, random, datetime

QUIPS = {
    "idle":    ["...zzzz...","Bored now 🥱","Pet me!","Wanna play?",
                "I see you!","Squirrel?!","Is it treat time?","*yawns*",
                "What are we doing?","Hello? Anyone there?","...*sniff*..."],
    # Cat idle quips — aloof, dignified
    "idle_cat":["...","I am thinking.","*slow blink*","...whatever.",
                "hmm.","You may acknowledge me.","I suppose.",
                "*stares at nothing*","I was not sleeping. I was meditating."],
    # Dragon idle quips — majestic, dramatic
    "idle_dragon":["*surveys the realm*","I am magnificent.","Behold. 🐉",
                   "The mightiest of all pixels.","*breathes smoke*",
                   "All shall know my glory.","I require tribute.","...scales gleaming."],
    "night":   ["It's late...","You should sleep! 🌙","Still here?",
                "Midnight grind?","*yawns loudly*","We're night owls! 🦉",
                "The moon is pretty 🌕","Don't burn out!"],
    "morning": ["Good morning! ☀️","Rise and shine!","New day new treats!",
                "Ready to play! 🐾","Morning!! Morning!! Morning!!",
                "Did you sleep well?","Best part of waking up = me 🐶"],
    "hungry":  ["...food?","Treat? Please? 🥺","My tummy is rumbling!",
                "Feed me hooman!","I did tricks for THIS?!",
                "*stares at bowl*","I'm a little hungry...","Excuse me... 🍖"],
    "starving":["I'M STARVING 😭","FOOD. NOW. PLEASE.","*dramatic collapse*",
                "I may not survive...","Have mercy!! 🥺","FEED👏ME👏NOW👏"],
    "fed":     ["NOM NOM NOM 😋","SO GOOD! Thank you!","Mmmmm delicious!",
                "Bone appetite! 🦴","*happy tail wags*","You're the BEST!",
                "10/10 would eat again","*licks lips*"],
    "trick":   ["Did you see that?! 🌟","Ta-daaa! 🎉","I'm amazing!",
                "Tip your dog please 🐾","5 stars ⭐⭐⭐⭐⭐",
                "Round of applause?","And THAT is how it's done!",
                "I should be on TV 📺"],
    "levelup": ["Level up!! 💪🎉","New tricks unlocked! 🎓",
                "Look how much I've grown! 🌟","I am EVOLVING",
                "XP goes brrr ⬆️","Getting stronger every day!"],
    "spotify": ["Good taste! 🎵","I love this song!","Bop detected 🎶",
                "Dance with me! 🕺","*tail wags to beat*","🎵 *vibing* 🎵",
                "Turn it up!!","This SLAPS 🎧"],
    "vscode":  ["Debugging again? 🐛","Don't forget to commit!",
                "Need a break? 👀","git commit -m 'good boy'",
                "Stack Overflow time?","You've got this! 💪",
                "I believe in you!","That's definitely a feature, not a bug 😅",
                "rm -rf node_modules? 💀"],
    "browser": ["Procrastinating? 👀","Whatcha looking at?",
                "Ooh, research!","Back to work? 😅",
                "I'm watching you...","Just 5 more minutes?"],
    "youtube": ["YouTube time? 🎬","Ooh what are we watching?",
                "Popcorn time! 🍿","Skip the ad! Skip it!",
                "Is it a dog video? 🐶","I want to watch too!"],
    "github":  ["Open source! ❤️","PR review time?","Stars go up! ⭐",
                "Merge conflict? 😬","Push it! Push it!",
                "I'd give your repo 5 stars 🌟"],
    "meeting": ["Shhh... meeting... 🤫","Look professional!",
                "You've got this 💼","Camera on? You look great!",
                "I'll be quiet... 🐾","*sits very still*",
                "Is it over yet? 😬"],
    "afk_return":["HEY YOU'RE BACK!! 🎉","I MISSED YOU SO MUCH!",
                  "Where did you GO?!","*runs in circles*",
                  "Never leave me again 🥺","You came back!! 😭❤️"],
    "reminder": ["Break time! Stretch! 🧘","Stand up for a minute!",
                 "Water break? 💧","Rest your eyes! 👁️",
                 "Deep breath time 🌿","Quick walk? I'll join! 🐾",
                 "You've been working hard!","Hydrate!! 💧"],
    "excited":  ["YAAAAY!! 🎉","THIS IS THE BEST DAY!","WOW WOW WOW!!",
                 "*zooms around*","!!!!!!!","SO HAPPY RN 🐶"],
}


class SpeechBubble:
    SHOW_MS = 3800

    def __init__(self, root):
        self._root     = root
        self._win      = None
        self._after_id = None

    def say(self, msg: str, pet_x: int, pet_y: int):
        self._dismiss()
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.wm_attributes("-topmost", True)
        self._win.wm_attributes("-alpha", 0.96)
        self._win.configure(bg="#FFFDE7")

        outer = tk.Frame(self._win, bg="#FFFDE7",
                         highlightthickness=1, highlightbackground="#CCBB88")
        outer.pack(padx=1, pady=1)
        tk.Label(outer, text=msg, bg="#FFFDE7", fg="#222211",
                 font=("Segoe UI", 10), padx=10, pady=7,
                 wraplength=220).pack()

        tail = tk.Canvas(self._win, bg="#FFFDE7", width=16, height=9,
                         highlightthickness=0)
        tail.create_polygon(0,0, 16,0, 8,9, fill="#FFFDE7", outline="#CCBB88")
        tail.pack()

        self._win.update_idletasks()
        bw = self._win.winfo_width()
        bh = self._win.winfo_height()
        bx = pet_x + 48 - bw//2
        by = pet_y - bh - 2
        self._win.geometry(f"+{max(4,bx)}+{max(4,by)}")
        self._after_id = self._root.after(self.SHOW_MS, self._dismiss)

    def _dismiss(self):
        if self._after_id:
            try: self._root.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None
        if self._win:
            try: self._win.destroy()
            except Exception: pass
            self._win = None

    @staticmethod
    def pick(context: str = "idle", pet_type: str = "dog") -> str:
        h = datetime.datetime.now().hour
        # time-of-day override for idle
        if context == "idle":
            if h >= 23 or h <= 4:  context = "night"
            elif 5 <= h <= 9:      context = "morning"
            elif pet_type == "cat":    context = "idle_cat"
            elif pet_type == "dragon": context = "idle_dragon"
        pool = QUIPS.get(context, QUIPS["idle"])
        return random.choice(pool)