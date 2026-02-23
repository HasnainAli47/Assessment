import re
import requests

from config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    MAX_RETRIES, MIN_INPUT_WORDS, SYSTEM_PROMPT,
    summary_bounds,
)
from utils import count_words, is_health_content

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"\*(.+?)\*")
_HEADER = re.compile(r"^#{1,6}\s+", flags=re.MULTILINE)
_BULLET = re.compile(r"^[-*]\s+", flags=re.MULTILINE)


def _clean(text):
    """Strip leftover markdown formatting."""
    text = _BOLD.sub(r"\1", text)
    text = _ITALIC.sub(r"\1", text)
    text = _HEADER.sub("", text)
    text = _BULLET.sub("", text)
    return text.strip()


def _call_ollama(prompt):
    full = SYSTEM_PROMPT + "\n\n" + prompt
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": full,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 400},
        },
        timeout=120,
    )
    r.raise_for_status()
    return _clean(r.json().get("response", "").strip())


def _make_prompt(article, lo, hi, attempt):
    p = f"Summarize this health article in {lo} to {hi} words:\n\n{article}"
    if attempt > 0:
        p += (
            f"\n\nIMPORTANT: Your previous attempt was outside the {lo}-{hi} word range. "
            "Adjust carefully."
        )
    return p


class InputTooShortError(ValueError):
    pass


class NotHealthContentError(ValueError):
    pass


def summarize(article_text):
    wc_in = count_words(article_text)
    if wc_in < MIN_INPUT_WORDS:
        raise InputTooShortError(
            f"Article must be at least {MIN_INPUT_WORDS} words (got {wc_in})."
        )
    if not is_health_content(article_text):
        raise NotHealthContentError(
            "This doesn't look like a health/medical article. "
            "The system only processes health-related content."
        )

    lo, hi = summary_bounds(wc_in)

    summary, wc = "", 0
    for attempt in range(MAX_RETRIES + 1):
        summary = _call_ollama(_make_prompt(article_text, lo, hi, attempt))
        wc = count_words(summary)
        if lo <= wc <= hi:
            break

    return {
        "summary": summary,
        "word_count": wc,
        "retries": attempt,
        "target_min": lo,
        "target_max": hi,
    }
