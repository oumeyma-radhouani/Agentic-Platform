import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from src.backend.context_store import clear_contexts
from src.backend.azure_rag import clear_document_index


def fake_analyzer(customer_id, score, comment):
    return {
        "prediction": {
            "theme_id": "POSITIVE_EXPERIENCE",
            "sentiment": "positive",
            "urgency": "low",
            "summary": comment,
            "evidence": comment,
        },
        "model_metadata": {
            "provider": "test",
            "model_name": "fake-analyzer",
            "prompt_version": "test-v1",
        },
    }


class BatchApiTests(unittest.TestCase):
    def tearDown(self):
        clear_contexts()
        clear_document_index()

    def test_batch_succeeds_when_optional_history_is_unavailable(self):
        payload = [
            {
                "feedback_id": "FBK-TEST-001",
                "customer_id": "CUST-1001",
                "source": "Web",
                "score": 10,
                "comment": "Excellent service.",
                "language": "EN",
            }
        ]

        with (
            patch("src.ai.extractor.analyze_feedback", side_effect=fake_analyzer),
            patch("main.get_mongo_history", side_effect=RuntimeError("disabled")),
        ):
            response = TestClient(app).post(
                "/api/batch",
                files={
                    "file": (
                        "feedback.json",
                        json.dumps(payload).encode("utf-8"),
                        "application/json",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["data_quality"]["total_valid"], 1)
        self.assertEqual(data["data_quality"]["total_rejected"], 0)
        self.assertEqual(data["dataset_manifest"]["schema_version"], "1.0.0")
        self.assertEqual(data["run_info"]["source_name"], "feedback.json")
        self.assertEqual(data["run_info"]["status"], "complete")

    def test_assistant_receives_the_active_batch_context(self):
        payload = [
            {
                "feedback_id": "FBK-CONTEXT-001",
                "customer_id": "CUST-1001",
                "source": "Web",
                "score": 10,
                "comment": "Excellent service.",
                "language": "EN",
            }
        ]
        captured_messages = []

        def fake_completion(messages, **kwargs):
            captured_messages.extend(messages)
            return "Grounded answer"

        with (
            patch("src.ai.extractor.analyze_feedback", side_effect=fake_analyzer),
            patch("main.get_mongo_history", side_effect=RuntimeError("disabled")),
        ):
            client = TestClient(app)
            client.post(
                "/api/batch",
                data={"session_id": "context-session"},
                files={"file": ("feedback.json", json.dumps(payload), "application/json")},
            )
            with (
                patch("main.is_azure_configured", return_value=True),
                patch("main.create_chat_completion", side_effect=fake_completion),
            ):
                response = client.post(
                    "/api/chat",
                    json={"message": "What is the NPS?", "session_id": "context-session"},
                )

        self.assertEqual(response.status_code, 200)
        serialized_messages = json.dumps(captured_messages)
        self.assertIn("FBK-CONTEXT-001", serialized_messages)
        self.assertIn("summary_metrics", serialized_messages)

    def test_text_document_is_really_indexed_and_retrieved(self):
        document = b"The refund policy allows a refund within thirty days of purchase."
        with patch("main.get_mongo_history", side_effect=RuntimeError("disabled")):
            response = TestClient(app).post(
                "/api/rag",
                data={"session_id": "rag-session"},
                files={"file": ("policy.txt", document, "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "indexed")
        self.assertGreater(data["word_count"], 0)
        self.assertGreater(data["chunk_count"], 0)

        from src.backend.azure_rag import retrieve_relevant_chunks

        chunks = retrieve_relevant_chunks("rag-session", "When can I get a refund?")
        self.assertEqual(chunks[0]["filename"], "policy.txt")
        self.assertIn("thirty days", chunks[0]["text"])

    def test_audio_endpoint_returns_configured_transcription_metadata(self):
        transcription = {
            "status": "complete",
            "transcript": "Customer requested a refund.",
            "provider": "azure_openai",
            "deployment": "transcribe-test",
            "filename": "temporary.wav",
        }
        with (
            patch("main.transcribe_audio", return_value=transcription),
            patch("main.get_mongo_history", side_effect=RuntimeError("disabled")),
        ):
            response = TestClient(app).post(
                "/api/audio",
                data={"session_id": "audio-session"},
                files={"file": ("call.wav", b"audio bytes", "audio/wav")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript"], "Customer requested a refund.")
        self.assertEqual(response.json()["deployment"], "transcribe-test")

    def test_upload_size_limit_is_enforced(self):
        with patch("main.MAX_BATCH_BYTES", 5):
            response = TestClient(app).post(
                "/api/batch",
                files={"file": ("feedback.json", b"123456", "application/json")},
            )

        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
