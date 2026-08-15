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

Authentication requires MongoDB. Add your local MongoDB or free MongoDB Atlas
connection string to `.env` (never commit the real value):

```dotenv
MONGO_URI="mongodb+srv://username:password@cluster.example.mongodb.net/?retryWrites=true&w=majority"
MONGO_DATABASE="nova_db"
NOVA_SESSION_HOURS="12"
NOVA_SESSION_COOKIE_SECURE="false"
```

URL-encode special characters in the MongoDB username or password. Then create
the first account from the project directory; the password is requested securely
and does not appear in shell history:

```powershell
Set-Location .\backend
& ..\.venv\Scripts\python.exe .\create_user.py --username admin --display-name "NOVA Admin" --role admin
Set-Location ..
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

## Authentication

NOVA has no public sign-up route. Administrators create accounts with
`backend/create_user.py`. Passwords are salted and hashed with scrypt; MongoDB
stores only password hashes and SHA-256 hashes of random session tokens. The raw
session token is kept in an `HttpOnly`, `SameSite=Lax` browser cookie, expires by
default after 12 hours, and is deleted from MongoDB on logout. Repeated failed
logins are temporarily rate-limited.

All batch, chat, audio, and document endpoints require login. Their server-side
scope is derived from the authenticated user, so a browser cannot select another
user's scope by changing a request field. MongoDB TTL indexes automatically remove
expired sessions and old login-attempt records. For HTTPS deployment, set
`NOVA_SESSION_COOKIE_SECURE="true"`.

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

## Local prompt-injection protection

NOVA uses a free deterministic detector (`local-rules-v1`) before untrusted text
reaches the model. It normalizes Unicode, removes zero-width characters, folds a
small set of common cross-script lookalikes, detects suspicious encoded blocks,
and scores instruction override, prompt extraction, role impersonation, and data
exfiltration patterns in English and French.

- Flagged feedback remains in `normalized_records`, is not sent for enrichment,
  and is added to `review_queue` with a payload-safe security assessment.
- Flagged documents are rejected before indexing.
- Flagged chat requests are blocked before an Azure model call or history write.
- Retrieved chunks are checked again before being added as reference data.
- Batch metrics and document excerpts are passed as untrusted user reference data,
  never as system instructions. Raw comments are excluded from assistant context.

This detector is a transparent first layer, not proof that prompt injection is
impossible. Its decisions and reason codes should be reviewed for false positives,
and model permissions must remain restricted independently of the detector.

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

## Logging

The backend logs request lifecycles and the batch, chat, audio, and document
workflows with status, counts, identifiers, and processing times. It does not log
feedback comments, prompts, transcripts, document text, API keys, or database
connection strings. Session IDs are replaced with stable one-way references.

Configure verbosity and output format in `.env`:

```dotenv
NOVA_LOG_LEVEL="INFO"
NOVA_LOG_FORMAT="text"
```

Use `NOVA_LOG_FORMAT="json"` for one structured JSON object per line, which is
easier to ingest into a centralized logging platform. Every HTTP response also
includes an `X-Request-ID` header for correlation.

## Tests

Run the complete local verification suite from the project directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test_project.ps1
```

This runs backend unit/API tests, frontend linting, a production frontend build,
and Git whitespace validation. The process-scoped execution-policy bypass does not
change the system policy. To omit the production build during a quick check, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test_project.ps1 -SkipFrontendBuild
```

To run only the backend tests:

```powershell
Set-Location .\backend
& ..\.venv\Scripts\python.exe -m unittest discover -s ..\tests -v
```
