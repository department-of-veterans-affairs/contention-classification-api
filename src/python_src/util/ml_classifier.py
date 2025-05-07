import os
import re
import string
import joblib
from typing import Optional, Tuple

# Load the models
TFIDF_PATH = os.path.join(os.path.dirname(__file__), 'models', 'tfidf_vectorizer.pkl')
CLASSIFIER_PATH = os.path.join(os.path.dirname(__file__), 'models', 'logistic_model.pkl')

tfidf_vectorizer = joblib.load(TFIDF_PATH)
logistic_model = joblib.load(CLASSIFIER_PATH)

# dummy clean text. will be replace by the one used on training pipeline
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(rf"[{re.escape(string.punctuation)}]", "", text) 
    text = re.sub(r"\s+", " ", text)  
    text = text.strip()
    return text


def ml_classify_text(text: str) -> Optional[int]:
    if not text:
        return None

    cleaned = clean_text(text)
    transformed = tfidf_vectorizer.transform([cleaned])
    prediction = logistic_model.predict(transformed)[0]

    return prediction