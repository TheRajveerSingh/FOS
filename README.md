# Figure of Speech Detector & Poetic Generator

A Flask-based Natural Language Processing (NLP) web application designed to automatically detect for various figures of speech in text or transform them into poetic masterpieces.

## 📌 Project Overview
The "Figure of Speech" app features a Dual-Mode interface that allows users to identify deeply embedded literary devices or generate poetic enhancements. The system is a **hybrid NLP engine** that combines traditional rule-based mechanics with deep learning transformers and semantic modeling for high-accuracy detection.

Currently, the system successfully detects 12 figures of speech:
- **Simile**
- **Metaphor**
- **Personification**
- **Hyperbole**
- **Alliteration**
- **Anaphora**
- **Oxymoron**
- **Idiom**
- **Sarcasm**
- **Situational Irony**
- **Transferred Epithet**
- **Enjambment**

## 🤔 Why It Was Made
This project was designed as a College Mini Project for a Natural Language Processing curriculum. The core objective was to demonstrate a functional understanding of foundational NLP concepts without abstracting the logic away into a black-box machine learning model. By using explicit rules and curated templates, the project provides **explainable results** and **transparent generation**, clearly mapping out *why* a specific string of text was flagged or how it was enhanced.

## ✨ Poetic Generator Mode
The new **Generator Mode** takes basic, flat text and transforms it into a more evocative, poetic version.
- **Rule of Six:** Requires at least 6 lines of text to ensure enough context for poetic flow.
- **Intelligent Injection:** Randomly applies Similes, Metaphors, and Personification based on identified Parts-of-Speech.
- **Anaphora Injection:** Occasionally adds repetitive structural markers at the end of the text for a rhythmic conclusion.
- **Detailed Logs:** Shows a "Before & After" breakdown for every transformation applied.

## 🚀 How to Use It
1. Launch the web application.
2. **Choose Your Mode:** Use the toggle in the top-right to switch between **Detector** and **Generator**.
3. **Input Text:** Use the provided text box to type or paste any paragraph, poem, or sentence.
4. **View Results:**
   - **In Detector Mode:** Read through the generated result cards showing the device name, context, and algorithm logic.
   - **In Generator Mode:** View the transformed "Poetic Version" and see the list of devices specifically injected into your text.

## 🧠 NLP Concepts Utilized
This project leans heavily on classical Natural Language Processing methodologies:
- **Tokenization:** Breaking down paragraphs into sentences (`sent_tokenize`) and sentences into individual words (`word_tokenize`) to process the text granularly.
- **Part-of-Speech (POS) Tagging:** Assigning grammatical categories (Nouns, Verbs, Adjectives) to words to understand sentence structure (e.g., finding an inanimate Noun followed by a human Verb to detect *Personification*).
- **Regex-Based Pattern Matching:** Utilizing complex structural string matching to capture phrases (e.g., detecting `like` or `as ... as` syntax for *Similes*).
- **Lexical Analysis:** Cross-referencing word tokens against predefined dictionaries of highly specific markers (e.g., analyzing known contradictory phrase pairs for *Oxymorons*).
- **Basic Syntactic Pattern Recognition:** Utilizing sequential matching logic rather than bag-of-words to preserve structural meaning.
- **Discourse-Level Repetition Detection:** Analyzing structural repetition across multiple subsequent clauses (used to detect *Anaphora*).

## 🆕 Updates

This project has recently been upgraded from a purely rule-based system to a hybrid engine that integrates deep learning transformers, sentiment analysis, and semantic modeling.

### 📁 New Project Structure
- **`ml_models.py`**: A new dedicated module that loads heavy models (RoBERTa, Brown Corpus, WordNet) once at startup to ensure high performance and resource reuse across requests.

### 🧠 New NLP Concepts & Upgrades

1. **RoBERTa Transformer — Sarcasm Detection**
   - **Old:** Hardcoded list of 8 exact phrases (e.g., "yeah, right").
   - **New:** Integration of the `cardiffnlp/twitter-roberta-base-irony` transformer model. It reads the entire sentence and classifies it as IRONY or NON_IRONY with a probability score.
   - **Why:** Sarcasm depends on context and tone. A transformer handles the linguistic nuance far better than static keywords.

2. **VADER Sentiment Analysis — Hyperbole Detection**
   - **Old:** All hyperbole markers (e.g., "extremely", "always") were flagged regardless of context.
   - **New:** Two-tier detection. "Hard markers" always fire, while "Weak intensifiers" only fire when **VADER's compound sentiment score** exceeds ±0.55.
   - **Why:** Adds an emotional charge requirement to reduce false positives in common speech.

3. **WordNet Semantic Distance — Metaphor Detection**
   - **Old:** Limited to a fixed list of 12 predicate nouns.
   - **New:** Uses **WordNet’s Wu-Palmer similarity score** to measure semantic distance between subject and predicate nouns. A score below 0.35 confirms a metaphor.
   - **Why:** Captures the linguistic intuition that metaphors equate two things from unrelated semantic domains.

4. **WordNet Synonym Filter — Simile False Positive Reduction**
   - **Old:** Pure regex pattern matching (`X like Y`).
   - **New:** After regex matching, WordNet checks if the compared words share synonyms. If they do, it's flagged as a possible false positive.
   - **Why:** Distinguishes between meaningful comparisons and trivial ones (e.g., "He runs like he runs").

5. **Brown Corpus N-gram Model — Idiom Detection**
   - **Old:** A hardcoded list of exactly 10 idioms.
   - **New:** A **bigram language model** trained on the entire Brown corpus (~1 million words). Phrases with very low log-probability (below -11.5) are flagged as potential idioms.
   - **Why:** Automatically flags unusual, statistically "bizarre" word combinations without needing a fixed list.

6. **CMU Pronouncing Dictionary — Phonetic Alliteration**
   - **Old:** Matched by the first letter of consecutive words.
   - **New:** Uses the **CMU Pronouncing Dictionary** to map words to phonemes. Matches based on the first sound (e.g., "Phone" and "fire" now match on the /F/ sound).
   - **Why:** Alliteration is a phonetic device, not an orthographic one.

7. **WordNet Lemmatizer — Morphological Normalization**
   - **Old:** Exact string matching against fixed lists.
   - **New:** Tokens are reduced to their base form (e.g., *winds* → *wind*, *winked* → *wink*) before checking.
   - **Why:** Ensures detection works regardless of word inflection or pluralization.

### 🎨 UI Enhancements
- **Confidence Bar:** Visual 0–100% bar on Metaphor, Hyperbole, and Sarcasm cards showing detection certainty.
- **Method Comparison Box:** Displays side-by-side results of old vs. new methods for Simile, Alliteration, and Idiom cards.
- **False Positive Badge:** Warns users when WordNet disagrees with the regex-based simile detection.


## 💻 Environment Setup
To run this project locally, ensure you have Python installed (preferably via a standard Conda environment).

**Required Core Libraries:**
- `nltk` (Natural Language Toolkit)
- `flask` (Web framework)
- `transformers` & `torch` (Deep Learning models)
- `pronouncing` (Phonetic analysis)
- `regex` / `re` (Standard Regex engine)

**Installation:**
```bash
pip install nltk flask transformers torch pronouncing
```
*(Note: The application will automatically download the required NLTK corpus datasets like `punkt`, `punkt_tab`, and `averaged_perceptron_tagger` on its first run).*

**Running the Application:**
Open your terminal in the project directory and run:
```bash
python app.py
```
Then navigate to `http://127.0.0.1:5000` in your web browser.

## 📁 Project Architecture (Files & Rationale)

- **`app.py`**
  - *Why it exists:* The main HTTP server written in Flask. It acts as the bridge routing data between the frontend user interface and the backend Python logic. It also handles the safety checks for downloading missing NLTK datasets.
- **`detector.py`**
  - *Why it exists:* The brain of the detection engine. It houses the `analyze_text(text)` function, iterating through tokenized text to apply 12 detection algorithms and format the output logs.
- **`enhancer.py`**
  - *Why it exists:* The generator engine. It uses POS-based template matching to transform flat sentences into poetic ones, maintaining a "Rule of Six" for minimum input length.
- **`templates/index.html`**
  - *Why it exists:* The structural frontend of the web app. Contains the dropdowns, input areas, and `<mark>` structural layouts.
- **`static/css/style.css`**
  - *Why it exists:* Provides a modern, dark-mode, glassmorphic aesthetic. It turns the flat HTML into a visually engaging, dynamic application using distinct color mapping for different literary devices.
- **`static/js/script.js`**
  - *Why it exists:* Handles the asynchronous Fetch API POST requests to the Flask server, preventing the webpage from needing to refresh every time the user clicks "Analyze". Creates the dynamic, animated result cards on the fly.
