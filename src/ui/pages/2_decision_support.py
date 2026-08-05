import streamlit as st

st.markdown("<h1>Decision Support <span style='color:#a371f7; font-size:1.2rem;'>// AI RECOMMENDATIONS</span></h1>", unsafe_allow_html=True)
st.markdown(f"Current Agent Autonomy: **{st.session_state.autonomy_level}**")
st.divider()

# In a real scenario, this data comes from upgrading your Prompt Engineering in batch_runner.py
# For now, we scaffold the UI to show your supervisor the target UX.

st.markdown("""
<div class="agent-card">
    <h3 style="margin-top:0;">⚡ Proactive Campaign: Server Outage Apology</h3>
    <p><strong>Proposed Action:</strong> Draft and send a targeted email campaign offering a 15% discount code to users affected by the V2.1 server outage.</p>
    
    <div class="agent-rationale">
        <strong>🧠 Agent Rationale:</strong> Analysis of the latest batch data indicates a 25% Detractor rate specifically citing 'slow loading times' and 'system crashes'. Cross-referencing CRM data shows these occurred during the V2.1 deployment window.
    </div>
</div>
""", unsafe_allow_html=True)

# Intent Preview Buttons
col1, col2, col3, _ = st.columns([1, 1, 1, 3])
with col1:
    if st.button("✅ Approve & Execute", key="exec_1"):
        st.success("Action queued for execution.")
with col2:
    st.button("✏️ Edit Strategy", key="edit_1")
with col3:
    st.button("❌ Dismiss", key="dismiss_1")

st.write("") # Spacer

st.markdown("""
<div class="agent-card">
    <h3 style="margin-top:0;">⚡ Route Tickets: Billing Department</h3>
    <p><strong>Proposed Action:</strong> Automatically escalate 14 pending tickets to the Tier 2 Billing dispute team.</p>
    
    <div class="agent-rationale">
        <strong>🧠 Agent Rationale:</strong> Natural Language extraction identified the phrase "charged twice" in multiple severe detractor comments (e.g., TKT-1005, TKT-1012).
    </div>
</div>
""", unsafe_allow_html=True)

col4, col5, col6, _ = st.columns([1, 1, 1, 3])
with col4:
    if st.session_state.autonomy_level == "Level 3: Act":
        st.button("✅ Auto-Executed by Agent", disabled=True)
    else:
        st.button("✅ Approve & Execute", key="exec_2")
with col5:
    st.button("✏️ Edit Strategy", key="edit_2")