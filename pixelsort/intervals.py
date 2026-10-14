"""Interval functions: which runs of a row get sorted together.

An interval function takes one row of pixels and returns a list of
``(start, end)`` slices. Pixels inside a slice are sorted among themselves;
pixels outside every slice never move. This is what turns a plain sort into
the "melting" look: bright runs stream sideways while dark edges hold still.
"""

from __future__ import annotations

import random
from typing import Callable, Sequence

from .keys import Key, Pixel

Span = tuple[int, int]


def whole_row(row: Sequence[Pixel], key: Key, **_: object) -> list[Span]:
    """Sort the entire row as one interval."""
    return [(0, len(row))] if row else []


def threshold(row: Sequence[Pixel], key: Key, lower: float = 0.25,
              upper: float = 0.8, **_: object) -> list[Span]:
    """Runs of pixels whose key falls inside ``[lower, upper]``.

    Pixels outside the band act as walls. Dark shadows and blown highlights
    stay where they are, everything in between gets dragged into streaks.
    """
    spans: list[Span] = []
    start = None
    for i, p in enumerate(row):
        inside = lower <= key(p) <= upper
        if inside and start is None:
            start = i
        elif not inside and start is not None:
            spans.append((start, i))
            start = None
    if start is not None:
        spans.append((start, len(row)))
    return [s for s in spans if s[1] - s[0] > 1]


def random_length(row: Sequence[Pixel], key: Key, length: int = 60,
                  rng: random.Random | None = None, **_: object) -> list[Span]:
    """Back-to-back intervals of random length, averaging ``length`` pixels."""
    rng = rng or random.Random()
    spans: list[Span] = []
    i, n = 0, len(row)
    while i < n:
        step = max(2, int(rng.uniform(0.2, 1.8) * length))
        spans.append((i, min(n, i + step)))
        i += step
    return spans


def edges(row: Sequence[Pixel], key: Key, lower: float = 0.08,
          **_: object) -> list[Span]:
    """Split wherever neighbouring pixels jump by more than ``lower``.

    Sorting stops at strong edges, so shapes keep their outline while their
    insides smear.
    """
    if not row:
        return []
    spans: list[Span] = []
    start = 0
    prev = key(row[0])
    for i in range(1, len(row)):
        cur = key(row[i])
        if abs(cur - prev) > lower:
            if i - start > 1:
                spans.append((start, i))
            start = i
        prev = cur
    if len(row) - start > 1:
        spans.append((start, len(row)))
    return spans


INTERVALS: dict[str, Callable[..., list[Span]]] = {
    "threshold": threshold,
    "random": random_length,
    "edges": edges,
    "none": whole_row,
}


def get_interval(name: str) -> Callable[..., list[Span]]:
    try:
        return INTERVALS[name]
    except KeyError:
        raise ValueError(f"unknown interval {name!r}; choose from {', '.join(INTERVALS)}") from None
