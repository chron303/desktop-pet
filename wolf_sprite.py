"""
wolf_sprite.py — Wolf form (Dog evolution Level 10)

Visual changes from Husky:
  - Dark grey/black fur — imposing presence
  - Yellow/amber eyes — wolf eyes
  - Sharper, more angular features
  - Larger build, more muscular
  - Scar on left eye (battle-hardened)
  - More upright posture
"""

from PIL import Image, ImageDraw
import math

SIZE = 96

C = {
    "bg":       (0,   0,   0,   0),
    "fur":      (55,  55,  65,  255),   # dark grey
    "fur_dark": (30,  30,  38,  255),   # near black
    "fur_lite": (90,  90,  105, 255),   # lighter underbelly
    "fur_mid":  (70,  70,  82,  255),
    "eye":      (200, 160, 30,  255),   # amber/yellow wolf eyes
    "pupil":    (15,  10,  5,   255),
    "eye_shine":(255, 255, 200, 255),
    "scar":     (140, 80,  80,  200),   # scar color
    "nose":     (20,  15,  20,  255),
    "mouth":    (40,  30,  30,  255),
    "fang":     (230, 225, 220, 255),   # white fangs
    "collar":   (80,  20,  20,  255),   # dark red collar
    "tag":      (160, 130, 20,  255),
    "tongue":   (200, 80,  100, 255),
    "tail":     (45,  45,  55,  255),
    "outline":  (20,  20,  28,  255),
    "shadow":   (0,   0,   0,   60),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), C["bg"])


def make_wolf_frame(f=0, look="forward", expr="normal", by=0,
                    wagging=False, sitting=False, howling=False):
    img = _new()
    d   = ImageDraw.Draw(img)

    # Shadow — larger than dog (bigger creature)
    d.ellipse([26, 78+by, 70, 88+by], fill=C["shadow"])

    # Body — stockier, more powerful
    d.ellipse([18, 36+by, 78, 74+by], fill=C["fur"])
    d.ellipse([22, 34+by, 74, 70+by], fill=C["fur"])
    # Underbelly lighter
    d.ellipse([30, 48+by, 66, 72+by], fill=C["fur_lite"])
    # Back darker
    d.ellipse([20, 34+by, 76, 52+by], fill=C["fur_dark"])

    # Tail — thick, held lower than husky
    ox_body = {"left": -3, "right": 3, "forward": 0}[look]
    swing   = int(5 * (0.5 - abs((f % 8)/8 - 0.5))) if wagging else -2
    tail_pts = [(58, 54+by), (68+swing, 46+by), (74+swing, 38+by),
                (72+swing, 30+by), (66+swing, 34+by), (62, 44+by)]
    d.polygon(tail_pts, fill=C["fur_dark"])
    d.polygon([(72+swing, 30+by), (66+swing, 34+by), (68+swing, 40+by)],
              fill=C["fur_lite"])

    # Legs — powerful
    leg_y = 64+by
    if sitting:
        d.ellipse([22, leg_y-6, 40, leg_y+16], fill=C["fur_dark"])
        d.ellipse([56, leg_y-6, 74, leg_y+16], fill=C["fur_dark"])
    else:
        sl = int(7 * math.sin(f / 6 * 2 * math.pi))
        sr = int(7 * math.sin(f / 6 * 2 * math.pi + math.pi))
        d.ellipse([20, leg_y+sl, 34, leg_y+18+sl], fill=C["fur_dark"])
        d.ellipse([60, leg_y+sr, 74, leg_y+18+sr], fill=C["fur_dark"])
        d.ellipse([28, leg_y-sl, 42, leg_y+14-sl], fill=C["fur"])
        d.ellipse([52, leg_y-sr, 66, leg_y+14-sr], fill=C["fur"])

    ox = {"left": -4, "right": 4, "forward": 0}[look]

    # Head — more angular, larger
    if howling:
        # Head tilted up for howl
        d.ellipse([24+ox, 8+by, 72+ox, 48+by], fill=C["fur"])
        d.ellipse([26+ox, 10+by, 70+ox, 44+by], fill=C["fur_mid"])
        d.ellipse([28+ox, 8+by, 68+ox, 30+by], fill=C["fur_dark"])
    else:
        d.ellipse([24+ox, 14+by, 72+ox, 54+by], fill=C["fur"])
        d.ellipse([26+ox, 16+by, 70+ox, 50+by], fill=C["fur_mid"])
        d.ellipse([26+ox, 12+by, 70+ox, 34+by], fill=C["fur_dark"])

    # Snout — longer, more prominent
    d.ellipse([36+ox, 34+by, 60+ox, 52+by], fill=C["fur_lite"])

    # Ears — larger, more pointed
    d.polygon([(26+ox, 20+by), (18+ox, -2+by), (38+ox, 14+by)], fill=C["fur_dark"])
    d.polygon([(70+ox, 20+by), (78+ox, -2+by), (58+ox, 14+by)], fill=C["fur_dark"])
    d.polygon([(27+ox, 18+by), (21+ox, 4+by), (36+ox, 14+by)], fill=C["fur_mid"])

    # Amber eyes
    eye_ox = {"left": -5, "right": 5, "forward": 0}[look]
    ey = 28 if not howling else 22
    # Left eye
    d.ellipse([30+ox+eye_ox, ey+by, 42+ox+eye_ox, ey+10+by], fill=C["eye"])
    d.ellipse([33+ox+eye_ox, ey+1+by, 40+ox+eye_ox, ey+9+by], fill=C["pupil"])
    d.ellipse([34+ox+eye_ox, ey+1+by, 36+ox+eye_ox, ey+3+by], fill=C["eye_shine"])
    # Right eye
    d.ellipse([54+ox+eye_ox, ey+by, 66+ox+eye_ox, ey+10+by], fill=C["eye"])
    d.ellipse([57+ox+eye_ox, ey+1+by, 64+ox+eye_ox, ey+9+by], fill=C["pupil"])
    d.ellipse([58+ox+eye_ox, ey+1+by, 60+ox+eye_ox, ey+3+by], fill=C["eye_shine"])

    # Scar over left eye
    d.line([(34+ox+eye_ox, ey-2+by), (40+ox+eye_ox, ey+8+by)],
           fill=C["scar"], width=2)

    # Nose — larger
    d.ellipse([42+ox, 36+by, 54+ox, 44+by], fill=C["nose"])
    d.ellipse([44+ox, 37+by, 47+ox, 39+by], fill=(50, 50, 70, 255))

    # Mouth — show fangs
    ny = 48 if not howling else 38
    d.arc([40+ox, ny+by, 56+ox, ny+8+by], 0, 180, fill=C["mouth"], width=2)
    # Fangs
    d.polygon([(42+ox, ny+2+by), (44+ox, ny+6+by), (46+ox, ny+2+by)],
              fill=C["fang"])
    d.polygon([(50+ox, ny+2+by), (52+ox, ny+6+by), (54+ox, ny+2+by)],
              fill=C["fang"])

    if howling:
        # Open mouth for howl
        d.ellipse([40+ox, 34+by, 56+ox, 50+by], fill=C["nose"])
        d.ellipse([42+ox, 36+by, 54+ox, 48+by], fill=(20, 10, 10, 255))
        d.polygon([(42+ox, 36+by), (44+ox, 42+by), (46+ox, 36+by)], fill=C["fang"])
        d.polygon([(50+ox, 36+by), (52+ox, 42+by), (54+ox, 36+by)], fill=C["fang"])

    # Collar — dark red
    d.rectangle([30+ox, 48+by, 66+ox, 54+by], fill=C["collar"])
    d.ellipse([45+ox, 50+by, 51+ox, 56+by], fill=C["tag"])

    return img


def _seq(count, **kw):
    return [make_wolf_frame(f=i, **kw) for i in range(count)]


def wolf_idle(night=False):
    return [make_wolf_frame(f=f, by=(1 if f in (2,3,6,7) else 0))
            for f in range(8)]

def wolf_walk(direction="right"):
    out = []
    for f in range(8):
        by   = -1 if f in (1,2,5,6) else 0
        look = "right" if direction == "right" else "left"
        frame = make_wolf_frame(f=f, by=by, look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def wolf_sleep(night=False):
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        by  = 10
        d.ellipse([16, 52+by, 80, 74+by], fill=C["fur"])
        d.ellipse([14, 54+by, 46, 72+by], fill=C["fur_lite"])
        d.ellipse([16, 44+by, 58, 68+by], fill=C["fur_dark"])
        breathe = 1 if f > 2 else 0
        d.line([(20, 54+by+breathe), (30, 52+by+breathe)], fill=C["fur_lite"], width=2)
        d.line([(34, 52+by+breathe), (44, 54+by+breathe)], fill=C["fur_lite"], width=2)
        out.append(img)
    return out

def wolf_howl():
    """Unique wolf animation — howling at the moon."""
    out = []
    for f in range(12):
        head_up = f > 3
        img = make_wolf_frame(f=f, howling=head_up,
                              by=(-4 if head_up else 0))
        d = ImageDraw.Draw(img)
        if head_up and f > 6:
            # Draw moon
            d.ellipse([2, 2, 18, 18], fill=(220, 220, 180, 180))
            # Sound waves
            alpha = int(180 * (f - 6) / 6)
            for r in range(3):
                d.arc([8-r*6, 8-r*6, 24+r*6, 24+r*6],
                      270, 360, fill=(200, 200, 160, max(0, alpha - r*40)),
                      width=2)
        out.append(img)
    return out

def wolf_happy():
    return [make_wolf_frame(f=f, by=(-2 if f in (1,2,3) else 0),
                            expr="happy", wagging=True)
            for f in range(8)]

def wolf_curious(direction="right"):
    out = []
    for f in range(6):
        look  = "right" if direction == "right" else "left"
        frame = make_wolf_frame(f=f, by=(1 if f%2 else 0), look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def wolf_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    return [make_wolf_frame(f=0, by=b, expr="happy") for b in arc]

def wolf_spin():
    looks = ["forward","right","right","forward","left","left","forward","right"]
    return [make_wolf_frame(f=i, look=l, expr="happy") for i,l in enumerate(looks)]

def wolf_sit():
    return [make_wolf_frame(f=0, sitting=True) for _ in range(4)]

def wolf_dance():
    out = []
    for f in range(12):
        by   = -3 if f%4 < 2 else 0
        look = "right" if f%4 < 2 else "left"
        out.append(make_wolf_frame(f=f, by=by, look=look, wagging=True))
    return out

def make_wolf_icon(size=32):
    img = make_wolf_frame(f=0, look="forward")
    return img.resize((size, size), Image.LANCZOS)


ANIMATIONS = {
    "idle":          wolf_idle(),
    "idle_night":    wolf_idle(night=True),
    "walk_right":    wolf_walk("right"),
    "walk_left":     wolf_walk("left"),
    "sleep":         wolf_sleep(),
    "sleep_night":   wolf_sleep(night=True),
    "curious_right": wolf_curious("right"),
    "curious_left":  wolf_curious("left"),
    "happy":         wolf_happy(),
    "surprised":     wolf_happy(),
    "jump":          wolf_jump(),
    "spin":          wolf_spin(),
    "dance":         wolf_dance(),
    "wiggle":        wolf_dance(),
    "backflip":      wolf_jump(),
    "leg_shake":     wolf_idle(),
    "panting":       wolf_happy(),
    "bone_walk":     wolf_walk("right"),
    "bone_sit":      wolf_sit(),
    "sneeze":        wolf_idle(),
    "hiccup":        wolf_idle(),
    "dizzy":         wolf_spin(),
    "love":          wolf_happy(),
    "angry":         wolf_idle(),
    "moonwalk":      wolf_walk("left"),
    "roll_over":     wolf_idle(),
    "petting":       wolf_happy(),
    "wag":           wolf_happy(),
    "shake_no":      wolf_curious("right"),
    "sit_beg":       wolf_sit(),
    "howl":          wolf_howl(),     # unique wolf animation
}

TRICK_ANIMS = ["jump", "spin", "dance", "wiggle", "howl", "wag"]
