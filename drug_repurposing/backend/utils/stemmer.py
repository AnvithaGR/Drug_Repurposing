import re

def simple_stemmer(text):
    # Basic text cleaning
    text = text.lower()
    # Replace punctuation with space
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    
    stemmed = []
    for t in tokens:
        # Avoid stemming very short words
        if len(t) < 4:
            stemmed.append(t)
            continue
        # Manual suffix stripping (naive but effective for symptoms)
        t = re.sub(r'ing$|ny$|ed$|s$|es$|ly$', '', t)
        # Handle custom cases like running -> run, runny -> run
        if t.endswith('run'): t = 'run'
        stemmed.append(t)
    return stemmed
