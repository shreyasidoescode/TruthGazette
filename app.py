from flask import Flask, render_template, request, jsonify
import joblib
import math
import os
import re
import warnings
from newspaper import Article, Config

# Silence warnings for a clean terminal
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)

# 1. LOAD THE MODEL
MODEL_PATH = 'models/full_model_pipeline.pkl'
if os.path.exists(MODEL_PATH):
    pipeline = joblib.load(MODEL_PATH)
    print("AI Model loaded successfully!")
else:
    pipeline = None
    print("ERROR: Model file not found. Run train_model.py first!")

def stealth_scrape(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        config = Config()
        config.browser_user_agent = headers['User-Agent']
        article = Article(url, config=config)
        article.download()
        article.parse()
        return article.text if len(article.text) > 50 else article.title
    except:
        return None

def get_heuristic_adjustment(text):
    text = text.upper()
    adj = 0
    
    # SATIRE & MEME HANDLES (Instant Red)
    satire_handles = ["RIYAL NEWS", "FAUXY", "THE IRONIC TIMES", "RVCJ", "REAL NEWS INDIA"]
    for handle in satire_handles:
        if handle in text: adj -= 70

    # LOGICAL INCONSISTENCY
    singers = ["ARIJIT SINGH", "NEHA KAKKAR", "BADSHAH", "SHREYA GHOSHAL", "SONU NIGAM"]
    sports_terms = ["TEST CRICKET", "RETIREMENT", "IPL", "ICC", "FORMAT", "BOWLING", "BATTING"]
    if any(s in text for s in singers) and any(sp in text for sp in sports_terms):
        adj -= 60

    # INSTITUTIONAL BOOST (Official news)
    inst_boost = ["IMF", "INTERNATIONAL MONETARY FUND", "RESERVE BANK", "FISCAL YEAR", "QUARTERLY REPORT"]
    for word in inst_boost:
        if word in text: adj += 35

    # SPECULATIVE PENALTY (Rumors)
    speculative = ["WHISPERING", "MYSTERIOUS", "UNIDENTIFIED", "COMING TO LIGHT", "SECRET DEAL", "RUMORS"]
    for word in speculative:
        if word in text: adj -= 20

    # COMMON FAKE PHRASES
    if "CURE CANCER" in text or "BIG PHARMA" in text or "SPREAD THE WORD" in text:
        adj -= 50
        
    return adj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if not pipeline:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.json
    content = data.get("content", "").strip()
    
    # 1. Scraping
    if content.startswith('http'):
        text_to_analyze = stealth_scrape(content)
        if not text_to_analyze: text_to_analyze = content
    else:
        text_to_analyze = content

    # 2. Base AI Score
    decision = pipeline.decision_function([text_to_analyze])[0]
    score = int(100 / (1 + math.exp(-decision)))

    # 3. Initial "Short Text" Caution
    if len(text_to_analyze.split()) < 20 and score > 60:
        score -= 10

    # 4. Apply Adjustments
    adj = get_heuristic_adjustment(text_to_analyze)
    score = max(5, min(98, score + adj))

    # 5. Domain Overrides
    content_lower = content.lower()
    if any(d in content_lower for d in ['nature.com', 'bbc.com', 'reuters.com', 'apnews.com']):
        score = max(score, 94)
    if any(d in content_lower for d in ['theonion.com', 'babylonbee.com', 'riyalnews']):
        score = 15

    # 6. Final Result Mapping
    if score <= 39:
        label, color, note = "FAKE", "red", "Sensationalist patterns or parody detected."
    elif score <= 64: 
        label, color, note = "SUSPICIOUS", "yellow", "Unverified claims or speculative tone detected."
    else:
        label, color, note = "CREDIBLE", "green", "Matches patterns of factual, professional reporting."

    return jsonify({"label": label, "score": score, "color": color, "note": note})

if __name__ == '__main__':
    app.run(debug=True)