"""
cat_sprite.py — Pixel-art cat companion sprite.

Distinct personality: aloof, graceful, does what it wants.
Unique animations: stretch, groom, knead, tail-flick, zoomies.
Color: dark grey tabby with white chest and green eyes.
"""

from PIL import Image, ImageDraw
import math

# ── Cat palette ───────────────────────────────────────────────────────────
C = {
    "body":    ( 80,  75,  80, 255),   # dark grey tabby
    "body_l":  (115, 110, 115, 255),   # lighter fur
    "stripe":  ( 55,  50,  55, 200),   # tabby stripes
    "chest":   (220, 215, 210, 255),   # white chest
    "face":    (140, 135, 138, 255),   # face fur
    "ear":     ( 65,  60,  65, 255),   # ear outer
    "ear_i":   (200, 140, 140, 255),   # ear inner (pink)
    "eye":     ( 15,  15,  10, 255),   # pupil
    "eye_w":   (255, 255, 255, 255),   # eye white (small)
    "iris":    ( 60, 160,  60, 255),   # green iris
    "shine":   (255, 255, 255, 200),
    "nose":    (200, 100, 100, 255),   # pink nose
    "mouth":   ( 60,  40,  40, 255),
    "whisker": (200, 200, 200, 180),   # whiskers
    "paw":     (100,  95, 100, 255),   # paw pads
    "paw_p":   (180, 120, 130, 255),   # pink paw pads
    "tail":    ( 75,  70,  75, 255),   # tail
    "tail_tip":(220, 215, 210, 255),   # white tail tip
    "collar":  (200,  50,  50, 255),   # red collar
    "tag":     (220, 180,  40, 255),   # gold tag
    "shadow":  ( 40,  35,  40, 120),
    "bg":      (  0,   0,   0,   0),
}
SIZE = 96


def _new(): return Image.new("RGBA", (SIZE, SIZE), C["bg"])


def _shadow(d, by=0):
    cx = SIZE // 2
    d.ellipse([cx-24, SIZE-14+by, cx+24, SIZE-6+by], fill=C["shadow"])


def _tail(d, f, by, up=False, flick=False):
    """Cat tail — elegant, curves up or wraps around."""
    swing = int(math.sin(f * 0.6) * 6)
    if flick:
        swing = int(math.sin(f * 2.0) * 12)
    if up:
        # Tail curves up high behind the cat
        pts = [(60,55+by),(68,45+by),(70,32+by),(65,20+by),
               (60,18+by),(58,24+by),(60,38+by),(58,52+by)]
    else:
        pts = [(60,55+by),(70+swing,48+by),(76+swing,40+by),
               (74+swing,32+by),(66+swing,30+by),(62+swing,38+by),(58,52+by)]
    d.polygon(pts, fill=C["tail"])
    # White tail tip
    tip_x = pts[-3][0]
    tip_y = pts[-3][1]
    d.ellipse([tip_x-5, tip_y-5, tip_x+5, tip_y+5], fill=C["tail_tip"])


def _body(d, by, stretched=False):
    if stretched:
        # Long stretched body
        d.ellipse([10, 48+by, 72, 74+by], fill=C["body"])
        d.ellipse([18, 52+by, 64, 72+by], fill=C["chest"])
    else:
        d.ellipse([16, 44+by, 66, 74+by], fill=C["body"])
        # Chest patch
        d.ellipse([24, 48+by, 58, 72+by], fill=C["chest"])
    # Tabby stripes
    for sx, sw in [(20, 3), (28, 2), (52, 2), (58, 3)]:
        d.ellipse([sx, 50+by, sx+sw, 68+by], fill=C["stripe"])


def _legs(d, f, by, sit=False, stretch=False):
    if sit:
        # Sitting — front paws neatly together
        d.rounded_rectangle([26, 64+by, 34, 80+by], radius=4, fill=C["paw"])
        d.rounded_rectangle([46, 64+by, 54, 80+by], radius=4, fill=C["paw"])
        # Pink paw pads
        for px in [27,30,33]: d.ellipse([px,76+by,px+3,80+by], fill=C["paw_p"])
        for px in [47,50,53]: d.ellipse([px,76+by,px+3,80+by], fill=C["paw_p"])
    elif stretch:
        # Front legs stretched way forward
        d.rounded_rectangle([8,  64+by, 22, 78+by], radius=5, fill=C["paw"])
        d.rounded_rectangle([58, 64+by, 72, 78+by], radius=5, fill=C["paw"])
    else:
        gl = int(math.sin(f * 1.3) * 5)
        gr = int(math.sin(f * 1.3 + math.pi) * 5)
        d.rounded_rectangle([18, 62+by, 30, 80+by+gl], radius=4, fill=C["paw"])
        d.rounded_rectangle([52, 62+by, 64, 80+by+gr], radius=4, fill=C["paw"])
        for px in [19,23,27]: d.ellipse([px,76+by+gl,px+3,80+by+gl], fill=C["paw_p"])
        for px in [53,57,61]: d.ellipse([px,76+by+gr,px+3,80+by+gr], fill=C["paw_p"])


def _collar(d, by):
    d.rounded_rectangle([26, 50+by, 56, 57+by], radius=3, fill=C["collar"])
    d.ellipse([38, 53+by, 44, 60+by], fill=C["tag"])


def _head(d, by):
    # Rounder cat head
    d.ellipse([16, 10+by, 66, 54+by], fill=C["body"])
    # Face centre
    d.ellipse([22, 18+by, 60, 52+by], fill=C["face"])


def _ears(d, by, flat=False):
    if flat:
        # Flattened/irritated ears
        d.polygon([(18, 18+by),(28, 12+by),(22, 22+by)], fill=C["ear"])
        d.polygon([(64, 18+by),(54, 12+by),(60, 22+by)], fill=C["ear"])
    else:
        # Pointy upright ears
        d.polygon([(16, 22+by),(26, 8+by),(32, 20+by)], fill=C["ear"])
        d.polygon([(66, 22+by),(56, 8+by),(50, 20+by)], fill=C["ear"])
        # Pink inner
        d.polygon([(20, 20+by),(26, 11+by),(30, 20+by)], fill=C["ear_i"])
        d.polygon([(62, 20+by),(56, 11+by),(52, 20+by)], fill=C["ear_i"])


def _eyes(d, by, look="forward", expr="normal"):
    ox = {"left":-4, "right":4, "forward":0}[look]
    if expr in ("sleep","blink"):
        d.arc([20+ox, 26+by, 36+ox, 36+by], 0, 180, fill=C["eye"], width=2)
        d.arc([46+ox, 26+by, 62+ox, 36+by], 0, 180, fill=C["eye"], width=2)
        return
    if expr == "squint":
        # Half-closed, aloof
        d.arc([20+ox, 22+by, 36+ox, 36+by], 200, 340, fill=C["iris"], width=4)
        d.arc([46+ox, 22+by, 62+ox, 36+by], 200, 340, fill=C["iris"], width=4)
        return
    # Full eyes — green with vertical slit pupil
    d.ellipse([20+ox, 22+by, 36+ox, 38+by], fill=C["iris"])
    d.ellipse([46+ox, 22+by, 62+ox, 38+by], fill=C["iris"])
    # Slit pupil — wider/narrower based on mood
    pw = 3 if expr == "alert" else 5
    d.ellipse([27+ox, 23+by, 27+ox+pw, 37+by], fill=C["eye"])
    d.ellipse([53+ox, 23+by, 53+ox+pw, 37+by], fill=C["eye"])
    # Shine
    d.ellipse([21+ox, 23+by, 25+ox, 27+by], fill=C["shine"])
    d.ellipse([47+ox, 23+by, 51+ox, 27+by], fill=C["shine"])


def _nose(d, by):
    d.polygon([(38, 36+by),(43, 36+by),(40.5, 40+by)], fill=C["nose"])


def _mouth(d, by, expr="normal"):
    if expr == "happy":
        d.arc([34, 40+by, 48, 50+by], 0, 180, fill=C["mouth"], width=2)
    elif expr == "open":
        d.ellipse([36, 40+by, 46, 50+by], fill=C["mouth"])
    else:
        d.line([36, 42+by, 40, 44+by], fill=C["mouth"], width=1)
        d.line([41, 44+by, 46, 42+by], fill=C["mouth"], width=1)


def _whiskers(d, by):
    # Left whiskers
    for wy in [32, 36, 40]:
        d.line([(4, wy+by),(28, wy+by)], fill=C["whisker"], width=1)
    # Right whiskers
    for wy in [32, 36, 40]:
        d.line([(54, wy+by),(78, wy+by)], fill=C["whisker"], width=1)


# ── Frame factory ─────────────────────────────────────────────────────────

def make_cat_frame(f=0, look="forward", expr="normal", by=0,
                   sit=False, tail_up=False, tail_flick=False,
                   stretched=False, flat_ears=False):
    img = _new()
    d   = ImageDraw.Draw(img)
    _shadow(d, 0)
    _tail(d, f, by, up=tail_up, flick=tail_flick)
    _body(d, by, stretched=stretched)
    _legs(d, f, by, sit=sit, stretch=stretched)
    _collar(d, by)
    _head(d, by)
    _ears(d, by, flat=flat_ears)
    _eyes(d, by, look=look, expr=expr)
    _nose(d, by)
    _mouth(d, by, expr=expr)
    _whiskers(d, by)
    return img


# ── Animation builders ────────────────────────────────────────────────────

def cat_idle():
    out = []
    for f in range(12):
        # Cats have slow blinking (slow blink = affection)
        expr = "blink" if f == 9 else ("squint" if f in (8,10) else "normal")
        out.append(make_cat_frame(f, expr=expr, sit=True, tail_up=True))
    return out

def cat_idle_night():
    out = []
    for f in range(8):
        out.append(make_cat_frame(f, expr="sleep", sit=True, tail_up=False))
    return out

def cat_walk(direction="right"):
    look = "right" if direction == "right" else "left"
    out  = []
    for f in range(8):
        dy = int(math.sin(f / 8 * math.pi * 2) * -1)
        # Cats walk with tail flicking
        out.append(make_cat_frame(f*2, look=look, by=dy, tail_flick=True))
    return out

def cat_sleep():
    out = []
    for f in range(8):
        # Curled up sleeping cat
        img = make_cat_frame(f, expr="sleep", sit=True)
        out.append(img)
    return out

def cat_curious(direction="right"):
    look = direction
    out  = []
    for f in range(6):
        expr = "alert"
        out.append(make_cat_frame(f, look=look, expr=expr, sit=True, tail_up=True))
    return out

def cat_happy():
    out = []
    for f in range(8):
        dy   = int(math.sin(f / 8 * math.pi * 2) * 3)
        out.append(make_cat_frame(f, expr="happy", by=dy, sit=True, tail_up=True))
    return out

def cat_surprised():
    out = []
    for f in range(6):
        dy   = -3 if f < 3 else 0
        flat = f < 2  # ears flatten in surprise
        out.append(make_cat_frame(f, expr="alert", by=dy, flat_ears=flat))
    return out

def cat_stretch():
    """Cat morning stretch — front legs extended, butt up."""
    out = []
    for f in range(8):
        progress = f / 7
        # Start sitting, end fully stretched
        sit      = progress < 0.3
        stretched = progress > 0.5
        by       = int(progress * 6)
        out.append(make_cat_frame(f, expr="blink" if stretched else "normal",
                                  by=by, sit=sit, stretched=stretched))
    # Hold stretch then return
    for f in range(4):
        out.append(make_cat_frame(f, expr="normal", stretched=True))
    for f in range(4):
        out.append(make_cat_frame(f, expr="happy", sit=True, tail_up=True))
    return out

def cat_groom():
    """Cat licking paw and rubbing face."""
    out = []
    for cycle in range(3):
        for f in range(6):
            img = make_cat_frame(f, expr="blink" if f % 2 else "squint",
                                 sit=True, tail_up=True)
            d = ImageDraw.Draw(img)
            # Paw raised to face
            paw_y = 30 + int(math.sin(f/6*math.pi) * 8)
            d.rounded_rectangle([44, paw_y, 58, paw_y+14], radius=6, fill=C["paw"])
            for px in [45,49,53]: d.ellipse([px,paw_y+10,px+3,paw_y+14], fill=C["paw_p"])
            out.append(img)
    out.append(make_cat_frame(0, expr="squint", sit=True, tail_up=True))
    return out

def cat_knead():
    """Kneading — alternating front paws pushing down (biscuit making)."""
    out = []
    for f in range(10):
        img = make_cat_frame(f, expr="blink" if f % 3 == 0 else "squint",
                              sit=True)
        d = ImageDraw.Draw(img)
        # Alternate left/right paw pushing
        if f % 2 == 0:
            d.rounded_rectangle([20, 72, 32, 84], radius=5, fill=C["paw"])
            d.rounded_rectangle([48, 68, 60, 80], radius=5, fill=C["paw"])
        else:
            d.rounded_rectangle([20, 68, 32, 80], radius=5, fill=C["paw"])
            d.rounded_rectangle([48, 72, 60, 84], radius=5, fill=C["paw"])
        out.append(img)
    return out

def cat_tail_flick():
    """Irritated tail flicking — classic cat attitude."""
    out = []
    for f in range(8):
        out.append(make_cat_frame(f, expr="squint", sit=True, tail_flick=True))
    return out

def cat_zoomies():
    """Cat zoomies — frantic side to side, blur effect."""
    out = []
    for f in range(10):
        look = "right" if f % 2 else "left"
        dy   = int(math.sin(f / 10 * math.pi * 4) * 4)
        out.append(make_cat_frame(f*3, look=look, expr="alert", by=dy))
    return out

def cat_spin():
    out = []
    for f in range(8):
        look = ["right","right","forward","left","left","left","forward","right"][f]
        out.append(make_cat_frame(f*2, look=look, expr="happy", tail_flick=True))
    return out

def cat_jump():
    arc = [0,-4,-8,-12,-14,-12,-8,-4,0]
    out = []
    for i, dy in enumerate(arc):
        expr = "alert" if abs(dy) > 8 else "normal"
        out.append(make_cat_frame(i, expr=expr, by=dy, tail_up=True))
    return out

def cat_dance():
    out = []
    for f in range(8):
        dy   = int(math.sin(f / 8 * math.pi * 2) * 4)
        look = "right" if f < 4 else "left"
        out.append(make_cat_frame(f, look=look, expr="happy", by=dy, tail_up=True))
    return out

def make_cat_icon(size=32):
    img = make_cat_frame(0, sit=True, tail_up=True)
    return img.resize((size, size), Image.LANCZOS)


# ── Animation registry ────────────────────────────────────────────────────

CAT_ANIMATIONS = {
    "idle":           cat_idle(),
    "idle_night":     cat_idle_night(),
    "walk_right":     cat_walk("right"),
    "walk_left":      cat_walk("left"),
    "sleep":          cat_sleep(),
    "sleep_night":    cat_sleep(),
    "curious_right":  cat_curious("right"),
    "curious_left":   cat_curious("left"),
    "happy":          cat_happy(),
    "surprised":      cat_surprised(),
    "jump":           cat_jump(),
    "spin":           cat_spin(),
    "dance":          cat_dance(),
    "wiggle":         [make_cat_frame(f, expr="happy", by=int(math.sin(f/6*math.pi*2)*4), sit=True) for f in range(6)],
    # Cat exclusives
    "stretch":        cat_stretch(),
    "groom":          cat_groom(),
    "knead":          cat_knead(),
    "tail_flick":     cat_tail_flick(),
    "zoomies":        cat_zoomies(),
    # Shared
    "bone_sit":       cat_idle()[:6],
    "bone_walk":      cat_walk("right")[:4],
    "petting":        cat_groom()[:8],
    "wag":            cat_happy()[:6],
    "angry":          [make_cat_frame(f, expr="squint", flat_ears=True, sit=True, tail_flick=True) for f in range(6)],
    "love":           cat_happy(),
    "dizzy":          cat_spin(),
    "backflip":       cat_jump(),
    "leg_shake":      cat_knead(),
    "roll_over":      cat_stretch(),
    "sneeze":         [make_cat_frame(f, expr="alert" if f>3 else "normal", sit=True) for f in range(8)],
}

CAT_TRICKS = ["stretch", "groom", "knead", "tail_flick", "zoomies",
              "jump", "spin", "dance"]