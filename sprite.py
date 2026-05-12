"""
sprite.py - Full pixel-art dog with rich animations.
All drawn with Pillow - no external assets needed.
"""
from PIL import Image, ImageDraw, ImageFont
import math, random

C = {
    "body":   (110,100, 95,255), "body_l": (155,145,140,255),
    "ear":    ( 80, 70, 65,255), "ear_l":  (130,118,112,255),
    "face":   (220,210,200,255), "chest":  (240,235,228,255),
    "nose":   ( 40, 30, 30,255), "eye":    ( 30, 20, 15,255),
    "eye_w":  (255,255,255,255), "shine":  (255,255,255,200),
    "mouth":  ( 60, 40, 40,255), "tongue": (220, 90,100,255),
    "paw":    (130,118,112,255), "paw_d":  ( 80, 70, 65,255),
    "tail":   (140,128,120,255), "collar": ( 80,140,220,255),
    "tag":    (220,180, 40,255), "bg":     (  0,  0,  0,  0),
    "bone":   (240,230,210,255), "bone_d": (200,185,165,255),
    "star":   (255,220, 40,255), "heart":  (230, 60, 80,255),
    "zz":     (160,180,220,255), "pj":     (180,160,220,255),
    "shadow": ( 40, 30, 25,180),
    "night_o":(  0,  0, 40, 60),
}
SIZE = 96

def _new(): return Image.new("RGBA",(SIZE,SIZE),C["bg"])

# ── Core drawing helpers ─────────────────────────────────────────────────

def _tail(d, f, by, wagging=False):
    swing = int(math.sin(f*0.9)*7) if wagging else int(math.sin(f*0.5)*4)
    pts = [(60,50+by),(68+swing,38+by),(71+swing,28+by),
           (64+swing,26+by),(59+swing,33+by),(56,46+by)]
    d.polygon(pts, fill=C["tail"])
    d.ellipse([61+swing-5,23+by,61+swing+5,31+by], fill=C["body_l"])

def _body(d, by, pj=False):
    fc = C["pj"] if pj else C["body"]
    d.ellipse([16,42+by,66,74+by], fill=fc)
    d.ellipse([24,46+by,58,72+by], fill=C["chest"])
    if not pj: d.ellipse([18,44+by,38,60+by], fill=C["body_l"])

def _legs(d, f, by, dance=False, wiggle=False, sit=False):
    if sit:
        d.rounded_rectangle([18,62+by,30,82+by],radius=5,fill=C["paw"])
        d.rounded_rectangle([50,62+by,62,82+by],radius=5,fill=C["paw"])
        for px in [19,23,27]: d.ellipse([px,78+by,px+4,83+by],fill=C["paw_d"])
        for px in [51,55,59]: d.ellipse([px,78+by,px+4,83+by],fill=C["paw_d"])
        return
    if dance:
        ls = int(math.sin(f*1.5)*10)
        rs = int(math.cos(f*1.5)*10)
        d.rounded_rectangle([20,60+by+ls,30,80+by+ls],radius=5,fill=C["paw"])
        d.rounded_rectangle([50,60+by+rs,60,80+by+rs],radius=5,fill=C["paw"])
        d.rounded_rectangle([16,58+by,26,76+by],radius=5,fill=C["body"])
        d.rounded_rectangle([54,58+by,64,76+by],radius=5,fill=C["body"])
        return
    if wiggle:
        ls = int(math.sin(f*2.0)*8)
        rs = int(math.sin(f*2.0+math.pi)*8)
    else:
        ls = int(math.sin(f*1.2)*5)
        rs = int(math.sin(f*1.2+math.pi)*5)
    d.rounded_rectangle([16,60+by,26,78+by],radius=4,fill=C["body"])
    d.rounded_rectangle([54,60+by,64,78+by],radius=4,fill=C["body"])
    d.rounded_rectangle([22,62+by+ls,32,80+by+ls],radius=5,fill=C["paw"])
    d.rounded_rectangle([48,62+by+rs,58,80+by+rs],radius=5,fill=C["paw"])
    for px in [23,27,30]: d.ellipse([px,77+by+ls,px+4,82+by+ls],fill=C["paw_d"])
    for px in [49,53,57]: d.ellipse([px,77+by+rs,px+4,82+by+rs],fill=C["paw_d"])

def _collar(d, by):
    d.rounded_rectangle([23,52+by,59,59+by],radius=3,fill=C["collar"])
    d.ellipse([36,55+by,44,63+by],fill=C["tag"])
    d.ellipse([38,57+by,42,61+by],fill=(255,255,255,100))

def _head(d, by, night=False):
    fc = C["pj"] if night else C["body"]
    d.ellipse([12,10+by,68,58+by], fill=fc)
    d.ellipse([18,16+by,62,54+by], fill=C["face"])
    d.ellipse([16, 8+by,42,26+by], fill=C["body_l"])
    d.ellipse([38, 8+by,64,26+by], fill=C["body_l"])
    d.ellipse([24, 6+by,56,22+by], fill=C["chest"])

def _ears(d, by, flop=0):
    d.ellipse([ 5,16+by,28,54+by+flop], fill=C["ear"])
    d.ellipse([ 9,20+by,24,50+by+flop], fill=C["ear_l"])
    d.ellipse([52,16+by,75,54+by+flop], fill=C["ear"])
    d.ellipse([56,20+by,71,50+by+flop], fill=C["ear_l"])

def _eyes(d, by, look="forward", expr="normal"):
    ox = {"left":-4,"right":4,"forward":0}[look]
    px = {"left":-2,"right":2,"forward":0}[look]
    if expr=="sleep":
        d.arc([22+ox,26+by,38+ox,36+by],0,180,fill=C["eye"],width=2)
        d.arc([44+ox,26+by,60+ox,36+by],0,180,fill=C["eye"],width=2)
    elif expr=="blink":
        d.line([23+ox,31+by,37+ox,31+by],fill=C["eye"],width=2)
        d.line([45+ox,31+by,59+ox,31+by],fill=C["eye"],width=2)
    elif expr=="squint":
        d.arc([22+ox,28+by,38+ox,36+by],190,350,fill=C["eye"],width=2)
        d.arc([44+ox,28+by,60+ox,36+by],190,350,fill=C["eye"],width=2)
    elif expr=="excited":
        d.ellipse([21+ox,24+by,39+ox,40+by],fill=C["eye_w"])
        d.ellipse([43+ox,24+by,61+ox,40+by],fill=C["eye_w"])
        d.ellipse([25+ox+px,27+by,36+ox+px,37+by],fill=C["eye"])
        d.ellipse([47+ox+px,27+by,58+ox+px,37+by],fill=C["eye"])
        d.ellipse([26+ox,27+by,30+ox,31+by],fill=C["shine"])
        d.ellipse([48+ox,27+by,52+ox,31+by],fill=C["shine"])
    else:
        d.ellipse([22+ox,25+by,38+ox,38+by],fill=C["eye_w"])
        d.ellipse([44+ox,25+by,60+ox,38+by],fill=C["eye_w"])
        d.ellipse([25+ox+px,27+by,36+ox+px,37+by],fill=C["eye"])
        d.ellipse([47+ox+px,27+by,58+ox+px,37+by],fill=C["eye"])
        d.ellipse([26+ox,27+by,30+ox,31+by],fill=C["shine"])
        d.ellipse([48+ox,27+by,52+ox,31+by],fill=C["shine"])
        if expr=="happy":
            d.arc([22+ox,25+by,38+ox,38+by],180,360,fill=C["eye_w"],width=3)
            d.arc([44+ox,25+by,60+ox,38+by],180,360,fill=C["eye_w"],width=3)

def _nose(d, by):
    d.ellipse([32,38+by,48,47+by],fill=C["nose"])
    d.ellipse([34,39+by,38,43+by],fill=C["shine"])

def _mouth(d, by, expr="normal", bone=False):
    if bone:
        # Draw bone in mouth
        d.rectangle([28,47+by,52,51+by],fill=C["bone"])
        d.ellipse([24,44+by,32,54+by],fill=C["bone"])
        d.ellipse([28,44+by,36,54+by],fill=C["bone"])
        d.ellipse([44,44+by,52,54+by],fill=C["bone"])
        d.ellipse([48,44+by,56,54+by],fill=C["bone"])
        d.rectangle([28,47+by,52,51+by],fill=C["bone_d"])
        return
    if expr in ("happy","excited","dance"):
        d.arc([32,44+by,48,54+by],0,180,fill=C["mouth"],width=2)
        d.ellipse([35,47+by,45,55+by],fill=C["tongue"])
        d.line([40,47+by,40,55+by],fill=C["mouth"],width=1)
    elif expr=="sleep":
        d.arc([34,44+by,46,51+by],0,180,fill=C["mouth"],width=1)
    elif expr=="panting":
        d.arc([30,43+by,50,55+by],0,180,fill=C["mouth"],width=2)
        d.ellipse([33,47+by,47,57+by],fill=C["tongue"])
        d.line([40,47+by,40,57+by],fill=C["mouth"],width=1)
    else:
        d.arc([34,44+by,46,50+by],0,180,fill=C["mouth"],width=1)

def _nightcap(d, by):
    """Little sleeping cap for night mode"""
    pts = [(30,14+by),(48,14+by),(52,4+by),(44,-2+by),(38,6+by)]
    d.polygon(pts, fill=C["pj"])
    d.ellipse([35,2+by,45,10+by],fill=C["chest"])
    d.rectangle([28,12+by,52,17+by],fill=C["pj"])

def _shadow(d, by):
    d.ellipse([22,84+by,74,92+by],fill=C["shadow"])

# ── Full frame composer ──────────────────────────────────────────────────

def make_frame(f=0, look="forward", expr="normal", by=0,
               wagging=False, dance=False, wiggle=False, sit=False,
               bone=False, night=False, panting=False, flop=0,
               tint=None):
    img = _new()
    d   = ImageDraw.Draw(img)
    _shadow(d, by)
    _tail(d, f, by, wagging=wagging or dance)
    _body(d, by, pj=night)
    _legs(d, f, by, dance=dance, wiggle=wiggle, sit=sit)
    _collar(d, by)
    _head(d, by, night=night)
    _ears(d, by, flop=flop)
    _eyes(d, by, look=look, expr=expr)
    _nose(d, by)
    actual_expr = "panting" if panting else expr
    _mouth(d, by, expr=actual_expr, bone=bone)
    if night: _nightcap(d, by)
    if tint:
        ov = Image.new("RGBA",(SIZE,SIZE),(*tint,55))
        img = Image.alpha_composite(img, ov)
    return img

def make_icon(size=32):
    img = make_frame(0,"forward","happy")
    return img.resize((size,size),Image.LANCZOS)

# ── Animation factories ──────────────────────────────────────────────────

def _seq(count, **kw_fn):
    return [make_frame(f, **{k: v(f) if callable(v) else v
                              for k,v in kw_fn.items()})
            for f in range(count)]

def frames_idle(night=False):
    out=[]
    for f in range(20):
        expr = "blink" if f in (8,9) else "normal"
        by   = int(math.sin(f*0.3)*1)
        out.append(make_frame(f,"forward",expr,by=by,sit=True,night=night))
    return out

def frames_walk(direction="right"):
    look = "right" if direction=="right" else "left"
    out=[]
    for f in range(10):
        by = int(math.sin(f*math.pi/5)*-2)
        out.append(make_frame(f,look,"normal",by=by))
    return out

def frames_sleep(night=False):
    out=[]
    for f in range(12):
        expr="sleep"
        by=2
        out.append(make_frame(f,"forward",expr,by=by,sit=True,flop=4,night=night))
    return out

def frames_curious(direction="right"):
    look=direction
    out=[]
    for f in range(8):
        by=int(math.sin(f*0.8)*2)
        out.append(make_frame(f,look,"normal",by=by,sit=True))
    return out

def frames_happy():
    out=[]
    for f in range(10):
        by=int(math.sin(f*math.pi/5)*-4)
        out.append(make_frame(f,"forward","happy",by=by,wagging=True))
    return out

def frames_surprised():
    out=[]
    for f in range(8):
        by=int(f<3)*-4
        out.append(make_frame(f,"forward","excited",by=by))
    return out

def frames_jump():
    arc=[0,-4,-9,-14,-18,-18,-14,-9,-4,0,3,0]
    out=[]
    for i,dy in enumerate(arc):
        expr="excited" if dy<-10 else "happy" if dy<-4 else "normal"
        out.append(make_frame(i,"forward",expr,by=dy))
    return out

def frames_spin():
    out=[]
    for f in range(10):
        look=["right","right","right","forward","left","left","left","forward","right","right"][f]
        expr="happy" if f%2==0 else "excited"
        out.append(make_frame(f*2,look,expr,wagging=True))
    return out

def frames_dance():
    """Full body dance - legs kick, tail wags, ears flop"""
    out=[]
    for f in range(16):
        by=int(math.sin(f*math.pi/4)*-3)
        flop=int(abs(math.sin(f*0.8))*6)
        expr="happy" if f%4<2 else "excited"
        out.append(make_frame(f,"forward",expr,by=by,dance=True,flop=flop,wagging=True))
    return out

def frames_wiggle():
    """Butt wiggle - preparing for trick"""
    out=[]
    for f in range(8):
        look=["right","right","forward","left","left","forward","right","right"][f]
        by=int(math.sin(f*1.5)*2)
        out.append(make_frame(f,look,"happy",by=by,wiggle=True,wagging=True))
    return out

def frames_backflip():
    """Backflip - body rotates"""
    out=[]
    # Crouch
    for f in range(3):
        out.append(make_frame(f,"forward","normal",by=4,sit=True))
    # Launch
    for f in range(3):
        by=-f*6
        out.append(make_frame(f,"forward","excited",by=by))
    # Upside down (approximated - ears flopped fully)
    for f in range(4):
        out.append(make_frame(f,"forward","excited",by=-16,flop=16,wagging=True))
    # Land
    for f in range(3):
        by=-12+f*5
        out.append(make_frame(f,"forward","happy",by=by))
    out.append(make_frame(0,"forward","happy",by=0,wagging=True))
    return out

def frames_leg_shake():
    """Lying on back, legs in air wiggling"""
    out=[]
    for f in range(12):
        img = _new()
        d = ImageDraw.Draw(img)
        # Body on its back (rotated appearance)
        by = 8
        _shadow(d, by+10)
        # Draw body tilted
        d.ellipse([14,50+by,70,82+by],fill=C["body"])
        d.ellipse([22,52+by,60,80+by],fill=C["chest"])
        # Legs wiggling in air
        ls = int(math.sin(f*1.8)*14)
        rs = int(math.cos(f*1.8)*14)
        d.rounded_rectangle([10,30+ls,22,55+ls],radius=6,fill=C["paw"])
        d.rounded_rectangle([28,25+rs,40,50+rs],radius=6,fill=C["paw"])
        d.rounded_rectangle([48,25+ls,60,50+ls],radius=6,fill=C["paw"])
        d.rounded_rectangle([66,30+rs,78,55+rs],radius=6,fill=C["paw"])
        # Head sideways
        d.ellipse([4,44+by,46,80+by],fill=C["body"])
        d.ellipse([8,48+by,40,76+by],fill=C["face"])
        d.ellipse([2,46+by,18,70+by],fill=C["ear"])
        d.ellipse([4,50+by,14,66+by],fill=C["ear_l"])
        _nose(d, by+10)
        _mouth(d, by+10, expr="happy")
        _eyes(d, by+10, look="forward", expr="happy")
        _shadow(d, by+18)
        out.append(img)
    return out

def frames_panting():
    out=[]
    for f in range(8):
        by=int(math.sin(f*0.8)*1)
        out.append(make_frame(f,"forward","normal",by=by,sit=True,panting=True,wagging=True))
    return out

def frames_bone():
    """Walking with a bone in mouth - proud strut"""
    out=[]
    for f in range(10):
        by=int(math.sin(f*math.pi/5)*-2)
        look="right"
        out.append(make_frame(f,look,"normal",by=by,bone=True,wagging=True))
    return out

def frames_bone_sit():
    """Sitting happily with bone in mouth"""
    out=[]
    for f in range(10):
        by=int(math.sin(f*0.3)*1)
        expr="blink" if f in (5,6) else "normal"
        out.append(make_frame(f,"forward",expr,by=by,sit=True,bone=True,wagging=True))
    return out

def frames_night_idle():
    return frames_idle(night=True)

def frames_night_sleep():
    return frames_sleep(night=True)

# ── Build all animations ─────────────────────────────────────────────────

ANIMATIONS = {
    "idle":           frames_idle(),
    "idle_night":     frames_night_idle(),
    "walk_right":     frames_walk("right"),
    "walk_left":      frames_walk("left"),
    "sleep":          frames_sleep(),
    "sleep_night":    frames_night_sleep(),
    "curious_right":  frames_curious("right"),
    "curious_left":   frames_curious("left"),
    "happy":          frames_happy(),
    "surprised":      frames_surprised(),
    "jump":           frames_jump(),
    "spin":           frames_spin(),
    "dance":          frames_dance(),
    "wiggle":         frames_wiggle(),
    "backflip":       frames_backflip(),
    "leg_shake":      frames_leg_shake(),
    "panting":        frames_panting(),
    "bone_walk":      frames_bone(),
    "bone_sit":       frames_bone_sit(),
}

TRICK_ANIMS = ["jump","spin","dance","wiggle","backflip","leg_shake"]

# ── NEW EXPRESSIONS (added to _eyes / _mouth patches) ───────────────────
# These use the frame-level custom drawing approach for max expressiveness

def _draw_dizzy_eyes(d, by):
    """Spinning X eyes"""
    for cx, cy in [(30, 31+by), (52, 31+by)]:
        d.line([cx-5,cy-5,cx+5,cy+5], fill=C["eye"], width=2)
        d.line([cx+5,cy-5,cx-5,cy+5], fill=C["eye"], width=2)

def _draw_love_eyes(d, by):
    """Heart-shaped eyes"""
    for ex in [22, 44]:
        # Left half of heart
        d.ellipse([ex+1,25+by,ex+8,32+by], fill=C["heart"])
        # Right half
        d.ellipse([ex+7,25+by,ex+14,32+by], fill=C["heart"])
        # Bottom triangle
        d.polygon([(ex+1,30+by),(ex+15,30+by),(ex+8,38+by)], fill=C["heart"])

def _draw_angry_eyes(d, by, look="forward"):
    ox = {"left":-4,"right":4,"forward":0}[look]
    # Normal eye whites
    d.ellipse([22+ox,25+by,38+ox,38+by], fill=C["eye_w"])
    d.ellipse([44+ox,25+by,60+ox,38+by], fill=C["eye_w"])
    # Pupils low and center (angry look)
    d.ellipse([26+ox,30+by,36+ox,38+by], fill=C["eye"])
    d.ellipse([48+ox,30+by,58+ox,38+by], fill=C["eye"])
    # Angry V-brows
    d.line([20+ox,22+by,38+ox,27+by], fill=C["eye"], width=3)
    d.line([60+ox,22+by,44+ox,27+by], fill=C["eye"], width=3)

def _draw_confused_eyes(d, by):
    """One eye normal, one squinted"""
    # Left: normal
    d.ellipse([22,25+by,38,38+by], fill=C["eye_w"])
    d.ellipse([25,27+by,36,37+by], fill=C["eye"])
    d.ellipse([26,27+by,30,31+by], fill=C["shine"])
    # Right: squint
    d.arc([44,28+by,60,36+by],200,340, fill=C["eye"], width=2)
    # Question mark brow
    d.arc([46,20+by,58,28+by],200,360, fill=C["eye"], width=2)
    d.ellipse([51,29+by,54,32+by], fill=C["eye"])

def _draw_embarrassed_eyes(d, by):
    """Shy sideways look, rosy cheeks"""
    ox = 2
    d.ellipse([22+ox,25+by,38+ox,38+by], fill=C["eye_w"])
    d.ellipse([44+ox,25+by,60+ox,38+by], fill=C["eye_w"])
    # Pupils looking far right (shy)
    d.ellipse([32+ox,28+by,38+ox,36+by], fill=C["eye"])
    d.ellipse([54+ox,28+by,60+ox,36+by], fill=C["eye"])
    # Blush circles
    d.ellipse([14,36+by,26,44+by], fill=(220,100,100,90))
    d.ellipse([54,36+by,66,44+by], fill=(220,100,100,90))

def _draw_star_eyes(d, by):
    """Stars in eyes — amazed"""
    for cx, cy in [(30,32+by), (52,32+by)]:
        pts = []
        import math as _m
        for i in range(10):
            a = _m.radians(i*36 - 90)
            r = 8 if i%2==0 else 4
            pts.append((cx+r*_m.cos(a), cy+r*_m.sin(a)))
        d.polygon(pts, fill=C["star"])

def _draw_sneeze_face(d, by, f):
    """Building up sneeze expression"""
    # Scrunched nose
    d.ellipse([30,36+by,50,48+by], fill=C["nose"])
    d.ellipse([32,37+by,36,41+by], fill=C["shine"])
    # Closed scrunched eyes
    d.arc([22,27+by,38,35+by], 0, 180, fill=C["eye"], width=2)
    d.arc([44,27+by,60,35+by], 0, 180, fill=C["eye"], width=2)
    # Droplets when sneezing (later frames)
    if f >= 6:
        for dx, dy in [(20,-5),(30,-8),(42,-6),(55,-4)]:
            d.ellipse([dx,by+dy,dx+4,by+dy+6], fill=(180,210,240,180))

def _draw_hiccup_face(d, by, f):
    """Hiccup — lurching forward"""
    # Eyes wide on hiccup frames
    if f % 4 < 2:
        d.ellipse([20,23+by,40,42+by], fill=C["eye_w"])
        d.ellipse([42,23+by,62,42+by], fill=C["eye_w"])
        d.ellipse([25,27+by,36,37+by], fill=C["eye"])
        d.ellipse([47,27+by,58,37+by], fill=C["eye"])
    else:
        d.ellipse([22,25+by,38,38+by], fill=C["eye_w"])
        d.ellipse([44,25+by,60,38+by], fill=C["eye_w"])
        d.ellipse([25,27+by,36,37+by], fill=C["eye"])
        d.ellipse([47,27+by,58,37+by], fill=C["eye"])
    # Hiccup O-mouth
    if f % 4 < 2:
        d.ellipse([34,44+by,46,54+by], fill=C["mouth"])
    else:
        d.arc([34,44+by,46,50+by], 0, 180, fill=C["mouth"], width=1)


# ── New animation factories ──────────────────────────────────────────────

def frames_sneeze():
    """Build up and release sneeze — head bobs back then lurches forward"""
    import math
    out = []
    # Wind-up frames: head tilts back (negative by)
    for f in range(8):
        wind = -int(math.sin(f/7*math.pi/2)*6)
        img = _new(); d = ImageDraw.Draw(img)
        _shadow(d, 0)
        _tail(d, f, 0)
        _body(d, 0)
        _legs(d, f, 0, sit=True)
        _collar(d, 0)
        _head(d, wind)
        _ears(d, wind, flop=int(f/7*4))
        _draw_sneeze_face(d, wind, f)
        out.append(img)
    # ACHOO! Head lurches forward (positive by)
    for f in range(6):
        lurch = int(f/5*8)
        img = _new(); d = ImageDraw.Draw(img)
        _shadow(d, lurch)
        _tail(d, f, lurch, wagging=True)
        _body(d, lurch)
        _legs(d, f, lurch, sit=True)
        _collar(d, lurch)
        _head(d, lurch)
        _ears(d, lurch, flop=8)
        _draw_sneeze_face(d, lurch, f+8)
        # Spray droplets
        for dx, dy_off in [(60,-10),(70,-5),(75,-15),(80,-8)]:
            d.ellipse([dx, lurch+30+dy_off, dx+5, lurch+36+dy_off],
                      fill=(180,210,240,int(220*(1-f/5))))
        out.append(img)
    # Recover
    out += frames_happy()[:4]
    return out


def frames_hiccup():
    """Rapid hiccup — body jolts up repeatedly"""
    import math
    out = []
    for cycle in range(4):
        for f in range(8):
            jolt = int(math.sin(f/8*math.pi*2)*5) if f < 4 else 0
            img = _new(); d = ImageDraw.Draw(img)
            by = -jolt
            _shadow(d, 4)
            _tail(d, f, by)
            _body(d, by)
            _legs(d, f, by, sit=True)
            _collar(d, by)
            _head(d, by)
            _ears(d, by)
            _draw_hiccup_face(d, by, f)
            out.append(img)
    out.append(make_frame(0,"forward","embarrassed",by=0,sit=True))
    return out


def frames_dizzy():
    """Spinning stars around head, wobbly body"""
    import math
    out = []
    for f in range(16):
        img = _new(); d = ImageDraw.Draw(img)
        sway = int(math.sin(f/16*math.pi*3)*4)
        _shadow(d, 0)
        _tail(d, f, 0)
        _body(d, sway)
        _legs(d, f, sway, wiggle=True)
        _collar(d, sway)
        _head(d, sway)
        _ears(d, sway, flop=3)
        _draw_dizzy_eyes(d, sway)
        _nose(d, sway)
        _mouth(d, sway, expr="normal")
        # Orbiting stars
        for i in range(3):
            angle = math.radians(f/16*360 + i*120)
            sx = 40 + int(20*math.cos(angle))
            sy = 16 + int(10*math.sin(angle))
            pts = []
            for j in range(10):
                a2 = math.radians(j*36-90)
                r2 = 5 if j%2==0 else 2.5
                pts.append((sx+r2*math.cos(a2), sy+r2*math.sin(a2)))
            d.polygon(pts, fill=C["star"])
        out.append(img)
    return out


def frames_love():
    """Hearts floating up, love-struck expression"""
    import math
    out = []
    for f in range(12):
        img = _new(); d = ImageDraw.Draw(img)
        bounce = int(math.sin(f/12*math.pi*2)*2)
        _shadow(d, 0)
        _tail(d, f, bounce, wagging=True)
        _body(d, bounce)
        _legs(d, f, bounce, sit=True)
        _collar(d, bounce)
        _head(d, bounce)
        _ears(d, bounce, flop=2)
        _draw_love_eyes(d, bounce)
        _nose(d, bounce)
        _mouth(d, bounce, expr="happy")
        # Hearts floating up at different heights
        for i in range(3):
            progress = (f/12 + i/3) % 1.0
            hx = 30 + i*20
            hy = int(60 - progress*70)
            alpha = int(255*(1-progress))
            if alpha > 30:
                hs = max(4, int(10*(1-progress*0.4)))
                d.ellipse([hx,hy,hx+hs,hy+hs//2], fill=(*C["heart"][:3], alpha))
                d.ellipse([hx+hs//2,hy,hx+hs*2//2+hs//2,hy+hs//2], fill=(*C["heart"][:3], alpha))
                d.polygon([(hx,hy+hs//3),(hx+hs,hy+hs//3),(hx+hs//2,hy+hs)],
                          fill=(*C["heart"][:3], alpha))
        out.append(img)
    return out


def frames_angry():
    """Stamping feet, angry expression, steam from ears"""
    import math
    out = []
    for f in range(12):
        img = _new(); d = ImageDraw.Draw(img)
        stomp = int(abs(math.sin(f/12*math.pi*4))*4)
        _shadow(d, stomp//2)
        _tail(d, f, stomp, wagging=False)
        _body(d, stomp)
        # Stamping legs — alternate
        d.rounded_rectangle([16,60+stomp,26,78+stomp], radius=4, fill=C["body"])
        d.rounded_rectangle([54,60+stomp,64,78+stomp], radius=4, fill=C["body"])
        if f % 4 < 2:
            d.rounded_rectangle([22,62+stomp,32,82+stomp], radius=5, fill=C["paw"])
            d.rounded_rectangle([48,66+stomp,58,82+stomp], radius=5, fill=C["paw"])
        else:
            d.rounded_rectangle([22,66+stomp,32,82+stomp], radius=5, fill=C["paw"])
            d.rounded_rectangle([48,62+stomp,58,82+stomp], radius=5, fill=C["paw"])
        _collar(d, stomp)
        _head(d, stomp)
        _ears(d, stomp, flop=0)
        _draw_angry_eyes(d, stomp)
        _nose(d, stomp)
        _mouth(d, stomp, expr="normal")
        # Steam puffs from ears
        for sx, sy in [(10, 18+stomp), (70, 18+stomp)]:
            for i in range(3):
                a = int(12*(1-f/12))
                d.ellipse([sx-a+i*8, sy-i*6, sx+a+i*8, sy+a-i*6],
                          fill=(200,200,200,int(160*(1-f/12))))
        out.append(img)
    return out


def frames_moonwalk():
    """Smooth backwards slide — legs glide, head stays level"""
    import math
    out = []
    for f in range(12):
        img = _new(); d = ImageDraw.Draw(img)
        # Body slides right while feet glide left
        slide = int(math.sin(f/12*math.pi*2)*3)
        _shadow(d, 0)
        _tail(d, f, 0, wagging=True)
        _body(d, slide)
        _collar(d, slide)
        _head(d, 0)  # head stays stable — the "cool" part
        _ears(d, 0)
        _eyes(d, 0, look="left", expr="squint")  # looking backwards, cool
        _nose(d, 0)
        _mouth(d, 0, expr="normal")
        # Gliding legs — opposite phase to normal walk
        gl = int(math.sin(f/12*math.pi*2 + math.pi)*6)
        gr = int(math.sin(f/12*math.pi*2)*6)
        d.rounded_rectangle([16,60,26,78], radius=4, fill=C["body"])
        d.rounded_rectangle([54,60,64,78], radius=4, fill=C["body"])
        d.rounded_rectangle([22,62+gl,32,80+gl], radius=5, fill=C["paw"])
        d.rounded_rectangle([48,62+gr,58,80+gr], radius=5, fill=C["paw"])
        for px in [23,27,30]: d.ellipse([px,77+gl,px+4,82+gl], fill=C["paw_d"])
        for px in [49,53,57]: d.ellipse([px,77+gr,px+4,82+gr], fill=C["paw_d"])
        out.append(img)
    return out


def frames_roll_over():
    """Full roll — dog goes from sitting to fully on back and back again"""
    import math
    out = []
    # Phase 1: tip sideways
    for f in range(5):
        img = _new(); d = ImageDraw.Draw(img)
        lean = f * 8
        _shadow(d, 8)
        _body(d, lean)
        _legs(d, f, lean, sit=True)
        _collar(d, lean)
        _head(d, lean)
        _ears(d, lean, flop=lean//2)
        _eyes(d, lean, expr="happy")
        _nose(d, lean)
        _mouth(d, lean, expr="happy")
        out.append(img)
    # Phase 2: on back (reuse leg_shake approach)
    out += frames_leg_shake()[:8]
    # Phase 3: tip back up
    for f in range(5):
        img = _new(); d = ImageDraw.Draw(img)
        lean = (4-f) * 8
        _shadow(d, lean//2)
        _body(d, lean)
        _legs(d, f, lean, sit=True)
        _collar(d, lean)
        _head(d, lean)
        _ears(d, lean, flop=lean//2)
        _eyes(d, lean, expr="happy")
        _nose(d, lean)
        _mouth(d, lean, expr="happy")
        out.append(img)
    out.append(make_frame(0,"forward","happy",sit=True,wagging=True))
    return out


# ── Add new animations to registry ──────────────────────────────────────

ANIMATIONS.update({
    "sneeze":    frames_sneeze(),
    "hiccup":    frames_hiccup(),
    "dizzy":     frames_dizzy(),
    "love":      frames_love(),
    "angry":     frames_angry(),
    "moonwalk":  frames_moonwalk(),
    "roll_over": frames_roll_over(),
})

TRICK_ANIMS = ["jump","spin","dance","wiggle","backflip","leg_shake",
               "sneeze","hiccup","dizzy","moonwalk","roll_over"]


# ── Petting / hover animation ─────────────────────────────────────────────

def frames_petting():
    """Dog being petted — eyes close in contentment, tail wags fast, ears flop."""
    import math
    out = []
    for f in range(12):
        img = _new(); d = ImageDraw.Draw(img)
        bob = int(math.sin(f / 12 * math.pi * 2) * 2)
        _shadow(d, 0)
        _tail(d, f * 2, bob, wagging=True)
        _body(d, bob)
        _legs(d, f, bob, sit=True)
        _collar(d, bob)
        _head(d, bob)
        _ears(d, bob, flop=6)    # ears flopped down contentedly

        # Draw a hand patting the head
        hand_y = 8 + bob + int(abs(math.sin(f / 12 * math.pi * 2)) * 4)
        d.ellipse([30, hand_y, 58, hand_y+14], fill=(255, 210, 170, 180))
        d.ellipse([28, hand_y+4, 34, hand_y+12], fill=(255, 210, 170, 160))
        d.ellipse([56, hand_y+4, 62, hand_y+12], fill=(255, 210, 170, 160))

        # Closed happy eyes when being petted
        _eyes(d, bob, expr="blink" if f % 3 == 0 else "happy")
        _nose(d, bob)
        _mouth(d, bob, expr="happy")

        # Hearts floating up
        if f % 4 == 0:
            hx = 60 + (f // 4) * 8
            hy = 20 - (f // 4) * 6
            if 0 < hx < 90 and hy > 0:
                d.text((hx, hy), "♥", fill=(*C["heart"][:3], 200))
        out.append(img)
    return out


def frames_wag():
    """Simple fast tail wag — idle variant."""
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        _shadow(d, 0)
        _tail(d, f * 4, 0, wagging=True)
        _body(d, 0)
        _legs(d, f, 0, sit=True)
        _collar(d, 0)
        _head(d, 0)
        _ears(d, 0)
        _eyes(d, 0, expr="happy")
        _nose(d, 0)
        _mouth(d, 0, expr="happy")
        out.append(img)
    return out


def frames_shake():
    """Dog shaking head 'no' — used for refusals."""
    import math
    out = []
    for f in range(8):
        img = _new(); d = ImageDraw.Draw(img)
        sway = int(math.sin(f / 8 * math.pi * 4) * 6)  # head shakes L-R
        _shadow(d, 0)
        _tail(d, f, 0)
        _body(d, 0)
        _legs(d, f, 0, sit=True)
        _collar(d, 0)
        # Head shifts left/right
        _head(d, 0)
        _ears(d, 0, flop=abs(sway) // 2)
        look = "right" if sway > 2 else ("left" if sway < -2 else "forward")
        _eyes(d, 0, look=look, expr="normal")
        _nose(d, 0)
        _mouth(d, 0, expr="normal")
        out.append(img)
    return out


def frames_sit_beg():
    """Dog sitting up on hind legs begging — front paws up."""
    import math
    out = []
    for f in range(6):
        img = _new(); d = ImageDraw.Draw(img)
        bob = int(math.sin(f / 6 * math.pi) * 3)
        by  = -4 + bob   # slightly elevated body
        _shadow(d, 8)
        _tail(d, f * 2, 0, wagging=True)
        _body(d, by)
        # Back legs only
        d.rounded_rectangle([18, 60+by, 28, 76+by], radius=4, fill=C["body"])
        d.rounded_rectangle([52, 60+by, 62, 76+by], radius=4, fill=C["body"])
        # Front paws raised up
        d.rounded_rectangle([24, 44+by, 34, 58+by], radius=5, fill=C["paw"])
        d.rounded_rectangle([48, 44+by, 58, 58+by], radius=5, fill=C["paw"])
        for px in [25,29,32]: d.ellipse([px,54+by,px+4,58+by], fill=C["paw_d"])
        for px in [49,53,56]: d.ellipse([px,54+by,px+4,58+by], fill=C["paw_d"])
        _collar(d, by)
        _head(d, by)
        _ears(d, by, flop=3)
        _eyes(d, by, expr="happy")
        _nose(d, by)
        _mouth(d, by, expr="happy")
        out.append(img)
    return out


# Register new animations
ANIMATIONS.update({
    "petting":   frames_petting(),
    "wag":       frames_wag(),
    "shake_no":  frames_shake(),
    "sit_beg":   frames_sit_beg(),
})

# Add some tricks to pool
TRICK_ANIMS += ["wag", "sit_beg"]