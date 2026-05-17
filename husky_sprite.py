"""
husky_sprite.py — Husky form (Dog evolution Level 5)

Visual changes from base dog:
  - Blue/grey fur palette instead of brown
  - Blue eyes (striking husky eyes)
  - Thicker build, fluffier tail
  - White chest/belly patch
  - Slightly larger ears
"""

from PIL import Image, ImageDraw
import sprite as base   # reuse all base dog drawing logic

SIZE = 96

# ── Husky colour palette ──────────────────────────────────────────────────
C = {
    "bg":      (0,   0,   0,   0),    # transparent
    "fur":     (110, 120, 135, 255),  # blue-grey fur
    "fur_dark":(70,  80,  100, 255),  # darker grey for markings
    "fur_lite":(200, 210, 220, 255),  # light chest/belly
    "eye":     (80,  160, 220, 255),  # husky blue eyes ← key feature
    "pupil":   (20,  20,  40,  255),
    "eye_shine":(255,255,255,255),
    "nose":    (30,  25,  30,  255),
    "mouth":   (60,  40,  40,  255),
    "collar":  (180, 60,  60,  255),  # red collar
    "tag":     (220, 180, 40,  255),
    "tongue":  (220, 100, 120, 255),
    "tail":    (200, 210, 220, 255),  # fluffy white tail tip
    "tail_base":(100, 110, 130, 255),
    "outline": (40,  45,  60,  255),
    "shadow":  (0,   0,   0,   40),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), C["bg"])


def make_husky_frame(f=0, look="forward", expr="normal", by=0,
                     wagging=False, sitting=False, night=False):
    """Draw a single husky frame — reuses base structure, different colors."""
    img = _new()
    d   = ImageDraw.Draw(img)

    # Shadow
    d.ellipse([30, 78+by, 66, 86+by], fill=C["shadow"])

    # Body — blue-grey with white belly
    d.ellipse([22, 38+by, 74, 72+by], fill=C["fur"])
    d.ellipse([28, 36+by, 68, 68+by], fill=C["fur"])
    # White belly patch
    d.ellipse([32, 48+by, 64, 70+by], fill=C["fur_lite"])

    # Tail — fluffy, curled up (husky trait)
    ox = {"left": -3, "right": 3, "forward": 0}[look]
    swing = int(4 * (0.5 - abs((f % 8) / 8 - 0.5))) if wagging else 0
    tail_pts = [
        (60, 50+by), (70+swing, 36+by), (74+swing, 24+by),
        (68+swing, 18+by), (60+swing, 22+by), (58+swing, 30+by),
        (62, 42+by)
    ]
    d.polygon(tail_pts, fill=C["tail_base"])
    # White tail tip
    tip_pts = [(68+swing, 18+by), (60+swing, 22+by), (58+swing, 30+by),
               (64+swing, 26+by)]
    d.polygon(tip_pts, fill=C["tail"])

    # Legs
    leg_y = 64+by
    if sitting:
        # Sitting pose
        d.ellipse([26, leg_y-4, 42, leg_y+14], fill=C["fur"])
        d.ellipse([54, leg_y-4, 70, leg_y+14], fill=C["fur"])
    else:
        phase = (f % 6) / 6 * 3.14159
        import math
        swing_l = int(6 * math.sin(phase))
        swing_r = int(6 * math.sin(phase + 3.14159))
        # Back legs
        d.ellipse([24, leg_y+swing_l, 36, leg_y+16+swing_l], fill=C["fur_dark"])
        d.ellipse([58, leg_y+swing_r, 70, leg_y+16+swing_r], fill=C["fur_dark"])
        # Front legs
        d.ellipse([30, leg_y-swing_l, 42, leg_y+14-swing_l], fill=C["fur"])
        d.ellipse([52, leg_y-swing_r, 64, leg_y+14-swing_r], fill=C["fur"])

    # Head
    d.ellipse([26+ox, 14+by, 70+ox, 52+by], fill=C["fur"])
    # White face mask (husky marking)
    d.ellipse([30+ox, 20+by, 66+ox, 48+by], fill=C["fur_lite"])
    # Dark top of head
    d.ellipse([28+ox, 12+by, 68+ox, 34+by], fill=C["fur_dark"])

    # Ears — larger, pointed (husky ears)
    d.polygon([(28+ox, 20+by), (22+ox, 2+by), (36+ox, 14+by)], fill=C["fur_dark"])
    d.polygon([(66+ox, 20+by), (72+ox, 2+by), (58+ox, 14+by)], fill=C["fur_dark"])
    # Inner ear
    d.polygon([(29+ox, 18+by), (24+ox, 6+by), (34+ox, 14+by)], fill=C["fur"])

    # Blue eyes ← the signature husky feature
    eye_ox = {"left": -4, "right": 4, "forward": 0}[look]
    # Left eye
    d.ellipse([32+ox+eye_ox, 26+by, 42+ox+eye_ox, 34+by], fill=C["eye"])
    d.ellipse([35+ox+eye_ox, 27+by, 40+ox+eye_ox, 33+by], fill=C["pupil"])
    d.ellipse([36+ox+eye_ox, 27+by, 38+ox+eye_ox, 29+by], fill=C["eye_shine"])
    # Right eye
    d.ellipse([54+ox+eye_ox, 26+by, 64+ox+eye_ox, 34+by], fill=C["eye"])
    d.ellipse([57+ox+eye_ox, 27+by, 62+ox+eye_ox, 33+by], fill=C["pupil"])
    d.ellipse([58+ox+eye_ox, 27+by, 60+ox+eye_ox, 29+by], fill=C["eye_shine"])

    # Nose
    d.ellipse([44+ox, 36+by, 52+ox, 42+by], fill=C["nose"])
    d.ellipse([46+ox, 37+by, 49+ox, 39+by], fill=(80, 80, 100, 255))

    # Mouth
    if expr == "happy" or expr == "normal":
        d.arc([42+ox, 38+by, 54+ox, 46+by], 0, 180, fill=C["mouth"], width=2)
    if expr == "happy":
        d.ellipse([44+ox, 40+by, 52+ox, 48+by], fill=C["tongue"])

    # Collar
    d.rectangle([32+ox, 46+by, 64+ox, 52+by], fill=C["collar"])
    d.ellipse([46+ox, 48+by, 50+ox, 52+by], fill=C["tag"])

    return img


def _seq(count, **kwargs):
    return [make_husky_frame(f=i, **kwargs) for i in range(count)]


# ── Animation builders ────────────────────────────────────────────────────

def husky_idle(night=False):
    out = []
    for f in range(8):
        by = 1 if f in (2, 3, 6, 7) else 0
        out.append(make_husky_frame(f=f, by=by, look="forward"))
    return out

def husky_walk(direction="right"):
    out = []
    for f in range(8):
        by = -1 if f in (1, 2, 5, 6) else 0
        look = "right" if direction == "right" else "left"
        frame = make_husky_frame(f=f, by=by, look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def husky_sleep(night=False):
    out = []
    for f in range(6):
        by = 8
        img = _new()
        d   = ImageDraw.Draw(img)
        d.ellipse([20, 54+by, 76, 74+by], fill=C["fur"])
        d.ellipse([18, 56+by, 50, 72+by], fill=C["fur_lite"])
        d.ellipse([20, 46+by, 56, 68+by], fill=C["fur"])
        # Curled tail over body
        d.arc([40, 44+by, 70, 64+by], 200, 360, fill=C["tail"], width=4)
        # Sleeping head
        d.ellipse([16, 48+by, 52, 70+by], fill=C["fur"])
        d.ellipse([18, 50+by, 46, 66+by], fill=C["fur_lite"])
        # Closed eyes
        breathe = 1 if f > 2 else 0
        d.line([(22, 56+by+breathe), (30, 54+by+breathe)], fill=C["fur_dark"], width=2)
        d.line([(34, 54+by+breathe), (42, 56+by+breathe)], fill=C["fur_dark"], width=2)
        out.append(img)
    return out

def husky_happy():
    out = []
    for f in range(8):
        by = -2 if f in (1, 2, 3) else 0
        out.append(make_husky_frame(f=f, by=by, expr="happy", wagging=True))
    return out

def husky_curious(direction="right"):
    out = []
    for f in range(6):
        look = "right" if direction == "right" else "left"
        by   = 1 if f % 2 else 0
        frame = make_husky_frame(f=f, by=by, look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def husky_sit():
    return [make_husky_frame(f=0, sitting=True) for _ in range(4)]

def husky_jump():
    arc = [0, -4, -8, -12, -14, -12, -8, -4, 0]
    out = []
    for by in arc:
        out.append(make_husky_frame(f=0, by=by, expr="happy"))
    return out

def husky_spin():
    looks = ["forward", "right", "right", "forward", "left", "left", "forward", "right"]
    return [make_husky_frame(f=i, look=l, expr="happy")
            for i, l in enumerate(looks)]

def husky_dance():
    out = []
    for f in range(12):
        by   = -3 if f % 4 < 2 else 0
        look = "right" if f % 4 < 2 else "left"
        out.append(make_husky_frame(f=f, by=by, look=look, expr="happy", wagging=True))
    return out

def husky_love():
    out = []
    for f in range(8):
        img = make_husky_frame(f=f, expr="happy", wagging=True)
        d   = ImageDraw.Draw(img)
        # Draw little hearts
        hx = 14 + (f % 3) * 2
        hy = 10 - f * 1
        if f < 6:
            d.ellipse([hx,    hy,   hx+6, hy+6], fill=(220, 60, 80, 200))
            d.ellipse([hx+4,  hy,   hx+10,hy+6], fill=(220, 60, 80, 200))
            d.polygon([(hx, hy+4), (hx+5, hy+10), (hx+10, hy+4)],
                      fill=(220, 60, 80, 200))
        out.append(img)
    return out

def make_husky_icon(size=32):
    img = make_husky_frame(f=0, look="forward", expr="normal")
    return img.resize((size, size), Image.LANCZOS)


# ── Animation registry ────────────────────────────────────────────────────

ANIMATIONS = {
    "idle":          husky_idle(),
    "idle_night":    husky_idle(night=True),
    "walk_right":    husky_walk("right"),
    "walk_left":     husky_walk("left"),
    "sleep":         husky_sleep(),
    "sleep_night":   husky_sleep(night=True),
    "curious_right": husky_curious("right"),
    "curious_left":  husky_curious("left"),
    "happy":         husky_happy(),
    "surprised":     husky_happy(),
    "jump":          husky_jump(),
    "spin":          husky_spin(),
    "dance":         husky_dance(),
    "wiggle":        husky_dance(),
    "backflip":      husky_jump(),
    "leg_shake":     husky_idle(),
    "panting":       husky_happy(),
    "bone_walk":     husky_walk("right"),
    "bone_sit":      husky_sit(),
    "sneeze":        husky_idle(),
    "hiccup":        husky_idle(),
    "dizzy":         husky_spin(),
    "love":          husky_love(),
    "angry":         husky_idle(),
    "moonwalk":      husky_walk("left"),
    "roll_over":     husky_idle(),
    "petting":       husky_happy(),
    "wag":           husky_happy(),
    "shake_no":      husky_curious("right"),
    "sit_beg":       husky_sit(),
}

TRICK_ANIMS = ["jump", "spin", "dance", "wiggle", "love", "wag"]
