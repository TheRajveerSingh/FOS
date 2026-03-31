# Figure of Speech Detector

A Flask-based Natural Language Processing (NLP) web application designed to automatically detect and explain various figures of speech in normal human text.

## 📌 Project Overview
The "Figure of Speech Detector" allows users to input custom text or select from predefined samples to identify deeply embedded literary devices. Rather than relying on heavy predictive Machine Learning models (like LLMs), this system is built entirely on **rule-based NLP mechanics**. It breaks down each sentence and analyzes its core grammatical structure to spot stylistic language.

Currently, the system successfully detects:
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

## 🤔 Why It Was Made
This project was designed as a College Mini Project for a Natural Language Processing curriculum. The core objective was to demonstrate a functional understanding of foundational NLP concepts without abstracting the logic away into a black-box machine learning model. By using explicit rules, the project provides **explainable results**, clearly mapping out *why* a specific string of text was flagged as a figure of speech.

## 🚀 How to Use It
1. Launch the web application.
2. Use the provided text box to type or paste any paragraph, poem, or sentence.
3. Click "Analyze Text".
4. Read through the generated result cards! Each card will:
   - Identify the figure of speech.
   - Visually highlight the exact phrase within the context of the original sentence.
   - Provide a human-friendly definition.
   - Provide an "Algorithm Logic" breakdown explaining how the backend Python script detected it.

## 🧠 NLP Concepts Utilized
This project leans heavily on classical Natural Language Processing methodologies:
- **Tokenization:** Breaking down paragraphs into sentences (`sent_tokenize`) and sentences into individual words (`word_tokenize`) to process the text granularly.
- **Part-of-Speech (POS) Tagging:** Assigning grammatical categories (Nouns, Verbs, Adjectives) to words to understand sentence structure (e.g., finding an inanimate Noun followed by a human Verb to detect *Personification*).
- **Regex-Based Pattern Matching:** Utilizing complex structural string matching to capture phrases (e.g., detecting `like` or `as ... as` syntax for *Similes*).
- **Lexical Analysis:** Cross-referencing word tokens against predefined dictionaries of highly specific markers (e.g., analyzing known contradictory phrase pairs for *Oxymorons*).
- **Basic Syntactic Pattern Recognition:** Utilizing sequential matching logic rather than bag-of-words to preserve structural meaning.
- **Discourse-Level Repetition Detection:** Analyzing structural repetition across multiple subsequent clauses (used to detect *Anaphora*).

## 💻 Environment Setup
To run this project locally, ensure you have Python installed (preferably via a standard Conda environment).

**Required Core Libraries:**
- `nltk` (Natural Language Toolkit)
- `flask` (Web framework)
- `regex` / `re` (Standard Regex engine)

**Installation:**
```bash
pip install nltk flask
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
  - *Why it exists:* The brain of the project. It houses the `analyze_text(text)` function, decoupling the heavy NLP logic from the web server. This file iterates through the tokenized text, applies the 10 detection algorithms, and formats the output logs.
- **`templates/index.html`**
  - *Why it exists:* The structural frontend of the web app. Contains the dropdowns, input areas, and `<mark>` structural layouts.
- **`static/css/style.css`**
  - *Why it exists:* Provides a modern, dark-mode, glassmorphic aesthetic. It turns the flat HTML into a visually engaging, dynamic application using distinct color mapping for different literary devices.
- **`static/js/script.js`**
  - *Why it exists:* Handles the asynchronous Fetch API POST requests to the Flask server, preventing the webpage from needing to refresh every time the user clicks "Analyze". Creates the dynamic, animated result cards on the fly.
