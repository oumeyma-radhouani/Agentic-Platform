import streamlit as st
import time
import requests
import datetime
import json
from src.backend.aggregator import parse_agent_response

# --- IMPORT SAID'S BACKEND FUNCTION ---
# Wrapping in a try/except just in case the branch hasn't synced properly yet
try:
    from src.backend.batch_runner import run_batch
except ImportError:
    st.error("Backend Error: Could not import run_batch from src.backend.batch_runner. Ensure you are on the correct branch.")
    def run_batch(data): return {} # Dummy fallback

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

# --- MOCK BACKEND (For Live Console) ---
def mock_langchain_response(user_prompt, model, temp):
    time.sleep(1.2)  
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
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] .stMarkdown h1, section[data-testid="stSidebar"] .stMarkdown h2 { color: #58a6ff; }
    h1, h2, h3, h4, h5 { color: #f0f6fc; font-weight: 700; }
    [data-testid="stMetricValue"] { color: #58a6ff; font-weight: 800; font-size: 2.2rem; }
    [data-testid="stMetricLabel"] { color: #8b949e; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
    [data-testid="stMetricDelta"] { font-size: 0.9rem; }
    div.stContainer { border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stChatInputContainer { border-top: 1px solid #30363d; background-color: #0d1117; }
    #MainMenu, footer {visibility: hidden;}
    .nova-header { background-color: #161b22; padding: 10px 20px; border-radius: 12px; border: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #1f2428; border-bottom: 2px solid #58a6ff; color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)

is_ollama_online = check_ollama_status()
available_models = get_installed_models()
current_time = datetime.datetime.now().strftime("%H:%M:%S")
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# --- SIDEBAR: AGENT CONFIGURATION PANEL ---
with st.sidebar:
    st.header("⚙️ Agentic Node Setup")
    st.divider()

    if available_models:
        selected_model = st.selectbox("Active Inference Model", available_models)
    else:
        st.warning("No models detected. Pulled model is required via Ollama.")
        selected_model = None
    
    temperature = st.slider("Generation Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    st.divider()
    st.caption(f"📅 Node Date: {current_date}")
    st.caption(f"🌐 Platform: NOVA v0.2.0-beta")
    st.caption("Deployment: `nova-local-dev`")

# --- MAIN DASHBOARD: COMMAND CENTER ---
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

status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    with st.container(border=True):
        if is_ollama_online:
            st.metric(label="System Backend", value="Online", delta="Connected", delta_color="normal")
        else:
            st.metric(label="System Backend", value="Offline", delta="Disconnected", delta_color="inverse")
with status_col2:
    with st.container(border=True):
        st.metric(label="Model Registry", value=f"{len(available_models)} Models", delta="Idle", delta_color="off")
with status_col3:
    with st.container(border=True):
        st.metric(label="Telemetry Status", value="Nominal", delta="No Alert", delta_color="off")

st.divider()

# --- TABS FOR UI SEPARATION ---
tab_console, tab_batch = st.tabs(["💬 Live Console", "🗃️ Batch Analysis Pipeline"])

# --- TAB 1: ORIGINAL CHAT INTERFACE ---
with tab_console:
    st.subheader("Console Input/Output Logs")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if is_ollama_online and selected_model:
        if prompt := st.chat_input("Initialize agent task... [Ctrl+Enter]"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(f"NOVA Operating..."):
                    raw_response = mock_langchain_response(prompt, selected_model, temperature)
                    formatted_response = parse_agent_response(raw_response)
                    st.markdown(formatted_response)
            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
    else:
        st.info("System Console is locked. Ensure local Ollama is running.")

# --- TAB 2: NEW BATCH ANALYSIS PIPELINE ---
with tab_batch:
    st.subheader("Batch Data Processing")
    st.markdown("Upload structured JSON/JSONL payloads for high-volume automated agentic analysis.")
    
    # 1. File Uploader
    uploaded_file = st.file_uploader("Select Dataset", type=["json", "jsonl"])
    
    if uploaded_file is not None:
        try:
            # Parse the uploaded file to pass clean Python objects to Said's backend
            if uploaded_file.name.endswith(".jsonl"):
                batch_data = [json.loads(line) for line in uploaded_file]
            else:
                batch_data = json.load(uploaded_file)
                
            st.success(f"Loaded {len(batch_data) if isinstance(batch_data, list) else 1} records from `{uploaded_file.name}`.")
            
            # 2. Run Batch Button
            if st.button("🚀 Initialize Batch Run", type="primary", use_container_width=True):
                if not is_ollama_online:
                    st.error("Cannot run batch: Ollama is offline.")
                else:
                    # 3. Progress Bar Integration
                    progress_text = "Transmitting payload to local inference engine..."
                    my_bar = st.progress(0, text=progress_text)
                    
                    # Simulating progress before the blocking backend call
                    for percent_complete in range(100):
                        time.sleep(0.01)
                        my_bar.progress(percent_complete + 1, text="Executing batch pipeline via src/backend/batch_runner.py...")
                    
                    with st.spinner("Awaiting backend processing..."):
                        # --- CALLING SAID'S BACKEND FUNCTION ---
                        try:
                            # Assuming run_batch takes the parsed data and the selected model
                            batch_results = run_batch(batch_data) 
                            
                            st.success("Batch pipeline executed successfully!")
                            
                            # 4. Summary Cards (using summary_metrics)
                            if "summary_metrics" in batch_results:
                                st.markdown("### Executive Summary")
                                metric_cols = st.columns(len(batch_results["summary_metrics"]))
                                for i, (key, value) in enumerate(batch_results["summary_metrics"].items()):
                                    metric_cols[i].metric(label=str(key).replace("_", " ").title(), value=value)
                            
                            st.divider()
                            
                            # 5. Top Themes (Chart/Table)
                            if "top_themes" in batch_results and batch_results["top_themes"]:
                                st.markdown("### Top Extracted Themes")
                                # Streamlit renders dicts natively as bar charts if formatted correctly
                                st.bar_chart(batch_results["top_themes"])
                            
                            # 6. Processed Records Table
                            if "processed_records" in batch_results:
                                st.markdown("### Processed Records")
                                st.dataframe(batch_results["processed_records"], use_container_width=True)
                                
                            # 7. Errors Table
                            if "errors" in batch_results and batch_results["errors"]:
                                st.markdown("### ⚠️ Pipeline Exceptions")
                                st.dataframe(batch_results["errors"], use_container_width=True)

                            # 8. Download Button
                            st.divider()
                            st.download_button(
                                label="📥 Download Complete Telemetry (JSON)",
                                data=json.dumps(batch_results, indent=4),
                                file_name=f"NOVA_BatchResult_{current_date}.json",
                                mime="application/json",
                                type="primary"
                            )
                            
                        except Exception as e:
                            st.error(f"Backend execution failed: {e}")
                            
        except Exception as e:
            st.error(f"Failed to parse uploaded file. Ensure it is valid JSON/JSONL. Error: {e}")