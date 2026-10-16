"""pixelsort: glitch art by sorting pixels."""

from .core import Options, pixelsort, sort_file, sort_row
from .intervals import INTERVALS
from .keys import KEYS
from .presets import PRESETS, preset

__version__ = "0.3.0"
__all__ = ["Options", "pixelsort", "sort_file", "sort_row", "KEYS", "INTERVALS", "PRESETS", "preset"]
