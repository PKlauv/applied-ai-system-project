import json
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-pro"
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.")
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=None,
        )
    return _client


def call_structured(system: str, prompt: str, max_retries: int = 2) -> dict:
    """Call Gemini and parse the response as JSON. Retries on parse failure."""
    client = _get_client()
    full_prompt = f"{system}\n\n{prompt}"

    for attempt in range(max_retries + 1):
        response = client.generate_content(full_prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini adds them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            if attempt == max_retries:
                raise ValueError(
                    f"Gemini returned non-JSON after {max_retries + 1} attempts. "
                    f"Last response: {raw[:300]}"
                ) from exc
            # retry
