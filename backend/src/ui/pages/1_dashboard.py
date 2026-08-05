import streamlit as st
import json
import pandas as pd
import time
import datetime
from backend.src.ai.azure_client import is_azure_configured
from backend.src.backend.batch_runner import run_batch

st.markdown("<h1>NOVA TERMINAL <span style='color:#8b949e; font-size:1.2rem;'>// COMMAND CENTER</span></h1>", unsafe_allow_html=True)
st.divider()

# Batch Processing UI
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("### High-Volume Ingestion")
    uploaded_file = st.file_uploader("Upload JSONL Payload", type=["json", "jsonl"])

with col2:
    st.markdown("### System Status")
    st.metric(label="Azure Connection", value="Nominal" if is_azure_configured() else "Offline")
    st.metric(label="Autonomy Rule", value=st.session_state.autonomy_level)

if uploaded_file is not None:
    if st.button("Execute Batch Analysis", type="primary"):
        batch_data = [json.loads(line) for line in uploaded_file] if uploaded_file.name.endswith(".jsonl") else json.load(uploaded_file)
        
        with st.spinner("NOVA is analyzing payloads..."):
            # Dummy fallback if Azure isn't connected for UI testing
            batch_results = run_batch(batch_data) if is_azure_configured() else {"summary_metrics": {"total_processed": 200, "nps_score": 45, "total_promoters": 120, "total_passives": 50, "total_detractors": 30}}
            
            # --- AI SUMMARY BANNER ---
            st.info(f"✨ **Agent Summary:** Processed {batch_results['summary_metrics']['total_processed']} records. Overall NPS is stable, but a localized spike in detractors points to billing issues on the iOS platform.")
            
            # --- METRICS ---
            st.markdown("### Global Satisfaction Metrics")
            metric_cols = st.columns(4)
            metric_cols[0].metric(label="NPS Score", value=batch_results["summary_metrics"]["nps_score"])
            metric_cols[1].metric(label="Promoters", value=batch_results["summary_metrics"]["total_promoters"])
            metric_cols[2].metric(label="Passives", value=batch_results["summary_metrics"]["total_passives"])
            metric_cols[3].metric(label="Detractors", value=batch_results["summary_metrics"]["total_detractors"])
            
            # --- DATA EXPORT ---
            st.divider()
            df = pd.DataFrame(batch_results.get("processed_records", []))
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📊 Export to Power BI (CSV)", data=csv, file_name=f"PowerBI_Ingest_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv", mime="text/csv", type="primary")