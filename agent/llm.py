import json
import os
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Copy .env.example to .env and add your key.")
        _client = Groq(api_key=api_key)
    return _client


def call_structured(system: str, prompt: str, max_retries: int = 2) -> dict:
    """Call Groq and parse the response as JSON. Retries on parse failure."""
    client = _get_client()

    for attempt in range(max_retries + 1):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if the model adds them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            if attempt == max_retries:
                raise ValueError(
                    f"Groq returned non-JSON after {max_retries + 1} attempts. "
                    f"Last response: {raw[:300]}"
                ) from exc
