from config import (
    FKGL_HARD_THRESHOLD, FKGL_ESCALATION_THRESHOLD,
    ESCALATION_COVERAGE_THRESHOLD,
)


def compute_risk(eval_result, word_count, target_min, target_max):
    flags = {
        "missing_numbers":     bool(eval_result.get("missing_numbers")),
        "low_entity_coverage": bool(eval_result.get("entity_coverage_low")),
        "hard_readability":    eval_result.get("fkgl", 0) > FKGL_HARD_THRESHOLD,
        "hallucination":       bool(eval_result.get("hallucination_flag")),
        "toxicity_flag":       False,  
        "length_violation":    not (target_min <= word_count <= target_max),
    }

    score = sum(flags.values())
    if score >= 2:
        level = "High"
    elif score == 1:
        level = "Medium"
    else:
        level = "Low"

    cov = eval_result.get("entity_coverage", 1.0)
    fkgl = eval_result.get("fkgl", 0)

    escalate = (
        level == "High"
        or cov < ESCALATION_COVERAGE_THRESHOLD
        or flags["length_violation"]
        or flags["hallucination"]
        or fkgl > FKGL_ESCALATION_THRESHOLD
    )

    return {
        "flags": flags,
        "risk_score": score,
        "risk_level": level,
        "escalate": escalate,
    }
