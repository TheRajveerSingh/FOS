# Figure of Speech Detector: Project Overview

## 1. What We Have Done
We have built a transparent, rule-based Natural Language Processing (NLP) web application capable of **identifying 12 distinct figures of speech** and **generating poetic enhancements** for user-provided text. The underlying engine runs on Python via Flask, leveraging the `nltk` library alongside sophisticated regular expressions and POS-based template matching. The front-end features a modern, animated, glassmorphic dark-mode interface with a dual-mode toggle between detection and generation.

## 2. Why It Was Done
The goal was to create an educational and analytical tool that goes beyond "black-box" AI models. Rather than just predicting that a sentence contains a metaphor, this project explicitly outlines *how* it arrived at that conclusion (e.g., pointing out the precise part-of-speech structure or keyword matches). It's designed to help writers, students, and language enthusiasts understand literary devices while demonstrating practical applications of foundational NLP concepts in a highly visual, interactive way.

---

## 3. Figures of Speech Included & Their Logic

1. **Simile**
   * **Logic:** Regex matching for structures like `as [word] as` and `[words] like a/an/the [word]`. It includes a custom fuzzy-matching function (`difflib`) to prevent false positives for "self-comparisons" (e.g., "coffee like coffee").
2. **Metaphor**
   * **Logic:** POS tagging to find nouns/pronouns connected by a "to-be" verb (is/are/was/were) directly to a noun from a predefined dictionary of metaphorical targets (e.g., "monster", "machine", "ocean").
3. **Personification**
   * **Logic:** Adjacent POS tag tracking. It detects when a noun from a predefined list of inanimate/elemental words (e.g., "wind", "moon", "city") is immediately followed by a verb from a human-action dictionary (e.g., "whispered", "danced").
4. **Hyperbole**
   * **Logic:** Lexical matching against a curated list of extreme exaggeration idioms (e.g., "million times", "takes forever").
5. **Alliteration**
   * **Logic:** Sub-word token iteration. It identifies 3 or more consecutive alphabetical words (ignoring punctuation) that share the same initial consonant/vowel character.
6. **Anaphora**
   * **Logic:** Sentence/clause boundary detection. It splits text using punctuation (`,`, `;`, `.`) and evaluates if consecutive clauses start with the exact same identical word.
7. **Oxymoron**
   * **Logic:** Exact sequence matching for established contradictory bigrams (e.g., "deafening silence", "bittersweet", "living dead").
8. **Idiom**
   * **Logic:** String matching against popular English idiomatic phrases whose figurative meaning differs from literal semantics.
9. **Sarcasm**
   * **Logic:** A hybrid approach using exact lexical markers (e.g., "yeah, right", "clear as mud") and a structural regex pattern detecting an interjection closely followed by an extreme positive adjective (e.g., `Wow... great`).
10. **Irony**
    * **Logic:** Keyword matching for explicit paradox/irony markers and classic situational irony examples (e.g., "ironically", "fire station burned down").
11. **Transferred Epithet**
    * **Logic:** Bigram POS tagging matching an Adjective (`JJ`) to a Noun (`NN`). It flags combinations where the adjective belongs to a human emotion dictionary (e.g., "weary", "sleepless") and the noun belongs to an inanimate object dictionary (e.g., "road", "night").
12. **Enjambment**
    * **Logic:** Multi-line structural analysis. It evaluates text split by line breaks (`\n`). If a line contains text but does not end with terminal punctuation (`. , ; : ! ?`), and immediately flows to the next line, it is flagged.

---

## 4. Poetic Enhancer (Generator Mode) Logic

The Poetic Generator transforms standard text into a more literary version by "injecting" stylistic devices based on the grammatical structure of the input.

*   **Input Constraint:** Requires at least 6 lines of text to ensure the output maintains a poetic flow and rhythmic structure.
*   **Simile Transformation:** Identifies key adjectives (e.g., "bright", "strong") and appends a randomized comparative phrase from a curated dictionary (e.g., "bright like a newborn star").
*   **Metaphor Construction:** Detects a Noun + "To-Be" verb structure and replaces the object with a metaphorical target (e.g., "Life is a journey").
*   **Personification Injection:** Identifies inanimate nouns followed by verbs and replaces the action with a human-centric verb (e.g., "The wind whispered").
*   **Alliteration Matching:** Occasionally flags a noun and prepends an adjective starting with the same consonant to create a phonetic "streak" (e.g., "Silent sky").
*   **Rhythmic Anaphora:** Analyzes the final lines of the text and prepends uniform markers (e.g., "And yet...", "Beyond the horizon...") to create a sense of poetic repetition and closure.

---

## 5. Project Files & Their Roles

| File path | Purpose |
| :--- | :--- |
| **`detector.py`** | The core detection engine. It processes incoming text via the `analyze_text()` function and returns a list of detected figures with algorithmic explanations. |
| **`enhancer.py`** | The poetic generation engine. It processes text via the `enhance_text()` function, applying a "Rule of Six" and injecting devices via template randomization. |
| **`app.py`** | The backend Flask web server. It handles routing for both `/analyze` and `/enhance` endpoints and manages NLTK dataset initialization. |
| **`templates/index.html`** | The structure of the user interface. It contains the title, interactive text area, "Try a sample" dropdown, and the empty container where javascript injects the results. |
| **`static/css/style.css`** | The visual styling of the app. It creates the modern, premium aesthetic including the dark mode background, glassmorphic (frosted glass) panels, typography, and hover animations for the interactive elements. |
| **`static/js/script.js`** | The frontend logic. It listens for button clicks, sends the user's text to the Flask API asynchronously using `fetch`, handles the loading spinners, and dynamically generates HTML cards for the returned figures of speech. |
| **`README.md`** | The main documentation file for Git/GitHub detailing how to install, step-up, and run the project locally. |

---

## 6. NLP Concepts Covered

* **Tokenization:** Breaking down paragraphs into individual sentences (`sent_tokenize`), and sentences into individual words/punctuation (`word_tokenize`) to allow programmatic analysis.
* **Part-of-Speech (POS) Tagging:** Using the NLTK Perceptron tagger to classify words into their grammatical roles (Nouns, Verbs, Adjectives). Used heavily in Metaphor, Personification, and Transferred Epithet detection.
* **Lexical Semantics:** Storing and referencing meaning through curated dictionaries of words grouped by semantic meaning class (e.g., inanimate targets, human verbs, emotional adjectives).
* **Syntactic Pattern Recognition:** Using Regular Expressions to map complex sentence structures (like interjections followed by adjectives, or separated `as...as` boundaries).
* **Discourse & Paragraph-Level Mapping:** Tracking structural features that span across boundaries—such as consecutive clauses (Anaphora) and line-breaks (Enjambment).
* **Fuzzy String Matching / Edit Distance:** Using sequence matchers (`difflib`) to measure character similarity between words, preventing false similarities and spelling typos from breaking comparisons.
* **Template-Based Text Generation:** Utilizing slot-filling and randomization within curated lexical dictionaries to transform sentence semantics without losing structural coherence.
* **Non-Deterministic Heuristics:** Applying probabilistic triggers (randomized weights) to determine when and where a figure of speech should be injected during the generation process.
