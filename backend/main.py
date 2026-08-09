import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from src.backend.batch_runner import run_batch
from src.ai.azure_client import is_azure_configured, create_chat_completion

app = FastAPI(title="NOVA API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "executive_dashboard_session"

def get_mongo_history(session_id: str):
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    # Forçage pour contrer (si possible) le pare-feu du fournisseur d'accès
    if "tlsallowinvalidcertificates" not in mongo_uri.lower():
        separator = "&" if "?" in mongo_uri else "?"
        mongo_uri += f"{separator}tlsAllowInvalidCertificates=true"

    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=mongo_uri,
        database_name="nova_db", 
        collection_name="chat_histories"
    )

@app.get("/api/health")
def health_check():
    return {"status": "online", "azure_ready": is_azure_configured()}

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        content = await file.read()
        filename = file.filename or ""
        
        if filename.endswith('.jsonl'):
            lines = content.decode('utf-8').splitlines()
            batch_data = [json.loads(line) for line in lines if line.strip()]
        else:
            parsed_data = json.loads(content.decode('utf-8'))
            # CORRECTION ICI : On extrait la liste 'records' si c'est un dictionnaire
            if isinstance(parsed_data, dict) and "records" in parsed_data:
                batch_data = parsed_data["records"]
            elif isinstance(parsed_data, dict):
                batch_data = [parsed_data]
            else:
                batch_data = parsed_data
            
        results = run_batch(batch_data)
        
        # FILET DE SÉCURITÉ
        try:
            history = get_mongo_history(session_id)
            total = results.get('summary_metrics', {}).get('total_processed', 0)
            nps = results.get('summary_metrics', {}).get('nps_score', 0)
            history.add_ai_message(f"[Système] L'analyse stratégique est terminée. J'ai examiné {total} retours (Score NPS : {nps}) et généré des recommandations d'aide à la décision.")
        except Exception as db_err:
            print(f"⚠️ Avertissement MongoDB (Blocage Réseau ignoré) : La sauvegarde dans l'historique a échoué, mais l'analyse continue.")
        
        return {"success": True, "data": results}
    except Exception as e:
        print(f"Erreur API Batch: {e}") 
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    try:
        if not is_azure_configured():
            return {"response": "Erreur : Azure OpenAI n'est pas configuré."}
        
        system_prompt = (
            "Vous êtes NOVA, un Assistant IA d'analyse de données et d'aide à la décision. "
            "Soyez clair, précis et concis en français."
        )
        messages_for_azure = [{"role": "system", "content": system_prompt}]
        
        # FILET DE SÉCURITÉ MONGODB
        history = None
        try:
            history = get_mongo_history(payload.session_id)
            for msg in history.messages:
                role = "user" if msg.type == "human" else "assistant"
                messages_for_azure.append({"role": role, "content": msg.content})
        except Exception as db_err:
            print(f"⚠️ Historique MongoDB inaccessible, mode sans-mémoire activé.")
            
        messages_for_azure.append({"role": "user", "content": payload.message})
        response = create_chat_completion(messages_for_azure)
        
        if history:
            try:
                history.add_user_message(payload.message)
                history.add_ai_message(response)
            except:
                pass
        
        return {"response": response}
        
    except Exception as e:
        print(f"Erreur Chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/chat/history")
async def get_history(session_id: str = "executive_dashboard_session"):
    try:
        history = get_mongo_history(session_id)
        formatted_messages = []
        for msg in history.messages:
            sender = "user" if msg.type == "human" else "copilot"
            formatted_messages.append({"sender": sender, "text": msg.content})
        return {"success": True, "messages": formatted_messages}
    except Exception as e:
        print(f"⚠️ Impossible de charger l'historique MongoDB (Blocage Réseau).")
        return {"success": True, "messages": []}

@app.post("/api/audio")
async def process_audio(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        from src.backend.audio import transcribe_audio
        
        suffix = os.path.splitext(file.filename or ".wav")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            transcript = transcribe_audio(tmp_path)
            
            try:
                history = get_mongo_history(session_id)
                history.add_ai_message(f"[Système] J'ai analysé l'interaction vocale ({file.filename}).")
            except:
                pass
            
            return {"success": True, "transcript": transcript}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag")
async def process_rag(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        from src.backend.azure_rag import process_and_vectorize
        
        suffix = os.path.splitext(file.filename or ".pdf")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            success = process_and_vectorize(tmp_path, file.filename or "doc")
            
            if success:
                try:
                    history = get_mongo_history(session_id)
                    history.add_ai_message(f"[Système] J'ai assimilé les données du document ({file.filename}).")
                except:
                    pass
                
            return {"success": success, "filename": file.filename}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))