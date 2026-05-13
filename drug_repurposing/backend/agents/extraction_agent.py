from typing import List, Dict


class ExtractionAgent:
    def __init__(self):
        # Import spaCy lazily to avoid import-time failures on incompatible Python
        self.spacy_available = False
        self.nlp = None
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.spacy_available = True
            except Exception:
                # model not available — fall back to blank English pipeline if possible
                try:
                    self.nlp = spacy.blank("en")
                    self.spacy_available = True
                except Exception:
                    self.nlp = None
                    self.spacy_available = False
        except Exception:
            # spaCy not installed or fails to import (e.g., Python version incompatibility)
            self.nlp = None
            self.spacy_available = False

    def extract_entities_from_papers(self, papers: List[dict]) -> Dict[str, dict]:
        # Returns a mapping paper_id -> extracted entities
        out = {}
        for p in papers:
            pid = p.get("id")
            entities = {"drugs": [], "diseases": [], "genes": [], "symptoms": [], "evidence": []}
            # Prefer fields in the mock data if present
            if p.get("drugs"):
                entities["drugs"] = p.get("drugs")
            if p.get("diseases"):
                entities["diseases"] = p.get("diseases")
            if p.get("genes"):
                entities["genes"] = p.get("genes")
            if p.get("symptoms"):
                entities["symptoms"] = p.get("symptoms")

            # fallback: run NER on abstract to pick entities (always run if abstract is present)
            text = p.get("abstract", "")
            
            # Symptom detection glossary for diagnostic features
            symptom_glossary = [
                "Cold", "Fever", "Cough", "Inflammation", "Fatigue", "Nausea", "Pain", 
                "Neuropathy", "Dyspnea", "Anosmia", "Arrhythmia", "Insomnia",
                "Cytokine Storm", "Respiratory Distress", "Cognitive Decline", "Memory Loss"
            ]

            # Evidence / Outcome detection for Real-World Evidence Tracker
            evidence_keywords = ["mortality", "survival", "recovery", "improvement", "reduced", "significant", "superior", "lower risk", "neuroprotective"]
            if text:
                low_text = text.lower()
                for kw in evidence_keywords:
                    # Capture surrounding sentence or phrase if possible
                    if kw in low_text:
                        # naive capture of context: find sentence ending in .
                        parts = text.split(". ")
                        for snt in parts:
                            if kw in snt.lower() and snt not in entities["evidence"]:
                                entities["evidence"].append(snt.strip() + ".")
                
                # Use glossary to extract symptoms from text if not already present
                for sym in symptom_glossary:
                    if sym.lower() in low_text and sym not in entities["symptoms"]:
                        entities["symptoms"].append(sym)

            if text and self.spacy_available and self.nlp is not None:
                try:
                    doc = self.nlp(text)
                    for ent in getattr(doc, "ents", []):
                        if ent.label_ in ("DISEASE", "PROBLEM") and ent.text not in entities["diseases"]:
                            entities["diseases"].append(ent.text)
                        elif ent.label_ in ("CHEMICAL", "DRUG", "ORG", "PERSON") and ent.text not in entities["drugs"]:
                            # Fallback labels like ORG or PERSON often catch proprietary drug names / genes in blank models
                            entities["drugs"].append(ent.text)
                        elif ent.label_ in ("GENE_OR_GENE_PRODUCT", "GENE", "PRODUCT") and ent.text not in entities["genes"]:
                            entities["genes"].append(ent.text)
                except Exception:
                    pass
            
            # simple heuristic fallback if no specific drugs/genes extracted
            if not entities["drugs"] and not entities["genes"] and text:
                import re
                caps = re.findall(r"\b([A-Z][a-zA-Z0-9]{2,})\b", text)
                if len(caps) > 0: entities["diseases"].extend(caps[:1])
                if len(caps) > 1: entities["genes"].extend(caps[1:4])
                if len(caps) > 4: entities["drugs"].extend(caps[4:7])

            # simple de-dup
            for k in entities:
                entities[k] = list(dict.fromkeys(entities[k]))

            out[pid] = entities
        return out
