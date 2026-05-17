"""
panther_sprite.py — Panther form (Cat evolution Level 10)

Visual changes from Lynx:
  - All black fur with subtle sheen
  - Glowing amber/gold eyes
  - Sleek, powerful build — no spots visible
  - Long elegant tail
  - Silent, predatory grace
  - Unique: shadow clone ability animation
"""

from PIL import Image, ImageDraw
import math

SIZE = 96

C = {
    "bg":        (0,   0,   0,   0),
    "fur":       (25,  20,  30,  255),   # near black
    "fur_dark":  (10,  8,   15,  255),   # pure black
    "fur_sheen": (50,  40,  60,  255),   # subtle purple sheen
    "fur_lite":  (40,  35,  50,  255),   # barely lighter belly
    "eye":       (220, 160, 20,  255),   # amber/gold eyes
    "pupil":     (10,  5,   0,   255),
    "eye_glow":  (255, 200, 50,  150),   # eye glow
    "eye_shine": (255, 255, 200, 220),
    "nose":      (80,  50,  60,  255),
    "mouth":     (60,  40,  50,  255),
    "fang":      (200, 195, 185, 255),
    "whisker":   (180, 170, 160, 160),
    "claw":      (180, 170, 150, 200),
    "shadow_clone": (40, 30, 50, 120),   # ghost/shadow clone
    "shadow":    (0,   0,   0,   50),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), C["bg"])


def _sheen(d, x, y, w, h):
    """Draw subtle fur sheen highlight."""
    d.ellipse([x, y, x+w, y+h], fill=C["fur_sheen"])


def make_panther_frame(f=0, look="forward", expr="normal", by=0,
                       sitting=False, stalking=False, phantom=False):
    img = _new()
    d   = ImageDraw.Draw(img)

    ox = {"left": -4, "right": 4, "forward": 0}[look]

    # Phantom mode — draw ghost trail
    if phantom:
        ghost = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
        gd    = ImageDraw.Draw(ghost)
        gd.ellipse([18+8, 38+by+4, 78+8, 72+by+4], fill=C["shadow_clone"])
        img = Image.alpha_composite(img, ghost)
        d   = ImageDraw.Draw(img)

    # Shadow — barely visible (panther is shadow)
    d.ellipse([28, 80+by, 68, 88+by], fill=(0, 0, 0, 30))

    # Body — sleek and powerful
    d.ellipse([18, 38+by, 78, 72+by], fill=C["fur"])
    d.ellipse([20, 36+by, 76, 68+by], fill=C["fur"])
    # Subtle belly
    d.ellipse([28, 48+by, 68, 70+by], fill=C["fur_lite"])
    # Sheen highlights on shoulders
    _sheen(d, 22, 40+by, 20, 12)
    _sheen(d, 58, 40+by, 20, 12)

    # Long elegant tail
    swing = int(8 * math.sin(f * 0.6))
    tail_pts = [
        (60, 56+by), (70+swing, 44+by),
        (78+swing, 32+by), (82+swing, 22+by),
        (80+swing, 18+by)
    ]
    d.line(tail_pts, fill=C["fur_dark"], width=5)
    d.line(tail_pts, fill=C["fur_sheen"], width=2)
    # Tail tip curl
    d.arc([76+swing, 12+by, 86+swing, 22+by], 0, 270,
          fill=C["fur"], width=4)

    # Legs — long, muscular
    leg_y = 66+by
    if sitting:
        d.ellipse([22, leg_y-6, 40, leg_y+20], fill=C["fur_dark"])
        d.ellipse([56, leg_y-6, 74, leg_y+20], fill=C["fur_dark"])
        d.ellipse([22, leg_y-6, 40, leg_y+20], fill=C["fur"])
        d.ellipse([56, leg_y-6, 74, leg_y+20], fill=C["fur"])
        # Claws
        for cx2 in [24, 28, 32, 36]:
            d.ellipse([cx2, leg_y+18, cx2+3, leg_y+22], fill=C["claw"])
        for cx2 in [58, 62, 66, 70]:
            d.ellipse([cx2, leg_y+18, cx2+3, leg_y+22], fill=C["claw"])
    elif stalking:
        # Low crouched walk
        d.ellipse([18, leg_y+2, 34, leg_y+18], fill=C["fur_dark"])
        d.ellipse([60, leg_y+2, 76, leg_y+18], fill=C["fur_dark"])
        d.ellipse([30, leg_y-2, 46, leg_y+14], fill=C["fur"])
        d.ellipse([50, leg_y-2, 66, leg_y+14], fill=C["fur"])
    else:
        sl = int(8 * math.sin(f / 6 * 2 * math.pi))
        sr = int(8 * math.sin(f / 6 * 2 * math.pi + math.pi))
        d.ellipse([20, leg_y+sl, 36, leg_y+20+sl], fill=C["fur_dark"])
        d.ellipse([60, leg_y+sr, 76, leg_y+20+sr], fill=C["fur_dark"])
        d.ellipse([28, leg_y-sl, 44, leg_y+14-sl], fill=C["fur"])
        d.ellipse([52, leg_y-sr, 68, leg_y+14-sr], fill=C["fur"])

    # Head — angular, predatory
    d.ellipse([26+ox, 14+by, 70+ox, 54+by], fill=C["fur"])
    d.ellipse([28+ox, 12+by, 68+ox, 36+by], fill=C["fur_dark"])
    # Sheen on forehead
    _sheen(d, 34+ox, 14+by, 28, 14)
    # Cheeks
    d.ellipse([22+ox, 30+by, 36+ox, 46+by], fill=C["fur_lite"])
    d.ellipse([60+ox, 30+by, 74+ox, 46+by], fill=C["fur_lite"])

    # Small rounded ears (panther has smaller ears than lynx)
    d.ellipse([28+ox, 10+by, 42+ox, 22+by], fill=C["fur_dark"])
    d.ellipse([54+ox, 10+by, 68+ox, 22+by], fill=C["fur_dark"])
    d.ellipse([30+ox, 12+by, 40+ox, 20+by], fill=C["fur"])
    d.ellipse([56+ox, 12+by, 66+ox, 20+by], fill=C["fur"])

    # Glowing amber eyes
    eye_ox = {"left": -4, "right": 4, "forward": 0}[look]
    for ex, ey_b in [(32, 26), (54, 26)]:
        # Glow
        d.ellipse([ex+ox+eye_ox-3, ey_b+by-2,
                   ex+ox+eye_ox+13, ey_b+by+10], fill=C["eye_glow"])
        # Eye
        d.ellipse([ex+ox+eye_ox, ey_b+by,
                   ex+ox+eye_ox+10, ey_b+by+8], fill=C["eye"])
        # Slit pupil
        d.ellipse([ex+ox+eye_ox+3, ey_b+by+1,
                   ex+ox+eye_ox+7, ey_b+by+7], fill=C["pupil"])
        # Shine
        d.ellipse([ex+ox+eye_ox+2, ey_b+by+1,
                   ex+ox+eye_ox+5, ey_b+by+4], fill=C["eye_shine"])

    # Nose
    d.ellipse([44+ox, 36+by, 52+ox, 42+by], fill=C["nose"])

    # Mouth — subtle, showing one fang
    d.arc([42+ox, 38+by, 54+ox, 46+by], 0, 180, fill=C["mouth"], width=2)
    if expr in ("angry", "surprised"):
        d.polygon([(42+ox, 40+by), (44+ox, 46+by), (46+ox, 40+by)],
                  fill=C["fang"])

    # Whiskers — thin, elegant
    wx, wy = 48+ox, 40+by
    for dy in [-2, 0, 2]:
        d.line([(wx-18, wy+dy), (wx-4, wy+dy//2)],
               fill=C["whisker"], width=1)
        d.line([(wx+4, wy+dy//2), (wx+18, wy+dy)],
               fill=C["whisker"], width=1)

    return img


def _shadow_frame(base_frame: Image.Image, offset: int) -> Image.Image:
    """Create ghost/shadow clone effect."""
    result = base_frame.copy()
    ghost  = base_frame.copy()
    # Tint ghost purple
    tint = Image.new("RGBA", ghost.size, (60, 20, 80, 100))
    ghost = Image.alpha_composite(ghost, tint)
    # Offset ghost
    canvas = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    canvas.paste(ghost, (offset, 0), ghost)
    return Image.alpha_composite(canvas, result)


def panther_idle():
    return [make_panther_frame(f=f, by=(1 if f in (2,3,6,7) else 0))
            for f in range(8)]

def panther_walk(direction="right"):
    out = []
    for f in range(8):
        look  = "right" if direction == "right" else "left"
        frame = make_panther_frame(f=f, by=(-1 if f in (1,2,5,6) else 0),
                                   look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def panther_stalk():
    """Unique panther animation — low stealthy walk."""
    out = []
    for f in range(8):
        look  = "right"
        frame = make_panther_frame(f=f, by=4, stalking=True, look=look)
        out.append(frame)
    return out

def panther_shadow_clone():
    """Unique panther ability — phantom shadow trail."""
    out = []
    for f in range(12):
        base   = make_panther_frame(f=f, look="forward")
        offset = int(8 * math.sin(f * 0.8))
        frame  = _shadow_frame(base, offset)
        out.append(frame)
    return out

def panther_sleep():
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        by  = 10
        d.ellipse([18, 52+by, 80, 74+by], fill=C["fur"])
        d.ellipse([16, 54+by, 50, 72+by], fill=C["fur_lite"])
        d.ellipse([18, 44+by, 62, 68+by], fill=C["fur_dark"])
        _sheen(d, 22, 48+by, 30, 14)
        breathe = 1 if f > 2 else 0
        d.line([(22, 54+by+breathe),(34, 52+by+breathe)],
               fill=C["fur_lite"], width=2)
        d.line([(38, 52+by+breathe),(50, 54+by+breathe)],
               fill=C["fur_lite"], width=2)
        out.append(img)
    return out

def panther_happy():
    return [make_panther_frame(f=f, by=(-2 if f in (1,2,3) else 0))
            for f in range(8)]

def panther_sit():
    return [make_panther_frame(f=0, sitting=True) for _ in range(4)]

def panther_curious(direction="right"):
    out = []
    for f in range(6):
        look  = "right" if direction == "right" else "left"
        frame = make_panther_frame(f=f, by=(1 if f%2 else 0), look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def panther_jump():
    arc = [0,-4,-8,-14,-18,-14,-8,-4,0]
    return [make_panther_frame(f=0, by=b) for b in arc]

def panther_spin():
    looks = ["forward","right","right","forward","left","left","forward","right"]
    return [make_panther_frame(f=i, look=l) for i,l in enumerate(looks)]

def make_panther_icon(size=32):
    img = make_panther_frame(f=0)
    return img.resize((size, size), Image.LANCZOS)


CAT_ANIMATIONS = {
    "idle":          panther_idle(),
    "idle_night":    panther_idle(),
    "walk_right":    panther_walk("right"),
    "walk_left":     panther_walk("left"),
    "sleep":         panther_sleep(),
    "sleep_night":   panther_sleep(),
    "curious_right": panther_curious("right"),
    "curious_left":  panther_curious("left"),
    "happy":         panther_happy(),
    "surprised":     panther_happy(),
    "jump":          panther_jump(),
    "spin":          panther_spin(),
    "dance":         panther_happy(),
    "wiggle":        panther_spin(),
    "backflip":      panther_jump(),
    "leg_shake":     panther_idle(),
    "panting":       panther_happy(),
    "bone_walk":     panther_walk("right"),
    "bone_sit":      panther_sit(),
    "sneeze":        panther_idle(),
    "hiccup":        panther_idle(),
    "dizzy":         panther_spin(),
    "love":          panther_happy(),
    "angry":         panther_idle(),
    "moonwalk":      panther_walk("left"),
    "roll_over":     panther_idle(),
    "petting":       panther_happy(),
    "wag":           panther_happy(),
    "shake_no":      panther_curious("right"),
    "sit_beg":       panther_sit(),
    "stalk":         panther_stalk(),
    "shadow_clone":  panther_shadow_clone(),
    "pounce":        panther_jump(),
}

CAT_TRICKS = ["jump", "spin", "stalk", "shadow_clone", "pounce"]
