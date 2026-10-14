import random

import pytest

from pixelsort.intervals import edges, random_length, threshold, whole_row
from pixelsort.keys import KEYS, get_key, hue, lightness

BLACK, WHITE, GREY = (0, 0, 0), (255, 255, 255), (128, 128, 128)


def test_keys_are_normalised():
    for name, k in KEYS.items():
        for p in [BLACK, WHITE, GREY, (255, 0, 0), (0, 255, 0), (12, 200, 99)]:
            assert 0.0 <= k(p) <= 1.0, name


def test_lightness_orders_black_grey_white():
    assert lightness(BLACK) < lightness(GREY) < lightness(WHITE)


def test_hue_red_is_zero():
    assert hue((255, 0, 0)) == 0.0


def test_unknown_key():
    with pytest.raises(ValueError):
        get_key("vibes")


def test_threshold_walls():
    row = [BLACK, GREY, GREY, BLACK, GREY, GREY, GREY, WHITE]
    assert threshold(row, lightness, lower=0.25, upper=0.8) == [(1, 3), (4, 7)]


def test_threshold_drops_single_pixel_runs():
    row = [BLACK, GREY, BLACK]
    assert threshold(row, lightness) == []


def test_random_length_covers_row_once():
    row = [GREY] * 500
    spans = random_length(row, lightness, length=40, rng=random.Random(1))
    assert spans[0][0] == 0 and spans[-1][1] == 500
    assert all(a[1] == b[0] for a, b in zip(spans, spans[1:]))


def test_edges_split_on_jumps():
    row = [BLACK, BLACK, WHITE, WHITE, WHITE]
    assert edges(row, lightness, lower=0.5) == [(0, 2), (2, 5)]


def test_whole_row():
    assert whole_row([GREY] * 3, lightness) == [(0, 3)]
    assert whole_row([], lightness) == []
