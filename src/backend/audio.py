import whisper
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def transcribe_audio(file_path: str) -> str:
    """
    Loads a local Whisper model to transcribe audio files into text.
    """
    logging.info(f"Loading Whisper model to transcribe {file_path}...")
    try:
        # Using 'base' model for speed. 
        model = whisper.load_model("base") 
        result = model.transcribe(file_path)
        
        logging.info("Transcription successful.")
        return result["text"]
        
    except Exception as e:
        logging.error(f"Speech-to-Text engine failed: {e}")
        raise RuntimeError(f"Could not transcribe audio: {e}")