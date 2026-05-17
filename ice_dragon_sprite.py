"""
ice_dragon_sprite.py — Ice Dragon form (Dragon evolution Level 10)

Visual changes:
  - Ice blue/white scales
  - Piercing cyan eyes
  - Ice crystal spikes on back and tail
  - Frost breath instead of fire
  - Crystalline wing pattern
"""

from PIL import Image, ImageDraw
import math

SIZE = 96

D = {
    "bg":        (0,   0,   0,   0),
    "scale":     (100, 160, 200, 255),  # ice blue
    "scale_dark":(60,  100, 150, 255),  # deep blue
    "scale_lite":(180, 220, 240, 255),  # pale ice
    "belly":     (220, 240, 255, 255),  # near white belly
    "wing":      (140, 200, 240, 160),  # translucent ice wing
    "wing_bone": (80,  140, 190, 255),
    "crystal":   (200, 230, 255, 230),  # ice crystal
    "crystal2":  (160, 210, 240, 200),
    "eye":       (0,   220, 255, 255),  # bright cyan eyes
    "pupil":     (0,   40,  80,  255),
    "eye_glow":  (100, 230, 255, 150),
    "frost":     (200, 230, 255, 180),  # frost breath
    "frost2":    (160, 200, 240, 120),
    "horn":      (180, 220, 245, 255),  # ice horns
    "nose":      (60,  100, 140, 255),
    "mouth":     (40,  80,  120, 255),
    "fang":      (220, 240, 255, 255),  # ice fangs
    "shadow":    (0,   0,   0,   40),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), D["bg"])


def _ice_crystal(d, cx, cy, size, rotation=0):
    """Draw a hexagonal ice crystal."""
    pts = []
    for i in range(6):
        angle = rotation + i * 60
        rad   = angle * math.pi / 180
        pts.append((cx + size * math.cos(rad),
                    cy + size * math.sin(rad)))
    d.polygon(pts, fill=D["crystal"])
    # Inner crystal
    inner = []
    for i in range(6):
        angle = rotation + i * 60
        rad   = angle * math.pi / 180
        inner.append((cx + (size//2) * math.cos(rad),
                      cy + (size//2) * math.sin(rad)))
    d.polygon(inner, fill=D["crystal2"])


def _frost_breath(d, cx, cy, f):
    """Draw frost/ice breath effect."""
    for i in range(6):
        angle  = -20 + i * 8
        rad    = angle * math.pi / 180
        dist   = 10 + f * 4
        alpha  = max(0, 200 - f * 20)
        px     = cx + int(dist * math.cos(rad))
        py     = cy + int(dist * math.sin(rad))
        r      = max(1, 5 - i)
        d.ellipse([px-r, py-r, px+r, py+r],
                  fill=(*D["frost"][:3], alpha))
    # Snowflake particles
    for i in range(3):
        sx = cx + (f * 3 + i * 8)
        sy = cy + int(4 * math.sin(f + i))
        d.ellipse([sx-2, sy-2, sx+2, sy+2], fill=D["crystal"])


def make_ice_dragon_frame(f=0, look="forward", expr="normal", by=0,
                           breathing=False, flying=False):
    img = _new()
    d   = ImageDraw.Draw(img)

    ox = {"left": -4, "right": 4, "forward": 0}[look]

    # Shadow — blue tinted
    d.ellipse([28, 80+by, 68, 88+by], fill=(0, 30, 60, 40))

    # Wings — crystalline, translucent
    flap = int(8 * math.sin(f * 0.8)) if flying else int(2 * math.sin(f * 0.5))
    wing_l = [(34+ox, 42+by), (8+ox, 18+by-flap),
              (4+ox, 34+by-flap), (18+ox, 50+by)]
    d.polygon(wing_l, fill=D["wing"])
    # Crystal pattern on wing
    d.line([(34+ox, 42+by), (8+ox, 18+by-flap)], fill=D["wing_bone"], width=2)
    d.line([(8+ox, 18+by-flap), (18+ox, 34+by-flap//2)],
           fill=D["wing_bone"], width=1)
    wing_r = [(62+ox, 42+by), (88+ox, 18+by-flap),
              (92+ox, 34+by-flap), (78+ox, 50+by)]
    d.polygon(wing_r, fill=D["wing"])
    d.line([(62+ox, 42+by), (88+ox, 18+by-flap)], fill=D["wing_bone"], width=2)

    # Body
    d.ellipse([24, 38+by, 72, 72+by], fill=D["scale"])
    d.ellipse([26, 36+by, 70, 68+by], fill=D["scale"])
    d.ellipse([30, 46+by, 66, 70+by], fill=D["belly"])
    # Back ice spikes
    for i in range(5):
        sx = 26 + i * 9
        _ice_crystal(d, sx, 34+by, 5, rotation=i*15)

    # Tail with ice crystal tip
    swing = int(4 * math.sin(f * 0.7))
    tail_pts = [(64, 56+by), (74+swing, 48+by), (80+swing, 38+by),
                (78+swing, 28+by)]
    d.line(tail_pts, fill=D["scale_dark"], width=6)
    _ice_crystal(d, 78+swing, 26+by, 8, rotation=f*5)

    # Legs
    sl = int(5 * math.sin(f / 6 * 2 * math.pi))
    d.ellipse([26, 66+by+sl, 40, 82+by+sl], fill=D["scale_dark"])
    d.ellipse([58, 66+by-sl, 72, 82+by-sl], fill=D["scale_dark"])

    # Head
    d.ellipse([26+ox, 14+by, 70+ox, 54+by], fill=D["scale"])
    d.ellipse([28+ox, 12+by, 68+ox, 36+by], fill=D["scale_dark"])
    d.ellipse([34+ox, 34+by, 62+ox, 54+by], fill=D["scale_lite"])

    # Ice horns — long, crystalline
    d.polygon([(30+ox, 18+by), (16+ox, -8+by), (36+ox, 12+by)],
              fill=D["horn"])
    d.polygon([(66+ox, 18+by), (80+ox, -8+by), (60+ox, 12+by)],
              fill=D["horn"])
    _ice_crystal(d, 16+ox, -8+by, 4, rotation=30)
    _ice_crystal(d, 80+ox, -8+by, 4, rotation=60)

    # Cyan glowing eyes
    eye_ox = {"left": -5, "right": 5, "forward": 0}[look]
    for ex, ey_b in [(32, 26), (56, 26)]:
        d.ellipse([ex+ox+eye_ox-2, ey_b+by-2,
                   ex+ox+eye_ox+12, ey_b+by+10], fill=D["eye_glow"])
        d.ellipse([ex+ox+eye_ox, ey_b+by,
                   ex+ox+eye_ox+10, ey_b+by+8], fill=D["eye"])
        d.ellipse([ex+ox+eye_ox+3, ey_b+by+1,
                   ex+ox+eye_ox+7, ey_b+by+7], fill=D["pupil"])
        # Glint
        d.ellipse([ex+ox+eye_ox+2, ey_b+by+1,
                   ex+ox+eye_ox+4, ey_b+by+3], fill=(255, 255, 255, 200))

    # Nose
    d.ellipse([44+ox, 38+by, 52+ox, 44+by], fill=D["nose"])
    # Frost from nostrils
    if f % 3 < 2:
        d.ellipse([43+ox, 33+by, 47+ox, 38+by], fill=D["frost2"])
        d.ellipse([50+ox, 32+by, 54+ox, 37+by], fill=D["frost2"])

    # Mouth
    ny = 46
    if breathing:
        _frost_breath(d, 62+ox, ny+4+by, f-4)
    else:
        d.arc([38+ox, ny+by, 58+ox, ny+8+by], 0, 180,
              fill=D["mouth"], width=2)
        d.polygon([(40+ox, ny+2+by), (42+ox, ny+7+by), (44+ox, ny+2+by)],
                  fill=D["fang"])
        d.polygon([(52+ox, ny+2+by), (54+ox, ny+7+by), (56+ox, ny+2+by)],
                  fill=D["fang"])

    return img


def ice_idle():
    return [make_ice_dragon_frame(f=f, by=(1 if f in (2,3,6,7) else 0))
            for f in range(8)]

def ice_walk(direction="right"):
    out = []
    for f in range(8):
        look  = "right" if direction == "right" else "left"
        frame = make_ice_dragon_frame(f=f, by=(-1 if f in (1,2,5,6) else 0),
                                      look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def ice_sleep():
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        by  = 10
        d.ellipse([18, 52+by, 78, 74+by], fill=D["scale"])
        d.ellipse([16, 54+by, 52, 72+by], fill=D["belly"])
        d.ellipse([18, 44+by, 60, 68+by], fill=D["scale_dark"])
        breathe = 1 if f > 2 else 0
        d.line([(22, 54+by+breathe),(32, 52+by+breathe)],
               fill=D["scale_lite"], width=2)
        d.line([(36, 52+by+breathe),(46, 54+by+breathe)],
               fill=D["scale_lite"], width=2)
        if f % 2:
            _ice_crystal(d, 50, 58+by, 4, rotation=f*20)
        out.append(img)
    return out

def ice_breath():
    return [make_ice_dragon_frame(f=f, breathing=(f > 3))
            for f in range(12)]

def ice_happy():
    return [make_ice_dragon_frame(f=f, by=(-2 if f in (1,2,3) else 0))
            for f in range(8)]

def ice_fly():
    return [make_ice_dragon_frame(f=f, flying=True,
                                  by=(-4 if f%4 < 2 else -2))
            for f in range(12)]

def ice_spin():
    looks = ["forward","right","right","forward","left","left","forward","right"]
    return [make_ice_dragon_frame(f=i, look=l) for i,l in enumerate(looks)]

def ice_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    return [make_ice_dragon_frame(f=0, by=b) for b in arc]

def ice_curious(direction="right"):
    out = []
    for f in range(6):
        look  = "right" if direction == "right" else "left"
        frame = make_ice_dragon_frame(f=f, by=(1 if f%2 else 0), look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def make_ice_dragon_icon(size=32):
    img = make_ice_dragon_frame(f=0)
    return img.resize((size, size), Image.LANCZOS)


DRAGON_ANIMATIONS = {
    "idle":          ice_idle(),
    "idle_night":    ice_idle(),
    "walk_right":    ice_walk("right"),
    "walk_left":     ice_walk("left"),
    "sleep":         ice_sleep(),
    "sleep_night":   ice_sleep(),
    "curious_right": ice_curious("right"),
    "curious_left":  ice_curious("left"),
    "happy":         ice_happy(),
    "surprised":     ice_happy(),
    "jump":          ice_jump(),
    "spin":          ice_spin(),
    "dance":         ice_fly(),
    "wiggle":        ice_spin(),
    "backflip":      ice_jump(),
    "leg_shake":     ice_idle(),
    "panting":       ice_happy(),
    "bone_walk":     ice_walk("right"),
    "bone_sit":      ice_idle(),
    "sneeze":        ice_idle(),
    "hiccup":        ice_idle(),
    "dizzy":         ice_spin(),
    "love":          ice_happy(),
    "angry":         ice_idle(),
    "moonwalk":      ice_walk("left"),
    "roll_over":     ice_idle(),
    "petting":       ice_happy(),
    "wag":           ice_happy(),
    "shake_no":      ice_curious("right"),
    "sit_beg":       ice_idle(),
    "fire_breath":   ice_breath(),
    "fly":           ice_fly(),
    "roar":          ice_idle(),
}

DRAGON_TRICKS = ["fire_breath", "fly", "jump", "spin", "dance"]
