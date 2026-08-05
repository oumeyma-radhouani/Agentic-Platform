import streamlit as st

def inject_enterprise_css():
    st.markdown("""
    <style>
        /* Global Theme */
        .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        
        /* Typography */
        h1, h2, h3, h4, h5 { color: #f0f6fc; font-weight: 700; }
        
        /* Premium Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #161b22; border: 1px solid #30363d; padding: 15px 20px;
            border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="metric-container"]:hover { transform: translateY(-2px); border-color: #58a6ff; }
        
        /* Agentic Recommendation Cards (NEW) */
        .agent-card {
            background-color: #1c2128; border-left: 4px solid #a371f7;
            padding: 20px; border-radius: 8px; margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        .agent-rationale {
            background-color: #22272e; padding: 12px; border-radius: 6px;
            font-size: 0.9rem; color: #8b949e; border: 1px dashed #444c56;
            margin-top: 10px; margin-bottom: 15px;
        }
        .ai-text-highlight { color: #a371f7; font-weight: 600; }
        
        /* Premium Buttons */
        .stButton>button { background-color: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; transition: all 0.3s ease; }
        .stButton>button:hover { border-color: #8b949e; background-color: #30363d; }
        .stButton>button[kind="primary"] { background-color: #238636; border-color: #238636; color: white; }
        .stButton>button[kind="primary"]:hover { background-color: #2ea043; border-color: #2ea043; }
    </style>
    """, unsafe_allow_html=True)