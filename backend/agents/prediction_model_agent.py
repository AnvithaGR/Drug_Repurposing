import pickle
import os
import re
from backend.utils.stemmer import simple_stemmer

class PredictionModelAgent:
    def __init__(self, model_path="models/disease_model.pkl", vectorizer_path="models/disease_vectorizer.pkl"):
        self.model = None
        self.vectorizer = None
        
        if os.path.exists(model_path) and os.path.exists(vectorizer_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            with open(vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
        else:
            print("Model files not found. Please run scripts/train_model.py first.")

    def predict_disease(self, symptoms_text):
        if not self.model or not self.vectorizer:
            return "Unknown"
        
        # Transform input
        vec = self.vectorizer.transform([symptoms_text])
        
        # Predict
        prediction = self.model.predict(vec)
        probs = self.model.predict_proba(vec)
        confidence = max(probs[0])
        
        return prediction[0], round(float(confidence), 3)
