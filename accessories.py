"""
accessories.py — Draws accessories on top of sprite frames.

Accessories are unlocked by level:
  Level 1+: bow tie, bandana
  Level 3+: sunglasses, party hat
  Level 5+: crown, top hat, santa hat (December only)
  Level 8+: wizard hat, pirate hat

Each accessory is a function that draws onto a PIL ImageDraw
at the correct position on the 96x96 sprite.
"""

from PIL import Image, ImageDraw
import datetime

# ── Accessory drawing functions ──────────────────────────────────────────

def _draw_party_hat(d: ImageDraw.Draw, by: int = 0):
    """Colourful conical party hat with pompom."""
    # Cone
    d.polygon([(48, 2+by), (32, 22+by), (64, 22+by)], fill=(220, 60, 120, 230))
    # Stripes
    for i, col in enumerate([(255,200,0),(60,200,255),(255,100,50)]):
        y = 6 + i*5 + by
        d.line([(36+i*2, y+2), (60-i*2, y+2)], fill=col, width=2)
    # Pompom
    d.ellipse([42, -2+by, 54, 8+by], fill=(255, 230, 50, 240))
    # Rim
    d.ellipse([30, 20+by, 66, 28+by], fill=(240, 200, 40, 220))

def _draw_crown(d: ImageDraw.Draw, by: int = 0):
    """Gold crown with gems."""
    # Crown base
    pts = [(28,22+by),(28,10+by),(36,16+by),(48,6+by),(60,16+by),(68,10+by),(68,22+by)]
    d.polygon(pts, fill=(220,180,30,240))
    d.line([(28,22+by),(68,22+by)], fill=(180,140,20,255), width=2)
    # Gems
    for gx, gc in [(34,( 255,50,50)), (48,(50,180,255)), (62,(50,220,80))]:
        d.ellipse([gx-3, 10+by, gx+3, 16+by], fill=(*gc,230))

def _draw_top_hat(d: ImageDraw.Draw, by: int = 0):
    """Classic black top hat."""
    # Brim
    d.ellipse([24, 20+by, 72, 28+by], fill=(25,20,20,240))
    # Cylinder
    d.rectangle([32, 2+by, 64, 22+by], fill=(25,20,20,240))
    # Hat band
    d.rectangle([32, 17+by, 64, 22+by], fill=(180,140,30,240))

def _draw_sunglasses(d: ImageDraw.Draw, by: int = 0):
    """Cool sunglasses over the eyes."""
    # Left lens
    d.ellipse([20, 28+by, 40, 40+by], fill=(20,10,10,200))
    d.ellipse([20, 28+by, 40, 40+by], outline=(60,60,60,255), width=2)
    # Right lens
    d.ellipse([44, 28+by, 64, 40+by], fill=(20,10,10,200))
    d.ellipse([44, 28+by, 64, 40+by], outline=(60,60,60,255), width=2)
    # Bridge
    d.line([(40,33+by),(44,33+by)], fill=(60,60,60,255), width=2)
    # Arms
    d.line([(20,33+by),(14,30+by)], fill=(60,60,60,255), width=2)
    d.line([(64,33+by),(70,30+by)], fill=(60,60,60,255), width=2)

def _draw_bow_tie(d: ImageDraw.Draw, by: int = 0):
    """Red bow tie at collar level."""
    cx, cy = 48, 53+by
    # Left wing
    d.polygon([(cx-14,cy-5),(cx-2,cy),(cx-14,cy+5)], fill=(200,40,40,230))
    # Right wing
    d.polygon([(cx+14,cy-5),(cx+2,cy),(cx+14,cy+5)], fill=(200,40,40,230))
    # Knot
    d.ellipse([cx-3,cy-3,cx+3,cy+3], fill=(160,20,20,240))

def _draw_bandana(d: ImageDraw.Draw, by: int = 0):
    """Red bandana around neck."""
    pts = [(28,50+by),(68,50+by),(72,56+by),(48,64+by),(24,56+by)]
    d.polygon(pts, fill=(200,40,40,200))
    # Pattern dots
    for px, py in [(36,54),(48,58),(60,54)]:
        d.ellipse([px-2,py+by,px+2,py+4+by], fill=(220,80,80,200))

def _draw_santa_hat(d: ImageDraw.Draw, by: int = 0):
    """Santa hat — only in December."""
    # Red cone
    d.polygon([(48,0+by),(28,22+by),(68,22+by)], fill=(200,30,30,240))
    # White brim
    d.ellipse([24,18+by,72,28+by], fill=(240,240,240,240))
    # White pompom
    d.ellipse([42,0+by,56,12+by], fill=(240,240,240,240))

def _draw_wizard_hat(d: ImageDraw.Draw, by: int = 0):
    """Purple wizard hat with stars."""
    import math
    # Cone
    d.polygon([(48,0+by),(26,26+by),(70,26+by)], fill=(80,30,140,230))
    # Brim
    d.ellipse([22,22+by,74,32+by], fill=(80,30,140,230))
    d.ellipse([22,22+by,74,32+by], outline=(140,80,220,200), width=2)
    # Stars on hat
    for sx, sy, r in [(40,8,3),(55,14,2),(44,18,2)]:
        pts = []
        for i in range(10):
            a = math.radians(i*36-90)
            rad = r if i%2==0 else r//2+1
            pts.append((sx+rad*math.cos(a), sy+rad*math.sin(a)+by))
        d.polygon(pts, fill=(255,220,50,230))

def _draw_pirate_hat(d: ImageDraw.Draw, by: int = 0):
    """Black pirate tricorn with skull."""
    # Hat body
    d.polygon([(30,22+by),(48,4+by),(66,22+by),(72,18+by),(48,2+by),(24,18+by)],
              fill=(20,15,15,240))
    d.ellipse([24,16+by,72,26+by], fill=(20,15,15,240))
    # Skull face
    d.ellipse([42,7+by,54,17+by], fill=(220,215,205,230))
    d.ellipse([44,9+by,47,12+by], fill=(20,15,15,220))
    d.ellipse([49,9+by,52,12+by], fill=(20,15,15,220))
    d.rectangle([44,14+by,52,16+by], fill=(20,15,15,180))

def _draw_graduation_cap(d: ImageDraw.Draw, by: int = 0):
    """Academic mortarboard."""
    # Board (flat top)
    d.polygon([(24,14+by),(48,6+by),(72,14+by),(48,22+by)], fill=(20,15,15,240))
    # Cylindrical base
    d.ellipse([32,18+by,64,26+by], fill=(20,15,15,240))
    # Tassel
    d.line([(60,10+by),(66,10+by),(66,20+by)], fill=(200,160,30,240), width=2)
    d.ellipse([63,19+by,69,25+by], fill=(200,160,30,200))


# ── Per-pet head position offsets ────────────────────────────────────────
# Each pet has a different head position on the 96x96 canvas.
# (y_offset, x_offset, scale) — accessories shift by these amounts.
PET_OFFSETS = {
    "dog":    {"y": 0,   "x": 0,  "scale": 1.0},  # baseline
    "dragon": {"y": -4,  "x": 2,  "scale": 0.95}, # dragon head slightly higher
    "cat":    {"y": 2,   "x": 0,  "scale": 0.92}, # cat head slightly smaller
}


# ── Registry ─────────────────────────────────────────────────────────────

ACCESSORIES = {
    "bow_tie":       (_draw_bow_tie,       1),   # (draw_fn, min_level)
    "bandana":       (_draw_bandana,       1),
    "sunglasses":    (_draw_sunglasses,    3),
    "party_hat":     (_draw_party_hat,     3),
    "graduation":    (_draw_graduation_cap,4),
    "crown":         (_draw_crown,         5),
    "top_hat":       (_draw_top_hat,       5),
    "wizard_hat":    (_draw_wizard_hat,    8),
    "pirate_hat":    (_draw_pirate_hat,    8),
    "santa_hat":     (_draw_santa_hat,     1),   # December only
}


def unlocked_accessories(level: int) -> list[str]:
    """Return list of accessory names unlocked at this level."""
    month = datetime.datetime.now().month
    result = []
    for name, (fn, min_lvl) in ACCESSORIES.items():
        if level < min_lvl:
            continue
        if name == "santa_hat" and month != 12:
            continue
        result.append(name)
    return result


def apply_accessory(frame: Image.Image, name: str,
                    body_dy: int = 0, pet_type: str = "dog") -> Image.Image:
    """
    Draw accessory on top of a sprite frame.
    pet_type adjusts offsets for each animal's head position.
    Returns new RGBA image.
    """
    if name not in ACCESSORIES:
        return frame
    result = frame.copy()
    d      = ImageDraw.Draw(result)
    fn, _  = ACCESSORIES[name]

    # Apply pet-type head offset
    offsets = PET_OFFSETS.get(pet_type, PET_OFFSETS["dog"])
    total_by = body_dy + offsets["y"]

    fn(d, by=total_by)
    return result


def apply_accessory_to_all(frames: list, name: str,
                            pet_type: str = "dog") -> list:
    """Apply accessory to every frame in an animation list."""
    return [apply_accessory(f, name, pet_type=pet_type) for f in frames]