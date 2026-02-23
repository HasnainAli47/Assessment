import spacy
import textstat
from rouge_score import rouge_scorer

from config import (
    SPACY_MODEL, SCISPACY_MODEL,
    KEY_NER_LABELS, ENTITY_COVERAGE_THRESHOLD,
)
from utils import extract_numbers

# lazy-loaded models
_nlp = None
_sci_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(SPACY_MODEL)
    return _nlp


def _get_sci_nlp():
    global _sci_nlp
    if _sci_nlp is None:
        try:
            _sci_nlp = spacy.load(SCISPACY_MODEL)
        except OSError:
            _sci_nlp = False
    return _sci_nlp



def readability_scores(text):
    return {
        "fkgl": round(textstat.flesch_kincaid_grade(text), 2),
        "fre": round(textstat.flesch_reading_ease(text), 2),
    }



def extract_entities(text):
    nlp = _get_nlp()
    doc = nlp(text)
    ents = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents if ent.label_ in KEY_NER_LABELS
    ]
    sci = _get_sci_nlp()
    if sci and sci is not False:
        for ent in sci(text).ents:
            ents.append({"text": ent.text, "label": "DISEASE/ENTITY"})
    return ents


def _ent_texts(ents):
    return {e["text"].lower().strip() for e in ents}



def entity_coverage(original, summary):
    orig = _ent_texts(extract_entities(original))
    if not orig:
        return 1.0  # nothing to miss
    summ = _ent_texts(extract_entities(summary))
    summary_lower = summary.lower()
    matched = sum(1 for e in orig if e in summ or e in summary_lower)
    return round(matched / len(orig), 4)


def entity_coverage_flag(cov):
    return cov < ENTITY_COVERAGE_THRESHOLD


def hallucination_check(original, summary):
    orig = _ent_texts(extract_entities(original))
    summ = _ent_texts(extract_entities(summary))
    original_lower = original.lower()
    extra = {e for e in summ if e not in orig and e not in original_lower}
    return {
        "extra_entities": sorted(extra),
        "count": len(extra),
        "hallucination_flag": len(extra) > 0,
    }


def numeric_consistency(original, summary):
    orig_nums = extract_numbers(original)
    summ_nums = extract_numbers(summary)
    missing = orig_nums - summ_nums
    return {
        "original_numbers": sorted(orig_nums),
        "summary_numbers": sorted(summ_nums),
        "missing_numbers": sorted(missing),
        "has_missing": len(missing) > 0,
    }

def rouge_scores(summary, reference=None):
    if not reference:
        return None
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    s = scorer.score(reference, summary)
    return {
        "rouge1_f": round(s["rouge1"].fmeasure, 4),
        "rougeL_f": round(s["rougeL"].fmeasure, 4),
    }




def evaluate(original, summary, reference=None):
    rd = readability_scores(summary)
    cov = entity_coverage(original, summary)
    hall = hallucination_check(original, summary)
    nums = numeric_consistency(original, summary)
    rouge = rouge_scores(summary, reference)

    return {
        **rd,
        "entity_coverage": cov,
        "entity_coverage_low": entity_coverage_flag(cov),
        "hallucination": hall,
        "hallucination_flag": hall["hallucination_flag"],
        "hallucinated_entities": hall["extra_entities"],
        "numeric": nums,
        "missing_numbers": nums["has_missing"],
        "rouge": rouge,
    }
