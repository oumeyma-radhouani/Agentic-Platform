import streamlit as st
import os
from backend.src.backend.audio import transcribe_audio
from backend.src.ai.azure_client import create_chat_completion, is_azure_configured

# Optional: Import LangChain's Mongo handler if you have it installed
try:
    from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

st.markdown("<h1>Interaction Deep-Dive <span style='color:#a371f7; font-size:1.2rem;'>// AUDIO & CHAT HUB</span></h1>", unsafe_allow_html=True)
st.divider()

# --- INITIALIZE MONGODB MEMORY ---
# In a real app, 'session_id' would be tied to the logged-in user.
session_id = "agentic_session_001"
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if MONGO_AVAILABLE and os.getenv("MONGO_URI"):
    # Connect to MongoDB
    db_history = MongoDBChatMessageHistory(
        connection_string=mongo_uri,
        session_id=session_id,
        database_name="nova_db",
        collection_name="chat_histories"
    )
    # Load past messages from Mongo into Streamlit state
    if not st.session_state.chat_history:
        st.session_state.chat_history = [{"role": msg.type, "content": msg.content} for msg in db_history.messages]

# --- SPLIT SCREEN UI ---
col_audio, col_chat = st.columns([1, 1.2], gap="large")

with col_audio:
    st.markdown("### 🎙️ Audio Processing Pipeline")
    audio_file = st.file_uploader("Upload Call Recording", type=["wav", "mp3", "m4a"])
    
    if audio_file is not None:
        st.audio(audio_file)
        if st.button("Transcribe via Whisper", type="primary", use_container_width=True):
            with st.spinner("Whisper model running locally..."):
                temp_audio_path = "temp_audio_upload.wav"
                with open(temp_audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())
                
                try:
                    transcript = transcribe_audio(temp_audio_path)
                    st.session_state.current_transcript = transcript
                    st.success("Transcription Complete!")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

    # Display Transcript if it exists in session
    if "current_transcript" in st.session_state:
        st.markdown("""
        <div style="background-color:#161b22; padding:15px; border-radius:8px; border-left:4px solid #58a6ff; max-height:400px; overflow-y:auto;">
            <p style="color:#8b949e; font-size:0.85rem; text-transform:uppercase;">Raw Transcript</p>
            <p style="color:#c9d1d9; line-height:1.6;">{}</p>
        </div>
        """.format(st.session_state.current_transcript), unsafe_allow_html=True)
        
        if st.button("Load Transcript into Agent Memory"):
            system_msg = f"CONTEXT LOADED: The user is currently looking at this transcript: '{st.session_state.current_transcript}'"
            st.session_state.chat_history.append({"role": "system", "content": system_msg})
            if MONGO_AVAILABLE:
                db_history.add_user_message(system_msg) # Saving context silently
            st.toast("Transcript loaded into Agent context.")

with col_chat:
    st.markdown("### 💬 Conversational Agent")
    
    # Chat Container
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.chat_history:
            # Hide system messages from the UI to keep it clean
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Chat Input
    if is_azure_configured():
        prompt = st.chat_input("Ask NOVA to analyze the transcript or query the data...")
        if prompt:
            # 1. Show user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # 2. Save to Mongo
            if MONGO_AVAILABLE:
                db_history.add_user_message(prompt)

            # 3. Call Azure (Passing the full history for memory)
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("NOVA Operating..."):
                        try:
                            # Use create_chat_completion to pass the whole array, not just the string
                            response_content = create_chat_completion(
                                messages=st.session_state.chat_history,
                                temperature=0.7
                            )
                            st.markdown(response_content)
                            
                            # 4. Save response
                            st.session_state.chat_history.append({"role": "assistant", "content": response_content})
                            if MONGO_AVAILABLE:
                                db_history.add_ai_message(response_content)
                                
                        except Exception as exc:
                            st.error(f"Azure OpenAI request failed: {exc}")
    else:
        st.warning("Agent disconnected. Azure API key missing.")