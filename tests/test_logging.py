import io
import json
import logging
import unittest

from src.backend.logging_config import NovaFormatter, anonymize_identifier, log_event
from src.backend.batch_runner import run_batch


def _fake_analyzer(customer_id, score, comment):
    return {
        "prediction": {
            "theme_id": "SUPPORT_QUALITY",
            "sentiment": "positive",
            "urgency": "low",
            "summary": "Resolved",
            "evidence": "Resolved",
        },
        "model_metadata": {"provider": "test", "model_name": "test"},
    }


class LoggingTests(unittest.TestCase):
    def test_identifier_is_stable_and_not_logged_verbatim(self):
        first = anonymize_identifier("private-session-id")
        second = anonymize_identifier("private-session-id")

        self.assertEqual(first, second)
        self.assertNotEqual(first, "private-session-id")
        self.assertEqual(len(first), 12)

    def test_json_formatter_preserves_safe_structured_context(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(NovaFormatter(json_output=True))
        logger = logging.getLogger("nova.logging.test")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)

        log_event(
            logger,
            logging.INFO,
            "batch_processing_completed",
            batch_id="BATCH-TEST",
            total_valid=3,
        )

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["event"], "batch_processing_completed")
        self.assertEqual(payload["batch_id"], "BATCH-TEST")
        self.assertEqual(payload["total_valid"], 3)
        self.assertNotIn("private-session-id", stream.getvalue())

    def test_batch_logs_do_not_contain_feedback_comments(self):
        sensitive_comment = "Resolved for private.person@example.com"
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(NovaFormatter(json_output=True))
        logger = logging.getLogger("src.backend.batch_runner")
        previous_handlers = logger.handlers
        previous_propagate = logger.propagate
        previous_level = logger.level
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)

        try:
            run_batch(
                [
                    {
                        "feedback_id": "FBK-LOG-001",
                        "customer_id": "CUST-LOG-001",
                        "source": "Web",
                        "score": 10,
                        "comment": sensitive_comment,
                        "language": "EN",
                    }
                ],
                analyzer=_fake_analyzer,
            )
        finally:
            logger.handlers = previous_handlers
            logger.propagate = previous_propagate
            logger.setLevel(previous_level)

        self.assertNotIn(sensitive_comment, stream.getvalue())
        self.assertNotIn("private.person@example.com", stream.getvalue())
        self.assertIn("batch_processing_completed", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
