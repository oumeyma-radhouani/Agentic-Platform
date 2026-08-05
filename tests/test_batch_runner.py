import json
import tempfile
import unittest
from pathlib import Path

from src.backend.batch_runner import run_batch


def fake_analyzer(customer_id, score, comment):
    theme = "Problème technique" if score <= 6 else "Retard de traitement"
    return {
        "customer_id": customer_id,
        "score": score,
        "rag_verified": True,
        "ai_analysis": {
            "theme": theme,
            "urgency": "Haute" if score <= 6 else "Basse",
            "sentiment": "negative" if score <= 6 else "positive",
            "main_cause": "Test cause",
            "summary": comment,
        },
    }


class BatchRunnerTests(unittest.TestCase):
    def test_batch_continues_after_an_invalid_record(self):
        progress = []
        source = [
            {"feedback_id": "FBK-001", "customer_id": "C001", "score": 2, "comment": "Panne"},
            {"feedback_id": "FBK-002", "customer_id": "C002", "score": 12, "comment": "Invalid"},
            {"feedback_id": "FBK-003", "customer_id": "C003", "score": 9, "comment": "Excellent"},
        ]

        result = run_batch(
            source,
            analyzer=fake_analyzer,
            progress_callback=lambda current, total: progress.append((current, total)),
        )

        self.assertEqual(result["summary_metrics"]["total_processed"], 2)
        self.assertEqual(result["run_info"]["total_received"], 3)
        self.assertEqual(result["run_info"]["total_failed"], 1)
        self.assertEqual(result["errors"][0]["feedback_id"], "FBK-002")
        self.assertEqual(progress, [(1, 3), (2, 3), (3, 3)])
        self.assertTrue(result["processed_records"][0]["rag_verified"])

    def test_current_mock_id_field_is_normalized(self):
        result = run_batch(
            [{"id": "C001", "score": 4, "comment": "Service lent"}],
            analyzer=fake_analyzer,
        )

        record = result["processed_records"][0]
        self.assertEqual(record["feedback_id"], "C001")
        self.assertEqual(record["customer_id"], "C001")
        self.assertEqual(record["original_score"], 4)

    def test_jsonl_source(self):
        lines = [
            {"feedback_id": "FBK-001", "score": 2, "comment": "Panne"},
            {"feedback_id": "FBK-002", "score": 9, "comment": "Excellent"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.jsonl"
            path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
            result = run_batch(path, analyzer=fake_analyzer)

        self.assertEqual(result["run_info"]["source_name"], "feedback.jsonl")
        self.assertEqual(result["run_info"]["total_succeeded"], 2)

    def test_duplicate_feedback_ids_are_reported(self):
        source = [
            {"feedback_id": "FBK-001", "score": 5, "comment": "First"},
            {"feedback_id": "FBK-001", "score": 5, "comment": "Duplicate"},
        ]

        result = run_batch(source, analyzer=fake_analyzer)

        self.assertEqual(result["run_info"]["total_succeeded"], 1)
        self.assertIn("Duplicate feedback_id", result["errors"][0]["error_reason"])


if __name__ == "__main__":
    unittest.main()
