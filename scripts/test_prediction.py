from backend.agents.prediction_model_agent import PredictionModelAgent

agent = PredictionModelAgent()
test_cases = [
    "Sore throat and running nose.",
    "Severe headache with vomiting",
    "fever cough shortness of breath"
]

for t in test_cases:
    res, conf = agent.predict_disease(t)
    print(f"Input: {t} => Predicted: {res} ({conf})")
