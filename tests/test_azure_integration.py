import os
import unittest
from unittest.mock import patch

from backend.src.ai import azure_client
from backend.src.ai.extractor import analyze_feedback


class AzureConfigurationTests(unittest.TestCase):
    def test_placeholder_key_is_not_treated_as_configured(self):
        with patch.dict(
            os.environ,
            {"AZURE_OPENAI_API_KEY": "<your-api-key>"},
            clear=False,
        ):
            self.assertFalse(azure_client.is_azure_configured())

    def test_deployment_can_be_overridden(self):
        with patch.dict(
            os.environ,
            {"AZURE_OPENAI_DEPLOYMENT": "custom-deployment"},
            clear=False,
        ):
            self.assertEqual(azure_client.get_deployment_name(), "custom-deployment")


class AzureFeedbackAnalysisTests(unittest.TestCase):
    @patch("src.ai.extractor.create_chat_completion")
    def test_feedback_response_is_normalized_for_batch_runner(self, completion):
        completion.return_value = (
            '{"sentiment":"negative","main_cause":"delay",'
            '"theme":"support","urgency":"high","summary":"Late reply"}'
        )

        result = analyze_feedback("CUST-1", 3, "The reply was late")

        self.assertEqual(result["customer_id"], "CUST-1")
        self.assertEqual(result["nps_category"], "detracteur")
        self.assertEqual(result["ai_analysis"]["theme"], "support")
        completion.assert_called_once()


if __name__ == "__main__":
    unittest.main()
