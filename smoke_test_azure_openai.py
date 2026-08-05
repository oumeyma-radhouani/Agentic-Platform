"""smoke_test_azure_openai.py"""
"""Quick Azure OpenAI connectivity smoke test."""

import os

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAIError


load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://novaso.openai.azure.com/")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")


def main() -> None:
    if not API_KEY or API_KEY == "<your-api-key>":
        raise SystemExit(
            "Set AZURE_OPENAI_API_KEY in a .env file or in your environment first."
        )

    client = AzureOpenAI(
        api_version=API_VERSION,
        azure_endpoint=ENDPOINT,
        api_key=API_KEY,
        timeout=30.0,
        max_retries=0,
    )

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Name three must-see places in Paris."},
            ],
            max_completion_tokens=200,
        )
    except OpenAIError as exc:
        raise SystemExit(f"Azure OpenAI request failed: {exc}") from exc

    content = response.choices[0].message.content
    print(content or "Azure OpenAI returned an empty response.")


if __name__ == "__main__":
    main()
