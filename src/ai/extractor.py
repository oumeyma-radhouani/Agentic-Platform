import json
from langchain_ollama import ChatOllama

def classify_nps(score: int) -> str:
    """NPS rules defined in the specs."""
    if not 0 <= score <= 10:
        raise ValueError("The score must be between 0 and 10.")
    if score >= 9:
        return "promoteur"
    if score >= 7:
        return "neutre"
    return "détracteur"

def analyze_feedback(client_id: str, score: int, comment: str) -> dict:
    """Runs the Ollama model on the client data."""
    # Using the local model Saïd tested
    llm = ChatOllama(model="qwen3:1.7b", temperature=0, format="json") 
    
    prompt = f"""
    Analyze this customer feedback. Return only valid JSON with these keys:
    sentiment, main_cause, theme, summary.
    Do not invent details.

    Score: {score}/10
    Comment: {comment}
    """
    
    response = llm.invoke(prompt)
    
    result = {
        "customer_id": client_id,
        "score": score,
        "nps_category": classify_nps(score),
        "ai_analysis": json.loads(response.content),
    }
    return result