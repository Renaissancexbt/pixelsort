"""Sort keys: how a pixel turns into a number.

Every key maps an ``(r, g, b)`` tuple with channels in ``0..255`` to a float in
``0.0..1.0``. Thresholds on the command line use the same scale, so
``--lower 0.25`` means "a quarter of the way up" for any key.
"""

from __future__ import annotations

import colorsys
from typing import Callable

Pixel = tuple[int, ...]
Key = Callable[[Pixel], float]


def lightness(p: Pixel) -> float:
    """Perceived brightness (Rec. 709 luma)."""
    return (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255.0


def intensity(p: Pixel) -> float:
    """Plain average of the three channels."""
    return (p[0] + p[1] + p[2]) / 765.0


def hue(p: Pixel) -> float:
    """Position on the colour wheel, red at 0.0."""
    return colorsys.rgb_to_hsv(p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)[0]


def saturation(p: Pixel) -> float:
    """How far the colour is from grey."""
    return colorsys.rgb_to_hsv(p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)[1]


def red(p: Pixel) -> float:
    return p[0] / 255.0


def green(p: Pixel) -> float:
    return p[1] / 255.0


def blue(p: Pixel) -> float:
    return p[2] / 255.0


KEYS: dict[str, Key] = {
    "lightness": lightness,
    "intensity": intensity,
    "hue": hue,
    "saturation": saturation,
    "red": red,
    "green": green,
    "blue": blue,
}


def get_key(name: str) -> Key:
    try:
        return KEYS[name]
    except KeyError:
        raise ValueError(f"unknown key {name!r}; choose from {', '.join(KEYS)}") from None
