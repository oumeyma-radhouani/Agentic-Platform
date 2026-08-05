from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json

# Import your existing AI logic!
from src.backend.batch_runner import run_batch
from src.ai.azure_client import is_azure_configured

app = FastAPI(title="NOVA Agentic API", version="2.0")

# CRITICAL: This allows your Next.js frontend (Port 3000) to talk to this backend (Port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """Check if the backend and Azure are online."""
    return {
        "status": "online", 
        "azure_ready": is_azure_configured()
    }

@app.post("/api/batch")
async def process_batch(file: UploadFile = File(...)):
    """Receives a JSONL file from React, runs the LangChain/Azure logic, and returns insights."""
    try:
        content = await file.read()
        
        # Handle JSONL vs JSON
        if file.filename.endswith('.jsonl'):
            lines = content.decode('utf-8').splitlines()
            batch_data = [json.loads(line) for line in lines if line.strip()]
        else:
            batch_data = json.loads(content.decode('utf-8'))
            
        # Execute your existing backend logic
        results = run_batch(batch_data)
        
        return {"success": True, "data": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))