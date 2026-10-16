"""Command line interface.

    pixelsort photo.jpg                          default melt, writes photo.sorted.png
    pixelsort photo.jpg -o out.png --angle 90    vertical streaks
    pixelsort photo.jpg --key hue --interval random --length 120
    pixelsort photo.jpg --lower 0.1 --upper 0.6 --reverse
    pixelsort photo.jpg --mask sky.png           sort only where the mask is white
    pixelsort photo.jpg --angle 90 --animate drip.mp4   watch it sort (needs numpy)
    pixelsort photo.jpg --preset rain            a named look: melt drip rain diagonal rainbow outline
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .core import Options, sort_file
from .intervals import INTERVALS
from .keys import KEYS
from .presets import PRESETS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pixelsort", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="default: <input>.sorted.png")
    ap.add_argument("-p", "--preset", choices=list(PRESETS),
                    help="start from a named look; other flags override it")
    ap.add_argument("-k", "--key", default=None, choices=sorted(KEYS),
                    help="what to sort by (default: lightness)")
    ap.add_argument("-i", "--interval", default=None, choices=sorted(INTERVALS),
                    help="how rows are cut into runs (default: threshold)")
    ap.add_argument("-l", "--lower", type=float, default=None,
                    help="threshold: lower bound 0..1; edges: jump size (default 0.25)")
    ap.add_argument("-u", "--upper", type=float, default=None, help="threshold: upper bound 0..1 (default 0.8)")
    ap.add_argument("-n", "--length", type=int, default=None, help="random: average run length in px (default 60)")
    ap.add_argument("-a", "--angle", type=float, default=None, help="sorting direction in degrees (default 0)")
    ap.add_argument("-r", "--reverse", action="store_true", default=None, help="sort bright to dark")
    ap.add_argument("-m", "--mask", type=Path, help="black/white image; only white areas are sorted")
    ap.add_argument("-s", "--seed", type=int, help="seed for the random interval")
    ap.add_argument("--animate", type=Path, metavar="OUT",
                    help="also render the sort as a video: OUT.mp4 (needs ffmpeg) or OUT.gif")
    ap.add_argument("--seconds", type=float, default=5.0, help="animation length (default 5)")
    ap.add_argument("--fps", type=int, default=30, help="animation frame rate (default 30)")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if not a.input.exists():
        print(f"pixelsort: {a.input}: no such file", file=sys.stderr)
        return 2
    given = {f: getattr(a, f) for f in ("key", "interval", "lower", "upper", "length", "angle",
                                        "reverse", "seed") if getattr(a, f) is not None}
    opts = Options(**{**(PRESETS[a.preset] if a.preset else {}), **given})
    if not 0 <= opts.lower <= 1 or not 0 <= opts.upper <= 1:
        print("pixelsort: --lower and --upper must be between 0 and 1", file=sys.stderr)
        return 2
    out = a.output or a.input.with_name(a.input.stem + ".sorted.png")
    t = time.perf_counter()
    try:
        if a.animate:
            if a.mask:
                raise ValueError("--animate does not support --mask yet")
            from PIL import Image

            from .animate import animate

            def bar(i: int, n: int) -> None:
                fill = int(30 * i / n)
                print(f"\r  sorting [{'#' * fill}{'.' * (30 - fill)}] {i}/{n}", end="",
                      file=sys.stderr, flush=True)

            img = Image.open(a.input)
            final = animate(img, opts, str(a.animate), seconds=a.seconds, fps=a.fps, on_progress=bar)
            print(file=sys.stderr)
            final.save(out)
            print(f"{a.animate}")
        else:
            sort_file(str(a.input), str(out), opts, str(a.mask) if a.mask else None)
    except (ValueError, RuntimeError) as e:
        print(f"pixelsort: {e}", file=sys.stderr)
        return 2
    print(f"{out}  ({time.perf_counter() - t:.1f}s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
