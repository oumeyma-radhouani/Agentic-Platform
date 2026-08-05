import streamlit as st
import datetime
from backend.src.ai.azure_client import get_deployment_name, is_azure_configured
from backend.src.ui.styles import inject_enterprise_css
from pathlib import Path

# --- ADVANCED UI CONFIGURATION ---
st.set_page_config(page_title="NOVA Enterprise", page_icon="🌌", layout="wide", initial_sidebar_state="expanded")
inject_enterprise_css()

# --- INITIALIZE SESSION STATE ---
if "autonomy_level" not in st.session_state:
    st.session_state.autonomy_level = "Level 1: Suggest"

# --- SIDEBAR: GLOBAL AGENT CONTROL ---
with st.sidebar:
    st.header("⚙️ Agentic Control Plane")
    st.divider()
    
    st.markdown("### The Autonomy Dial")
    st.session_state.autonomy_level = st.select_slider(
        "Agent Authority Level",
        options=["Level 1: Suggest", "Level 2: Notify", "Level 3: Act"],
        value=st.session_state.autonomy_level,
        help="Determines if the AI requires human approval before executing actions."
    )
    
    st.divider()
    st.text_input("Azure Deployment", value=get_deployment_name(), disabled=True)
    if not is_azure_configured():
        st.error("Azure OpenAI Key Missing (.env)")
    
    st.caption(f"NOVA v2.0-agentic | {datetime.datetime.now().strftime('%Y-%m-%d')}")

# --- PAGE ROUTING ---
# Dynamically get the absolute path to the folder containing app.py
current_dir = Path(__file__).parent

# Use absolute paths so Streamlit never gets confused
dashboard = st.Page(str(current_dir / "pages" / "1_dashboard.py"), title="Executive Command", icon="📊", default=True)
decision = st.Page(str(current_dir / "pages" / "2_decision_support.py"), title="Decision Support", icon="🧠")
audio = st.Page(str(current_dir / "pages" / "3_audio_hub.py"), title="Interaction Deep-Dive", icon="🎙️")
rag = st.Page(str(current_dir / "pages" / "4_knowledge_base.py"), title="Knowledge Base", icon="📚")

pg = st.navigation([dashboard, decision, audio, rag])
pg.run()