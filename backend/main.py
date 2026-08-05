import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import de votre logique IA existante
from src.ai.azure_client import is_azure_configured, create_chat_completion
from src.backend.batch_runner import run_batch

app = FastAPI(title="NOVA Agentic API", version="2.0")

# Autoriser React (Port 3000) à communiquer avec FastAPI (Port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de données pour le Chat
class ChatRequest(BaseModel):
    message: str

@app.get("/api/health")
def health_check():
    """Vérification de l'état du serveur."""
    return {"status": "online", "azure_ready": is_azure_configured()}

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...)):
    """Reçoit un fichier JSONL, exécute l'analyse et retourne les résultats."""
    try:
        content = await file.read()
        filename = file.filename or ""
        
        if filename.endswith('.jsonl'):
            lines = content.decode('utf-8').splitlines()
            batch_data = [json.loads(line) for line in lines if line.strip()]
        else:
            batch_data = json.loads(content.decode('utf-8'))
            
        results = run_batch(batch_data)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """Gère les messages du NOVA Copilot."""
    try:
        if not is_azure_configured():
            return {"response": "Erreur : Clé Azure OpenAI manquante. Veuillez vérifier votre fichier .env."}
        
        system_prompt = (
            "Vous êtes NOVA, l'Assistant IA d'Analyse de la Satisfaction Client "
            "pour CloudShift. Répondez de manière professionnelle et concise en français."
        )
        
        response = create_chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.message}
        ])
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))