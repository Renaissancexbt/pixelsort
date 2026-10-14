"""Paint the demo picture used in the README: a synthetic sunset over water.

Everything is procedural, so the repo ships no third-party photos.
    python examples/make_scene.py examples/sunset.png
"""

import math
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H = 960, 600
HORIZON = 360


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(img):
    """Radial glow around the sun, so every row changes colour left to right."""
    top, mid, low = (34, 18, 74), (196, 64, 112), (255, 170, 80)
    px = img.load()
    cx, cy = 600, 175
    for y in range(HORIZON):
        for x in range(W):
            d = math.hypot((x - cx) * 0.8, (y - cy) * 1.4) / 620
            t = max(0.0, min(1.0, 1 - d)) ** 1.3
            t = 0.55 * t + 0.45 * (y / HORIZON)
            px[x, y] = lerp(top, mid, t / 0.6) if t < 0.6 else lerp(mid, low, (t - 0.6) / 0.4)


def clouds(img, rng):
    """Soft streaky clouds from upscaled random noise."""
    small = Image.new("L", (18, 9))
    small.putdata([rng.randrange(256) for _ in range(18 * 9)])
    n = small.resize((W, HORIZON), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    n = n.point(lambda v: max(0, v - 120) * 2)
    tint = Image.new("RGB", (W, HORIZON), (255, 180, 200))
    region = img.crop((0, 0, W, HORIZON))
    img.paste(Image.composite(Image.blend(region, tint, 0.55), region, n), (0, 0))


def grain(img, rng, amount=6):
    noise = Image.effect_noise(img.size, amount).convert("RGB")
    img.paste(ImageChops.add(img, noise, offset=-128))  # noise is centred on 128


def sun(img):
    glow = Image.new("RGB", (W, H), 0)
    g = ImageDraw.Draw(glow)
    cx, cy = 600, 175
    for r in range(220, 0, -4):
        a = int(110 * (1 - r / 220) ** 2)
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(a, int(a * 0.6), int(a * 0.25)))
    img.paste(ImageChops.add(img, glow))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(255, 236, 170))
    # sun stripes like an 80s poster
    for i, yy in enumerate(range(cy + 10, cy + 70, 12)):
        d.rectangle([cx - 80, yy, cx + 80, yy + 3 + i],
                    fill=lerp((214, 84, 110), (255, 160, 90), (yy - cy) / 70))


def ridge(rng, base, amp, rough):
    pts, y = [], base
    for x in range(0, W + 8, 8):
        y += rng.uniform(-rough, rough)
        y = max(base - amp, min(base + amp * 0.3, y))
        pts.append((x, y))
    return pts


def mountains(img, rng):
    d = ImageDraw.Draw(img)
    layers = [(HORIZON - 80, 90, 14, (92, 40, 108)), (HORIZON - 40, 70, 12, (60, 26, 84)),
              (HORIZON - 10, 40, 9, (28, 14, 52))]
    for base, amp, rough, col in layers:
        pts = ridge(rng, base, amp, rough)
        d.polygon(pts + [(W, HORIZON), (0, HORIZON)], fill=col)


def water(img, rng):
    top = img.crop((0, 0, W, HORIZON)).transpose(Image.FLIP_TOP_BOTTOM)
    top = top.resize((W, H - HORIZON))
    dark = Image.new("RGB", top.size, (18, 10, 40))
    refl = Image.blend(top, dark, 0.45)
    px = refl.load()
    src = refl.copy().load()
    for y in range(refl.size[1]):
        shift = int(6 * math.sin(y * 0.35) + rng.uniform(-3, 3)) * (1 + y // 60)
        for x in range(W):
            px[x, y] = src[min(W - 1, max(0, x + shift)), y]
    d = ImageDraw.Draw(refl)
    for _ in range(140):
        y = rng.randrange(refl.size[1])
        x = rng.randrange(W)
        L = rng.randrange(10, 80)
        d.line([(x, y), (x + L, y)], fill=(255, 200, 140) if abs(x - 600) < 110 else (90, 60, 120))
    img.paste(refl.filter(ImageFilter.GaussianBlur(0.6)), (0, HORIZON))


def stars(img, rng):
    d = ImageDraw.Draw(img)
    for _ in range(160):
        x, y = rng.randrange(W), rng.randrange(HORIZON // 2)
        v = rng.randrange(150, 255)
        d.point((x, y), fill=(v, v, v))


def main(out):
    rng = random.Random(1999)
    img = Image.new("RGB", (W, H))
    sky(img)
    clouds(img, rng)
    stars(img, rng)
    sun(img)
    mountains(img, rng)
    water(img, rng)
    grain(img, rng)
    img.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sunset.png")
