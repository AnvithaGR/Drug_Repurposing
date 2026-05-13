# AI-Based Multi-Agent System for Drug Repurposing

This mini project implements a small multi-agent pipeline to demonstrate literature retrieval, NLP-based entity extraction, knowledge graph construction, simple prediction, and a frontend visualization.

Features:
- Search input for disease name
- Display extracted entities per paper
- Visualize knowledge graph
- Show drug repurposing suggestions with confidence and evidence (paper ids)

Tech stack:
- Backend: FastAPI (Python)
- NLP: spaCy
- Graph: NetworkX
- Frontend: HTML/CSS/JS + vis-network

Run locally (Windows / VS Code):

1. Create a virtual environment and activate it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Start the app

```powershell
uvicorn backend.app:app --reload
```

4. Open http://127.0.0.1:8000 in your browser

Notes:
- This project uses a small mock dataset in `data/sample_papers.json`. You can replace retrieval logic in `backend/agents/retrieval_agent.py` to call PubMed or other APIs.
- The NLP agent uses spaCy's small English model for demonstration. For better biomedical extraction, swap to SciSpacy models.
