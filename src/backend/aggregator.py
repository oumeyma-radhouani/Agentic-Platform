import json
import logging

# Set up basic logging so we can see errors in the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_agent_response(raw_response: str) -> str:
    """
    Takes the raw text/JSON output from Said's LangChain agents 
    and formats it cleanly for the Streamlit UI.
    """
    try:
        # First, try to parse it as a standard JSON dictionary
        # This handles cases where the agent outputs strict JSON
        parsed_data = json.loads(raw_response)
        
        # If it's a dictionary, let's format it beautifully into Markdown
        if isinstance(parsed_data, dict):
            formatted_output = "### Agent Task Report\n\n"
            for key, value in parsed_data.items():
                # Capitalize the key and make it bold
                clean_key = str(key).replace("_", " ").title()
                formatted_output += f"**{clean_key}:**\n{value}\n\n"
            return formatted_output
            
        # If it parsed but isn't a dict, just return it as a string
        return str(parsed_data)

    except json.JSONDecodeError:
        # If it fails to parse, it means the agent just sent normal conversational text.
        # In that case, we just return the text exactly as it is!
        logging.info("Response is not standard JSON, returning raw text.")
        return raw_response
        
    except Exception as e:
        # Catch-all for any weird formatting errors so it doesn't crash the dashboard
        logging.error(f"Error parsing agent output: {e}")
        return f"⚠️ **Output Parsing Error:** Could not format the agent's response. \n\n*Raw output:* {raw_response}"

# --- Quick Test (You can run this file directly to see it work) ---
if __name__ == "__main__":
    # Fake JSON from an agent
    fake_agent_output = '{"status": "success", "extracted_entities": ["User A", "Server B"], "confidence_score": "98%", "next_steps": "Awaiting manual approval."}'
    
    print("--- PARSED OUTPUT ---")
    print(parse_agent_response(fake_agent_output))"""Deterministic statistics for analyzed customer feedback."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping


def classify_nps(score: int) -> str:
    """Return the standard NPS category for an integer score from 0 to 10."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("The score must be an integer between 0 and 10.")
    if not 0 <= score <= 10:
        raise ValueError("The score must be between 0 and 10.")
    if score >= 9:
        return "promoter"
    if score >= 7:
        return "passive"
    return "detractor"


def _display_number(value: float) -> int | float:
    """Keep whole-number metrics tidy while retaining useful decimal precision."""
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def calculate_summary_metrics(
    processed_records: Iterable[Mapping[str, Any]],
) -> dict[str, int | float]:
    """Calculate NPS metrics from successfully processed records."""
    records = list(processed_records)
    categories = Counter(
        classify_nps(record["original_score"])
        for record in records
    )
    total = len(records)
    promoters = categories["promoter"]
    passives = categories["passive"]
    detractors = categories["detractor"]
    nps_score = 0 if total == 0 else ((promoters - detractors) / total) * 100

    return {
        "total_processed": total,
        "nps_score": _display_number(nps_score),
        "total_promoters": promoters,
        "total_passives": passives,
        "total_detractors": detractors,
    }


def calculate_top_themes(
    processed_records: Iterable[Mapping[str, Any]],
    *,
    limit: int | None = 5,
) -> list[dict[str, int | str]]:
    """Count assigned themes and order them by frequency, then by name."""
    if limit is not None and limit < 0:
        raise ValueError("The theme limit cannot be negative.")

    themes = Counter(
        str(record["assigned_theme"]).strip()
        for record in processed_records
        if str(record.get("assigned_theme", "")).strip()
    )
    ordered = sorted(themes.items(), key=lambda item: (-item[1], item[0].casefold()))
    if limit is not None:
        ordered = ordered[:limit]
    return [{"theme": theme, "count": count} for theme, count in ordered]


def aggregate_results(
    processed_records: Iterable[Mapping[str, Any]],
    *,
    top_theme_limit: int | None = 5,
) -> dict[str, Any]:
    """Build the stable backend payload consumed by the dashboard."""
    records = [dict(record) for record in processed_records]
    return {
        "summary_metrics": calculate_summary_metrics(records),
        "top_themes": calculate_top_themes(records, limit=top_theme_limit),
        "processed_records": records,
    }
