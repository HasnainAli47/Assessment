import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluator import entity_coverage, entity_coverage_flag


def test_returns_float():
    cov = entity_coverage(
        "The WHO reported COVID-19 affected 200 million people in 2023.",
        "WHO noted COVID-19 impacted 200 million individuals in 2023.",
    )
    assert isinstance(cov, float)


def test_always_between_zero_and_one():
    cov = entity_coverage(
        "Dr. Smith from the CDC in Atlanta reported 45% efficacy on January 5.",
        "A study reported efficacy results.",
    )
    assert 0.0 <= cov <= 1.0


def test_identical_text_gives_full_coverage():
    text = "The World Health Organization declared a pandemic."
    assert entity_coverage(text, text) == 1.0


def test_no_entities_means_nothing_to_miss():
    assert entity_coverage(
        "There are many possible outcomes in this scenario.",
        "Outcomes vary widely.",
    ) == 1.0


def test_flag_triggers_below_threshold():
    assert entity_coverage_flag(0.5) is True
    assert entity_coverage_flag(0.8) is False
