from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import timedelta
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.extraction_agent import ExtractionAgent
from backend.agents.prediction_model_agent import PredictionModelAgent
from backend.agents.graph_agent import GraphAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.safety_agent import SafetyAgent
from backend.utils.security import (
    create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.utils.database import user_db
from backend.utils.email_service import (
    send_verification_email, generate_verification_token, verify_token, ENABLE_EMAIL
)
from backend.models.user import Token, TokenData, UserLogin, UserCreate, User
import uvicorn
from fastapi import UploadFile, File
import os
from pathlib import Path
import difflib

app = FastAPI(title="AI-Based Multi-Agent System for Drug Repurposing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency to get the current authenticated user from token."""
    payload = decode_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_db.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Serve frontend static files from the frontend/ folder
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the main application page. Frontend will handle auth checks and redirects."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/login.html", response_class=HTMLResponse)
def login_page():
    with open("frontend/login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

retriever = RetrievalAgent("data/sample_papers.json")
extraction_agent = ExtractionAgent()
graph_agent = GraphAgent(drug_gene_path="data/drug_gene.csv", gene_disease_path="data/gene_disease.csv")
prediction_model_agent = PredictionModelAgent()
validation_agent = ValidationAgent()
safety_agent = SafetyAgent()

# Build disease list from dataset for validation
_DATASET_DISEASES = []
for p in retriever.papers:
    for d in p.get('diseases', []):
        if d and d not in _DATASET_DISEASES:
            _DATASET_DISEASES.append(d)


# Local language mapping for better matching (Kannada, Tamil, etc.)
LOCAL_LANGUAGE_MAPPING = {
    # Kannada
    "ನಗಡಿ": "Common Cold",
    "ನೆಗಡಿ": "Common Cold",
    "negdi": "Common Cold",
    "ಜ್ವರ": "Fever",
    "ಕ್ಯಾನ್ಸರ್": "Cancer",
    "ಮಧುಮೇಹ": "Diabetes",
    "ಲಂಕದ ಕ್ಯಾನ್ಸರ್": "Lung Cancer",
    # Tamil
    "ஜுரம்": "Fever",
    "கோல்ட்": "Common Cold",
    "காய்ச்சல்": "Fever",
    "சளி": "Common Cold",
    "புற்றுநோய்": "Cancer",
    "நீரிழிவு": "Diabetes",
    "மார்பகப் புற்றுநோய்": "Breast Cancer",
    "ஜலதோஷம்": "Common Cold"
}

@app.get("/api/validate_disease")
def validate_disease(name: str, real_data: bool = False) -> dict:
    """Validate a disease name against dataset diseases. Returns matched name or suggestions.

    - If exact or sufficiently close match found, `accepted` is true and `matched_name` is provided.
    - Otherwise `suggestions` contains close candidates (may be empty).
    """
    if not name or not name.strip():
        return {"accepted": False, "suggestions": _DATASET_DISEASES[:10], "message": "Empty disease name"}

    q = name.strip()
    
    # Check Local Language mapping
    if q in LOCAL_LANGUAGE_MAPPING:
        return {"accepted": True, "matched_name": LOCAL_LANGUAGE_MAPPING[q], "suggestions": [], "message": "Local language match found"}
    
    # Exact case-insensitive match
    for d in _DATASET_DISEASES:
        if d.lower() == q.lower():
            return {"accepted": True, "matched_name": d, "suggestions": [], "message": "Exact match found"}

    # Fuzzy matching using difflib
    candidates = difflib.get_close_matches(q, _DATASET_DISEASES, n=5, cutoff=0.0)
    # Compute ratios and sort
    scored = []
    for c in candidates:
        ratio = difflib.SequenceMatcher(None, q.lower(), c.lower()).ratio()
        scored.append((c, ratio))
    scored.sort(key=lambda x: x[1], reverse=True)

    ACCEPT_THRESHOLD = 0.78
    SUGGEST_THRESHOLD = 0.50

    if scored and scored[0][1] >= ACCEPT_THRESHOLD:
        return {"accepted": True, "matched_name": scored[0][0], "suggestions": [s for s, r in scored], "message": "Close match accepted"}

    suggestions = [s for s, r in scored if r >= SUGGEST_THRESHOLD]
    # If no strong matches, include all available diseases as fallback suggestions
    if not suggestions:
        suggestions = _DATASET_DISEASES[:15]  # Show first 15 diseases
    
    # If no dataset suggestions but real_data is requested, indicate remote attempt
    if real_data:
        return {"accepted": True, "matched_name": q, "suggestions": suggestions, "message": "Will attempt live retrieval"}

    return {"accepted": False, "suggestions": suggestions, "message": "No confident match found"}

SIDE_EFFECTS = {
    "Remdesivir": "Nausea, increased liver enzymes",
    "Chloroquine": "Nausea, Arrhythmia, blurred vision",
    "Dexamethasone": "Insomnia, increased appetite, mood changes",
    "Baricitinib": "Upper respiratory infections, nausea",
    "Metformin": "Nausea, diarrhea, metallic taste",
    "Tocilizumab": "Headache, hypertension, injection site reactions",
    "Donepezil": "Nausea, diarrhea, insomnia",
    "Memantine": "Dizziness, headache, confusion",
    "Liraglutide": "Nausea, vomiting, hypoglycemia",
}


@app.post("/api/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Login endpoint - accepts username and password, returns JWT token."""
    user = user_db.get_user_by_username(form_data.username)
    
    # First check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not (user and user_db.authenticate_user(form_data.username, form_data.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if email is verified
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Email not verified. Please check {user['email']} for verification link."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email")
        }
    }


@app.post("/api/register", response_model=dict)
async def register(user_data: UserCreate) -> dict:
    """Register a new user with email verification."""
    try:
        # Create user
        new_user = user_db.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )

        # Generate verification token and link
        verification_token = generate_verification_token(new_user["email"])
        verification_link = f"http://127.0.0.1:8000/api/verify-email?token={verification_token}"

        # If email sending is disabled (dev mode), auto-verify and return link/token in response
        if not ENABLE_EMAIL:
            user_db.verify_user_email(new_user["email"])
            return {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "email_verified": True,
                "message": "User registered and auto-verified (dev mode).",
                "verification_link": verification_link,
                "verification_token": verification_token
            }

        # Production-like flow: send email (email_service prints token in dev fallback)
        sent = send_verification_email(new_user["email"], new_user["username"], verification_token)
        if not sent:
            # Fall back to returning the verification link if email sending fails
            return {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "email_verified": new_user["email_verified"],
                "message": "Registered but failed to send verification email. Returning verification link for convenience.",
                "verification_link": verification_link
            }

        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "email_verified": new_user["email_verified"],
            "message": "User registered successfully. Please check your email to verify your account."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@app.get("/api/verify-email")
async def verify_email(token: str) -> dict:
    """Verify user's email address using token."""
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark email as verified
    if user_db.verify_user_email(email):
        return {
            "message": "Email verified successfully!",
            "email": email,
            "redirect": "http://127.0.0.1:8000/api/docs"  # Redirect to API docs or login page
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User email not found"
        )


@app.post("/api/resend-verification")
async def resend_verification(email: str) -> dict:
    """Resend verification email."""
    user = user_db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate and send new verification email
    verification_token = generate_verification_token(email)
    if send_verification_email(email, user["username"], verification_token):
        return {
            "message": "Verification email sent. Please check your inbox."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@app.post("/api/login", response_model=Token)
async def login_json(user_login: UserLogin) -> Token:
    """Alternative login endpoint that accepts JSON instead of form data."""
    user = user_db.authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email")
        }
    }


@app.get("/api/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)) -> User:
    """Get current user info from token."""
    return User(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email"),
        is_active=current_user.get("is_active", True),
        email_verified=current_user.get("email_verified", False)
    )

@app.get("/api/diseases")
def get_diseases(current_user: dict = Depends(get_current_user)):
    # extract all unique diseases from retriever papers
    diseases = set()
    for p in retriever.papers:
        if p.get("diseases"):
            diseases.update(p["diseases"])
    return JSONResponse(list(diseases))

@app.get("/api/process")
def process(disease: str = Query(..., description="Disease or symptoms to search"), real_data: bool = Query(False, description="Use real PubMed API"), current_user: dict = Depends(get_current_user)):
    # 1. Flow Check: If input contains multiple symptoms (commas or and), use ML model
    q = disease.strip()
    predicted_disease = q
    confidence = 1.0
    is_prediction = False

    if "," in q or " and " in q.lower() or len(q.split()) > 3:
        predicted_disease, confidence = prediction_model_agent.predict_disease(q)
        is_prediction = True
    
    # 2. Get drugs from Knowledge Graph (drug -> gene -> disease)
    predictions = graph_agent.suggest_drugs(predicted_disease)
    
    # 3. Add safety/validation to predictions
    for p in predictions:
        val = validation_agent.validate_drug(p["drug"])
        if val["status"] == "warning":
            p["breakdown"] += f"<br><span style='color:#ef4444;'>⚠️ Warning: {val['message']}</span>"
        p["clinical_trial"] = val.get("clinical_trial", False)
        
        safety = safety_agent.evaluate_safety(p["drug"])
        if safety["status"] == "caution":
            p["breakdown"] += f"<br><span style='color:#facc15; font-weight:bold;'>🛡️ SAFETY: {safety['major_warning']}</span>"

    # 4. Get Graph Visualization Data
    graph_data = graph_agent.get_graph_data()

    report = {
        "disease": predicted_disease,
        "is_prediction": is_prediction,
        "prediction_confidence": confidence,
        "papers": [], # CSV flow doesn't use papers directly
        "entities": {},
        "graph": graph_data,
        "predictions": predictions,
        "evidence": [],
        "clinical_evidence": [],
    }
    return JSONResponse(report)

@app.get("/api/similar_diseases")
def get_similar_diseases(disease: str, current_user: dict = Depends(get_current_user)):
    # Find diseases shared in the research context
    all_papers = retriever.papers
    target_genes = set()
    for p in all_papers:
        if disease.lower() in [d.lower() for d in p.get("diseases", [])]:
            target_genes.update(p.get("genes", []))
            
    similar_scores = {}
    for p in all_papers:
        p_diseases = p.get("diseases", [])
        if any(d.lower() == disease.lower() for d in p_diseases):
            continue
        # calculate gene intersection
        p_genes = set(p.get("genes", []))
        overlap = len(p_genes.intersection(target_genes))
        if overlap > 0:
            for d in p_diseases:
               similar_scores[d] = similar_scores.get(d, 0) + overlap
               
    sorted_sim = sorted(similar_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    return JSONResponse([{"name": name, "score": score} for name, score in sorted_sim])

@app.get("/api/compare_drugs")
def compare_drugs(drug1: str, drug2: str, current_user: dict = Depends(get_current_user)):
    all_papers = retriever.papers
    def get_info(name):
        genes = set()
        papers_count = 0
        for p in all_papers:
            if any(name.lower() == d.lower() for d in p.get("drugs", [])):
                genes.update(p.get("genes", []))
                papers_count += 1
        return {"genes": list(genes), "papers": papers_count}
        
    info1 = get_info(drug1)
    info2 = get_info(drug2)
    
    return JSONResponse({
        "drug1": {"name": drug1, "side_effects": SIDE_EFFECTS.get(drug1, "Nausea, fatigue"), **info1},
        "drug2": {"name": drug2, "side_effects": SIDE_EFFECTS.get(drug2, "Nausea, fatigue"), **info2}
    })

@app.get("/api/symptom_discovery")
def symptom_discovery(symptoms: str = Query(..., description="Comma separated symptoms"), current_user: dict = Depends(get_current_user)):
    # 1. Use ML Model to predict disease from symptoms
    predicted_disease, confidence = prediction_model_agent.predict_disease(symptoms)
    
    if predicted_disease == "Unknown":
        return JSONResponse([])

    # 2. Get drug suggestions for the predicted disease from the Knowledge Graph
    suggestions = graph_agent.suggest_drugs(predicted_disease)
    
    # 3. Format as discovery results
    # We'll return the predicted disease as the top match
    results = [{
        "disease": predicted_disease,
        "match_score": f"{int(confidence * 100)}%",
        "matched_symptoms": [symptoms],
        "suggested_drugs": [p["drug"] for p in suggestions[:3]]
    }]
        
    return JSONResponse(results)


if __name__ == "__main__":
    # run server
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
