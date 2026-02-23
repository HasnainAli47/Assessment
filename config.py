OLLAMA_MODEL = "gemma3:4b"
OLLAMA_BASE_URL = "http://localhost:11434"

SUMMARY_RATIO_LOW = 0.30  
SUMMARY_RATIO_HIGH = 0.50  
SUMMARY_FLOOR = 25         
SUMMARY_CEILING = 200      
MAX_RETRIES = 2

# minimum input length 
MIN_INPUT_WORDS = 30

SPACY_MODEL = "en_core_web_sm"
SCISPACY_MODEL = "en_core_sci_sm"  
KEY_NER_LABELS = {
    "ORG", "GPE", "PERSON", "DATE",
    "PERCENT", "MONEY", "QUANTITY",
}

ENTITY_COVERAGE_THRESHOLD = 0.6    
ESCALATION_COVERAGE_THRESHOLD = 0.5  
FKGL_HARD_THRESHOLD = 10   
FKGL_ESCALATION_THRESHOLD = 12  

SYSTEM_PROMPT = (
    "You are a medical summarization assistant.\n"
    "Rules:\n"
    "- Neutral, objective tone.\n"
    "- Preserve all numbers and statistics exactly.\n"
    "- Add uncertainty caveats ('according to the study', 'data suggests') "
    "where appropriate.\n"
    "- Do NOT invent or fabricate any facts not in the article.\n"
    "- Do NOT use markdown (no bold, italic, headers, bullets).\n"
    "- Return ONLY the plain-text summary."
)

# simple keyword gate to reject non-medical input 
HEALTH_KEYWORDS = {
    "patient", "patients", "clinical", "treatment", "therapy", "disease",
    "diagnosis", "symptom", "symptoms", "medical", "health", "healthcare",
    "hospital", "physician", "doctor", "surgery", "drug", "drugs",
    "medication", "medicine", "vaccine", "vaccination", "immunization",
    "infection", "virus", "chronic", "acute", "mortality",
    "prevalence", "incidence", "epidemic", "pandemic",
    "cancer", "tumor", "diabetes", "cardiovascular", "cardiac", "stroke",
    "respiratory", "pulmonary", "neurological",
    "psychiatric", "mental", "depression", "anxiety", "obesity",
    "hypertension", "insulin", "antibiotic", "chemotherapy",
    "transplant", "biomarker", "pharmacology", "efficacy", "adverse",
    "placebo", "randomized", "controlled", "trial", "cohort",
    "epidemiology", "public health", "who", "cdc", "nih", "fda",
    "blood", "cell", "cells", "organ", "tissue", "protein", "gene",
    "immune", "immunity", "inflammation", "disorder", "syndrome",
    "hospitalization", "icu", "telehealth", "screening",
    "study", "studies", "research", "participants",
}
MIN_HEALTH_KEYWORD_HITS = 5

# output paths
RESULTS_DIR = "results"
SUMMARIES_FILE = "results/summaries.json"
EVALUATION_FILE = "results/evaluation.csv"
RAW_ARTICLES_DIR = "data/raw_articles"


def summary_bounds(input_word_count):
    """Calculate the target min/max summary words based on input length."""
    lo = max(SUMMARY_FLOOR, int(input_word_count * SUMMARY_RATIO_LOW))
    hi = max(lo + 5, int(input_word_count * SUMMARY_RATIO_HIGH))
    lo = min(lo, SUMMARY_CEILING)
    hi = min(hi, SUMMARY_CEILING)
    return lo, hi
