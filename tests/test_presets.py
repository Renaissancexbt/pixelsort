import re
from pathlib import Path

import pytest
from PIL import Image

from pixelsort import PRESETS, Options, pixelsort, preset
from pixelsort.cli import main
from pixelsort.core import pixels

ROOT = Path(__file__).resolve().parent.parent


def test_preset_overrides():
    o = preset("rain", lower=0.3)
    assert o.angle == 270 and o.reverse and o.lower == 0.3


def test_unknown_preset():
    with pytest.raises(ValueError):
        preset("vaporwave")


def test_presets_match_playground():
    """The browser playground and the CLI must offer the same named looks."""
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    block = re.search(r"const PRESETS = \[(.*?)\];", html, re.S).group(1)
    names = re.findall(r'\["(\w+)"', block)
    assert names == list(PRESETS)


def test_cli_preset_equals_flags(tmp_path):
    src = tmp_path / "in.png"
    Image.effect_noise((40, 30), 60).convert("RGB").save(src)
    assert main([str(src), "--preset", "drip", "-o", str(tmp_path / "a.png")]) == 0
    assert main([str(src), "--angle", "90", "--lower", "0.2", "--upper", "0.9", "-o", str(tmp_path / "b.png")]) == 0
    assert pixels(Image.open(tmp_path / "a.png")) == pixels(Image.open(tmp_path / "b.png"))


def test_cli_flag_beats_preset(tmp_path):
    src = tmp_path / "in.png"
    img = Image.effect_noise((40, 30), 60).convert("RGB")
    img.save(src)
    assert main([str(src), "--preset", "rain", "--angle", "0", "-o", str(tmp_path / "c.png")]) == 0
    want = pixelsort(img, Options(**{**PRESETS["rain"], "angle": 0}))
    assert pixels(Image.open(tmp_path / "c.png").convert("RGB")) == pixels(want.convert("RGB"))
