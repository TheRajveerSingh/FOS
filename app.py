
from flask import Flask, render_template, request, jsonify
import nltk
 
app = Flask(__name__)
 
 
def setup_nltk():
    print("Downloading required NLTK data...")
    for pkg in ('punkt', 'punkt_tab', 'averaged_perceptron_tagger',
                'averaged_perceptron_tagger_eng', 'vader_lexicon',
                'wordnet', 'omw-1.4', 'brown'):
        nltk.download(pkg, quiet=True)
    print("NLTK data loaded.")
 
 
def warmup_models():
    print("Loading ML models...")
    try:
        import ml_models  # noqa: F401
        print("ML models ready.")
    except Exception as e:
        print(f"WARNING: ML model warm-up failed: {e}")
 
 
@app.route('/')
def home():
    return render_template('index.html')
 
 
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')
        if not text:
            return jsonify({"error": "No text provided", "results": []}), 400
        from detector import analyze_text
        results = analyze_text(text)
        return jsonify({"results": results})
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print("Error during analysis:", error_msg)
        return jsonify({"error": str(e), "traceback": error_msg}), 500
 
 
@app.route('/enhance', methods=['POST'])
def enhance():
    try:
        data = request.json
        text = data.get('text', '')
        if not text:
            return jsonify({"error": "No text provided"}), 400
        from enhancer import enhance_text
        result = enhance_text(text)
        return jsonify(result)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print("Error during enhancement:", error_msg)
        return jsonify({"error": str(e), "traceback": error_msg}), 500
 
 
if __name__ == '__main__':
    setup_nltk()
    warmup_models()
    app.run(debug=True, port=5000)