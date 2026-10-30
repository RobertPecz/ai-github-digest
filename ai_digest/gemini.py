"""Gemini API adapter."""
import json
import re

from .http import request_json
from .models import Report, Repository
from .validation import validate_report

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def choose_gemini(
    repos: list[Repository], api_key: str, *, model: str, instructions: str,
) -> Report:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ValueError("Invalid Gemini model identifier")
    response = request_json(
        "POST",
        GEMINI_API.format(model=model),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        data={
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "Repository metadata:\n"
                            + json.dumps(repos[:80], ensure_ascii=False)
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 8192,
            },
        },
    )
    candidates = response.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    report = json.loads(text)
    validate_report(report, repos)
    return report
