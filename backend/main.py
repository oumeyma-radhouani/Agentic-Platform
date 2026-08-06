import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

# === IMPORTS DE VOTRE LOGIQUE EXISTANTE ===
from src.backend.batch_runner import run_batch
from src.ai.azure_client import is_azure_configured, create_chat_completion

app = FastAPI(title="NOVA API", version="2.0")

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
    session_id: str = "admin_dashboard_session"

def get_mongo_history(session_id: str):
    """Fonction utilitaire pour récupérer l'historique MongoDB de la session"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=mongo_uri,
        database_name="nova_db", # Base de données renommée au nom du produit
        collection_name="chat_histories"
    )

@app.get("/api/health")
def health_check():
    return {"status": "online", "azure_ready": is_azure_configured()}

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...), session_id: str = Form("admin_dashboard_session")):
    try:
        content = await file.read()
        filename = file.filename or ""
        
        if filename.endswith('.jsonl'):
            lines = content.decode('utf-8').splitlines()
            batch_data = [json.loads(line) for line in lines if line.strip()]
        else:
            batch_data = json.loads(content.decode('utf-8'))
            
        results = run_batch(batch_data)
        
        # SAUVEGARDE DANS LA MÉMOIRE MONGODB
        history = get_mongo_history(session_id)
        history.add_ai_message(f"[Système] L'analyse du lot est terminée. J'ai traité {results['summary_metrics']['total_processed']} retours avec un NPS global de {results['summary_metrics']['nps_score']}.")
        
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """Gère la conversation avec NOVA et sauvegarde dans MongoDB."""
    try:
        if not is_azure_configured():
            return {"response": "Erreur : Azure OpenAI n'est pas configuré."}
        
        history = get_mongo_history(payload.session_id)

        # Prompt système réinitialisé avec l'identité NOVA
        system_prompt = (
            "Vous êtes NOVA, un Assistant IA d'analyse de données et d'aide à la décision. "
            "Vous avez accès aux résultats des fichiers uploadés par l'utilisateur. "
            "Soyez clair, précis et concis en français."
        )
        messages_for_azure = [{"role": "system", "content": system_prompt}]
        
        # Injecter l'historique précédent depuis MongoDB
        for msg in history.messages:
            role = "user" if msg.type == "human" else "assistant"
            messages_for_azure.append({"role": role, "content": msg.content})
            
        # Ajouter le message actuel
        messages_for_azure.append({"role": "user", "content": payload.message})

        # Appel à Azure OpenAI
        response = create_chat_completion(messages_for_azure)
        
        # Sauvegarder dans MongoDB
        history.add_user_message(payload.message)
        history.add_ai_message(response)
        
        return {"response": response}
        
    except Exception as e:
        print(f"Erreur MongoDB/Chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/chat/history")
async def get_history(session_id: str = "admin_dashboard_session"):
    """Récupère l'historique complet des messages depuis MongoDB."""
    try:
        history = get_mongo_history(session_id)
        formatted_messages = []
        for msg in history.messages:
            sender = "user" if msg.type == "human" else "copilot"
            formatted_messages.append({"sender": sender, "text": msg.content})
        return {"success": True, "messages": formatted_messages}
    except Exception as e:
        print(f"Erreur récupération historique: {e}")
        return {"success": True, "messages": []}

@app.post("/api/audio")
async def process_audio(file: UploadFile = File(...), session_id: str = Form("admin_dashboard_session")):
    """Reçoit un fichier audio, le transcrit avec Whisper et sauvegarde dans MongoDB."""
    try:
        from src.backend.audio import transcribe_audio
        
        suffix = os.path.splitext(file.filename or ".wav")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            transcript = transcribe_audio(tmp_path)
            
            # SAUVEGARDE DANS LA MÉMOIRE MONGODB
            history = get_mongo_history(session_id)
            history.add_ai_message(f"[Système] J'ai transcrit le fichier audio {file.filename}. Voici le contenu : {transcript}")
            
            return {"success": True, "transcript": transcript}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        print(f"Erreur Audio interne: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag")
async def process_rag(file: UploadFile = File(...), session_id: str = Form("admin_dashboard_session")):
    """Reçoit un document PDF/TXT pour l'indexation RAG et sauvegarde dans MongoDB."""
    try:
        from src.backend.azure_rag import process_and_vectorize
        
        suffix = os.path.splitext(file.filename or ".pdf")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            success = process_and_vectorize(tmp_path, file.filename or "doc")
            
            # SAUVEGARDE DANS LA MÉMOIRE MONGODB
            if success:
                history = get_mongo_history(session_id)
                history.add_ai_message(f"[Système] J'ai indexé et vectorisé le document {file.filename} dans la base de connaissances.")
                
            return {"success": success, "filename": file.filename}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        print(f"Erreur RAG interne: {e}")
        raise HTTPException(status_code=500, detail=str(e))