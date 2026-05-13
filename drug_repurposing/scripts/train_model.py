import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import VotingClassifier
from sklearn.naive_bayes import MultinomialNB
import pickle
import os

# Create models directory
os.makedirs("models", exist_ok=True)

# Use shared stemmer
from backend.utils.stemmer import simple_stemmer

def train_novel_model():
    # Load dataset
    df = pd.read_csv("data/symptom_disease.csv")
    
    X = df["symptoms"]
    y = df["disease"]
    
    # Text Vectorization with Simple Stemming
    vectorizer = TfidfVectorizer(tokenizer=simple_stemmer, ngram_range=(1, 2), token_pattern=None)
    X_vec = vectorizer.fit_transform(X)
    
    # Defining a 'Novel' Hybrid Ensemble Classifier
    clf1 = LogisticRegression(max_iter=2000, C=10)
    clf2 = MultinomialNB(alpha=0.1) # Lower alpha for better fit to rare symptoms
    
    # The 'Novel' part: Weighted Soft Voting Ensemble
    model = VotingClassifier(
        estimators=[('lr', clf1), ('nb', clf2)],
        voting='soft',
        weights=[2, 1] # Prioritize Logistic Regression for its better handling of overlapping symptoms
    )
    
    print("Training Hybrid Semantic Ensemble Model...")
    model.fit(X_vec, y)
    
    # Save the model components
    with open("models/disease_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    
    with open("models/disease_model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    print("Model and Vectorizer saved to 'models/'")

if __name__ == "__main__":
    train_novel_model()
