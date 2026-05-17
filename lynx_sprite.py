"""
lynx_sprite.py — Lynx form (Cat evolution Level 5)

Visual changes from base cat:
  - Tufted ears (signature lynx feature)
  - Spotted/tabby pattern on body
  - Longer legs, more athletic build
  - Green/yellow eyes
  - Shorter tail with black tip
  - Slightly larger, more muscular
"""

from PIL import Image, ImageDraw
import math

SIZE = 96

C = {
    "bg":        (0,   0,   0,   0),
    "fur":       (180, 150, 110, 255),  # tawny/tan fur
    "fur_dark":  (120, 90,  60,  255),  # darker markings
    "fur_lite":  (220, 200, 170, 255),  # lighter belly
    "spot":      (100, 75,  45,  200),  # spots
    "eye":       (100, 180, 60,  255),  # bright green eyes
    "pupil":     (20,  15,  10,  255),
    "eye_shine": (255, 255, 255, 255),
    "nose":      (200, 120, 120, 255),
    "mouth":     (80,  50,  50,  255),
    "whisker":   (220, 210, 200, 200),
    "ear_inner": (220, 160, 160, 255),
    "ear_tuft":  (60,  50,  40,  255),   # dark ear tuft
    "tail":      (160, 130, 90,  255),
    "tail_tip":  (20,  15,  10,  255),   # black tail tip
    "paw":       (160, 130, 100, 255),
    "shadow":    (0,   0,   0,   40),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), C["bg"])


def _spots(d, cx, cy, count, offset=0):
    """Draw leopard-style spots."""
    positions = [
        (cx-12, cy-4), (cx+8, cy-6), (cx-6, cy+8),
        (cx+14, cy+4), (cx-16, cy+10), (cx+6, cy+12),
    ]
    for i, (sx, sy) in enumerate(positions[:count]):
        d.ellipse([sx+offset, sy, sx+offset+6, sy+5], fill=C["spot"])


def make_lynx_frame(f=0, look="forward", expr="normal", by=0,
                    sitting=False, pouncing=False):
    img = _new()
    d   = ImageDraw.Draw(img)

    ox = {"left": -4, "right": 4, "forward": 0}[look]

    # Shadow
    d.ellipse([28, 80+by, 68, 88+by], fill=C["shadow"])

    # Body — athletic, slightly longer
    d.ellipse([20, 38+by, 76, 72+by], fill=C["fur"])
    d.ellipse([22, 36+by, 74, 68+by], fill=C["fur"])
    # Belly — lighter
    d.ellipse([30, 48+by, 66, 70+by], fill=C["fur_lite"])
    # Spots on body
    _spots(d, 48, 50+by, 4)

    # Short bobbed tail with black tip
    swing = int(6 * math.sin(f * 0.8))
    tail_pts = [(62, 54+by), (72+swing, 46+by), (76+swing, 40+by),
                (74+swing, 36+by)]
    d.line(tail_pts, fill=C["tail"], width=5)
    # Black tip
    d.ellipse([71+swing, 32+by, 78+swing, 39+by], fill=C["tail_tip"])

    # Legs — longer than base cat
    leg_y = 66+by
    if sitting:
        d.ellipse([24, leg_y-4, 40, leg_y+18], fill=C["fur_dark"])
        d.ellipse([56, leg_y-4, 72, leg_y+18], fill=C["fur_dark"])
        d.ellipse([26, leg_y+10, 40, leg_y+20], fill=C["paw"])
        d.ellipse([58, leg_y+10, 72, leg_y+20], fill=C["paw"])
    elif pouncing:
        d.ellipse([16, leg_y-10, 32, leg_y+8], fill=C["fur_dark"])
        d.ellipse([62, leg_y-8, 78, leg_y+6], fill=C["fur_dark"])
        d.ellipse([28, leg_y+4, 44, leg_y+18], fill=C["fur_dark"])
        d.ellipse([50, leg_y+2, 66, leg_y+16], fill=C["fur_dark"])
    else:
        sl = int(7 * math.sin(f / 6 * 2 * math.pi))
        sr = int(7 * math.sin(f / 6 * 2 * math.pi + math.pi))
        d.ellipse([22, leg_y+sl, 36, leg_y+18+sl], fill=C["fur_dark"])
        d.ellipse([60, leg_y+sr, 74, leg_y+18+sr], fill=C["fur_dark"])
        d.ellipse([30, leg_y-sl, 44, leg_y+14-sl], fill=C["fur"])
        d.ellipse([52, leg_y-sr, 66, leg_y+14-sr], fill=C["fur"])
        d.ellipse([30, leg_y+10-sl, 42, leg_y+18-sl], fill=C["paw"])
        d.ellipse([54, leg_y+10-sr, 66, leg_y+18-sr], fill=C["paw"])

    # Head
    d.ellipse([26+ox, 14+by, 70+ox, 54+by], fill=C["fur"])
    d.ellipse([28+ox, 16+by, 68+ox, 50+by], fill=C["fur"])
    # Face marking — darker forehead
    d.ellipse([30+ox, 14+by, 66+ox, 34+by], fill=C["fur_dark"])
    # Cheek tufts
    d.ellipse([20+ox, 30+by, 34+ox, 46+by], fill=C["fur_lite"])
    d.ellipse([62+ox, 30+by, 76+ox, 46+by], fill=C["fur_lite"])

    # Ears — tufted (KEY lynx feature)
    # Ear base
    d.polygon([(30+ox, 20+by), (26+ox, 4+by), (42+ox, 16+by)],
              fill=C["fur_dark"])
    d.polygon([(66+ox, 20+by), (70+ox, 4+by), (54+ox, 16+by)],
              fill=C["fur_dark"])
    # Inner ear
    d.polygon([(31+ox, 18+by), (28+ox, 8+by), (40+ox, 16+by)],
              fill=C["ear_inner"])
    d.polygon([(65+ox, 18+by), (68+ox, 8+by), (56+ox, 16+by)],
              fill=C["ear_inner"])
    # EAR TUFTS — lynx signature
    d.polygon([(26+ox, 4+by), (24+ox, -4+by), (30+ox, 2+by)],
              fill=C["ear_tuft"])
    d.polygon([(70+ox, 4+by), (72+ox, -4+by), (66+ox, 2+by)],
              fill=C["ear_tuft"])

    # Green eyes
    eye_ox = {"left": -4, "right": 4, "forward": 0}[look]
    for ex, ey_b in [(32, 26), (54, 26)]:
        d.ellipse([ex+ox+eye_ox, ey_b+by, ex+ox+eye_ox+10, ey_b+by+8],
                  fill=C["eye"])
        # Slit pupil (cat eyes)
        d.ellipse([ex+ox+eye_ox+3, ey_b+by+1, ex+ox+eye_ox+7, ey_b+by+7],
                  fill=C["pupil"])
        d.ellipse([ex+ox+eye_ox+2, ey_b+by+1, ex+ox+eye_ox+4, ey_b+by+3],
                  fill=C["eye_shine"])

    # Nose — pink
    d.ellipse([44+ox, 36+by, 52+ox, 42+by], fill=C["nose"])
    d.ellipse([46+ox, 37+by, 49+ox, 39+by], fill=(240, 180, 180, 255))

    # Mouth
    d.arc([42+ox, 38+by, 54+ox, 46+by], 0, 180, fill=C["mouth"], width=2)
    if expr == "happy":
        d.arc([42+ox, 38+by, 54+ox, 46+by], 0, 180,
              fill=C["mouth"], width=2)

    # Whiskers — longer than cat
    wx = 48+ox
    wy = 40+by
    d.line([(wx-20, wy-2), (wx-4, wy)], fill=C["whisker"], width=1)
    d.line([(wx-20, wy+2), (wx-4, wy+2)], fill=C["whisker"], width=1)
    d.line([(wx+4, wy), (wx+20, wy-2)], fill=C["whisker"], width=1)
    d.line([(wx+4, wy+2), (wx+20, wy+2)], fill=C["whisker"], width=1)

    return img


def lynx_idle():
    return [make_lynx_frame(f=f, by=(1 if f in (2,3,6,7) else 0))
            for f in range(8)]

def lynx_walk(direction="right"):
    out = []
    for f in range(8):
        look  = "right" if direction == "right" else "left"
        frame = make_lynx_frame(f=f, by=(-1 if f in (1,2,5,6) else 0),
                                look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def lynx_sleep():
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        by  = 10
        d.ellipse([20, 54+by, 76, 74+by], fill=C["fur"])
        d.ellipse([18, 56+by, 50, 72+by], fill=C["fur_lite"])
        d.ellipse([20, 46+by, 58, 68+by], fill=C["fur_dark"])
        # Spots visible
        _spots(d, 38, 58+by, 3)
        breathe = 1 if f > 2 else 0
        d.line([(24, 56+by+breathe),(34, 54+by+breathe)],
               fill=C["fur_lite"], width=2)
        d.line([(38, 54+by+breathe),(48, 56+by+breathe)],
               fill=C["fur_lite"], width=2)
        out.append(img)
    return out

def lynx_pounce():
    """Unique lynx animation — hunting pounce."""
    frames = []
    # Crouch
    for f in range(4):
        frames.append(make_lynx_frame(f=f, by=4, sitting=True))
    # Launch
    for by in [2, -2, -6, -10, -8, -4, 0]:
        frames.append(make_lynx_frame(f=0, by=by, pouncing=True))
    # Land
    for f in range(3):
        frames.append(make_lynx_frame(f=f, by=2))
    return frames

def lynx_happy():
    return [make_lynx_frame(f=f, by=(-2 if f in (1,2,3) else 0), expr="happy")
            for f in range(8)]

def lynx_sit():
    return [make_lynx_frame(f=0, sitting=True) for _ in range(4)]

def lynx_curious(direction="right"):
    out = []
    for f in range(6):
        look  = "right" if direction == "right" else "left"
        frame = make_lynx_frame(f=f, by=(1 if f%2 else 0), look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def lynx_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    return [make_lynx_frame(f=0, by=b, pouncing=(b < -4)) for b in arc]

def lynx_spin():
    looks = ["forward","right","right","forward","left","left","forward","right"]
    return [make_lynx_frame(f=i, look=l, expr="happy") for i,l in enumerate(looks)]

def make_lynx_icon(size=32):
    img = make_lynx_frame(f=0)
    return img.resize((size, size), Image.LANCZOS)


CAT_ANIMATIONS = {
    "idle":          lynx_idle(),
    "idle_night":    lynx_idle(),
    "walk_right":    lynx_walk("right"),
    "walk_left":     lynx_walk("left"),
    "sleep":         lynx_sleep(),
    "sleep_night":   lynx_sleep(),
    "curious_right": lynx_curious("right"),
    "curious_left":  lynx_curious("left"),
    "happy":         lynx_happy(),
    "surprised":     lynx_happy(),
    "jump":          lynx_jump(),
    "spin":          lynx_spin(),
    "dance":         lynx_happy(),
    "wiggle":        lynx_spin(),
    "backflip":      lynx_jump(),
    "leg_shake":     lynx_idle(),
    "panting":       lynx_happy(),
    "bone_walk":     lynx_walk("right"),
    "bone_sit":      lynx_sit(),
    "sneeze":        lynx_idle(),
    "hiccup":        lynx_idle(),
    "dizzy":         lynx_spin(),
    "love":          lynx_happy(),
    "angry":         lynx_idle(),
    "moonwalk":      lynx_walk("left"),
    "roll_over":     lynx_idle(),
    "petting":       lynx_happy(),
    "wag":           lynx_happy(),
    "shake_no":      lynx_curious("right"),
    "sit_beg":       lynx_sit(),
    "pounce":        lynx_pounce(),
}

CAT_TRICKS = ["jump", "spin", "dance", "pounce", "wag"]
