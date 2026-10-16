"""Named looks, shared with the browser playground (docs/index.html)."""

from __future__ import annotations

from .core import Options

PRESETS: dict[str, dict] = {
    "melt": {},
    "drip": {"angle": 90, "lower": 0.2, "upper": 0.9},
    "rain": {"angle": 270, "reverse": True, "lower": 0.1, "upper": 0.7},
    "diagonal": {"angle": 30, "lower": 0.15, "upper": 0.95},
    "rainbow": {"key": "hue", "interval": "random", "length": 140, "seed": 4},
    "outline": {"interval": "edges", "lower": 0.1},
}


def preset(name: str, **overrides) -> Options:
    """Options for a named look, with any keyword overriding the preset."""
    try:
        base = PRESETS[name]
    except KeyError:
        raise ValueError(f"unknown preset {name!r}; choose from {', '.join(PRESETS)}") from None
    return Options(**{**base, **overrides})


__all__ = ["PRESETS", "preset"]
