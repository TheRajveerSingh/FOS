import re
import nltk
import difflib
from nltk.tokenize import word_tokenize, sent_tokenize

from ml_models import (
    get_sarcasm_score, get_vader_intensity, wordnet_path_similarity,
    wordnet_synonyms, bigram_log_probability,
    get_first_phoneme, pronouncing_available,
)

for pkg in ('punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Generic helpers
# ──────────────────────────────────────────────────────────────────────────────

def highlight_context(sentence, match_text):
    pattern = re.compile(re.escape(match_text), re.IGNORECASE)
    m = pattern.search(sentence)
    if m:
        return sentence[:m.start()] + f"<mark>{m.group()}</mark>" + sentence[m.end():]
    return sentence


def is_self_comparison(phrase):
    phrase_lower = phrase.lower()

    def same(w1, w2):
        if w1 == w2:
            return True
        if len(w1) >= 4 and len(w2) >= 4:
            return difflib.SequenceMatcher(None, w1, w2).ratio() >= 0.88
        return False

    stops = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'like', 'as'}

    if ' like ' in phrase_lower:
        parts = re.split(r'\blike\b', phrase_lower, 1)
        if len(parts) == 2:
            L = [w for w in re.findall(r'\w+', parts[0]) if w not in stops]
            R = [w for w in re.findall(r'\w+', parts[1]) if w not in stops]
            if any(same(lw, rw) for lw in L for rw in R):
                return True

    m = re.search(r'(.*?)\bas\b.*?\bas\b(.*)', phrase_lower)
    if m:
        L = [w for w in re.findall(r'\w+', m.group(1)) if w not in stops]
        R = [w for w in re.findall(r'\w+', m.group(2)) if w not in stops]
        if any(same(lw, rw) for lw in L for rw in R):
            return True

    return False


# ──────────────────────────────────────────────────────────────────────────────
# SIMILE  —  old: regex only   |   new: regex + WordNet synonym filter
# ──────────────────────────────────────────────────────────────────────────────

def detect_simile(sentence: str) -> list:
    results = []
    skip = {"i like", "you like", "we like", "they like",
            "looks like", "seems like"}

    patterns = [
        (r'\b((?:\w+\s+){0,2}as\s+\w+\s+as\s+(?:\w+\s*){1,2})\b',
         "Regex matching 'as [word] as' with surrounding context."),
        (r'\b((?:\w+\s+){0,2}like\s+(?:a|an|the)?\s*\w+)\b',
         "Regex matching '[words] like a/an/the [word]'."),
    ]

    for pattern, algo in patterns:
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            phrase = match.group(0).strip()

            if any(s in phrase.lower() for s in skip):
                continue
            if is_self_comparison(phrase):
                continue

            # ── New method: WordNet synonym check ──────────────────────────
            words = re.findall(r'\b[a-zA-Z]{3,}\b', phrase)
            content = [w for w in words
                       if w.lower() not in
                       {'like', 'the', 'a', 'an', 'as', 'was', 'is', 'are'}]

            new_verdict       = None
            comparison_note   = ""
            is_false_positive = False

            if len(content) >= 2:
                w1, w2  = content[0].lower(), content[-1].lower()
                syns_w1 = wordnet_synonyms(w1)
                syns_w2 = wordnet_synonyms(w2)
                overlap = syns_w1 & syns_w2

                if overlap:
                    is_false_positive = True
                    new_verdict = (
                        f"Filtered out — WordNet shows '{w1}' and '{w2}' "
                        f"share synonyms {list(overlap)[:3]}, "
                        f"so they are semantically similar (not a true simile)."
                    )
                    comparison_note = (
                        f"Old method (regex) flagged this. "
                        f"New method (WordNet synonym filter) rejects it "
                        f"because compared words are near-synonyms."
                    )
                else:
                    new_verdict = (
                        f"Confirmed — WordNet finds no synonym overlap "
                        f"between '{w1}' and '{w2}', so they come from "
                        f"different semantic domains (genuine simile)."
                    )
                    comparison_note = (
                        f"Both methods agree: regex matched the pattern "
                        f"and WordNet confirms semantic distance."
                    )
            else:
                new_verdict     = "WordNet check skipped (insufficient content words)."
                comparison_note = "Only regex method applied."

            results.append({
                "name": "Simile",
                "text": phrase,
                "explanation": "A direct comparison using 'like' or 'as'.",
                "algorithm_explanation": (
                    f"<b>Old (Regex):</b> {algo}<br>"
                    f"<b>New (WordNet synonym filter):</b> {new_verdict}"
                ),
                "context": highlight_context(sentence, phrase),
                "is_false_positive": is_false_positive,
                "comparison": comparison_note,
            })

    return results


# ──────────────────────────────────────────────────────────────────────────────
# METAPHOR  —  WordNet semantic distance
# ──────────────────────────────────────────────────────────────────────────────

METAPHOR_FALLBACK = [
    "monster", "star", "diamond", "pig", "fire", "ice", "machine",
    "ocean", "breeze", "angel", "devil", "nightmare",
]
WORDNET_METAPHOR_THRESHOLD = 0.35


def detect_metaphor(tagged, sentence):
    hits = []
    for i in range(len(tagged) - 3):
        if tagged[i][1] not in ('NN', 'NNS', 'NNP', 'PRP'):
            continue
        if tagged[i+1][0].lower() not in ('is', 'are', 'was', 'were'):
            continue
        if tagged[i+2][0].lower() not in ('a', 'an', 'the'):
            continue

        subj   = tagged[i][0].lower()
        pred   = tagged[i+3][0].lower()
        phrase = " ".join(t[0] for t in tagged[i:i+4])
        sim    = wordnet_path_similarity(subj, pred)

        if sim is not None:
            if sim < WORDNET_METAPHOR_THRESHOLD:
                conf = round(1.0 - sim, 3)
                hits.append({
                    "name": "Metaphor",
                    "text": phrase,
                    "explanation": "An indirect comparison identifying one thing as another.",
                    "algorithm_explanation": (
                        f"POS pattern Noun+BE+Article+Noun matched. "
                        f"WordNet Wu-Palmer similarity between '{subj}' and "
                        f"'{pred}' = {sim:.3f} (below threshold "
                        f"{WORDNET_METAPHOR_THRESHOLD}) — semantically distant "
                        f"domains confirm metaphor. Confidence: {conf:.0%}."
                    ),
                    "context": highlight_context(sentence, phrase),
                    "confidence": conf,
                })
        elif pred in METAPHOR_FALLBACK:
            hits.append({
                "name": "Metaphor",
                "text": phrase,
                "explanation": "An indirect comparison identifying one thing as another.",
                "algorithm_explanation": (
                    f"POS Tagging matched Noun+BE+Article+Noun. "
                    f"WordNet has no synset for '{pred}'; matched via "
                    f"fallback keyword list. Confidence: 70%."
                ),
                "context": highlight_context(sentence, phrase),
                "confidence": 0.70,
            })
    return hits


# ──────────────────────────────────────────────────────────────────────────────
# HYPERBOLE  —  VADER-assisted
# ──────────────────────────────────────────────────────────────────────────────

HARD_HYPERBOLE = [
    "million times", "tons of", "takes forever", "weighs a ton",
    "dying of", "best in the world", "end of the world",
    "millions of", "billions of", "endless", "countless", "infinite",
    "a mountain of", "a flood of", "for ages", "an eternity",
    "in a second", "in no time",
]
INTENSITY_HYPERBOLE = [
    "extremely", "absolutely", "totally", "completely", "utterly",
    "incredibly", "unbelievably", "insanely", "ridiculously", "exceptionally",
    "always", "never", "everyone", "no one", "everything", "nothing",
    "forever", "all the time",
]
VADER_THRESHOLD = 0.55


def detect_hyperbole(sentence):
    hits   = []
    lower  = sentence.lower()
    vscore = get_vader_intensity(sentence)

    for marker in HARD_HYPERBOLE:
        if marker in lower:
            m = re.search(re.escape(marker), sentence, re.IGNORECASE)
            if m:
                hits.append({
                    "name": "Hyperbole",
                    "text": m.group(0),
                    "explanation": "An extreme exaggeration used to make a point.",
                    "algorithm_explanation": (
                        f"Hard marker match ('{marker}'). "
                        f"VADER compound: {vscore:+.3f}."
                    ),
                    "context": highlight_context(sentence, m.group(0)),
                    "confidence": 0.90,
                })

    if abs(vscore) > VADER_THRESHOLD:
        for marker in INTENSITY_HYPERBOLE:
            if marker in lower:
                m = re.search(re.escape(marker), sentence, re.IGNORECASE)
                if m:
                    conf = round(min(0.5 + abs(vscore) * 0.5, 0.95), 3)
                    hits.append({
                        "name": "Hyperbole",
                        "text": m.group(0),
                        "explanation": "Extreme intensifier supported by high sentiment intensity.",
                        "algorithm_explanation": (
                            f"Intensity marker '{marker}' detected. "
                            f"VADER compound {vscore:+.3f} exceeds "
                            f"threshold ±{VADER_THRESHOLD}. "
                            f"Confidence: {conf:.0%}."
                        ),
                        "context": highlight_context(sentence, m.group(0)),
                        "confidence": conf,
                    })
    return hits


# ──────────────────────────────────────────────────────────────────────────────
# ALLITERATION  —  old: first-letter  |  new: first phoneme (CMU dict)
# ──────────────────────────────────────────────────────────────────────────────

def _find_streaks_by_key(words_only, key_fn, min_len=3):
    streaks = []
    streak  = []
    for w in words_only:
        k = key_fn(w)
        if k is None:
            if len(streak) >= min_len and len({s.lower() for s in streak}) > 1:
                streaks.append(streak[:])
            streak = []
        elif not streak:
            streak = [w]
        elif key_fn(streak[0]) == k:
            streak.append(w)
        else:
            if len(streak) >= min_len and len({s.lower() for s in streak}) > 1:
                streaks.append(streak[:])
            streak = [w]
    if len(streak) >= min_len and len({s.lower() for s in streak}) > 1:
        streaks.append(streak[:])
    return streaks


def detect_alliteration(tokens, sentence):
    results    = []
    words_only = [w for w in tokens if w.isalpha()]

    # ── Old method: first letter ───────────────────────────────────────────
    letter_streaks = _find_streaks_by_key(words_only, lambda w: w[0].lower())

    # ── New method: first phoneme (CMU) ────────────────────────────────────
    phoneme_streaks = []
    if pronouncing_available():
        phoneme_streaks = _find_streaks_by_key(words_only, get_first_phoneme)

    def make_result(streak, method_label, algo_note, comparison_note):
        pat = r'\b' + r'\W+'.join(re.escape(w) for w in streak) + r'\b'
        m   = re.search(pat, sentence, re.IGNORECASE)
        if not m:
            return None
        if method_label == "Letter (old)":
            key_display = f"letter '{streak[0][0].upper()}'"
        else:
            ph = get_first_phoneme(streak[0])
            key_display = f"phoneme /{ph}/" if ph else f"phoneme of '{streak[0]}'"

        return {
            "name": "Alliteration",
            "text": m.group(0),
            "explanation": (
                f"Repetition of the initial sound ({key_display}) "
                f"across {len(streak)} consecutive words."
            ),
            "algorithm_explanation": (
                f"<b>Method:</b> {method_label}<br>{algo_note}"
            ),
            "context": highlight_context(sentence, m.group(0)),
            "comparison": comparison_note,
        }

    letter_word_sets  = [frozenset(s) for s in letter_streaks]
    phoneme_word_sets = [frozenset(s) for s in phoneme_streaks]

    for streak in letter_streaks:
        fs = frozenset(streak)
        if fs in phoneme_word_sets:
            note = ("Both methods agree — first letter and first phoneme "
                    "match, so these words genuinely alliterate.")
        else:
            ph_sample = get_first_phoneme(streak[0]) if pronouncing_available() else None
            note = (
                f"Old method (letter) flagged this. "
                f"New method (phoneme) does NOT — '{streak[0]}' starts with "
                f"letter '{streak[0][0]}' but phoneme /{ph_sample or '?'}/, "
                f"which may differ from the others."
                if ph_sample else
                "Phoneme check unavailable (`pronouncing` not installed)."
            )
        r = make_result(
            streak, "Letter (old)",
            f"Token iteration: {len(streak)} consecutive words "
            f"share first letter '{streak[0][0].lower()}'.",
            note,
        )
        if r:
            results.append(r)

    for streak in phoneme_streaks:
        fs = frozenset(streak)
        if fs not in letter_word_sets:
            ph   = get_first_phoneme(streak[0]) or "?"
            note = (
                f"New method (phoneme) found this; old method (letter) missed it. "
                f"Words start with different letters but share phoneme /{ph}/."
            )
            r = make_result(
                streak, "Phoneme (new)",
                f"CMU Pronouncing Dictionary: {len(streak)} consecutive words "
                f"share first phoneme /{ph}/.",
                note,
            )
            if r:
                results.append(r)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# IDIOM  —  old: exact list  |  new: N-gram probability scoring
# ──────────────────────────────────────────────────────────────────────────────

KNOWN_IDIOMS = [
    "piece of cake", "break a leg", "bite the bullet",
    "under the weather", "spill the beans", "hit the sack",
    "let the cat out of the bag", "cost an arm and a leg",
    "elephant in the room", "raining cats and dogs",
]

# Stricter threshold — ordinary phrases rarely score below -11.5
NGRAM_IDIOM_THRESHOLD = -11.5

# Common/function words that alone don't signal an idiom
_COMMON_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her',
    'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'not', 'with',
    'this', 'that', 'have', 'has', 'had', 'do', 'did', 'does', 'just', 'very',
    'so', 'up', 'out', 'if', 'as', 'by', 'from', 'about', 'into', 'then',
    'than', 'there', 'their', 'they', 'what', 'when', 'who', 'will', 'would',
    'could', 'should', 'can', 'may', 'might', 'all', 'more', 'one', 'two',
    'some', 'any', 'no', 'its', 'our', 'also', 'after', 'before', 'over',
}


def detect_idiom(sentence):
    results = []
    lower   = sentence.lower()

    # ── Old method: exact list ─────────────────────────────────────────────
    list_hits = set()
    for idiom in KNOWN_IDIOMS:
        if idiom in lower:
            list_hits.add(idiom)

    # ── New method: sliding N-gram window (3-6 word phrases) ──────────────
    words      = sentence.split()
    ngram_hits = {}  # phrase_lower -> (log_prob, original_phrase)

    for n in range(3, 7):
        for i in range(len(words) - n + 1):
            chunk     = words[i:i+n]
            phrase    = " ".join(chunk)
            phrase_lc = phrase.lower()

            # Skip if already covered by the known list
            if any(phrase_lc in idiom or idiom in phrase_lc
                   for idiom in KNOWN_IDIOMS):
                continue

            # Skip chunks made entirely of common/function words
            chunk_words   = re.findall(r'[a-z]+', phrase_lc)
            content_words = [w for w in chunk_words if w not in _COMMON_WORDS]
            if len(content_words) < 2:
                continue

            lp = bigram_log_probability(phrase_lc)
            if lp < NGRAM_IDIOM_THRESHOLD:
                ngram_hits[phrase_lc] = (round(lp, 3), phrase)

    # ── Build results — list hits first ────────────────────────────────────
    for idiom in list_hits:
        m = re.search(re.escape(idiom), sentence, re.IGNORECASE)
        if not m:
            continue
        lp             = bigram_log_probability(idiom)
        ngram_confirms = lp < NGRAM_IDIOM_THRESHOLD

        comparison = (
            f"Both methods agree: exact list matched AND "
            f"N-gram log-prob ({lp:.2f}) is below threshold "
            f"{NGRAM_IDIOM_THRESHOLD} (very unusual phrase)."
            if ngram_confirms else
            f"Old method (list) flagged this. "
            f"N-gram log-prob ({lp:.2f}) is above threshold — "
            f"phrase is not statistically unusual in the Brown corpus, "
            f"but it is a known idiom so we keep it."
        )

        results.append({
            "name": "Idiom",
            "text": m.group(0),
            "explanation": "A phrase whose figurative meaning differs from literal semantics.",
            "algorithm_explanation": (
                f"<b>Old (List match):</b> Matched against curated idiom list.<br>"
                f"<b>New (N-gram):</b> Brown corpus bigram log-prob = {lp:.2f} "
                f"(threshold: {NGRAM_IDIOM_THRESHOLD})."
            ),
            "context": highlight_context(sentence, m.group(0)),
            "comparison": comparison,
        })

    # ── N-gram only hits (not in known list) ───────────────────────────────
    for phrase_lc, (lp, phrase_orig) in ngram_hits.items():
        m = re.search(re.escape(phrase_orig), sentence, re.IGNORECASE)
        if not m:
            continue
        results.append({
            "name": "Idiom",
            "text": m.group(0),
            "explanation": "Statistically unusual phrase — possible idiom or fixed expression.",
            "algorithm_explanation": (
                f"<b>Old (List match):</b> Not in the curated idiom list.<br>"
                f"<b>New (N-gram):</b> Brown corpus bigram log-prob = {lp:.2f}, "
                f"below threshold {NGRAM_IDIOM_THRESHOLD}. "
                f"Phrase is statistically rare — likely figurative."
            ),
            "context": highlight_context(sentence, m.group(0)),
            "comparison": (
                f"New method (N-gram) found this; old method (list) missed it. "
                f"Log-prob {lp:.2f} indicates this is an unusual word combination."
            ),
        })

    return results


# ──────────────────────────────────────────────────────────────────────────────
# SARCASM  —  transformer-based
# ──────────────────────────────────────────────────────────────────────────────

def detect_sarcasm(sentence):
    result = get_sarcasm_score(sentence)
    if not result["is_sarcastic"]:
        return []

    confidence = result["confidence"]
    method     = result["method"]
    algo_note  = (
        f"RoBERTa irony model (cardiffnlp/twitter-roberta-base-irony) "
        f"classified this sentence as IRONY with confidence {confidence:.0%}."
        if method == "transformer" else
        f"Rule-based fallback: exact sarcasm marker matched. "
        f"Confidence: {confidence:.0%}."
    )
    return [{
        "name": "Sarcasm",
        "text": sentence,
        "explanation": "Ironic or sarcastic language detected at the sentence level.",
        "algorithm_explanation": algo_note,
        "context": f"<mark>{sentence}</mark>",
        "confidence": confidence,
    }]


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def analyze_text(text):
    results   = []
    sentences = sent_tokenize(text)

    for sentence in sentences:
        sentence_lower = sentence.lower()
        tokens         = word_tokenize(sentence)
        tagged         = nltk.pos_tag(tokens)

        # 1. Simile
        results.extend(detect_simile(sentence))

        # 2. Metaphor
        results.extend(detect_metaphor(tagged, sentence))

        # 3. Personification
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
                        f"Adjacent token match: inanimate noun '{tagged[i][0]}' "
                        f"followed by human verb '{tagged[i+1][0]}'."
                    ),
                    "context": highlight_context(sentence, phrase),
                })

        # 4. Hyperbole
        results.extend(detect_hyperbole(sentence))

        # 5. Alliteration (dual method)
        results.extend(detect_alliteration(tokens, sentence))

        # 7. Oxymoron
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

        # 8. Idiom (dual method)
        results.extend(detect_idiom(sentence))

        # 9. Sarcasm
        results.extend(detect_sarcasm(sentence))

        # 10. Irony
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
                            f"Exact phrase indicating irony or paradox ('{im}')."
                        ),
                        "context": highlight_context(sentence, m.group(0)),
                    })

        # 11. Transferred Epithet
        human_adj = {
            "angry", "wonderful", "weary", "nervous", "sleepless", "happy",
            "sad", "cruel", "blind", "lazy", "cheerful", "anxious",
            "melancholy", "restless", "busy", "guilty", "terrified",
            "frightened", "bored", "jealous", "suspicious", "proud",
            "lonely", "joyful", "sorrowful", "unhappy", "glad", "mad",
            "dreary", "bleak",
        }
        inanimate_tgt = {
            "finger", "day", "road", "smile", "night", "pillow", "sky",
            "wind", "sea", "journey", "room", "house", "city", "chair",
            "bed", "morning", "evening", "hour", "year", "mind", "heart",
            "tear", "tears", "street", "silence", "shadow", "song", "task",
            "work", "duty", "life", "world", "path", "wood", "glass",
        }
        for i in range(len(tagged) - 1):
            if (tagged[i][1] in ('JJ', 'JJR', 'JJS')
                    and tagged[i+1][1] in ('NN', 'NNS')):
                adj  = tagged[i][0].lower()
                noun = tagged[i+1][0].lower()
                if adj in human_adj and noun in inanimate_tgt:
                    phrase = f"{tagged[i][0]} {tagged[i+1][0]}"
                    results.append({
                        "name": "Transferred Epithet",
                        "text": phrase,
                        "explanation": (
                            "A human emotion adjective applied to an "
                            "inanimate object or concept."
                        ),
                        "algorithm_explanation": (
                            f"POS Tagging: adjective '{adj}' (human emotion) "
                            f"modifies noun '{noun}' (inanimate object)."
                        ),
                        "context": highlight_context(sentence, phrase),
                    })

    # 6. Anaphora (cross-sentence)
    segments = [s.strip() for s in re.split(r'[,;.]\s*', text) if s.strip()]
    i = 0
    while i < len(segments) - 1:
        w1 = segments[i].split()
        w2 = segments[i+1].split()
        common = []
        for a, b in zip(w1, w2):
            if a.lower() == b.lower():
                common.append(a)
            else:
                break
        if common:
            pl = [w.lower() for w in common]
            k  = i + 1
            while k < len(segments):
                kw = segments[k].split()
                if (len(kw) >= len(pl)
                        and [w.lower() for w in kw[:len(pl)]] == pl):
                    k += 1
                else:
                    break
            if k - i >= 2:
                phrase = " ".join(common)
                results.append({
                    "name": "Anaphora",
                    "text": f"'{phrase}' repeated",
                    "explanation": (
                        f"Repetition of '{phrase}' at the start of "
                        f"{k-i} consecutive clauses."
                    ),
                    "algorithm_explanation": (
                        f"Greedy prefix matcher: {len(common)}-word shared "
                        f"sequence '{phrase}' across {k-i} segments."
                    ),
                    "context": (
                        f"...<mark>{phrase}</mark> "
                        f"{' '.join(w1[len(common):len(common)+3])}... "
                        f"<mark>{phrase}</mark> "
                        f"{' '.join(w2[len(common):len(common)+3])}..."
                    ),
                })
                i = k - 1
        i += 1

    # 12. Enjambment
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        cur = lines[i].strip()
        nxt = lines[i+1].strip()
        if cur and nxt and cur[-1] not in '.,:;!?' and len(cur.split()) >= 3:
            c_d = cur if len(cur) < 50 else "..." + cur[-47:]
            n_d = nxt if len(nxt) < 50 else nxt[:47] + "..."
            results.append({
                "name": "Enjambment",
                "text": "Line break without punctuation",
                "explanation": "A sentence continues across a line break without terminal punctuation.",
                "algorithm_explanation": (
                    f"Line ended with '{cur[-1]}' instead of punctuation, "
                    f"flowing into the next line."
                ),
                "context": f"{c_d} <mark>↵</mark> {n_d}",
            })

    # Deduplication
    unique, seen = [], set()
    for r in results:
        key = f"{r['name']}_{r['context']}_{r['text']}"
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique