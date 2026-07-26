import streamlit as st
import json
import os
import sys

# Add the src folder to Python's path so we can import the AI engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai.extractor import analyze_feedback

# Load Mock Data
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'mock_data.json')
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

mock_db = load_data()

st.title("☁️ CloudShift: Chatbot Agentic AI (Mock-up)")
st.write("Tapez l'ID d'un client (ex: C001 ou C002) pour générer une analyse.")

if prompt := st.chat_input("Entrez l'ID du client..."):
    with st.chat_message("user"):
        st.write(prompt)
        
    with st.chat_message("assistant"):
        # Search for the client in the mock JSON
        client = next((item for item in mock_db if item["id"].upper() == prompt.upper()), None)
        
        if client:
            # Replaced st.write with a dynamic status container
            with st.status("Analyse en cours via Ollama...") as status:
                # Call Saïd's AI function
                analysis = analyze_feedback(client["id"], client["score"], client["comment"])
                
                # Display the result
                st.json(analysis)
                
                # Update the status to show it is finished!
                status.update(label="Analyse terminée!", state="complete", expanded=True)
        else:
            st.write("Client non trouvé dans le Mock SI.")