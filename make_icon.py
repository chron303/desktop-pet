"""
make_icon.py — Run this ONCE before build.bat to generate icon.ico

Usage:
    python make_icon.py
"""

from PIL import Image
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SIZES = [16, 32, 48, 64, 128, 256]

def make_icon():
    # Get the base image from sprite
    for module_name, fn_name in [
        ("sprite",        "make_icon"),
        ("dog_sprite",    "make_icon"),
        ("dragon_sprite", "make_dragon_icon"),
        ("cat_sprite",    "make_cat_icon"),
    ]:
        try:
            mod = __import__(module_name)
            fn  = getattr(mod, fn_name, None)
            if fn:
                img = fn(256)
                if img and isinstance(img, Image.Image):
                    print(f"[icon] Using {module_name}.{fn_name}() — {img.size} {img.mode}")

                    # Ensure RGBA
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")

                    # Build each size as a separate Image object
                    imgs = []
                    for size in SIZES:
                        resized = img.resize((size, size), Image.LANCZOS)
                        # Pillow's ICO writer needs "RGBA" or "RGB"
                        imgs.append(resized.convert("RGBA"))

                    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

                    # Save the LARGEST image first, append the rest
                    # This is the correct Pillow ICO multi-size pattern
                    imgs[-1].save(
                        out,
                        format  = "ICO",
                        append_images = imgs[:-1],
                    )

                    size_kb = os.path.getsize(out) // 1024
                    print(f"[icon] Saved icon.ico ({size_kb} KB) — sizes: {SIZES}")
                    print(f"[icon] Path: {out}")
                    return
        except Exception as e:
            print(f"[icon] {module_name} skipped: {e}")
            continue

    print("[icon] ERROR: could not load any sprite module.")
    sys.exit(1)

if __name__ == "__main__":
    make_icon()