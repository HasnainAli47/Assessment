import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import extract_numbers
from evaluator import numeric_consistency


def test_integers():
    assert extract_numbers("There were 500 cases") == {"500"}


def test_decimals():
    assert extract_numbers("Rate was 3.14 per 1000") == {"3.14", "1000"}


def test_percentages():
    assert "94.5%" in extract_numbers("Efficacy was 94.5% in the trial")


def test_mixed():
    nums = extract_numbers("In 2023, 42% of 1200 patients had 2.5 point gain")
    assert nums == {"2023", "42%", "1200", "2.5"}


def test_no_numbers():
    assert extract_numbers("No numbers here") == set()


def test_consistency_all_present():
    r = numeric_consistency(
        "85% efficacy among 300 patients.",
        "Efficacy was 85% in 300 patients.",
    )
    assert r["has_missing"] is False


def test_consistency_detects_missing():
    r = numeric_consistency(
        "85% efficacy among 300 patients in 2023.",
        "The study reported efficacy findings.",
    )
    assert r["has_missing"] is True
    assert len(r["missing_numbers"]) > 0
