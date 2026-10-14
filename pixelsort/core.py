"""The sorter: rows in, sorted rows out."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from PIL import Image

from .intervals import get_interval
from .keys import Pixel, get_key


def pixels(img: Image.Image) -> list:
    """Flat list of pixel tuples on every Pillow version (getdata is going away in 14)."""
    fn = getattr(img, "get_flattened_data", None)
    return list(fn() if fn else img.getdata())


@dataclass
class Options:
    key: str = "lightness"
    interval: str = "threshold"
    lower: float = 0.25
    upper: float = 0.8
    length: int = 60
    angle: float = 0.0
    reverse: bool = False
    seed: int | None = None


def sort_row(row: Sequence[Pixel], opts: Options, rng: random.Random) -> list[Pixel]:
    """Return a new row with every interval sorted by the chosen key."""
    key = get_key(opts.key)
    spans = get_interval(opts.interval)(row, key, lower=opts.lower, upper=opts.upper,
                                        length=opts.length, rng=rng)
    out = list(row)
    for a, b in spans:
        out[a:b] = sorted(out[a:b], key=key, reverse=opts.reverse)
    return out


def _sort_rows(img: Image.Image, opts: Options, rng: random.Random,
               mask: Image.Image | None = None) -> Image.Image:
    w, h = img.size
    px = pixels(img)
    mpx = pixels(mask) if mask is not None else None
    out: list[Pixel] = []
    for y in range(h):
        row = px[y * w:(y + 1) * w]
        sorted_row = sort_row(row, opts, rng)
        if mpx is not None:
            mrow = mpx[y * w:(y + 1) * w]
            sorted_row = [s if m else o for s, o, m in zip(sorted_row, row, mrow)]
        out.extend(sorted_row)
    res = Image.new(img.mode, img.size)
    res.putdata(out)
    return res


def pixelsort(img: Image.Image, opts: Options | None = None, **kw: object) -> Image.Image:
    """Pixel-sort ``img`` and return a new image of the same size and mode.

    ``angle`` rotates the sorting direction: 0 sorts left to right, 90 sorts
    top to bottom, anything in between streaks diagonally. The rotation is
    undone afterwards and the canvas cropped back, so the output always lines
    up with the input.
    """
    opts = opts or Options(**kw)  # type: ignore[arg-type]
    rng = random.Random(opts.seed)
    src = img.convert("RGBA")
    angle = opts.angle % 360

    if angle == 0:
        return _sort_rows(src, opts, rng).convert(img.mode)

    w, h = src.size
    rot = src.rotate(angle, expand=True, resample=Image.NEAREST)
    # remember which pixels belong to the picture, not the padding
    alpha = Image.new("L", src.size, 255).rotate(angle, expand=True, resample=Image.NEAREST)
    alpha = alpha.point(lambda v: 255 if v else 0)
    sorted_rot = _sort_rows_masked_by_padding(rot, alpha, opts, rng)
    back = sorted_rot.rotate(-angle, expand=True, resample=Image.NEAREST)
    bw, bh = back.size
    left, top = (bw - w) // 2, (bh - h) // 2
    out = back.crop((left, top, left + w, top + h))
    # pixels lost to nearest-neighbour rounding fall back to the original
    out = Image.composite(out, src, out.getchannel("A").point(lambda v: 255 if v else 0))
    return out.convert(img.mode)


def _sort_rows_masked_by_padding(img: Image.Image, alpha: Image.Image, opts: Options,
                                 rng: random.Random) -> Image.Image:
    """Sort only the picture part of each rotated row, never the empty corners."""
    w, h = img.size
    px = pixels(img)
    apx = pixels(alpha)
    out = list(px)
    for y in range(h):
        base = y * w
        x = 0
        while x < w:
            while x < w and not apx[base + x]:
                x += 1
            start = x
            while x < w and apx[base + x]:
                x += 1
            if x - start > 1:
                out[base + start:base + x] = sort_row(px[base + start:base + x], opts, rng)
    res = Image.new(img.mode, img.size)
    res.putdata(out)
    return res


def sort_file(src: str, dst: str, opts: Options, mask_path: str | None = None) -> None:
    img = Image.open(src)
    if mask_path:
        if opts.angle % 360:
            raise ValueError("--mask works with --angle 0 only")
        mask = Image.open(mask_path).convert("L").resize(img.size).point(lambda v: 255 if v > 127 else 0)
        rng = random.Random(opts.seed)
        out = _sort_rows(img.convert("RGBA"), opts, rng, mask).convert(img.mode)
    else:
        out = pixelsort(img, opts)
    out.save(dst)
