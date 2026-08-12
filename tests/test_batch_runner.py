import json
import tempfile
import unittest
from pathlib import Path

from src.backend.batch_runner import run_batch


def fake_analyzer(customer_id, score, comment):
    return {
        "customer_id": customer_id,
        "score": score,
        "prediction": {
            "theme_id": "TECHNICAL_RELIABILITY" if score <= 6 else "POSITIVE_EXPERIENCE",
            "urgency": "high" if score <= 6 else "low",
            "sentiment": "negative" if score <= 6 else "positive",
            "summary": comment,
            "evidence": comment,
        },
        "prediction_needs_review": False,
        "model_metadata": {
            "provider": "test",
            "model_name": "fake-analyzer",
            "prompt_version": "test-v1",
            "enrichment_schema_version": "1.0.0",
        },
    }


def feedback(feedback_id, score, comment, **overrides):
    record = {
        "feedback_id": feedback_id,
        "customer_id": f"CUSTOMER-{feedback_id}",
        "source": "Web",
        "score": score,
        "comment": comment,
        "language": "EN",
    }
    record.update(overrides)
    return record


class BatchRunnerTests(unittest.TestCase):
    def test_batch_continues_after_an_invalid_record(self):
        progress = []
        source = [
            feedback("FBK-001", 2, "Outage"),
            feedback("FBK-002", 12, "Invalid"),
            feedback("FBK-003", 9, "Excellent"),
        ]

        result = run_batch(
            source,
            analyzer=fake_analyzer,
            progress_callback=lambda current, total: progress.append((current, total)),
        )

        self.assertEqual(result["summary_metrics"]["total_processed"], 2)
        self.assertEqual(result["run_info"]["total_received"], 3)
        self.assertEqual(result["run_info"]["total_failed_validation"], 1)
        self.assertEqual(result["errors"][0]["feedback_id"], "FBK-002")
        self.assertEqual(result["errors"][0]["stage"], "validation")
        self.assertEqual(progress, [(1, 3), (2, 3), (3, 3)])
        self.assertEqual(
            result["enriched_records"][0]["predicted_theme_id"],
            "TECHNICAL_RELIABILITY",
        )

    def test_canonical_fields_are_normalized(self):
        result = run_batch(
            [feedback("FBK-001", 4, "Slow service", language="en_us")],
            analyzer=fake_analyzer,
        )

        record = result["normalized_records"][0]
        self.assertEqual(record["feedback_id"], "FBK-001")
        self.assertEqual(record["score"], 4)
        self.assertEqual(record["language"], "EN-US")
        self.assertEqual(set(record), set(result["dataset_manifest"]["canonical_fields"]))

    def test_jsonl_source(self):
        lines = [
            feedback("FBK-001", 2, "Outage"),
            feedback("FBK-002", 9, "Excellent"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.jsonl"
            path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
            result = run_batch(path, analyzer=fake_analyzer)

        self.assertEqual(result["run_info"]["source_name"], "feedback.jsonl")
        self.assertEqual(result["run_info"]["total_enriched"], 2)

    def test_duplicate_feedback_ids_are_reported(self):
        source = [
            feedback("FBK-001", 5, "First"),
            feedback("FBK-001", 5, "Duplicate"),
        ]

        result = run_batch(source, analyzer=fake_analyzer)

        self.assertEqual(result["run_info"]["total_valid"], 1)
        self.assertIn("duplicate value", result["errors"][0]["error_reason"])

    def test_missing_required_fields_are_reported(self):
        result = run_batch(
            [{"feedback_id": "FBK-001", "score": 5, "comment": "Incomplete"}],
            analyzer=fake_analyzer,
        )

        self.assertEqual(result["data_quality"]["total_rejected"], 1)
        self.assertEqual(result["data_quality"]["missing_field_counts"]["language"], 1)
        self.assertIn("customer_id", result["errors"][0]["error_reason"])
        self.assertIn("source", result["errors"][0]["error_reason"])

    def test_score_is_not_silently_coerced_from_text(self):
        result = run_batch(
            [feedback("FBK-001", "10", "Wrong score type")],
            analyzer=fake_analyzer,
        )

        self.assertEqual(result["data_quality"]["total_rejected"], 1)
        self.assertIn("valid integer", result["errors"][0]["error_reason"])

    def test_duplicate_comments_create_a_quality_warning(self):
        result = run_batch(
            [
                feedback("FBK-001", 5, "Repeated comment"),
                feedback("FBK-002", 6, "Repeated comment"),
            ],
            analyzer=fake_analyzer,
        )

        quality = result["data_quality"]
        self.assertEqual(quality["unique_comment_count"], 1)
        self.assertEqual(quality["duplicate_comment_rows"], 1)
        self.assertIn("DUPLICATE_COMMENTS", [warning["code"] for warning in quality["warnings"]])

    def test_metrics_include_valid_records_when_enrichment_fails(self):
        def failing_analyzer(customer_id, score, comment):
            raise RuntimeError("model unavailable")

        result = run_batch(
            [feedback("FBK-001", 0, "Outage")],
            analyzer=failing_analyzer,
        )

        self.assertEqual(result["summary_metrics"]["total_processed"], 1)
        self.assertEqual(result["summary_metrics"]["total_detractors"], 1)
        self.assertEqual(result["data_quality"]["enrichment_failed"], 1)
        self.assertEqual(result["enriched_records"], [])

    def test_review_required_predictions_are_excluded_from_findings(self):
        def review_analyzer(customer_id, score, comment):
            result = fake_analyzer(customer_id, score, comment)
            result["prediction_needs_review"] = True
            return result

        result = run_batch(
            [feedback("FBK-001", 1, "Ambiguous model output")],
            analyzer=review_analyzer,
        )

        self.assertEqual(result["run_info"]["status"], "partial")
        self.assertEqual(result["data_quality"]["predictions_review_required"], 1)
        self.assertEqual(result["data_quality"]["predictions_ready"], 0)
        self.assertEqual(result["evidence_insights"]["predicted_theme_breakdown"], [])
        self.assertEqual(result["top_themes"], [])
        self.assertEqual(result["review_queue"][0]["feedback_id"], "FBK-001")
        self.assertIn(
            "PREDICTIONS_REQUIRE_REVIEW",
            [warning["code"] for warning in result["data_quality"]["warnings"]],
        )

    def test_sensitive_identifiers_are_masked_before_enrichment(self):
        observed_comments = []

        def observing_analyzer(customer_id, score, comment):
            observed_comments.append(comment)
            return fake_analyzer(customer_id, score, comment)

        original = "Contact alice@example.com or +1 212 555 0199 for help"
        result = run_batch(
            [feedback("FBK-001", 5, original)], analyzer=observing_analyzer
        )

        self.assertNotIn("alice@example.com", observed_comments[0])
        self.assertIn("[EMAIL]", observed_comments[0])
        self.assertIn("[PHONE]", observed_comments[0])
        self.assertEqual(result["normalized_records"][0]["comment"], original)
        self.assertTrue(result["enriched_records"][0]["model_input_redacted"])
        self.assertEqual(result["data_quality"]["model_inputs_redacted"], 1)


if __name__ == "__main__":
    unittest.main()
