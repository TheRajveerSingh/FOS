"""
ml_models.py
------------
Loads heavy ML models ONCE at import time so every request reuses
the same in-memory objects (no repeated cold-start delays).
 
Models used
-----------
1. cardiffnlp/twitter-roberta-base-irony
   - Fine-tuned RoBERTa for irony / sarcasm detection
   - Returns labels: IRONY / NON_IRONY with a confidence score
 
2. VADER SentimentIntensityAnalyzer (from nltk)
   - Lexicon-based sentiment scorer
   - compound score in [-1, +1]; extremes signal hyperbole
 
3. WordNet (via nltk.corpus)
   - Used for semantic distance in metaphor detection
"""
 
import nltk
 
# ── NLTK data ────────────────────────────────────────────────────────────────
for pkg in ('punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng', 'vader_lexicon', 'wordnet',
            'omw-1.4'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass
 
# ── VADER ─────────────────────────────────────────────────────────────────────
from nltk.sentiment.vader import SentimentIntensityAnalyzer
vader = SentimentIntensityAnalyzer()
 
# ── Transformer (irony / sarcasm) ─────────────────────────────────────────────
# We wrap the import in a try/except so the whole app still works if
# `transformers` or `torch` is not installed — it just falls back to
# the old rule-based approach.
sarcasm_pipeline = None
SARCASM_MODEL = "cardiffnlp/twitter-roberta-base-irony"
 
try:
    from transformers import pipeline as hf_pipeline
    sarcasm_pipeline = hf_pipeline(
        "text-classification",
        model=SARCASM_MODEL,
        top_k=None,          # return scores for ALL labels
        truncation=True,
        max_length=128,
    )
    print(f"[ml_models] Sarcasm/Irony model loaded: {SARCASM_MODEL}")
except Exception as e:
    print(f"[ml_models] WARNING — Could not load transformer model: {e}")
    print("[ml_models] Falling back to rule-based sarcasm detection.")
 
# ── WordNet ───────────────────────────────────────────────────────────────────
from nltk.corpus import wordnet as wn
 
 
# ── Public helpers ────────────────────────────────────────────────────────────
 
def get_sarcasm_score(text: str) -> dict:
    """
    Returns a dict:
        {
          "is_sarcastic": bool,
          "confidence":   float,   # 0-1
          "method":       str      # "transformer" | "rules"
        }
 
    Uses the RoBERTa model when available, otherwise falls back to
    the original keyword-matching rules.
    """
    if sarcasm_pipeline is not None:
        try:
            results = sarcasm_pipeline(text)[0]   # list of {label, score}
            label_map = {r['label'].lower(): r['score'] for r in results}
            # Model labels are 'irony' and 'non_irony' (lowercase)
            irony_score = label_map.get('irony', 0.0)
            return {
                "is_sarcastic": irony_score > 0.55,   # tunable threshold
                "confidence":   round(irony_score, 3),
                "method":       "transformer"
            }
        except Exception as e:
            print(f"[ml_models] Transformer inference failed: {e}")
 
    # ── Rule-based fallback ────────────────────────────────────────────────
    text_lower = text.lower()
    markers = [
        "yeah, right", "oh, great", "what a surprise",
        "just what i needed", "clear as mud", "big deal",
        "tell me about it", "oh, fantastic",
    ]
    hit = any(m in text_lower for m in markers)
    return {
        "is_sarcastic": hit,
        "confidence":   0.85 if hit else 0.15,
        "method":       "rules"
    }
 
 
def get_vader_intensity(text: str) -> float:
    """
    Returns the VADER compound score for `text` in the range [-1, +1].
    Scores near ±1 indicate extreme sentiment — a useful proxy for
    hyperbolic language.
    """
    return vader.polarity_scores(text)['compound']
 
 
def wordnet_path_similarity(word1: str, word2: str) -> float | None:
    """
    Returns the maximum Wu-Palmer path similarity between any two
    noun synsets for word1 and word2 (0 = unrelated, 1 = identical).
    Returns None if either word has no noun synsets.
    """
    synsets1 = wn.synsets(word1, pos=wn.NOUN)
    synsets2 = wn.synsets(word2, pos=wn.NOUN)
    if not synsets1 or not synsets2:
        return None
 
    best = 0.0
    for s1 in synsets1[:3]:   # limit to top-3 senses for speed
        for s2 in synsets2[:3]:
            try:
                sim = s1.wup_similarity(s2)
                if sim and sim > best:
                    best = sim
            except Exception:
                pass
    return round(best, 3) if best > 0 else None