import os
import json
import tempfile
import logging
import io
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.backend.batch_runner import run_batch
from src.backend.context_store import format_batch_context, store_batch_context
from src.backend.audio import is_transcription_configured, transcribe_audio
from src.backend.azure_rag import get_document_count, retrieve_relevant_chunks
from src.ai.azure_client import is_azure_configured, create_chat_completion

app = FastAPI(title="NOVA API", version="2.0")
logger = logging.getLogger(__name__)

MAX_BATCH_BYTES = 10 * 1024 * 1024
MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024

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


async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {max_bytes // (1024 * 1024)} MB limit.",
        )
    return content

def get_mongo_history(session_id: str):
    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if not mongo_uri:
        raise RuntimeError("MongoDB history is disabled because MONGO_URI is not configured.")

    options = {
        "serverSelectionTimeoutMS": "2000",
        "connectTimeoutMS": "2000",
        "socketTimeoutMS": "2000",
    }
    for key, value in options.items():
        if key.casefold() not in mongo_uri.casefold():
            separator = "&" if "?" in mongo_uri else "?"
            mongo_uri += f"{separator}{key}={value}"

    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=mongo_uri,
        database_name="nova_db", 
        collection_name="chat_histories"
    )

@app.get("/api/health")
def health_check():
    azure_ready = is_azure_configured()
    return {
        "status": "online",
        "modules": {
            "batch_validation": {"ready": True},
            "batch_enrichment": {
                "ready": azure_ready,
                "reason": None if azure_ready else "Azure OpenAI is not configured.",
            },
            "assistant": {
                "ready": azure_ready,
                "reason": None if azure_ready else "Azure OpenAI is not configured.",
            },
            "audio": {
                "ready": is_transcription_configured(),
                "reason": None if is_transcription_configured() else "A transcription deployment is required.",
            },
            "documents": {"ready": True, "index_type": "local_lexical_cosine"},
        },
    }

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        content = await read_upload_limited(file, MAX_BATCH_BYTES)
        filename = file.filename or ""
        source = io.StringIO(content.decode("utf-8-sig"))
        source.name = filename
        results = run_batch(source)
        store_batch_context(session_id, results)
        
        try:
            history = get_mongo_history(session_id)
            quality = results.get("data_quality", {})
            history.add_ai_message(
                "[Systeme] Validation terminee : "
                f"{quality.get('total_valid', 0)} lignes valides, "
                f"{quality.get('total_rejected', 0)} rejetees et "
                f"{quality.get('enrichment_succeeded', 0)} enrichies."
            )
        except Exception:
            logger.info("MongoDB history unavailable; batch result was not persisted.")
        
        return {"success": True, "data": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch API failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    try:
        if not is_azure_configured():
            return {"response": "Erreur : Azure OpenAI n'est pas configuré."}
        
        system_prompt = (
            "Vous etes NOVA, un assistant de qualite et d'analyse de donnees. "
            "Distinguez les donnees source des predictions de modele, mentionnez les "
            "tailles d'echantillon et les limites, et n'inventez jamais d'impact metier. "
            "Soyez clair, precis et concis en francais."
        )
        messages_for_azure = [{"role": "system", "content": system_prompt}]

        batch_context = format_batch_context(payload.session_id)
        if batch_context:
            messages_for_azure.append(
                {
                    "role": "system",
                    "content": (
                        "Verified context for the active feedback batch follows as JSON. "
                        "Use only these values for dataset-specific claims and cite batch "
                        "metrics or feedback IDs when possible:\n" + batch_context
                    ),
                }
            )

        retrieved_chunks = retrieve_relevant_chunks(payload.session_id, payload.message)
        if retrieved_chunks:
            messages_for_azure.append(
                {
                    "role": "system",
                    "content": (
                        "Relevant indexed document excerpts follow as JSON. Cite the "
                        "filename and chunk index for claims derived from them:\n"
                        + json.dumps(retrieved_chunks, ensure_ascii=False)
                    ),
                }
            )
        
        # FILET DE SÉCURITÉ MONGODB
        history = None
        try:
            history = get_mongo_history(payload.session_id)
            for msg in history.messages:
                role = "user" if msg.type == "human" else "assistant"
                messages_for_azure.append({"role": role, "content": msg.content})
        except Exception:
            logger.info("MongoDB history unavailable; chat is running without memory.")
            
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
        logger.exception("Chat API failed")
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
    except Exception:
        logger.info("MongoDB history unavailable; returning an empty history.")
        return {"success": True, "messages": []}

@app.post("/api/audio")
async def process_audio(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        suffix = os.path.splitext(file.filename or ".wav")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await read_upload_limited(file, MAX_AUDIO_BYTES)
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = transcribe_audio(tmp_path)
            
            try:
                history = get_mongo_history(session_id)
                history.add_ai_message(f"[Système] J'ai analysé l'interaction vocale ({file.filename}).")
            except:
                pass
            
            return {"success": True, **result, "filename": file.filename}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag")
async def process_rag(file: UploadFile = File(...), session_id: str = Form("executive_dashboard_session")):
    try:
        from src.backend.azure_rag import process_and_vectorize
        
        suffix = os.path.splitext(file.filename or ".pdf")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await read_upload_limited(file, MAX_DOCUMENT_BYTES)
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = process_and_vectorize(
                tmp_path, file.filename or "doc", session_id=session_id
            )
            
            if result["status"] == "indexed":
                try:
                    history = get_mongo_history(session_id)
                    history.add_ai_message(f"[Système] J'ai assimilé les données du document ({file.filename}).")
                except:
                    pass
                
            return {
                "success": True,
                **result,
                "documents_in_session": get_document_count(session_id),
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Document indexing failed")
        raise HTTPException(status_code=500, detail=str(e))
