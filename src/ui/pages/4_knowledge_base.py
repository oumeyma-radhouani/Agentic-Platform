import streamlit as st
import time
from src.backend.azure_rag import process_and_vectorize

st.markdown("<h1>Knowledge Base <span style='color:#a371f7; font-size:1.2rem;'>// RAG VECTOR STORE</span></h1>", unsafe_allow_html=True)
st.markdown("Upload standard operating procedures, manuals, or policy documents for the Agent to reference during Decision Support.")
st.divider()

col_upload, col_index = st.columns([1, 1])

with col_upload:
    st.markdown("""
    <div class="stContainer">
        <h3 style="margin-top:0;">Secure Document Ingestion</h3>
        <p style="color:#8b949e; font-size:0.9rem;">Supported formats: PDF, TXT, MD.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_doc = st.file_uploader("", type=["txt", "pdf", "md"], label_visibility="collapsed")
    
    if uploaded_doc is not None:
        st.info(f"📄 **Ready to process:** `{uploaded_doc.name}`")
        
        if st.button("Chunk & Vectorize Document", type="primary", use_container_width=True):
            
            # Simulated Agentic Step: Meta-data extraction
            st.markdown("""
            <div class="agent-rationale" style="border-left: 3px solid #a371f7;">
                <strong>🧠 Agent Pre-check:</strong> Scanning document structure... <br/>
                <em>Detected standard operating procedure formatting. Extracting technical entities...</em>
            </div>
            """, unsafe_allow_html=True)
            
            my_bar = st.progress(0, text="Connecting to Azure AI Search...")
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text="Chunking and Vectorizing...")
            
            # Save temporary file for the backend function
            temp_doc_path = f"temp_{uploaded_doc.name}"
            with open(temp_doc_path, "wb") as f:
                f.write(uploaded_doc.getbuffer())
                
            try:
                success = process_and_vectorize(temp_doc_path, uploaded_doc.name)
                if success:
                    st.success(f"Document `{uploaded_doc.name}` successfully indexed in Azure Vector Store!")
                    
                    # Update a session state list to show indexed files
                    if "indexed_docs" not in st.session_state:
                        st.session_state.indexed_docs = []
                    st.session_state.indexed_docs.append(uploaded_doc.name)
                    
            except Exception as e:
                st.error(f"Vectorization failed: {e}")

with col_index:
    st.markdown("### Active Vector Index")
    if "indexed_docs" in st.session_state and st.session_state.indexed_docs:
        for doc in set(st.session_state.indexed_docs):
            st.markdown(f"""
            <div style="background-color:#161b22; padding:10px 15px; border-radius:6px; border:1px solid #30363d; margin-bottom:8px; display:flex; justify-content:space-between;">
                <span>📚 {doc}</span>
                <span style="color:#2ea043; font-weight:bold;">ACTIVE</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:20px; text-align:center; border:1px dashed #30363d; border-radius:8px; color:#8b949e;">
            No documents currently indexed in this session.
        </div>
        """, unsafe_allow_html=True)