"""
fire_dragon_sprite.py — Fire Dragon form (Dragon evolution Level 5)

Visual changes from base dragon:
  - Deep red/orange scales instead of green
  - Glowing orange eyes
  - Flame effects on body and tail tip
  - More aggressive expression
  - Brighter wing membranes
"""

from PIL import Image, ImageDraw
import math

SIZE = 96

D = {
    "bg":        (0,   0,   0,   0),
    "scale":     (160, 40,  20,  255),   # deep red scales
    "scale_dark":(100, 20,  10,  255),   # darker red
    "scale_lite":(220, 80,  30,  255),   # orange highlights
    "belly":     (220, 140, 60,  255),   # orange-gold belly
    "wing":      (180, 60,  20,  200),   # dark red wing membrane
    "wing_bone": (130, 30,  10,  255),   # wing bone
    "eye":       (255, 160, 0,   255),   # glowing orange eyes
    "pupil":     (80,  20,  0,   255),
    "eye_glow":  (255, 220, 100, 180),   # eye glow effect
    "flame":     (255, 180, 0,   220),   # flame color
    "flame2":    (255, 100, 0,   180),   # inner flame
    "horn":      (120, 30,  10,  255),
    "nose":      (80,  20,  10,  255),
    "mouth":     (60,  20,  10,  255),
    "fang":      (230, 220, 200, 255),
    "spike":     (140, 40,  10,  255),
    "shadow":    (0,   0,   0,   50),
}


def _new():
    return Image.new("RGBA", (SIZE, SIZE), D["bg"])


def _flame(d, cx, cy, size, f, color1, color2):
    """Draw a flame effect."""
    flicker = int(3 * math.sin(f * 1.5))
    pts = [
        (cx, cy + size),
        (cx - size//2 + flicker, cy + size//3),
        (cx - size//3, cy - size//3),
        (cx + flicker, cy - size),
        (cx + size//3, cy - size//3),
        (cx + size//2 + flicker, cy + size//3),
    ]
    d.polygon(pts, fill=color1)
    inner = [(cx + flicker, cy + size//2),
             (cx - size//4, cy),
             (cx + flicker, cy - size//2),
             (cx + size//4, cy)]
    d.polygon(inner, fill=color2)


def make_fire_dragon_frame(f=0, look="forward", expr="normal", by=0,
                            breathing=False, flying=False):
    img = _new()
    d   = ImageDraw.Draw(img)

    ox = {"left": -4, "right": 4, "forward": 0}[look]

    # Shadow
    d.ellipse([28, 80+by, 68, 88+by], fill=D["shadow"])

    # Wings
    flap = int(8 * math.sin(f * 0.8)) if flying else int(2 * math.sin(f * 0.5))
    # Left wing
    wing_l = [(34+ox, 42+by),
              (10+ox, 20+by-flap),
              (6+ox,  36+by-flap),
              (18+ox, 50+by)]
    d.polygon(wing_l, fill=D["wing"])
    d.line(wing_l[:2], fill=D["wing_bone"], width=2)
    # Right wing
    wing_r = [(62+ox, 42+by),
              (86+ox, 20+by-flap),
              (90+ox, 36+by-flap),
              (78+ox, 50+by)]
    d.polygon(wing_r, fill=D["wing"])
    d.line(wing_r[:2], fill=D["wing_bone"], width=2)

    # Body
    d.ellipse([24, 38+by, 72, 72+by], fill=D["scale"])
    d.ellipse([26, 36+by, 70, 68+by], fill=D["scale"])
    # Belly plates
    d.ellipse([32, 46+by, 64, 70+by], fill=D["belly"])
    # Back spikes - fire colored
    for i in range(4):
        sx = 30 + i * 10
        d.polygon([(sx, 36+by), (sx+4, 24+by-i), (sx+8, 36+by)],
                  fill=D["spike"])

    # Tail with flame tip
    swing = int(4 * math.sin(f * 0.7))
    tail_pts = [(64, 56+by), (74+swing, 48+by), (80+swing, 40+by),
                (78+swing, 32+by), (72+swing, 36+by)]
    d.polygon(tail_pts, fill=D["scale_dark"])
    # Flame at tail tip
    _flame(d, 76+swing, 30+by, 8, f, D["flame"], D["flame2"])

    # Legs
    leg_y = 66+by
    sl = int(5 * math.sin(f / 6 * 2 * math.pi))
    d.ellipse([26, leg_y+sl, 40, leg_y+16+sl], fill=D["scale_dark"])
    d.ellipse([58, leg_y-sl, 72, leg_y+16-sl], fill=D["scale_dark"])

    # Head
    d.ellipse([26+ox, 14+by, 70+ox, 54+by], fill=D["scale"])
    d.ellipse([28+ox, 12+by, 68+ox, 36+by], fill=D["scale_dark"])
    # Snout - more aggressive
    d.ellipse([34+ox, 34+by, 62+ox, 54+by], fill=D["scale_lite"])

    # Horns - curved back (more demonic)
    d.polygon([(32+ox, 16+by), (20+ox, -4+by), (36+ox, 10+by)],
              fill=D["horn"])
    d.polygon([(64+ox, 16+by), (76+ox, -4+by), (60+ox, 10+by)],
              fill=D["horn"])
    # Horn flames
    _flame(d, 20+ox, -4+by, 6, f, D["flame"], D["flame2"])
    _flame(d, 76+ox, -4+by, 6, f, D["flame"], D["flame2"])

    # Glowing orange eyes
    eye_ox = {"left": -5, "right": 5, "forward": 0}[look]
    for ex, ey_base in [(32, 26), (56, 26)]:
        # Glow
        d.ellipse([ex+ox+eye_ox-2, ey_base+by-2,
                   ex+ox+eye_ox+12, ey_base+by+12], fill=D["eye_glow"])
        # Eye
        d.ellipse([ex+ox+eye_ox, ey_base+by,
                   ex+ox+eye_ox+10, ey_base+by+8], fill=D["eye"])
        # Slit pupil
        d.ellipse([ex+ox+eye_ox+3, ey_base+by+1,
                   ex+ox+eye_ox+7, ey_base+by+7], fill=D["pupil"])

    # Nose
    d.ellipse([44+ox, 38+by, 52+ox, 44+by], fill=D["nose"])
    # Smoke from nostrils
    if f % 4 < 2:
        d.ellipse([44+ox, 34+by, 47+ox, 38+by], fill=(80, 80, 80, 120))
        d.ellipse([50+ox, 33+by, 53+ox, 37+by], fill=(80, 80, 80, 100))

    # Mouth with fangs
    ny = 46
    if breathing:
        # Fire breath
        d.ellipse([36+ox, ny+by, 60+ox, ny+12+by], fill=D["nose"])
        _flame(d, 48+ox, ny+6+by, 16, f, D["flame"], D["flame2"])
    else:
        d.arc([38+ox, ny+by, 58+ox, ny+8+by], 0, 180,
              fill=D["mouth"], width=2)
        # Visible fangs
        d.polygon([(40+ox, ny+2+by), (42+ox, ny+7+by), (44+ox, ny+2+by)],
                  fill=D["fang"])
        d.polygon([(52+ox, ny+2+by), (54+ox, ny+7+by), (56+ox, ny+2+by)],
                  fill=D["fang"])

    return img


def fire_idle():
    return [make_fire_dragon_frame(f=f, by=(1 if f in (2,3,6,7) else 0))
            for f in range(8)]

def fire_walk(direction="right"):
    out = []
    for f in range(8):
        look  = "right" if direction == "right" else "left"
        frame = make_fire_dragon_frame(f=f, by=(-1 if f in (1,2,5,6) else 0),
                                       look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def fire_sleep():
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
        # Ember glow while sleeping
        if f % 2:
            d.ellipse([40, 60+by, 50, 68+by], fill=(255, 100, 0, 60))
        out.append(img)
    return out

def fire_breath():
    return [make_fire_dragon_frame(f=f, breathing=(f > 3))
            for f in range(12)]

def fire_happy():
    return [make_fire_dragon_frame(f=f, by=(-2 if f in (1,2,3) else 0),
                                   expr="happy")
            for f in range(8)]

def fire_fly():
    return [make_fire_dragon_frame(f=f, flying=True,
                                   by=(-4 if f % 4 < 2 else -2))
            for f in range(12)]

def fire_spin():
    looks = ["forward","right","right","forward","left","left","forward","right"]
    return [make_fire_dragon_frame(f=i, look=l) for i,l in enumerate(looks)]

def fire_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    return [make_fire_dragon_frame(f=0, by=b, expr="happy") for b in arc]

def fire_curious(direction="right"):
    out = []
    for f in range(6):
        look  = "right" if direction == "right" else "left"
        frame = make_fire_dragon_frame(f=f, by=(1 if f%2 else 0), look=look)
        if direction == "left":
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        out.append(frame)
    return out

def make_fire_dragon_icon(size=32):
    img = make_fire_dragon_frame(f=0)
    return img.resize((size, size), Image.LANCZOS)


DRAGON_ANIMATIONS = {
    "idle":          fire_idle(),
    "idle_night":    fire_idle(),
    "walk_right":    fire_walk("right"),
    "walk_left":     fire_walk("left"),
    "sleep":         fire_sleep(),
    "sleep_night":   fire_sleep(),
    "curious_right": fire_curious("right"),
    "curious_left":  fire_curious("left"),
    "happy":         fire_happy(),
    "surprised":     fire_happy(),
    "jump":          fire_jump(),
    "spin":          fire_spin(),
    "dance":         fire_fly(),
    "wiggle":        fire_spin(),
    "backflip":      fire_jump(),
    "leg_shake":     fire_idle(),
    "panting":       fire_happy(),
    "bone_walk":     fire_walk("right"),
    "bone_sit":      fire_idle(),
    "sneeze":        fire_idle(),
    "hiccup":        fire_idle(),
    "dizzy":         fire_spin(),
    "love":          fire_happy(),
    "angry":         fire_idle(),
    "moonwalk":      fire_walk("left"),
    "roll_over":     fire_idle(),
    "petting":       fire_happy(),
    "wag":           fire_happy(),
    "shake_no":      fire_curious("right"),
    "sit_beg":       fire_idle(),
    "fire_breath":   fire_breath(),
    "fly":           fire_fly(),
    "roar":          fire_idle(),
}

DRAGON_TRICKS = ["fire_breath", "fly", "jump", "spin", "dance"]
