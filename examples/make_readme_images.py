"""Rebuild every picture in docs/img from examples/sunset.png.

    python examples/make_scene.py examples/sunset.png
    python examples/make_readme_images.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pixelsort import Options, pixelsort

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "img"
SRC = ROOT / "examples" / "sunset.png"

VARIANTS = {
    "melt": Options(),
    "drip": Options(angle=90, lower=0.2, upper=0.9),
    "rain": Options(angle=270, lower=0.1, upper=0.7, reverse=True),
    "diagonal": Options(angle=30, lower=0.15, upper=0.95),
    "hue": Options(key="hue", interval="random", length=140, seed=4),
    "edges": Options(interval="edges", lower=0.1),
}


def font(size, bold=True):
    for name in ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",):
        for d in ("/usr/share/fonts/truetype/dejavu/", ""):
            try:
                return ImageFont.truetype(d + name, size)
            except OSError:
                pass
    return ImageFont.load_default()


def save_jpg(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT / f"{name}.jpg", quality=86, optimize=True, progressive=True)


def hero(src, sorted_img):
    w, h = src.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(w * 0.42, 0), (w, 0), (w, h), (w * 0.58, h)], fill=255)
    img = Image.composite(sorted_img, src, mask)
    d = ImageDraw.Draw(img)
    d.line([(w * 0.42, 0), (w * 0.58, h)], fill=(255, 236, 170), width=3)
    d.text((40, h - 130), "pixelsort", font=font(78), fill=(255, 244, 220))
    d.text((44, h - 46), "glitch art by sorting pixels", font=font(26, bold=False), fill=(255, 214, 190))
    return img


def main():
    src = Image.open(SRC).convert("RGB")
    save_jpg(src, "original")
    done = {}
    for name, opts in VARIANTS.items():
        done[name] = pixelsort(src, opts)
        save_jpg(done[name], name)
    save_jpg(hero(src, done["rain"]), "hero")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.jpg"))))


if __name__ == "__main__":
    main()
