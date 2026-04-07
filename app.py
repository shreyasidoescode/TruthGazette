from flask import Flask, render_template, request, jsonify
import joblib
import math
import os
import re
import warnings
from newspaper import Article, Config

warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
pipeline = joblib.load('models/full_model_pipeline.pkl')

def stealth_scrape(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        config = Config()
        config.browser_user_agent = headers['User-Agent']
        article = Article(url, config=config)
        article.download(); article.parse()
        return article.text if len(article.text) > 50 else article.title
    except: return None

def get_heuristic_adjustment(text):
    text = text.upper()
    adj = 0
    
    # RUMOR & SCANDAL MARKERS (Strong Penalty)
    rumor_words = ["WHISPERING", "MANY ARE SAYING", "SEEMS THE", "COMING TO LIGHT", "MYSTERIOUS", "UNIDENTIFIED", "PRIVATE DINNER", "LURKING", "SECRET DEAL", "ALLEGEDLY", "RUMORS"]
    for word in rumor_words:
        if word in text: adj -= 15 # Each word found penalizes the score

    # SCIENTIFIC & ACADEMIC MARKERS (Strong Boost)
    science_words = ["SCIENTIFIC", "STUDY", "RESEARCH", "PEER-REVIEWED", "JOURNAL", "CLINICAL", "EVIDENCE", "DATA SHOWS", "PUBLISHED IN", "EXPERIMENT", "ANALYSIS OF", "OBSERVED"]
    for word in science_words:
        if word in text: adj += 15

    # CONSPIRACY/CLICKBAIT MARKERS
    if "CURE" in text and "CANCER" in text: adj -= 40
    if "BIG PHARMA" in text or "HIDING" in text: adj -= 30
    if text.count('!') > 2: adj -= 15
        
    return adj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    content = data.get("content", "").strip()
    
    if content.startswith('http'):
        text_to_analyze = stealth_scrape(content)
        if not text_to_analyze: text_to_analyze = content
    else:
        text_to_analyze = content

    # 1. BASE AI SCORE
    decision = pipeline.decision_function([text_to_analyze])[0]
    base_score = int(100 / (1 + math.exp(-decision)))

    # 2. HEURISTIC ADJUSTMENT
    adj = get_heuristic_adjustment(text_to_analyze)
    score = max(5, min(98, base_score + adj))

    # 3. DOMAIN OVERRIDES
    satire = ['theonion.com', 'babylonbee.com']
    trusted = ['reuters.com', 'bbc.com', 'apnews.com', 'thehindu.com', 'nature.com', 'pib.gov.in', 'science.org']

    if any(d in content.lower() for d in satire):
        score, label, color, note = 15, "FAKE (SATIRE)", "red", "Known parody source detected."
    elif any(d in content.lower() for d in trusted):
        score = max(score, 94) # Force high credibility for Nature/Reuters/etc
        label, color, note = "CREDIBLE", "green", "Verified high-authority domain detected."
    else:
        # Final Scoring Logic
        if score <= 39:
            label, color, note = "FAKE", "red", "Sensationalist or speculative patterns detected."
        elif score <= 59:
            label, color, note = "SUSPICIOUS", "yellow", "Mixed signals. Contains unverified rumors or biased language."
        else:
            label, color, note = "CREDIBLE", "green", "Matches patterns of factual, evidence-based reporting."

    return jsonify({"label": label, "score": score, "color": color, "note": note})

if __name__ == '__main__':
    app.run(debug=True)