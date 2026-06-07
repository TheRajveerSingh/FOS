"""
ml_models.py
------------
Loads heavy ML models ONCE at import time so every request reuses
the same in-memory objects (no repeated cold-start delays).
 
Models used
-----------
1. cardiffnlp/twitter-roberta-base-irony  (transformer, sarcasm)
2. VADER SentimentIntensityAnalyzer       (sentiment, hyperbole)
3. WordNet via nltk.corpus                (semantic distance, metaphor/simile)
4. Brown Corpus Bigram Model              (N-gram, idiom detection)
5. CMU Pronouncing Dictionary             (phoneme, alliteration)
"""
 
import math
import nltk
from collections import defaultdict
 
# ── NLTK data ─────────────────────────────────────────────────────────────────
for pkg in ('punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng', 'vader_lexicon',
            'wordnet', 'omw-1.4', 'brown'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass
 
# ── VADER ──────────────────────────────────────────────────────────────────────
from nltk.sentiment.vader import SentimentIntensityAnalyzer
vader = SentimentIntensityAnalyzer()
 
# ── Transformer (irony / sarcasm) ──────────────────────────────────────────────
sarcasm_pipeline = None
SARCASM_MODEL = "cardiffnlp/twitter-roberta-base-irony"
 
try:
    from transformers import pipeline as hf_pipeline
    sarcasm_pipeline = hf_pipeline(
        "text-classification",
        model=SARCASM_MODEL,
        top_k=None,
        truncation=True,
        max_length=128,
    )
    print(f"[ml_models] Sarcasm/Irony model loaded: {SARCASM_MODEL}")
except Exception as e:
    print(f"[ml_models] WARNING — Could not load transformer model: {e}")
    print("[ml_models] Falling back to rule-based sarcasm detection.")
 
# ── WordNet ────────────────────────────────────────────────────────────────────
from nltk.corpus import wordnet as wn
 
# ── Brown Corpus Bigram Model ──────────────────────────────────────────────────
print("[ml_models] Building Brown corpus bigram model...")
_unigram_counts = defaultdict(int)
_bigram_counts  = defaultdict(int)
_total_tokens   = 1
 
try:
    from nltk.corpus import brown
    for sent in brown.sents():
        tokens = [w.lower() for w in sent]
        for w in tokens:
            _unigram_counts[w] += 1
        for i in range(len(tokens) - 1):
            _bigram_counts[(tokens[i], tokens[i + 1])] += 1
    _total_tokens = sum(_unigram_counts.values())
    print(f"[ml_models] Bigram model ready ({_total_tokens:,} tokens).")
except Exception as e:
    print(f"[ml_models] WARNING — Brown corpus failed: {e}")
 
# ── CMU Pronouncing Dictionary ─────────────────────────────────────────────────
_pronouncing_available = False
try:
    import pronouncing  # noqa: F401
    _pronouncing_available = True
    print("[ml_models] CMU Pronouncing Dictionary loaded.")
except ImportError:
    print("[ml_models] WARNING — `pronouncing` not found. "
          "Install: pip install pronouncing")
 
 
# ══════════════════════════════════════════════════════════════════════════════
# Public helpers
# ══════════════════════════════════════════════════════════════════════════════
 
def get_sarcasm_score(text: str) -> dict:
    if sarcasm_pipeline is not None:
        try:
            results     = sarcasm_pipeline(text)[0]
            label_map   = {r['label'].lower(): r['score'] for r in results}
            irony_score = label_map.get('irony', 0.0)
            return {"is_sarcastic": irony_score > 0.55,
                    "confidence": round(irony_score, 3),
                    "method": "transformer"}
        except Exception as e:
            print(f"[ml_models] Transformer inference failed: {e}")
 
    text_lower = text.lower()
    markers = ["yeah, right", "oh, great", "what a surprise",
               "just what i needed", "clear as mud", "big deal",
               "tell me about it", "oh, fantastic"]
    hit = any(m in text_lower for m in markers)
    return {"is_sarcastic": hit,
            "confidence": 0.85 if hit else 0.15,
            "method": "rules"}
 
 
def get_vader_intensity(text: str) -> float:
    return vader.polarity_scores(text)['compound']
 
 
def wordnet_path_similarity(word1: str, word2: str):
    s1 = wn.synsets(word1, pos=wn.NOUN)
    s2 = wn.synsets(word2, pos=wn.NOUN)
    if not s1 or not s2:
        return None
    best = 0.0
    for a in s1[:3]:
        for b in s2[:3]:
            try:
                sim = a.wup_similarity(b)
                if sim and sim > best:
                    best = sim
            except Exception:
                pass
    return round(best, 3) if best > 0 else None
 
 
def wordnet_synonyms(word: str) -> set:
    """All lemma names for `word` across every synset."""
    syns = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            syns.add(lemma.name().lower().replace('_', ' '))
    return syns
 
 
def bigram_log_probability(phrase: str) -> float:
    """
    Average log-probability of consecutive bigrams in `phrase` using the
    Brown corpus model with Laplace smoothing.
    Lower (more negative) = more statistically unusual = stronger idiom signal.
    """
    words = phrase.lower().split()
    if len(words) < 2:
        return 0.0
    log_prob = 0.0
    count    = 0
    vocab_size = len(_unigram_counts)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        bc = _bigram_counts.get((w1, w2), 0)
        uc = _unigram_counts.get(w1, 0)
        prob      = (bc + 1) / (uc + vocab_size + 1)
        log_prob += math.log(prob)
        count    += 1
    return log_prob / count if count else 0.0
 
 
def get_first_phoneme(word: str):
    """
    Returns the first ARPAbet phoneme of `word` (stress digits stripped),
    e.g. 'phone' -> 'F', 'cat' -> 'K'.
    Returns None if word not in CMU dict or library not installed.
    """
    if not _pronouncing_available:
        return None
    try:
        import pronouncing
        phones_list = pronouncing.phones_for_word(word.lower())
        if phones_list:
            first = phones_list[0].split()[0]
            return ''.join(c for c in first if c.isalpha())
        return None
    except Exception:
        return None
 
 
def pronouncing_available() -> bool:
    return _pronouncing_available