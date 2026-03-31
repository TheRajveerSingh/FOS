from flask import Flask, render_template, request, jsonify
from detector import analyze_text
import nltk

app = Flask(__name__)

# Pre-download required NLTK datasets at startup
def setup_nltk():
    print("Downloading required NLTK data...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
    print("NLTK data loaded.")

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
        
        results = analyze_text(text)
        return jsonify({"results": results})
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print("Error during analysis:", error_msg)
        return jsonify({"error": str(e), "traceback": error_msg}), 500

if __name__ == '__main__':
    setup_nltk()
    app.run(debug=True, port=5000)
