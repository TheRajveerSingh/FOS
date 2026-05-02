import re
import nltk
import difflib
from nltk.tokenize import word_tokenize, sent_tokenize

# ML helpers (transformer + VADER + WordNet) — loaded once at import
from ml_models import get_sarcasm_score, get_vader_intensity, wordnet_path_similarity

# ── NLTK data ─────────────────────────────────────────────────────────────────
for pkg in ('punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def highlight_context(sentence, match_text):
    pattern = re.compile(re.escape(match_text), re.IGNORECASE)
    match = pattern.search(sentence)
    if match:
        return (sentence[:match.start()]
                + f"<mark>{match.group()}</mark>"
                + sentence[match.end():])
    return sentence


def is_self_comparison(phrase):
    phrase_lower = phrase.lower()

    def are_words_same(w1, w2):
        if w1 == w2:
            return True
        if len(w1) >= 4 and len(w2) >= 4:
            if difflib.SequenceMatcher(None, w1, w2).ratio() >= 0.88:
                return True
        return False

    stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'like', 'as'}

    if ' like ' in phrase_lower:
        parts = re.split(r'\blike\b', phrase_lower, 1)
        if len(parts) == 2:
            left  = [w for w in re.findall(r'\w+', parts[0]) if w not in stopwords]
            right = [w for w in re.findall(r'\w+', parts[1]) if w not in stopwords]
            for lw in left:
                for rw in right:
                    if are_words_same(lw, rw):
                        return True

    match = re.search(r'(.*?)\bas\b.*?\bas\b(.*)', phrase_lower)
    if match:
        left  = [w for w in re.findall(r'\w+', match.group(1)) if w not in stopwords]
        right = [w for w in re.findall(r'\w+', match.group(2)) if w not in stopwords]
        for lw in left:
            for rw in right:
                if are_words_same(lw, rw):
                    return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# HYPERBOLE: VADER-assisted intensity scoring
# ─────────────────────────────────────────────────────────────────────────────

# Hard-coded markers we keep (unmistakable exaggerations)
HARD_HYPERBOLE_MARKERS = [
    "million times", "tons of", "takes forever", "weighs a ton",
    "dying of", "best in the world", "end of the world",
    "millions of", "billions of", "endless", "countless", "infinite",
    "a mountain of", "a flood of", "for ages", "an eternity",
    "in a second", "in no time",
]

# Intensity-gated words: only flag when VADER compound is extreme (|score| > 0.6)
INTENSITY_GATED_HYPERBOLE = [
    "extremely", "absolutely", "totally", "completely", "utterly",
    "incredibly", "unbelievably", "insanely", "ridiculously", "exceptionally",
    "always", "never", "everyone", "no one", "everything", "nothing",
    "forever", "all the time",
]

VADER_HYPERBOLE_THRESHOLD = 0.55   # |compound| must exceed this


def detect_hyperbole(sentence: str) -> list[dict]:
    """
    Returns a list of hyperbole result dicts found in `sentence`.
    Strategy:
      • Hard markers  → always flag (unchanged from original)
      • Intensity words → only flag when VADER compound is extreme
    Confidence score is included in algorithm_explanation.
    """
    hits = []
    sentence_lower = sentence.lower()
    vader_score = get_vader_intensity(sentence)   # [-1, +1]

    # 1. Hard markers
    for marker in HARD_HYPERBOLE_MARKERS:
        if marker in sentence_lower:
            m = re.search(re.escape(marker), sentence, re.IGNORECASE)
            if m:
                hits.append({
                    "name": "Hyperbole",
                    "text": m.group(0),
                    "explanation": "An extreme exaggeration used to make a point.",
                    "algorithm_explanation": (
                        f"Hard marker match ('{marker}'). "
                        f"VADER compound: {vader_score:+.3f}."
                    ),
                    "context": highlight_context(sentence, m.group(0)),
                    "confidence": 0.90,
                })

    # 2. Intensity-gated markers
    abs_vader = abs(vader_score)
    for marker in INTENSITY_GATED_HYPERBOLE:
        if marker in sentence_lower and abs_vader > VADER_HYPERBOLE_THRESHOLD:
            m = re.search(re.escape(marker), sentence, re.IGNORECASE)
            if m:
                confidence = round(min(0.5 + abs_vader * 0.5, 0.95), 3)
                hits.append({
                    "name": "Hyperbole",
                    "text": m.group(0),
                    "explanation": "Extreme intensifier supported by high sentiment intensity.",
                    "algorithm_explanation": (
                        f"Intensity marker '{marker}' detected. "
                        f"VADER compound {vader_score:+.3f} exceeds threshold "
                        f"±{VADER_HYPERBOLE_THRESHOLD}. "
                        f"Confidence: {confidence:.0%}."
                    ),
                    "context": highlight_context(sentence, m.group(0)),
                    "confidence": confidence,
                })

    return hits


# ─────────────────────────────────────────────────────────────────────────────
# METAPHOR: WordNet semantic-distance check
# ─────────────────────────────────────────────────────────────────────────────

# Fallback list kept for cases where WordNet has no synsets
METAPHOR_FALLBACK_TARGETS = [
    "monster", "star", "diamond", "pig", "fire", "ice", "machine",
    "ocean", "breeze", "angel", "devil", "nightmare",
]

# Similarity threshold: below this → likely a metaphor (things are semantically distant)
WORDNET_METAPHOR_THRESHOLD = 0.35


def detect_metaphor(tagged: list, sentence: str) -> list[dict]:
    """
    Improved metaphor detection using WordNet path similarity.
    Pattern: <Noun/Pronoun> <is/are/was/were> <a/an/the> <Noun>
    The two nouns are compared via Wu-Palmer similarity:
      low similarity  → different semantic domains → likely metaphor
      high similarity → same domain → probably not metaphor
    """
    hits = []
    for i in range(len(tagged) - 3):
        subj_tag  = tagged[i][1]
        copula    = tagged[i+1][0].lower()
        article   = tagged[i+2][0].lower()
        pred_word = tagged[i+3][0].lower()

        if subj_tag not in ('NN', 'NNS', 'NNP', 'PRP'):
            continue
        if copula not in ('is', 'are', 'was', 'were'):
            continue
        if article not in ('a', 'an', 'the'):
            continue

        subj_word = tagged[i][0].lower()
        phrase    = " ".join([tagged[i][0], tagged[i+1][0],
                              tagged[i+2][0], tagged[i+3][0]])

        # ── WordNet similarity check ──────────────────────────────────────
        similarity = wordnet_path_similarity(subj_word, pred_word)

        if similarity is not None:
            # Low similarity between subject and predicate noun → metaphor
            if similarity < WORDNET_METAPHOR_THRESHOLD:
                confidence = round(1.0 - similarity, 3)
                hits.append({
                    "name": "Metaphor",
                    "text": phrase,
                    "explanation": "An indirect comparison identifying one thing as another.",
                    "algorithm_explanation": (
                        f"POS pattern Noun+BE+Article+Noun matched. "
                        f"WordNet Wu-Palmer similarity between '{subj_word}' and "
                        f"'{pred_word}' = {similarity:.3f} "
                        f"(below threshold {WORDNET_METAPHOR_THRESHOLD}) — "
                        f"semantically distant domains confirm metaphor. "
                        f"Confidence: {confidence:.0%}."
                    ),
                    "context": highlight_context(sentence, phrase),
                    "confidence": confidence,
                })
        else:
            # WordNet has no synsets for one/both words → use fallback list
            if pred_word in METAPHOR_FALLBACK_TARGETS:
                hits.append({
                    "name": "Metaphor",
                    "text": phrase,
                    "explanation": "An indirect comparison identifying one thing as another.",
                    "algorithm_explanation": (
                        f"NLTK POS Tagging identified Noun/Pronoun '{tagged[i][0]}' "
                        f"linked by '{tagged[i+1][0]}' to metaphorical keyword "
                        f"'{pred_word}' (WordNet fallback — no synset found)."
                    ),
                    "context": highlight_context(sentence, phrase),
                    "confidence": 0.70,
                })

    return hits


# ─────────────────────────────────────────────────────────────────────────────
# SARCASM: Transformer-based detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_sarcasm(sentence: str) -> list[dict]:
    """
    Uses the RoBERTa irony model (cardiffnlp/twitter-roberta-base-irony)
    via ml_models.get_sarcasm_score().
    Falls back to rule-based matching if the model is unavailable.
    """
    result = get_sarcasm_score(sentence)

    if not result["is_sarcastic"]:
        return []

    confidence = result["confidence"]
    method     = result["method"]

    if method == "transformer":
        algo_note = (
            f"RoBERTa irony model (cardiffnlp/twitter-roberta-base-irony) "
            f"classified this sentence as IRONY with confidence {confidence:.0%}."
        )
    else:
        algo_note = (
            f"Rule-based fallback: exact sarcasm marker matched. "
            f"Confidence: {confidence:.0%}."
        )

    # Highlight the full sentence (sarcasm is sentence-level)
    context_html = f"<mark>{sentence}</mark>"

    return [{
        "name": "Sarcasm",
        "text": sentence,
        "explanation": "Ironic or sarcastic language detected at the sentence level.",
        "algorithm_explanation": algo_note,
        "context": context_html,
        "confidence": confidence,
    }]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def analyze_text(text):
    results = []

    sentences = sent_tokenize(text)

    for sentence in sentences:
        sentence_lower = sentence.lower()
        tokens = word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        # ══ 1. Simile ════════════════════════════════════════════════════════
        simile_patterns = [
            (r'\b((?:\w+\s+){0,2}as\s+\w+\s+as\s+(?:\w+\s*){1,2})\b',
             "Regex matching 'as [word] as' with surrounding context."),
            (r'\b((?:\w+\s+){0,2}like\s+(?:a|an|the)?\s*\w+)\b',
             "Regex matching '[words] like a/an/the [word]'."),
        ]
        for pattern, algo in simile_patterns:
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                phrase = match.group(0).strip()
                skip_phrases = ["i like", "you like", "we like",
                                "they like", "looks like", "seems like"]
                if any(sp in phrase.lower() for sp in skip_phrases):
                    continue
                if is_self_comparison(phrase):
                    continue
                results.append({
                    "name": "Simile",
                    "text": phrase,
                    "explanation": "A direct comparison using 'like' or 'as'.",
                    "algorithm_explanation": algo,
                    "context": highlight_context(sentence, phrase),
                })

        # ══ 2. Metaphor (WordNet-enhanced) ═══════════════════════════════════
        results.extend(detect_metaphor(tagged, sentence))

        # ══ 3. Personification ═══════════════════════════════════════════════
        inanimate_nouns = ["wind", "sun", "moon", "car", "city", "ocean",
                           "tree", "flowers", "time", "death", "stars"]
        human_verbs     = ["whispered", "danced", "cried", "smiled", "sang",
                           "walked", "ran", "jumped", "spoke", "sighed",
                           "screamed", "groaned", "breathed"]
        for i in range(len(tagged) - 1):
            if (tagged[i][0].lower() in inanimate_nouns
                    and tagged[i+1][0].lower() in human_verbs):
                phrase = f"{tagged[i][0]} {tagged[i+1][0]}"
                results.append({
                    "name": "Personification",
                    "text": phrase,
                    "explanation": "Giving human actions to inanimate objects.",
                    "algorithm_explanation": (
                        f"Adjacent token match: Inanimate noun '{tagged[i][0]}' "
                        f"followed by human verb '{tagged[i+1][0]}'."
                    ),
                    "context": highlight_context(sentence, phrase),
                })

        # ══ 4. Hyperbole (VADER-assisted) ════════════════════════════════════
        results.extend(detect_hyperbole(sentence))

        # ══ 5. Alliteration ══════════════════════════════════════════════════
        words_only = [w for w in tokens if w.isalpha()]
        streak = []
        for w in words_only:
            if not streak:
                streak = [w]
            elif w[0].lower() == streak[0][0].lower():
                streak.append(w)
            else:
                if (len(streak) >= 3
                        and len({s.lower() for s in streak}) > 1):
                    pat = (r'\b'
                           + r'\W+'.join([re.escape(sw) for sw in streak])
                           + r'\b')
                    m = re.search(pat, sentence, re.IGNORECASE)
                    if m:
                        results.append({
                            "name": "Alliteration",
                            "text": m.group(0),
                            "explanation": (
                                f"Repetition of the initial consonant sound "
                                f"'{streak[0][0].upper()}'."
                            ),
                            "algorithm_explanation": (
                                f"Token iteration flagged {len(streak)} consecutive "
                                f"alphabetical words starting with '{streak[0][0].lower()}'."
                            ),
                            "context": highlight_context(sentence, m.group(0)),
                        })
                streak = [w]
        if len(streak) >= 3 and len({s.lower() for s in streak}) > 1:
            pat = (r'\b'
                   + r'\W+'.join([re.escape(sw) for sw in streak])
                   + r'\b')
            m = re.search(pat, sentence, re.IGNORECASE)
            if m:
                results.append({
                    "name": "Alliteration",
                    "text": m.group(0),
                    "explanation": (
                        f"Repetition of the initial consonant sound "
                        f"'{streak[0][0].upper()}'."
                    ),
                    "algorithm_explanation": (
                        f"Token iteration flagged {len(streak)} consecutive "
                        f"alphabetical words starting with '{streak[0][0].lower()}'."
                    ),
                    "context": highlight_context(sentence, m.group(0)),
                })

        # ══ 7. Oxymoron ══════════════════════════════════════════════════════
        oxymorons = [
            "jumbo shrimp", "deafening silence", "bittersweet",
            "living dead", "awfully good", "open secret", "original copy",
            "only choice", "liquid gas", "virtual reality", "old news",
            "pretty ugly",
        ]
        for oxy in oxymorons:
            if oxy in sentence_lower:
                m = re.search(re.escape(oxy), sentence, re.IGNORECASE)
                if m:
                    results.append({
                        "name": "Oxymoron",
                        "text": m.group(0),
                        "explanation": "Two contradictory terms appearing together.",
                        "algorithm_explanation": (
                            f"Exact sequence match for known oxymoronic phrase ('{oxy}')."
                        ),
                        "context": highlight_context(sentence, m.group(0)),
                    })

        # ══ 8. Idiom ═════════════════════════════════════════════════════════
        idioms = [
            "piece of cake", "break a leg", "bite the bullet",
            "under the weather", "spill the beans", "hit the sack",
            "let the cat out of the bag", "cost an arm and a leg",
            "elephant in the room", "raining cats and dogs",
        ]
        for idiom in idioms:
            if idiom in sentence_lower:
                m = re.search(re.escape(idiom), sentence, re.IGNORECASE)
                if m:
                    results.append({
                        "name": "Idiom",
                        "text": m.group(0),
                        "explanation": "A phrase whose figurative meaning differs from literal semantics.",
                        "algorithm_explanation": (
                            f"String matching against curated English idiom list ('{idiom}')."
                        ),
                        "context": highlight_context(sentence, m.group(0)),
                    })

        # ══ 9. Sarcasm (Transformer-based) ═══════════════════════════════════
        results.extend(detect_sarcasm(sentence))

        # ══ 10. Irony ════════════════════════════════════════════════════════
        irony_markers = [
            "ironically", "ironic that",
            "fire station burned down", "robbed the police station",
        ]
        for im in irony_markers:
            if im in sentence_lower:
                m = re.search(re.escape(im), sentence, re.IGNORECASE)
                if m:
                    results.append({
                        "name": "Irony",
                        "text": m.group(0),
                        "explanation": "Explicit marker of situational contrast.",
                        "algorithm_explanation": (
                            f"Exact phrase indicating irony / paradox ('{im}')."
                        ),
                        "context": highlight_context(sentence, m.group(0)),
                    })

        # ══ 11. Transferred Epithet ══════════════════════════════════════════
        human_adjectives = {
            "angry", "wonderful", "weary", "nervous", "sleepless", "happy",
            "sad", "cruel", "blind", "lazy", "cheerful", "anxious",
            "melancholy", "restless", "busy", "guilty", "terrified",
            "frightened", "bored", "jealous", "suspicious", "proud",
            "lonely", "joyful", "sorrowful", "unhappy", "glad", "mad",
            "dreary", "bleak",
        }
        inanimate_targets = {
            "finger", "day", "road", "smile", "night", "pillow", "sky",
            "wind", "sea", "journey", "room", "house", "city", "chair",
            "bed", "morning", "evening", "hour", "year", "mind", "heart",
            "tear", "tears", "street", "silence", "shadow", "song", "task",
            "work", "duty", "life", "world", "path", "wood", "glass",
        }
        for i in range(len(tagged) - 1):
            if tagged[i][1] in ('JJ', 'JJR', 'JJS') and tagged[i+1][1] in ('NN', 'NNS'):
                adj  = tagged[i][0].lower()
                noun = tagged[i+1][0].lower()
                if adj in human_adjectives and noun in inanimate_targets:
                    phrase = f"{tagged[i][0]} {tagged[i+1][0]}"
                    results.append({
                        "name": "Transferred Epithet",
                        "text": phrase,
                        "explanation": (
                            "A human emotion adjective is applied to "
                            "an inanimate object or concept."
                        ),
                        "algorithm_explanation": (
                            f"POS Tagging found adjective '{adj}' (human emotion) "
                            f"modifying noun '{noun}' (inanimate object)."
                        ),
                        "context": highlight_context(sentence, phrase),
                    })

    # ══ 6. Anaphora (cross-sentence) ═════════════════════════════════════════
    segments = [s.strip() for s in re.split(r'[,;.]\s*', text) if s.strip()]
    i = 0
    while i < len(segments) - 1:
        words1 = segments[i].split()
        words2 = segments[i + 1].split()
        common = []
        for w1, w2 in zip(words1, words2):
            if w1.lower() == w2.lower():
                common.append(w1)
            else:
                break
        if common:
            prefix_lower = [w.lower() for w in common]
            k = i + 1
            while k < len(segments):
                kw = segments[k].split()
                if (len(kw) >= len(prefix_lower)
                        and [w.lower() for w in kw[:len(prefix_lower)]] == prefix_lower):
                    k += 1
                else:
                    break
            if k - i >= 2:
                phrase = " ".join(common)
                results.append({
                    "name": "Anaphora",
                    "text": f"'{phrase}' repeated",
                    "explanation": (
                        f"Repetition of '{phrase}' at the beginning of "
                        f"{k - i} consecutive clauses/sentences."
                    ),
                    "algorithm_explanation": (
                        f"Greedy prefix matcher identified a {len(common)}-word "
                        f"shared sequence '{phrase}' across {k - i} segments."
                    ),
                    "context": (
                        f"...<mark>{phrase}</mark> "
                        f"{' '.join(words1[len(common):len(common)+3])}... "
                        f"<mark>{phrase}</mark> "
                        f"{' '.join(words2[len(common):len(common)+3])}..."
                    ),
                })
                i = k - 1
        i += 1

    # ══ 12. Enjambment (line-level) ══════════════════════════════════════════
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        cur  = lines[i].strip()
        nxt  = lines[i + 1].strip()
        if cur and nxt and cur[-1] not in '.,:;!?' and len(cur.split()) >= 3:
            c_disp = cur  if len(cur) < 50 else "..." + cur[-47:]
            n_disp = nxt  if len(nxt) < 50 else nxt[:47] + "..."
            results.append({
                "name": "Enjambment",
                "text": "Line break without punctuation",
                "explanation": "A sentence continues across a line break without terminal punctuation.",
                "algorithm_explanation": (
                    f"Line ended with '{cur[-1]}' instead of punctuation, "
                    f"flowing into the next line."
                ),
                "context": f"{c_disp} <mark>↵</mark> {n_disp}",
            })

    # ══ Exact-match deduplication ═════════════════════════════════════════════
    unique, seen = [], set()
    for r in results:
        key = f"{r['name']}_{r['context']}_{r['text']}"
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique