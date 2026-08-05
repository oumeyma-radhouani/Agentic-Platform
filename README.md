# NOVA Terminal (Agentic Platform)

NOVA is a Streamlit control plane for analyzing customer feedback with an Azure OpenAI deployment. It includes a live assistant console, batch JSON/JSONL processing, audio transcription, and a scaffolded Azure RAG workflow.

## Prerequisites

- Python 3.10 or newer
- An Azure OpenAI resource and API key
- The `gpt-4.1-mini` deployment, or another deployment configured in `.env`

## Setup

From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and replace `<your-api-key>` with the Azure OpenAI resource key. The default configuration is:

```dotenv
AZURE_OPENAI_ENDPOINT="https://novaso.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4.1-mini"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_API_KEY="<your-api-key>"
```

Do not commit `.env`; it is ignored by Git.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\ui\app.py
```

Open <http://localhost:8501> and press `Ctrl+C` in the terminal to stop the app.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
