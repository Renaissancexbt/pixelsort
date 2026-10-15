import random

import pytest
from PIL import Image

np = pytest.importorskip("numpy")

from pixelsort import Options, pixelsort  # noqa: E402
from pixelsort.animate import frames, write  # noqa: E402
from pixelsort.cli import main  # noqa: E402
from pixelsort.core import pixels  # noqa: E402


def noise(w=40, h=28, seed=5):
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h))
    img.putdata([(rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(w * h)])
    return img


@pytest.mark.parametrize("opts", [
    Options(),
    Options(angle=90, lower=0.2, upper=0.9),
    Options(angle=270, reverse=True, lower=0.1, upper=0.7),
    Options(angle=30),
    Options(key="hue", interval="random", length=9, seed=4),
    Options(interval="edges", lower=0.1),
    Options(interval="none", reverse=True),
])
def test_last_frame_equals_still(opts):
    img = noise()
    fs = frames(img, opts, seconds=0.5, fps=10, hold=0.2)
    assert pixels(fs[-1]) == pixels(pixelsort(img, opts))


def test_first_frame_is_original():
    img = noise()
    fs = frames(img, Options(), seconds=0.5, fps=10)
    assert pixels(fs[0]) == pixels(img)


def test_gif_and_cli(tmp_path):
    img = noise()
    fs = frames(img, Options(), seconds=0.4, fps=10, hold=0.2)
    write(fs, str(tmp_path / "a.gif"), fps=10)
    assert Image.open(tmp_path / "a.gif").n_frames > 1
    src = tmp_path / "in.png"
    img.save(src)
    assert main([str(src), "--animate", str(tmp_path / "b.gif"), "--seconds", "0.4", "--fps", "10"]) == 0
    assert (tmp_path / "b.gif").exists() and (tmp_path / "in.sorted.png").exists()
