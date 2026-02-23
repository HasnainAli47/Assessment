import json, os, re
from pathlib import Path
import pandas as pd

from config import (
    RESULTS_DIR, SUMMARIES_FILE, EVALUATION_FILE,
    HEALTH_KEYWORDS, MIN_HEALTH_KEYWORD_HITS,
)

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?%?")


def count_words(text):
    return len(text.split())


def extract_numbers(text):
    """Pull out all numeric tokens (integers, decimals, percentages)."""
    return set(NUMBER_PATTERN.findall(text))


def is_health_content(text):
    """Quick keyword check — rejects non-medical text before it reaches the LLM."""
    lower = text.lower()
    words = set(lower.split())
    hits = sum(1 for kw in HEALTH_KEYWORDS if kw in words or kw in lower)
    return hits >= MIN_HEALTH_KEYWORD_HITS


def ensure_dirs():
    for d in (RESULTS_DIR, "data/raw_articles", "data/processed"):
        os.makedirs(d, exist_ok=True)


def save_summaries_json(records):
    ensure_dirs()
    with open(SUMMARIES_FILE, "w") as f:
        json.dump(records, f, indent=2)


def save_evaluation_csv(records):
    ensure_dirs()
    cols = [
        "article_id", "word_count", "target_range", "fkgl", "fre",
        "entity_coverage", "missing_numbers", "hallucination_flag",
        "risk_level", "escalate",
    ]
    df = pd.DataFrame(records)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df[cols].to_csv(EVALUATION_FILE, index=False)


def load_articles(directory="data/raw_articles"):
    """Read every .txt file in the directory, return list of {id, text}."""
    articles = []
    folder = Path(directory)
    if not folder.exists():
        return articles
    for fp in sorted(folder.glob("*.txt")):
        articles.append({"id": fp.stem, "text": fp.read_text(encoding="utf-8").strip()})
    return articles
