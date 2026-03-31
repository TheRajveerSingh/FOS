import re
import nltk
import difflib
from nltk.tokenize import word_tokenize, sent_tokenize

# Ensure datasets are available
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
except Exception:
    pass

def highlight_context(sentence, match_text):
    pattern = re.compile(re.escape(match_text), re.IGNORECASE)
    match = pattern.search(sentence)
    if match:
        return sentence[:match.start()] + f"<mark>{match.group()}</mark>" + sentence[match.end():]
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
            left_words = [w for w in re.findall(r'\w+', parts[0]) if w not in stopwords]
            right_words = [w for w in re.findall(r'\w+', parts[1]) if w not in stopwords]
            for lw in left_words:
                for rw in right_words:
                    if are_words_same(lw, rw):
                        return True
                        
    match = re.search(r'(.*?)\bas\b.*?\bas\b(.*)', phrase_lower)
    if match:
        left_part = match.group(1)
        right_part = match.group(2)
        left_words = [w for w in re.findall(r'\w+', left_part) if w not in stopwords]
        right_words = [w for w in re.findall(r'\w+', right_part) if w not in stopwords]
        for lw in left_words:
            for rw in right_words:
                if are_words_same(lw, rw):
                    return True
                    
    return False

def analyze_text(text):
    results = []
    
    # 1. Split into sentences
    sentences = sent_tokenize(text)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        tokens = word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        # ====== 1. Simile ======
        # Improved: Extract up to 2 words before 'like'/'as' and 2 words after to give better phrase
        # E.g., "shines like a diamond", "was as brave as a lion"
        simile_patterns = [
            (r'\b((?:\w+\s+){0,2}as\s+\w+\s+as\s+(?:\w+\s*){1,2})\b', "Regex matching 'as [word] as' with surrounding context."),
            (r'\b((?:\w+\s+){0,2}like\s+(?:a|an|the)?\s*\w+)\b', "Regex matching '[words] like a/an/the [word]'.")
        ]
        for pattern, algo in simile_patterns:
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                phrase = match.group(0).strip()
                if not any(stop in phrase.lower() for stop in ["i like", "you like", "we like", "they like", "looks like", "seems like"]):
                    if not is_self_comparison(phrase):
                        results.append({
                        "name": "Simile",
                        "text": phrase,
                        "explanation": "A direct comparison using 'like' or 'as'.",
                        "algorithm_explanation": algo,
                        "context": highlight_context(sentence, phrase)
                    })

        # ====== 2. Metaphor ======
        metaphorical_targets = ["monster", "star", "diamond", "pig", "fire", "ice", "machine", "ocean", "breeze", "angel", "devil", "nightmare"]
        for i in range(len(tagged) - 3):
            if tagged[i][1] in ['NN', 'NNS', 'NNP', 'PRP']:
                if tagged[i+1][0].lower() in ['is', 'are', 'was', 'were']:
                    if tagged[i+2][0].lower() in ['a', 'an', 'the']:
                        target = tagged[i+3][0].lower()
                        if target in metaphorical_targets:
                            phrase = " ".join([tagged[i][0], tagged[i+1][0], tagged[i+2][0], tagged[i+3][0]])
                            results.append({
                                "name": "Metaphor",
                                "text": phrase,
                                "explanation": "An indirect comparison identifying one thing as another.",
                                "algorithm_explanation": f"NLTK POS Tagging identified Noun/Pronoun '{tagged[i][0]}' linked by '{tagged[i+1][0]}' to metaphorical keyword '{target}'.",
                                "context": highlight_context(sentence, phrase)
                            })

        # ====== 3. Personification ======
        inanimate_nouns = ["wind", "sun", "moon", "car", "city", "ocean", "tree", "flowers", "time", "death", "stars"]
        human_verbs = ["whispered", "danced", "cried", "smiled", "sang", "walked", "ran", "jumped", "spoke", "sighed", "screamed", "groaned", "breathed"]
        for i in range(len(tagged) - 1):
            if tagged[i][0].lower() in inanimate_nouns and tagged[i+1][0].lower() in human_verbs:
                phrase = f"{tagged[i][0]} {tagged[i+1][0]}"
                results.append({
                    "name": "Personification",
                    "text": phrase,
                    "explanation": "Giving human actions to inanimate objects.",
                    "algorithm_explanation": f"Adjacent token match: Inanimate dictionary noun '{tagged[i][0]}' followed immediately by human dictionary verb '{tagged[i+1][0]}'.",
                    "context": highlight_context(sentence, phrase)
                })

        # ====== 4. Hyperbole ======
        hyperboles = [
            "million times", "tons of", "takes forever", "weighs a ton", "dying of", "best in the world", "end of the world",
            "extremely", "absolutely", "totally", "completely", "utterly", "incredibly", "unbelievably", "insanely", "ridiculously", "exceptionally",
            "always", "never", "everyone", "no one", "everything", "nothing", "forever", "all the time",
            "millions of", "billions of", "endless", "countless", "infinite", "a mountain of", "a flood of",
            "for ages", "an eternity", "in a second", "in no time"
        ]
        for hyp in hyperboles:
            if hyp in sentence_lower:
                match = re.search(re.escape(hyp), sentence, re.IGNORECASE)
                if match:
                    results.append({
                        "name": "Hyperbole",
                        "text": match.group(0),
                        "explanation": "An extreme exaggeration used to make a point.",
                        "algorithm_explanation": f"Exact phrase match against a predefined list of common hyperbole markers ('{hyp}').",
                        "context": highlight_context(sentence, match.group(0))
                    })

        # ====== 5. Alliteration ======
        # Improved logic: iterate tokens and look for 3+ consecutive words starting with same alphabetical character
        words_only = [w for w in tokens if w.isalpha()]
        streak = []
        for w in words_only:
            if not streak:
                streak = [w]
            elif w[0].lower() == streak[0][0].lower():
                streak.append(w)
            else:
                if len(streak) >= 3 and len(set([w_str.lower() for w_str in streak])) > 1:
                    # Found a valid alliteration. Let's find its exact substring in the sentence to preserve original punctuation.
                    # Build regex to match these words in order
                    pattern_str = r'\b' + r'\W+'.join([re.escape(sw) for sw in streak]) + r'\b'
                    match = re.search(pattern_str, sentence, re.IGNORECASE)
                    if match:
                         results.append({
                             "name": "Alliteration",
                             "text": match.group(0),
                             "explanation": f"Repetition of the initial consonant sound '{streak[0][0].upper()}'.",
                             "algorithm_explanation": f"Token iteration flagged {len(streak)} consecutive alphabetical words starting with '{streak[0][0].lower()}', ignoring punctuation.",
                             "context": highlight_context(sentence, match.group(0))
                         })
                streak = [w]
        # check tail
        if len(streak) >= 3 and len(set([w_str.lower() for w_str in streak])) > 1:
            pattern_str = r'\b' + r'\W+'.join([re.escape(sw) for sw in streak]) + r'\b'
            match = re.search(pattern_str, sentence, re.IGNORECASE)
            if match:
                 results.append({
                     "name": "Alliteration",
                     "text": match.group(0),
                     "explanation": f"Repetition of the initial consonant sound '{streak[0][0].upper()}'.",
                     "algorithm_explanation": f"Token iteration flagged {len(streak)} consecutive alphabetical words starting with '{streak[0][0].lower()}', ignoring punctuation.",
                     "context": highlight_context(sentence, match.group(0))
                 })

        # ====== 7. Oxymoron ======
        oxymorons = ["jumbo shrimp", "deafening silence", "bittersweet", "living dead", "awfully good", "open secret", "original copy", "only choice", "liquid gas", "virtual reality", "old news", "pretty ugly"]
        for oxy in oxymorons:
            if oxy in sentence_lower:
                match = re.search(re.escape(oxy), sentence, re.IGNORECASE)
                if match:
                    results.append({
                        "name": "Oxymoron",
                        "text": match.group(0),
                        "explanation": "Two contradictory terms appearing together.",
                        "algorithm_explanation": f"Exact sequence match for a known oxymoronic phrase ('{oxy}').",
                        "context": highlight_context(sentence, match.group(0))
                    })

        # ====== 8. Idiom ======
        idioms = ["piece of cake", "break a leg", "bite the bullet", "under the weather", "spill the beans", "hit the sack", "let the cat out of the bag", "cost an arm and a leg", "elephant in the room", "raining cats and dogs"]
        for idiom in idioms:
            if idiom in sentence_lower:
                match = re.search(re.escape(idiom), sentence, re.IGNORECASE)
                if match:
                    results.append({
                        "name": "Idiom",
                        "text": match.group(0),
                        "explanation": "A common phrase whose figurative meaning differs from literal semantics.",
                        "algorithm_explanation": f"String matching against a curated list of popular English idioms ('{idiom}').",
                        "context": highlight_context(sentence, match.group(0))
                    })

        # ====== 9. Sarcasm ======
        # Combining exact markers and structural interjection patterns
        sarcasm_markers = ["yeah, right", "oh, great", "what a surprise", "just what i needed", "clear as mud", "big deal", "tell me about it", "oh, fantastic"]
        for sm in sarcasm_markers:
            if sm in sentence_lower:
                 match = re.search(re.escape(sm), sentence, re.IGNORECASE)
                 if match:
                     results.append({
                         "name": "Sarcasm",
                         "text": match.group(0),
                         "explanation": "Common sarcastic phrase used to mock or convey contempt.",
                         "algorithm_explanation": f"Triggered by the exact lexical marker '{sm}' which frequently denotes conversational sarcasm.",
                         "context": highlight_context(sentence, match.group(0))
                     })
                     
        # Structural sarcasm: "Wow, what [positive]" or "Wow... great/amazing"
        structural_sarcasm_pattern = r'\b(wow|oh)\b.*?\b(great|amazing|fantastic|brilliant|perfect)\b'
        match = re.search(structural_sarcasm_pattern, sentence, re.IGNORECASE)
        if match:
            # specifically extract the matched interjection phrase roughly
            phrase = match.group(0)
            if len(phrase.split()) <= 8: # keep it from matching across massive unbound sentences
                results.append({
                    "name": "Sarcasm",
                    "text": phrase,
                    "explanation": "An exaggerated positive interjection Often used sarcastically to mock a negative situation.",
                    "algorithm_explanation": "Regex detected an interjection ('wow' or 'oh') closely followed by an extreme positive adjective, a common structural pattern for verbal irony.",
                    "context": highlight_context(sentence, phrase)
                })

        # ====== 10. Irony ======
        irony_markers = ["ironically", "ironic that", "fire station burned down", "robbed the police station"]
        for im in irony_markers:
            if im in sentence_lower:
                 match = re.search(re.escape(im), sentence, re.IGNORECASE)
                 if match:
                     results.append({
                         "name": "Irony",
                         "text": match.group(0),
                         "explanation": "Explicit marker of situational contrast.",
                         "algorithm_explanation": f"Triggered by the exact text phrase indicating irony or a paradox ('{im}').",
                         "context": highlight_context(sentence, match.group(0))
                     })

        # ====== 11. Transferred Epithet ======
        human_adjectives = {"angry", "wonderful", "weary", "nervous", "sleepless", "happy", "sad", "cruel", "blind", "lazy", "cheerful", "anxious", "melancholy", "restless", "busy", "guilty", "terrified", "frightened", "bored", "jealous", "suspicious", "proud", "lonely", "joyful", "sorrowful", "unhappy", "glad", "mad", "dreary", "bleak"}
        inanimate_targets = {"finger", "day", "road", "smile", "night", "pillow", "sky", "wind", "sea", "journey", "room", "house", "city", "chair", "bed", "morning", "evening", "hour", "year", "mind", "heart", "tear", "tears", "street", "silence", "shadow", "song", "task", "work", "duty", "life", "world", "path", "wood", "glass"}
        
        for i in range(len(tagged) - 1):
            if tagged[i][1] in ['JJ', 'JJR', 'JJS'] and tagged[i+1][1] in ['NN', 'NNS']:
                adj = tagged[i][0].lower()
                noun = tagged[i+1][0].lower()
                if adj in human_adjectives and noun in inanimate_targets:
                    phrase = f"{tagged[i][0]} {tagged[i+1][0]}"
                    results.append({
                        "name": "Transferred Epithet",
                        "text": phrase,
                        "explanation": "An adjective describing a human emotion/state is applied to an inanimate object or concept.",
                        "algorithm_explanation": f"POS Tagging found adjective '{adj}' (human emotion) modifying noun '{noun}' (inanimate object).",
                        "context": highlight_context(sentence, phrase)
                    })

    # ====== 6. Anaphora (Evaluates across multiple sentences/clauses) ======
    clauses = re.split(r'[,;.]\s*', text)
    clauses = [c for c in clauses if len(c.split()) > 0]
    for i in range(len(clauses) - 1):
        words1 = clauses[i].split()
        words2 = clauses[i+1].split()
        if words1[0].lower() == words2[0].lower() and words1[0].isalpha():
            phrase = f"'{words1[0]}' at start of consecutive clauses"
            results.append({
                "name": "Anaphora",
                "text": phrase,
                "explanation": f"Repetition of '{words1[0]}' at the beginning of consecutive clauses.",
                "algorithm_explanation": f"Analyzed sub-clause boundaries (punctuation split) and validated that consecutive clauses begin with the exact same valid word '{words1[0]}'.",
                "context": f"...<mark>{words1[0]}</mark> {' '.join(words1[1:4])}... <mark>{words2[0]}</mark> {' '.join(words2[1:4])}..."
            })

    # ====== 12. Enjambment (Evaluates across multiple lines) ======
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        current_line = lines[i].strip()
        next_line = lines[i+1].strip()
        
        if current_line and next_line:
            if current_line[-1] not in ['.', ',', ';', ':', '!', '?']:
                if len(current_line.split()) >= 3:
                     phrase = "Line break without punctuation"
                     c_line_display = current_line if len(current_line) < 50 else "..." + current_line[-47:]
                     n_line_display = next_line if len(next_line) < 50 else next_line[:47] + "..."
                     results.append({
                         "name": "Enjambment",
                         "text": phrase,
                         "explanation": "A sentence or clause continues across a line break without terminal punctuation.",
                         "algorithm_explanation": f"Line ended with '{current_line[-1]}' instead of punctuation, flowing directly into the next line.",
                         "context": f"{c_line_display} <mark>↵</mark> {n_line_display}"
                     })

    # Exact Match Deduplication ONLY (allows multiple different similes etc.)
    unique_results = []
    seen = set()
    for r in results:
        # We define a unique signature based on Figure Type + the precise Context string it occurs within
        identifier = f"{r['name']}_{r['context']}_{r['text']}"
        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(r)

    return unique_results
