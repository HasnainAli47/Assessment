import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import count_words
from config import summary_bounds, SUMMARY_FLOOR, SUMMARY_CEILING


def test_basic_counting():
    assert count_words("hello world") == 2
    assert count_words("") == 0


def test_multiline():
    assert count_words("one two\nthree four") == 4


def test_bounds_short_article():
    # 60-word article → should get a small target, but not below floor
    lo, hi = summary_bounds(60)
    assert lo >= SUMMARY_FLOOR
    assert hi > lo
    assert hi <= 60  # never exceed input length


def test_bounds_medium_article():
    # 400-word article → 30-50% = 120-200
    lo, hi = summary_bounds(400)
    assert lo == 120
    assert hi == 200


def test_bounds_long_article():
    # 1000-word article → ratio says 300-500 but ceiling caps at 200
    lo, hi = summary_bounds(1000)
    assert lo <= SUMMARY_CEILING
    assert hi <= SUMMARY_CEILING


def test_bounds_always_valid():
    # across a range of inputs, lo < hi and both are positive
    for n in [30, 50, 80, 150, 300, 600, 1200]:
        lo, hi = summary_bounds(n)
        assert 0 < lo < hi or lo == hi == SUMMARY_CEILING
        assert lo >= SUMMARY_FLOOR
