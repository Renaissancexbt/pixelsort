import random
from collections import Counter

from PIL import Image

from pixelsort import Options, pixelsort, sort_row
from pixelsort.cli import main
from pixelsort.core import pixels
from pixelsort.keys import lightness


def noise(w=64, h=48, seed=3):
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h))
    img.putdata([(rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(w * h)])
    return img


def test_sort_row_sorts_inside_intervals_only():
    row = [(0, 0, 0), (200, 200, 200), (100, 100, 100), (0, 0, 0), (255, 255, 255)]
    out = sort_row(row, Options(lower=0.2, upper=0.9), random.Random(0))
    assert out == [(0, 0, 0), (100, 100, 100), (200, 200, 200), (0, 0, 0), (255, 255, 255)]


def test_reverse():
    row = [(50, 50, 50), (150, 150, 150), (100, 100, 100)]
    out = sort_row(row, Options(interval="none", reverse=True), random.Random(0))
    assert [lightness(p) for p in out] == sorted((lightness(p) for p in row), reverse=True)


def test_rows_keep_their_pixels():
    img = noise()
    out = pixelsort(img, interval="none")
    w, h = img.size
    a, b = pixels(img), pixels(out)
    for y in range(h):
        assert Counter(a[y * w:(y + 1) * w]) == Counter(b[y * w:(y + 1) * w])


def test_size_and_mode_preserved():
    img = noise()
    for angle in (0, 33, 90, 180):
        out = pixelsort(img, angle=angle)
        assert out.size == img.size and out.mode == img.mode


def test_angle_90_sorts_columns():
    img = noise(16, 16)
    out = pixelsort(img, interval="none", angle=90)
    w, h = out.size
    px = pixels(out)
    for x in range(w):
        col = [lightness(px[y * w + x]) for y in range(h)]
        assert col == sorted(col) or col == sorted(col, reverse=True)


def test_random_is_deterministic_with_seed():
    img = noise()
    a = pixelsort(img, interval="random", seed=7)
    b = pixelsort(img, interval="random", seed=7)
    assert pixels(a) == pixels(b)


def test_cli_roundtrip(tmp_path, capsys):
    src = tmp_path / "in.png"
    noise().save(src)
    assert main([str(src), "--angle", "45", "--key", "hue"]) == 0
    assert (tmp_path / "in.sorted.png").exists()
    assert main([str(tmp_path / "missing.png")]) == 2
    assert main([str(src), "--lower", "3"]) == 2


def test_cli_mask(tmp_path):
    src, mask, out = tmp_path / "in.png", tmp_path / "m.png", tmp_path / "o.png"
    img = noise(32, 32)
    img.save(src)
    m = Image.new("L", (32, 32), 0)
    m.paste(255, (0, 0, 16, 32))
    m.save(mask)
    assert main([str(src), "-o", str(out), "--mask", str(mask), "--interval", "none"]) == 0
    a, b = pixels(img), pixels(Image.open(out).convert("RGB"))
    for y in range(32):
        assert a[y * 32 + 16:(y + 1) * 32] == b[y * 32 + 16:(y + 1) * 32]
