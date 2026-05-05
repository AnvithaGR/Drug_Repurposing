from typing import Dict, List

class SafetyAgent:
    def __init__(self):
        # Mock database of Drug-Drug Interactions (DDI) and Safety Warnings
        self.ddi_database = {
            "Metformin": ["Insulin", "Cimetidine"],
            "Donepezil": ["Ketoconazole", "Quinidine"],
            "Remdesivir": ["Chloroquine", "Hydroxychloroquine"],
            "Baricitinib": ["Aspirin", "Prednisone"],
            "Liraglutide": ["Warfarin", "Digoxin"]
        }
        
        self.high_risk_warnings = {
            "Chloroquine": "Cardiac Arrhythmia risk; Requires ECG monitoring.",
            "Dexamethasone": "Immunosuppression risk; Long-term use requires taper.",
            "Tocilizumab": "Risk of severe neutropenia and hepatotoxicity.",
            "Baricitinib": "Increased risk of thrombosis.",
            "Donepezil": "Risk of bradycardia and syncope in sensitive patients."
        }

    def evaluate_safety(self, drugname: str) -> Dict:
        """Checks for severe warnings and interaction risks."""
        warnings = []
        status = "safe"
        
        # 1. Check for known clinical warnings
        if drugname in self.high_risk_warnings:
            warnings.append(self.high_risk_warnings[drugname])
            status = "caution"

        # 2. Extract potential interactions
        interactions = self.ddi_database.get(drugname, ["None known in current database"])
        
        return {
            "drug": drugname,
            "status": status,
            "major_warning": self.high_risk_warnings.get(drugname, "Standard clinical monitoring recommended."),
            "interactions": interactions,
            "risk_score": 0.8 if status == "caution" else 0.2
        }
