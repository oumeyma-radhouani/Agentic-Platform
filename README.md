# NOVA Feedback Data Platform

NOVA validates customer-feedback datasets, calculates deterministic NPS metrics,
adds schema-controlled AI predictions, transcribes calls through Azure OpenAI,
indexes PDF/DOCX/TXT documents, and grounds the assistant in the active batch and
document context. Source data and model predictions remain separate.

## Feedback schema v1

Each JSON or JSONL record must contain these six fields:

```json
{
  "feedback_id": "FBK-TEST-001",
  "customer_id": "CUST-1001",
  "source": "Web",
  "score": 10,
  "comment": "Excellent service. The support agent solved my issue in less than five minutes.",
  "language": "EN"
}
```

`score` must be an integer from 0 through 10. `language` is normalized to an
uppercase language or locale code such as `EN` or `EN-US`. Extra input fields
are reported in the quality report but are not copied into the canonical table.

## Setup

From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Copy-Item .env.example .env
Set-Location .\frontend
npm.cmd ci
```

Set the Azure OpenAI values in `.env`, especially `AZURE_OPENAI_API_KEY`.
To use audio transcription, also configure a compatible deployment:

```dotenv
AZURE_OPENAI_TRANSCRIPTION_DEPLOYMENT="your-transcription-deployment"
```

To embed the Power BI tab, create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_POWER_BI_EMBED_URL="https://app.powerbi.com/reportEmbed?..."
```

## Run

Start the backend from one PowerShell window:

```powershell
Set-Location .\backend
& ..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Start the frontend from another:

```powershell
Set-Location .\frontend
npm.cmd run dev
```

Open <http://localhost:3000>. A ready-to-upload example is available in
`test_payload.json`.

## Batch response

The `/api/batch` response includes:

- `normalized_records`: validated source-owned fields only.
- `enriched_records`: canonical fields plus explicitly prefixed predictions.
- `review_queue`: predictions requiring human inspection, with review reasons and provenance.
- `rejected_records`: schema-invalid rows and their validation errors.
- `data_quality`: missing fields, rejected rows, duplicates, distributions, and warnings.
- `evidence_insights`: descriptive findings with denominators, record IDs, and caveats.
- `dataset_manifest`: versioned JSON schema and field definitions.
- `errors`: validation and enrichment failures, each tagged with its processing stage.

Review-required predictions are retained for data-scientist inspection but are
excluded from theme aggregation and analytical findings. Common emails, phone
numbers, payment-card patterns, and IP addresses are masked before comments are
sent to the enrichment model; the canonical record retains the original text.

## Other modules

- **Assistant Data:** receives a bounded verified summary of the active batch and
  retrieves relevant indexed document chunks for grounded answers.
- **Documents:** extracts `.txt`, `.pdf`, and `.docx`, chunks the text, and builds a
  transparent in-memory lexical cosine index. The index lasts for the backend process.
- **Audio:** sends the uploaded recording to the separately configured Azure
  transcription deployment and returns provider/deployment provenance.
- **Power BI:** remains visible and reports configuration requirements until a real
  embed URL is supplied; it does not load a placeholder report.

The in-memory batch and document contexts are appropriate for the group-project
prototype. A multi-worker or production deployment should move them to shared
durable storage.

Upload limits are 10 MB for feedback batches, 20 MB for documents, and 25 MB
for audio. The browser cache retains only compact batch summaries; download the
full batch JSON during the active run when row-level artifacts are required.

## Tests

```powershell
Set-Location .\backend
& ..\.venv\Scripts\python.exe -m unittest discover -s ..\tests -v
```
