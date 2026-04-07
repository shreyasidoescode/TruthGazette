import pandas as pd
import re
import string
import joblib
import os
import warnings
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier # The modern replacement
from sklearn.pipeline import Pipeline

# Suppress annoying warnings for a clean terminal
warnings.filterwarnings("ignore", category=FutureWarning)

dataset_path = r"C:\Shrey\data.csv" 

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train():
    print("--- TRAINING MODERN SGD MODEL (99% TARGET) ---")
    df = pd.read_csv(dataset_path)

    # Detect Columns
    text_col = 'text' if 'text' in df.columns else df.columns[0]
    label_col = 'label' if 'label' in df.columns else df.columns[-1]
    
    df = df.dropna(subset=[text_col, label_col])
    if df[label_col].dtype == 'object':
        df[label_col] = df[label_col].map({'FAKE': 0, 'REAL': 1, 'fake': 0, 'real': 1})

    x = df[text_col].apply(clean_text)
    y = df[label_col]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    # NEW PIPELINE: Using SGDClassifier with 'modified_huber' 
    # This gives us the high accuracy AND the 0-100% score for the UI
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=10000, ngram_range=(1,2))),
        ('clf', SGDClassifier(loss='modified_huber', penalty='l2', alpha=1e-4, random_state=42, max_iter=1000))
    ])

    print("Training the Truth Gazette Engine...")
    pipeline.fit(x_train, y_train)

    if not os.path.exists('models'): os.makedirs('models')
    joblib.dump(pipeline, 'models/full_model_pipeline.pkl')

    accuracy = pipeline.score(x_test, y_test)
    print("-" * 30)
    print(f"STUNNING ACCURACY: {accuracy:.2%}")
    print("--- TRAINING FINISHED (NO WARNINGS) ---")

if __name__ == "__main__":
    train()