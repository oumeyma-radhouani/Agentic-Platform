import streamlit as st
import time
import requests
import datetime
import json
from src.backend.aggregator import parse_agent_response

# --- REAL LOCAL SYSTEM CHECKS ---
def check_ollama_status():
    try:
        response = requests.get("http://localhost:11434/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_installed_models():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        return []
    except requests.exceptions.RequestException:
        return []

# --- MOCK BACKEND (Waiting for Said's LangChain integration) ---
def mock_langchain_response(user_prompt, model, temp):
    time.sleep(1.2)  
    # Simulating the LangChain agent returning structured JSON
    mock_data = {
        "status": "AGENT_READY",
        "routed_model": model,
        "temperature": temp,
        "task_parsed": user_prompt,
        "next_action": "Awaiting execution parameters."
    }
    return json.dumps(mock_data)

# --- ADVANCED UI CONFIGURATION ---
st.set_page_config(page_title="NOVA Terminal", page_icon="🌌", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #58a6ff;
    }

    /* Target Headers */
    h1, h2, h3, h4, h5 {
        color: #f0f6fc;
        font-weight: 700;
    }

    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        color: #58a6ff;
        font-weight: 800;
        font-size: 2.2rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8b949e;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }

    /* Custom Styling for Containers and Cards */
    div.stContainer {
        border: 1px solid #30363d;
        border-radius: 12px;
        background-color: #161b22;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Styling the Chat Input Area */
    .stChatInputContainer {
        border-top: 1px solid #30363d;
        background-color: #0d1117;
    }
    
    /* Hide the Streamlit footer and main menu */
    #MainMenu, footer {visibility: hidden;}

    /* Custom Class for Header Bar */
    .nova-header {
        background-color: #161b22;
        padding: 10px 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }

</style>
""", unsafe_allow_html=True)

# Fetch real system data before rendering
is_ollama_online = check_ollama_status()
available_models = get_installed_models()
current_time = datetime.datetime.now().strftime("%H:%M:%S")
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# --- SIDEBAR: AGENT CONFIGURATION PANEL ---
with st.sidebar:
    st.header("⚙️ Agentic Node Setup")
    
    st.divider()

    # REAL PARAMETER: Model Dropdown 
    if available_models:
        selected_model = st.selectbox("Active Inference Model", available_models)
    else:
        st.warning("No models detected. Pulled model is required via Ollama.")
        selected_model = None
    
    # REAL PARAMETER: Generation Control
    temperature = st.slider("Generation Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    st.divider()
    
    st.caption(f"📅 Node Date: {current_date}")
    st.caption(f"🌐 Platform: NOVA v0.1.0-alpha")
    st.caption("Deployment: `nova-local-dev`")

# --- MAIN DASHBOARD: COMMAND CENTER ---

# 1. Custom Header Bar
st.markdown(f"""
<div class="nova-header">
    <div style="display:flex; align-items:center;">
        <span style="font-size:2rem; margin-right:15px;">📡</span>
        <div>
            <h1 style="margin:0; font-size:1.8rem; color:#f0f6fc;">NOVA TERMINAL</h1>
            <p style="margin:0; color:#8b949e; font-size:0.9rem;">PLATFORM OPERATIONAL LOCALHOST:11434</p>
        </div>
    </div>
    <div style="text-align:right;">
        <span style="font-family:'Courier New', monospace; color:#58a6ff; font-size:1.1rem; font-weight:bold;">{current_time} Zulu</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Row 1: Status Grid (Real Telemetry Cards)
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    with st.container(border=True):
        if is_ollama_online:
            st.metric(label="System Backend", value="Online", delta="Connected", delta_color="normal")
        else:
            st.metric(label="System Backend", value="Offline", delta="Disconnected", delta_color="inverse")

with status_col2:
    with st.container(border=True):
        model_count = len(available_models)
        st.metric(label="Model Registry", value=f"{model_count} Models", delta="Idle", delta_color="off")

with status_col3:
    with st.container(border=True):
        st.metric(label="Telemetry Status", value="Nominal", delta="No Alert", delta_color="off")

st.divider()

# 3. Row 2: Console Interface (Primary Chat)
st.subheader("Console Input/Output Logs")
st.markdown("Monitor system interactions and initialize agentic tasks below.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Styled chat history render
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Only allow input if the server is actually running and has a model
if is_ollama_online and selected_model:
    if prompt := st.chat_input("Initialize agent task... [Ctrl+Enter]"):
        
        # 1. Display user prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner(f"NOVA Operating..."):
                # Get the raw JSON string from the mock backend
                raw_response = mock_langchain_response(prompt, selected_model, temperature)
                
                # Pass it through our aggregator to format it cleanly!
                formatted_response = parse_agent_response(raw_response)
                
                st.markdown(formatted_response)
                
        # 3. Save the *formatted* response to state
        st.session_state.messages.append({"role": "assistant", "content": formatted_response})
else:
    st.info("System Console is currently locked. Ensure the local Ollama server is running and at least one model is installed to initialize agentic tasks.")