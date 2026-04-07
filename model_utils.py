import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import re
import string

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r"\\W"," ",text) 
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text

def predict_news(text):
    model = joblib.load('models/fake_news_model.pkl')
    vectorizer = joblib.load('models/vectorizer.pkl')
    
    cleaned = clean_text(text)
    vectorized = vectorizer.transform([cleaned])
    prediction_prob = model.predict_proba(vectorized)[0][1] # Probability of being "Credible"
    
    score = round(prediction_prob * 100, 2)
    
    if score < 40:
        label = "FAKE"
        color = "red"
        reason = "Sensationalist language and patterns typical of misinformation detected."
    elif score < 60:
        label = "SUSPICIOUS"
        color = "yellow"
        reason = "Mixed signals detected. Source reliability or phrasing is questionable."
    else:
        label = "CREDIBLE"
        color = "green"
        reason = "Content aligns with standard journalistic patterns and factual reporting."
        
    return {"label": label, "score": score, "color": color, "reason": reason}