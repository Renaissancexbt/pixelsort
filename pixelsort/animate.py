"""Watch the sort happen: render every stage of a pixel sort to MP4 or GIF.

The animation runs an odd-even transposition sort inside the same intervals
that :func:`pixelsort.pixelsort` uses. Neighbours swap one step at a time, so
bright pixels visibly drift through dark ones until every run is in order.
Equal keys never swap, which makes the last frame identical to the still image.

Needs numpy (``pip install "pixelsort-glitch[animate]"``). MP4 output also needs
ffmpeg on the PATH; GIF works with Pillow alone.
"""

from __future__ import annotations

import random
import shutil
import subprocess
from typing import Callable, Iterator

from PIL import Image

from .core import Options, pixels
from .intervals import get_interval
from .keys import get_key

try:  # numpy is an optional extra
    import numpy as np
except ImportError:  # pragma: no cover - exercised only without numpy
    np = None  # type: ignore[assignment]


def _need_numpy() -> None:
    if np is None:
        raise RuntimeError('--animate needs numpy: pip install "pixelsort-glitch[animate]"')


class _Plan:
    """Rotated working canvas, keys and run ids, exactly as the sorter sees them."""

    def __init__(self, img: Image.Image, opts: Options):
        _need_numpy()
        self.src = img.convert("RGBA")
        self.opts = opts
        self.angle = opts.angle % 360
        if self.angle:
            self.work = self.src.rotate(self.angle, expand=True, resample=Image.NEAREST)
            alpha = Image.new("L", self.src.size, 255).rotate(self.angle, expand=True,
                                                               resample=Image.NEAREST)
            valid = np.asarray(alpha) > 0
        else:
            self.work = self.src
            valid = np.ones((self.src.size[1], self.src.size[0]), dtype=bool)
        w, h = self.work.size
        flat = pixels(self.work)
        self.px = np.asarray(self.work, dtype=np.uint8).copy()
        key = get_key(opts.key)
        k = np.fromiter((key(p) for p in flat), dtype=np.float64, count=w * h).reshape(h, w)
        self.key = -k if opts.reverse else k
        self.ids = np.full((h, w), -1, dtype=np.int64)
        self._assign_runs(flat, valid, w, h)

    def _assign_runs(self, flat, valid, w, h) -> None:
        opts = self.opts
        rng = random.Random(opts.seed)
        interval = get_interval(opts.interval)
        key = get_key(opts.key)
        nxt = 0
        for y in range(h):
            row = valid[y]
            x = 0
            while x < w:
                while x < w and not row[x]:
                    x += 1
                start = x
                while x < w and row[x]:
                    x += 1
                if x - start <= 1 and self.angle:
                    continue
                seg = flat[y * w + start:y * w + x]
                if not seg:
                    continue
                for a, b in interval(seg, key, lower=opts.lower, upper=opts.upper,
                                     length=opts.length, rng=rng):
                    if b - a > 1:
                        self.ids[y, start + a:start + b] = nxt
                        nxt += 1

    def passes(self) -> Iterator[int]:
        """Advance one odd-even pass at a time; yields the number of swaps."""
        parity = 0
        quiet = 0
        while quiet < 2:
            ka, kb = self.key[:, parity:-1:2], self.key[:, parity + 1::2]
            m = min(ka.shape[1], kb.shape[1])
            ka, kb = ka[:, :m], kb[:, :m]
            ia, ib = self.ids[:, parity:-1:2][:, :m], self.ids[:, parity + 1::2][:, :m]
            swap = (ia == ib) & (ia >= 0) & (ka > kb)
            rows, cols = np.nonzero(swap)
            if len(rows):
                ca = parity + 2 * cols
                cb = ca + 1
                self.px[rows, ca], self.px[rows, cb] = self.px[rows, cb].copy(), self.px[rows, ca].copy()
                self.key[rows, ca], self.key[rows, cb] = self.key[rows, cb].copy(), self.key[rows, ca].copy()
                quiet = 0
            else:
                quiet += 1
            parity ^= 1
            yield len(rows)

    def frame(self) -> Image.Image:
        cur = Image.fromarray(self.px, "RGBA")
        if not self.angle:
            return cur.convert("RGB")
        w, h = self.src.size
        back = cur.rotate(-self.angle, expand=True, resample=Image.NEAREST)
        bw, bh = back.size
        left, top = (bw - w) // 2, (bh - h) // 2
        out = back.crop((left, top, left + w, top + h))
        out = Image.composite(out, self.src, out.getchannel("A").point(lambda v: 255 if v else 0))
        return out.convert("RGB")


def frames(img: Image.Image, opts: Options, seconds: float = 5.0, fps: int = 30,
           hold: float = 1.0, on_progress: Callable[[int, int], None] | None = None
           ) -> list[Image.Image]:
    """Return the frames of the animation: a short hold on the original, the sort
    speeding up as it goes, and a hold on the finished picture."""
    plan = _Plan(img, opts)
    # dry run to count passes, then replay on a fresh plan
    total = sum(1 for _ in _Plan(img, opts).passes())
    n = max(2, int(seconds * fps))
    targets = [int(round(total * ((i + 1) / n) ** 2.0)) for i in range(n)]
    hold_frames = int(hold * fps)
    first = plan.frame()
    out = [first] * max(1, hold_frames // 2)
    it = plan.passes()
    done = 0
    for i, t in enumerate(targets):
        while done < t:
            try:
                next(it)
            except StopIteration:
                break
            done += 1
        out.append(plan.frame())
        if on_progress:
            on_progress(i + 1, n)
    for _ in it:  # make sure the last frame is fully sorted
        pass
    final = plan.frame()
    out[-1] = final
    out.extend([final] * hold_frames)
    return out


def write(frames_: list[Image.Image], path: str, fps: int = 30) -> None:
    if path.lower().endswith(".gif"):
        step = max(1, round(fps / 15))  # GIFs stay small at ~15 fps
        sel = frames_[::step]
        sel[0].save(path, save_all=True, append_images=sel[1:], loop=0,
                    duration=int(1000 * step / fps), optimize=True)
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("MP4 needs ffmpeg on the PATH; use a .gif file name instead")
    w, h = frames_[0].size
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin
    for f in frames_:
        proc.stdin.write(f.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")


def animate(img: Image.Image, opts: Options, path: str, seconds: float = 5.0,
            fps: int = 30, on_progress: Callable[[int, int], None] | None = None) -> Image.Image:
    """Render the sort of ``img`` to ``path`` (.mp4 or .gif); return the final frame."""
    fs = frames(img, opts, seconds=seconds, fps=fps, on_progress=on_progress)
    write(fs, path, fps=fps)
    return fs[-1]
