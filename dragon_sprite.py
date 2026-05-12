"""
dragon_sprite.py — Pixel-art dragon companion sprite.

Distinct from the dog: larger head, horns, wings, spiked tail,
scaly green body, fire-breathing tricks, flying idle animation.

All drawn with Pillow — no external assets.
"""
from PIL import Image, ImageDraw
import math, random

# ── Dragon palette ────────────────────────────────────────────────────────
D = {
    "body":    ( 60, 140,  70, 255),   # forest green scales
    "body_l":  ( 90, 180, 100, 255),   # lighter scale highlight
    "belly":   (180, 220, 140, 255),   # cream/yellow belly
    "horn":    (200, 160,  30, 255),   # gold horns
    "horn_d":  (150, 110,  20, 255),   # dark horn
    "eye":     ( 20,  15,  10, 255),   # dark pupil
    "eye_w":   (255, 255, 200, 255),   # yellow sclera
    "iris":    (220,  80,  20, 255),   # orange iris
    "shine":   (255, 255, 255, 200),   # eye shine
    "wing":    ( 40, 100,  50, 200),   # wing membrane
    "wing_l":  ( 70, 150,  80, 180),   # wing highlight
    "wing_b":  ( 30,  70,  35, 255),   # wing bone/edge
    "tail":    ( 50, 120,  60, 255),   # tail
    "spike":   (200, 160,  30, 255),   # back spikes (gold)
    "mouth":   ( 30,  20,  15, 255),   # mouth line
    "tongue":  (200,  50,  50, 255),   # red tongue
    "fire_1":  (255, 200,  30, 230),   # bright yellow fire
    "fire_2":  (255, 120,  20, 200),   # orange fire
    "fire_3":  (200,  40,  10, 180),   # red fire core
    "smoke":   (180, 180, 190, 120),   # smoke puff
    "nose":    ( 30,  50,  25, 255),   # nostril
    "claw":    (180, 140,  30, 255),   # gold claws
    "shadow":  ( 20,  60,  25, 150),
    "bg":      (  0,   0,   0,   0),
}
SIZE = 96


def _new(): return Image.new("RGBA", (SIZE, SIZE), D["bg"])


# ── Core drawing helpers ──────────────────────────────────────────────────

def _shadow(d, by=0):
    cx = SIZE // 2
    d.ellipse([cx-26, SIZE-14+by, cx+26, SIZE-6+by], fill=D["shadow"])

def _tail(d, f, by, wagging=False):
    """Dragon tail — thick at base, spiked tip, curves up."""
    swing = int(math.sin(f * 0.7) * 8) if wagging else int(math.sin(f * 0.4) * 5)
    # Main tail curve
    pts = [(62,52+by), (70+swing,44+by), (76+swing,34+by),
           (80+swing,24+by), (74+swing,20+by), (68+swing,28+by),
           (64+swing,38+by), (58,50+by)]
    d.polygon(pts, fill=D["tail"])
    # Spikes along tail
    for i, (sx, sy) in enumerate([(68+swing//2, 36+by), (75+swing, 26+by)]):
        d.polygon([(sx-3, sy), (sx+3, sy), (sx, sy-7)], fill=D["spike"])

def _body(d, by):
    """Dragon body — rounder, more compact than dog, with belly."""
    # Main body
    d.ellipse([16, 44+by, 68, 76+by], fill=D["body"])
    # Belly (lighter)
    d.ellipse([24, 48+by, 60, 74+by], fill=D["belly"])
    # Scale texture (small bumps)
    d.ellipse([18, 46+by, 34, 58+by], fill=D["body_l"])
    d.ellipse([48, 46+by, 64, 56+by], fill=D["body_l"])

def _back_spikes(d, by):
    """Row of spikes along the dragon's back."""
    for sx, height in [(28,8),(36,10),(44,10),(52,8),(60,6)]:
        d.polygon([(sx-3, 44+by), (sx+3, 44+by), (sx, 44-height+by)],
                  fill=D["spike"])

def _wings(d, f, by, flap=0):
    """Small decorative wings — fold up on idle, spread on flight."""
    spread = flap + int(math.sin(f * 0.6) * 4)
    # Left wing
    d.polygon([(22, 44+by), (8-spread, 28+by), (14-spread, 48+by)],
              fill=D["wing"])
    d.line([(22, 44+by), (8-spread, 28+by)], fill=D["wing_b"], width=2)
    # Right wing
    d.polygon([(62, 44+by), (78+spread, 28+by), (70+spread, 48+by)],
              fill=D["wing"])
    d.line([(62, 44+by), (78+spread, 28+by)], fill=D["wing_b"], width=2)

def _legs(d, f, by, sit=False):
    """Short stubby dragon legs with gold claws."""
    if sit:
        d.rounded_rectangle([18,62+by,30,80+by], radius=4, fill=D["body"])
        d.rounded_rectangle([52,62+by,64,80+by], radius=4, fill=D["body"])
        for px in [19,23,27]: d.ellipse([px,76+by,px+4,82+by], fill=D["claw"])
        for px in [53,57,61]: d.ellipse([px,76+by,px+4,82+by], fill=D["claw"])
    else:
        gl = int(math.sin(f * 1.2) * 5)
        gr = int(math.sin(f * 1.2 + math.pi) * 5)
        d.rounded_rectangle([16,60+by,28,80+by+gl], radius=4, fill=D["body"])
        d.rounded_rectangle([54,60+by,66,80+by+gr], radius=4, fill=D["body"])
        for px in [17,21,25]: d.ellipse([px,76+by+gl,px+4,82+by+gl], fill=D["claw"])
        for px in [55,59,63]: d.ellipse([px,76+by+gr,px+4,82+by+gr], fill=D["claw"])

def _head(d, by):
    """Dragon head — wider, more triangular than dog."""
    # Main head
    d.ellipse([14, 10+by, 68, 54+by], fill=D["body"])
    # Snout — elongated
    d.ellipse([24, 30+by, 60, 56+by], fill=D["body_l"])
    d.ellipse([28, 34+by, 56, 54+by], fill=D["belly"])

def _horns(d, by):
    """Two curved horns on top of head."""
    # Left horn
    d.polygon([(26, 12+by), (20, -2+by), (30, 8+by)], fill=D["horn"])
    d.polygon([(26, 12+by), (22, 2+by), (28, 10+by)], fill=D["horn_d"])
    # Right horn
    d.polygon([(56, 12+by), (62, -2+by), (52, 8+by)], fill=D["horn"])
    d.polygon([(56, 12+by), (60, 2+by), (54, 10+by)], fill=D["horn_d"])

def _eyes(d, by, look="forward", expr="normal"):
    ox = {"left":-5, "right":5, "forward":0}[look]
    if expr == "sleep" or expr == "blink":
        d.arc([20+ox, 22+by, 38+ox, 34+by], 0, 180, fill=D["eye"], width=2)
        d.arc([44+ox, 22+by, 62+ox, 34+by], 0, 180, fill=D["eye"], width=2)
        return
    # Eye whites (yellow for dragon)
    d.ellipse([20+ox, 20+by, 38+ox, 36+by], fill=D["eye_w"])
    d.ellipse([44+ox, 20+by, 62+ox, 36+by], fill=D["eye_w"])
    # Orange iris
    px = {"left":-2, "right":2, "forward":0}[look]
    d.ellipse([22+ox+px, 22+by, 36+ox+px, 34+by], fill=D["iris"])
    d.ellipse([46+ox+px, 22+by, 60+ox+px, 34+by], fill=D["iris"])
    # Slit pupil (dragon!)
    d.rectangle([28+ox+px, 22+by, 31+ox+px, 34+by], fill=D["eye"])
    d.rectangle([52+ox+px, 22+by, 55+ox+px, 34+by], fill=D["eye"])
    # Shine
    d.ellipse([22+ox, 21+by, 26+ox, 25+by], fill=D["shine"])
    d.ellipse([46+ox, 21+by, 50+ox, 25+by], fill=D["shine"])
    # Angry V brows
    if expr == "angry":
        d.line([18+ox, 18+by, 38+ox, 22+by], fill=D["eye"], width=2)
        d.line([62+ox, 18+by, 44+ox, 22+by], fill=D["eye"], width=2)

def _nose(d, by):
    """Dragon nostrils."""
    d.ellipse([33, 36+by, 37, 40+by], fill=D["nose"])
    d.ellipse([45, 36+by, 49, 40+by], fill=D["nose"])

def _mouth(d, by, expr="normal", breathing=False):
    if expr in ("happy", "excited"):
        d.arc([30, 40+by, 52, 52+by], 0, 180, fill=D["mouth"], width=2)
        if expr == "excited":
            d.ellipse([36,44+by,46,52+by], fill=D["tongue"])
    elif expr == "open" or breathing:
        d.ellipse([32, 40+by, 50, 54+by], fill=D["mouth"])
        d.ellipse([34, 44+by, 48, 54+by], fill=D["tongue"])
    else:
        d.arc([34, 42+by, 48, 50+by], 0, 180, fill=D["mouth"], width=1)


# ── Frame factory ─────────────────────────────────────────────────────────

def make_dragon_frame(f=0, look="forward", expr="normal", by=0,
                      sit=False, flap=0, breathing=False, wagging=False):
    img = _new()
    d   = ImageDraw.Draw(img)
    _shadow(d, 0)
    _tail(d, f, by, wagging=wagging)
    _body(d, by)
    _back_spikes(d, by)
    _wings(d, f, by, flap=flap)
    _legs(d, f, by, sit=sit)
    _head(d, by)
    _horns(d, by)
    _eyes(d, by, look=look, expr=expr)
    _nose(d, by)
    _mouth(d, by, expr=expr, breathing=breathing)
    return img


# ── Animation builders ────────────────────────────────────────────────────

def dragon_idle():
    out = []
    for f in range(12):
        expr = "blink" if f == 8 else "normal"
        out.append(make_dragon_frame(f, expr=expr, sit=True))
    return out

def dragon_idle_night():
    out = []
    for f in range(8):
        expr = "sleep" if f > 4 else "blink"
        img  = make_dragon_frame(f, expr=expr, sit=True)
        from PIL import Image as Img
        ov = Img.new("RGBA", img.size, (0, 0, 40, 50))
        img = Img.alpha_composite(img, ov)
        out.append(img)
    return out

def dragon_walk(direction="right"):
    look = "right" if direction == "right" else "left"
    out  = []
    for f in range(8):
        dy = int(math.sin(f / 8 * math.pi * 2) * -2)
        out.append(make_dragon_frame(f * 2, look=look, by=dy))
    return out

def dragon_sleep():
    out = []
    for f in range(8):
        img = make_dragon_frame(f, expr="sleep", sit=True)
        out.append(img)
    # ZZZ drawn in particle system, not in sprite
    return out

def dragon_curious(direction="right"):
    look = direction
    out  = []
    for f in range(6):
        out.append(make_dragon_frame(f, look=look, sit=True))
    return out

def dragon_happy():
    out = []
    for f in range(8):
        dy = int(math.sin(f / 8 * math.pi * 2) * 4)
        out.append(make_dragon_frame(f, expr="excited", by=dy, wagging=True))
    return out

def dragon_surprised():
    out = []
    for f in range(6):
        dy = -3 if f < 3 else 0
        out.append(make_dragon_frame(f, expr="excited" if f < 3 else "normal", by=dy))
    return out

def dragon_fire_breath():
    """Signature dragon trick — inhale then BLAST fire."""
    out = []
    # Wind up / inhale (body expands)
    for f in range(4):
        scale = 1 + f * 0.5
        img = make_dragon_frame(f, expr="normal", sit=True)
        out.append(img)

    # FIRE! — draw fire jets coming from mouth
    for f in range(8):
        img = make_dragon_frame(f, expr="open", sit=True, breathing=True)
        d   = ImageDraw.Draw(img)
        progress = f / 8
        # Fire jet extending right from mouth
        jet_len = int(progress * 55)
        mx, my  = 52, 46   # mouth position
        for i in range(jet_len):
            t = i / max(1, jet_len)
            jx = mx + i + random.randint(-1, 2)
            jy = my + random.randint(-3, 3) + int(t * 5)
            r  = max(1, int(8 * (1 - t) * (1 - progress * 0.3)))
            # Fire gradient: yellow core → orange → red edge
            col = D["fire_1"] if t < 0.3 else (D["fire_2"] if t < 0.6 else D["fire_3"])
            d.ellipse([jx-r, jy-r, jx+r, jy+r], fill=col)
        # Smoke puffs
        if f > 4:
            for _ in range(2):
                sx = mx + jet_len + random.randint(-5, 10)
                sy = my - random.randint(0, 12)
                sr = random.randint(4, 10)
                d.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=D["smoke"])
        out.append(img)

    # Cooldown
    for f in range(3):
        out.append(make_dragon_frame(f, expr="happy", sit=True))
    return out

def dragon_fly():
    """Dragon hovers — wings beat, body bobs up/down."""
    out = []
    for f in range(10):
        fly_y = -int(abs(math.sin(f / 10 * math.pi * 2)) * 12)
        flap  = int(math.sin(f / 10 * math.pi * 2) * 14)
        out.append(make_dragon_frame(f, by=fly_y, flap=flap, expr="happy"))
    return out

def dragon_roar():
    """Dragon rears up and roars — head tilts back, mouth opens wide."""
    out = []
    for f in range(10):
        rearing = int(math.sin(f / 10 * math.pi) * 8)
        expr    = "open" if f > 3 and f < 8 else "angry"
        img     = make_dragon_frame(f, expr=expr, by=-rearing, sit=True)
        d       = ImageDraw.Draw(img)
        # Roar lines radiating from head
        if 3 < f < 8:
            cx, cy = 41, 30 - rearing
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                ex  = cx + int(math.cos(rad) * (16 + f * 2))
                ey  = cy + int(math.sin(rad) * (12 + f * 2))
                d.line([(cx, cy), (ex, ey)], fill=(*D["fire_2"][:3], 150), width=2)
        out.append(img)
    return out

def dragon_spin():
    out = []
    for f in range(8):
        look = ["right","right","forward","left","left","left","forward","right"][f]
        out.append(make_dragon_frame(f*2, look=look, expr="happy", wagging=True))
    return out

def dragon_wiggle():
    out = []
    for f in range(8):
        sway = int(math.sin(f / 8 * math.pi * 2) * 5)
        out.append(make_dragon_frame(f, by=sway, expr="happy", sit=True))
    return out

def dragon_dance():
    out = []
    for f in range(8):
        dy  = int(math.sin(f / 8 * math.pi * 2) * 4)
        flap = int(abs(math.sin(f / 8 * math.pi * 2)) * 8)
        out.append(make_dragon_frame(f, expr="excited", by=dy, flap=flap, wagging=True))
    return out

def dragon_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    out = []
    for i, dy in enumerate(arc):
        expr = "excited" if dy < -8 else "normal"
        out.append(make_dragon_frame(i, expr=expr, by=dy, flap=abs(dy)//2))
    return out


# ── Dragon icon ───────────────────────────────────────────────────────────

def make_dragon_icon(size=32):
    img = make_dragon_frame(0, sit=True)
    return img.resize((size, size), Image.LANCZOS)


# ── Animation registry ────────────────────────────────────────────────────

DRAGON_ANIMATIONS = {
    "idle":           dragon_idle(),
    "idle_night":     dragon_idle_night(),
    "walk_right":     dragon_walk("right"),
    "walk_left":      dragon_walk("left"),
    "sleep":          dragon_sleep(),
    "sleep_night":    dragon_sleep(),
    "curious_right":  dragon_curious("right"),
    "curious_left":   dragon_curious("left"),
    "happy":          dragon_happy(),
    "surprised":      dragon_surprised(),
    "jump":           dragon_jump(),
    "spin":           dragon_spin(),
    "dance":          dragon_dance(),
    "wiggle":         dragon_wiggle(),
    "fire_breath":    dragon_fire_breath(),
    "fly":            dragon_fly(),
    "roar":           dragon_roar(),
    "bone_sit":       dragon_idle()[:6],   # dragon eating looks same as idle
    "bone_walk":      dragon_walk("right")[:4],
    "petting":        dragon_happy()[:8],   # happy when petted
    "wag":            dragon_happy()[:6],
    "angry":          [make_dragon_frame(f, expr="angry", sit=True) for f in range(6)],
    "love":           dragon_happy(),
    "dizzy":          dragon_spin(),
}

DRAGON_TRICKS = ["fire_breath", "fly", "roar", "jump", "spin",
                 "dance", "wiggle", "happy"]