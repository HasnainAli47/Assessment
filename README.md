# HEAL-Summ-Lite

**Track B -- HEAL-Summ-Lite (NLP / Summarization + Quality Checks)**

A local health-article summarization tool with built-in quality checks, risk scoring, and a human-review escalation rule.

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# pull the model (Ollama must be installed)
ollama pull gemma3:4b

# start the server
uvicorn app:app --reload --port 8000
```

Open http://localhost:8000, drop `.txt` articles into `data/raw_articles/`, and click *Process articles*.

---

## System Design

### Pipeline Overview

The pipeline has four stages:

### 1. Summarise

Ollama (`gemma3:4b`) generates a summary whose length scales with the input. The target is 30-50% of the article's word count, clamped to:

- **Minimum:** 25 words
- **Maximum:** 200 words

If the word count falls outside the target range, the system retries up to twice using a stricter prompt. A lightweight keyword gate blocks clearly non-medical content before it reaches the LLM.

### 2. Evaluate

Five independent checks run on every summary:

- **Readability** -- Flesch-Kincaid Grade Level (FKGL) + Reading Ease
- **Entity Coverage** -- fraction of original named entities preserved
- **Hallucination Detection** -- entities present in the summary but not in the source
- **Numeric Consistency** -- preservation of original statistics
- **ROUGE** -- optional, when a reference summary is provided

### 3. Risk Scoring

Six binary flags are tallied:

- Missing numbers
- Low entity coverage
- Hard readability
- Hallucination
- Toxicity (reserved)
- Length violation

Risk levels:

- 0 → Low
- 1 → Medium
- 2+ → High

### 4. Human Review

A summary is escalated if **any** of the following hold:

- Risk level = High
- Entity coverage < 50%
- Word count outside target range
- Hallucination detected
- FKGL > 12

---

## Threshold Justification

- **FKGL 10 / 12:** CDC recommends health materials at ~8th-grade level. 10 flags, 12 forces escalation.
- **Entity coverage 0.6 / 0.5:** Below 60% summaries typically omit key information. Below 50% factual reliability drops sharply.
- **Dynamic length (30-50%):** Prevents short articles from being expanded (hallucination risk) and long ones from being under-compressed.

---

## Assessment Write-Up (Required)

### Approach Used and Why

I implemented a local LLM-based summarization system using Ollama (`gemma3:4b`) combined with a deterministic validation layer. The goal was not just to generate summaries, but to wrap LLM output inside transparent safety checks aligned with the ethical focus of HEAL-Summ.

I chose a local model over cloud APIs to ensure zero data exfiltration and full reproducibility.

### Assumptions Made

- Input articles are English-language health content.
- Articles are at least ~30 words long.
- Substring-based entity matching is sufficient for a lightweight prototype.
- Conservative thresholds are preferable in health contexts (false positives are safer than false negatives).

### What Worked

- The hallucination detector reliably flagged fabricated entities.
- Numeric consistency checks caught rounding and dropped statistics.
- Dynamic compression avoided expansion-based hallucinations on short inputs.
- The escalation rule successfully blocked high-risk summaries.

### Failure Case

Small 4B models frequently drop exact numbers (e.g., replacing "89.3%" with "approximately 90%") or omit statistics entirely. The retry mechanism mitigates this but does not fully eliminate it.

The model can also fabricate structured medical details when given vague input. Entity-level hallucination detection catches many of these cases, but relationship-level fabrications remain possible.

### Evaluation Metric Used

The primary evaluation metric is **Entity Coverage Ratio** -- the fraction of original named entities preserved in the summary.

This directly measures factual completeness. Readability (FKGL) is used as a secondary accessibility check.

### Human Review Rule

Any summary containing hallucinated entities, coverage below 50%, FKGL above 12, or length violation is automatically escalated.

No high-risk summary is delivered without human oversight.

---

## Known Limitations

- Substring entity matching can inflate coverage scores.
- Numeric regex does not capture written numbers or ranges.
- Hallucination detection operates at entity level only.
- Small models may preserve terminology but remain difficult to read (high FKGL).

## Future Improvements

- Fine-tune on medical summarization corpora (PubMed abstracts)
- Integrate scispaCy entity linking (UMLS)
- Add sentence-level confidence scoring
- Activate toxicity detection
- Replace substring matching with lemmatized or embedding-based comparison

---

## Project Layout

```
├── app.py              # FastAPI server + embedded UI
├── summarizer.py       # Ollama calls, retry logic, input validation
├── evaluator.py        # readability, NER, coverage, hallucination, ROUGE
├── risk.py             # flag counting, risk levels, escalation rules
├── utils.py            # shared helpers
├── config.py           # all tuneable constants
├── data/raw_articles/  # input .txt files go here
├── results/            # output JSON + CSV
├── tests/              # pytest suite
├── requirements.txt
└── README.md
```

## Tests

```bash
pytest tests/ -v
```

## Tools Used

| Tool | Purpose |
|---|---|
| Ollama (gemma3:4b) | Summary generation |
| spaCy | Named entity recognition |
| scispaCy | Biomedical NER (optional) |
| textstat | Readability scoring |
| rouge-score | ROUGE evaluation |
| FastAPI | Web server |

**Disclosure:** Summaries are generated by an LLM. All validation, scoring, risk classification, and escalation logic is deterministic code implemented by the developer.
