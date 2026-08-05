"""Generate synthetic customer-feedback records with Azure OpenAI."""

from __future__ import annotations

import json
from pathlib import Path

from backend.src.ai.azure_client import create_chat_completion, get_deployment_name


def _generate_batch(count: int) -> list[dict]:
    content = create_chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "You generate realistic structured customer-service test data. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""Generate exactly {count} feedback records under a top-level `records` key.
Each record must contain feedback_id, customer_id, source, score, comment, and language.
Use Web, App, or Email for source. Scores must be integers from 0 through 10.
Use French for half of the comments and English for half. Include positive, neutral,
negative, mixed, sarcastic, multi-topic, and vague feedback.""",
            },
        ],
        temperature=0.8,
        max_completion_tokens=4096,
        response_format={"type": "json_object"},
    )
    payload = json.loads(content)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Azure OpenAI did not return a JSON `records` list.")
    return records


def generate_golden_dataset(total_records: int = 200, batch_size: int = 20) -> None:
    """Generate records in bounded batches and save them to the data directory."""
    all_records: list[dict] = []
    print(f"Generating {total_records} records with {get_deployment_name()}...")

    for batch_number, start in enumerate(range(0, total_records, batch_size), start=1):
        requested = min(batch_size, total_records - start)
        print(f"Generating batch {batch_number}...")
        try:
            all_records.extend(_generate_batch(requested))
        except Exception as exc:
            print(f"Error generating batch {batch_number}: {exc}")

    output_path = Path(__file__).resolve().parents[2] / "data" / "golden_dataset.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(all_records, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(all_records)} records to {output_path}")


if __name__ == "__main__":
    generate_golden_dataset(total_records=200, batch_size=20)
