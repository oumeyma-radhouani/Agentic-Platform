import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === IMPORTS DE VOTRE LOGIQUE EXISTANTE ===
from src.backend.batch_runner import run_batch
from src.ai.azure_client import is_azure_configured, create_chat_completion

app = FastAPI(title="NOVA Agentic API", version="2.0")

# Autorise Next.js à communiquer avec ce backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/api/health")
def health_check():
    return {"status": "online", "azure_ready": is_azure_configured()}

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...)):
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
    """Gère la conversation avec le Copilot interactif."""
    try:
        if not is_azure_configured():
            return {"response": "Erreur : Azure OpenAI n'est pas configuré."}
        
        system_prompt = "Vous êtes NOVA, l'Assistant IA d'Analyse de la Satisfaction Client. Soyez clair et précis en français."
        response = create_chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.message}
        ])
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audio")
async def process_audio(file: UploadFile = File(...)):
    """Reçoit un fichier audio et le transcrit avec Whisper."""
    try:
        # Import de votre fonction d'origine
        # REMARQUE : Vérifiez que la fonction s'appelle bien "transcribe_audio" dans src.backend.audio
        from src.backend.audio import transcribe_audio
        
        suffix = os.path.splitext(file.filename or ".wav")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Exécution de Whisper
            transcript = transcribe_audio(tmp_path)
            return {"success": True, "transcript": transcript}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        print(f"Erreur Audio interne: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag")
async def process_rag(file: UploadFile = File(...)):
    """Reçoit un document PDF/TXT pour l'indexation RAG."""
    try:
        from src.backend.azure_rag import process_and_vectorize
        
        suffix = os.path.splitext(file.filename or ".pdf")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            success = process_and_vectorize(tmp_path, file.filename or "doc")
            return {"success": success, "filename": file.filename}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        print(f"Erreur RAG interne: {e}")
        raise HTTPException(status_code=500, detail=str(e))