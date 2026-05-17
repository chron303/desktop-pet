"""
evolution_animation.py — Transformation animation for pet evolution.

Plays a 3-second cinematic sequence:
  1. Pet glows brighter (0.5s)
  2. Burst of particles + white flash (0.5s)
  3. Spinning transformation (1s)
  4. New form fades in (1s)

Implemented as a sequence of PIL frames that main.py plays
over the normal animation loop.
"""

from PIL import Image, ImageDraw, ImageFilter
import math

SIZE = 96


def _glow_frame(base_frame: Image.Image, intensity: float) -> Image.Image:
    """Add a glowing halo around the sprite."""
    result = base_frame.copy()
    glow   = base_frame.copy().filter(ImageFilter.GaussianBlur(radius=4))
    # Brighten the glow
    from PIL import ImageEnhance
    glow = ImageEnhance.Brightness(glow).enhance(1 + intensity)
    result = Image.alpha_composite(glow, result)
    return result


def _flash_frame(base_frame: Image.Image, alpha: int) -> Image.Image:
    """White flash overlay."""
    result  = base_frame.copy()
    overlay = Image.new("RGBA", result.size, (255, 255, 255, alpha))
    result  = Image.alpha_composite(result, overlay)
    return result


def _spin_frame(base_frame: Image.Image, angle: float,
                scale: float = 1.0) -> Image.Image:
    """Rotate and scale frame for spin effect."""
    rotated = base_frame.rotate(angle, expand=False,
                                resample=Image.BICUBIC)
    if scale != 1.0:
        new_size = (int(SIZE * scale), int(SIZE * scale))
        rotated  = rotated.resize(new_size, Image.LANCZOS)
        # Paste back onto SIZE x SIZE canvas
        canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ox = (SIZE - new_size[0]) // 2
        oy = (SIZE - new_size[1]) // 2
        canvas.paste(rotated, (ox, oy), rotated)
        return canvas
    return rotated


def _particle_burst(f: int, color=(255, 220, 50)) -> Image.Image:
    """Draw radiating particle burst."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    n_particles = 12
    for i in range(n_particles):
        angle   = (i / n_particles) * 2 * math.pi
        dist    = 10 + f * 6
        alpha   = max(0, 255 - f * 30)
        px      = cx + int(dist * math.cos(angle))
        py      = cy + int(dist * math.sin(angle))
        r       = max(1, 4 - f // 3)
        d.ellipse([px-r, py-r, px+r, py+r],
                  fill=(*color, alpha))
    return img


def make_evolution_frames(old_frame: Image.Image,
                          new_frame: Image.Image,
                          pet_type: str = "dog") -> list:
    """
    Generate the full evolution animation sequence.
    Returns list of PIL RGBA frames to play.
    
    pet_type affects the particle color:
      dog    → golden yellow
      dragon → orange-red
      cat    → purple
    """
    particle_colors = {
        "dog":    (255, 220, 50),
        "dragon": (255, 100, 30),
        "cat":    (180, 80, 220),
    }
    p_color = particle_colors.get(pet_type, (255, 220, 50))

    frames = []

    # Phase 1: Glow build-up (8 frames)
    for i in range(8):
        intensity = i / 8 * 1.5
        frame     = _glow_frame(old_frame, intensity)
        frames.append(frame)

    # Phase 2: Particle burst + flash (8 frames)
    for i in range(8):
        base    = _glow_frame(old_frame, 1.5)
        burst   = _particle_burst(i, p_color)
        frame   = Image.alpha_composite(base, burst)
        flash_a = min(255, i * 40)
        frame   = _flash_frame(frame, flash_a)
        frames.append(frame)

    # Phase 3: White flash peak (4 frames)
    for i in range(4):
        frame = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 220))
        frames.append(frame)

    # Phase 4: Spin in new form (12 frames)
    for i in range(12):
        angle  = (1 - i/12) * 360
        scale  = 0.3 + (i/12) * 0.7
        frame  = _spin_frame(new_frame, angle, scale)
        burst  = _particle_burst(max(0, 6 - i), p_color)
        frame  = Image.alpha_composite(frame, burst)
        frames.append(frame)

    # Phase 5: Settle + final glow (6 frames)
    for i in range(6):
        intensity = (1 - i/6) * 0.8
        frame     = _glow_frame(new_frame, intensity)
        frames.append(frame)

    return frames   # ~38 frames at 16ms = ~600ms total
