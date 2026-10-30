import json
import unittest
from unittest.mock import patch

from ai_digest.configuration import load_content
from ai_digest.fallback import fallback_report
from ai_digest.gemini import choose_gemini
from tests.support import sample_repos


class TestGemini(unittest.TestCase):
    def setUp(self):
        self.content = load_content()
        self.repos = sample_repos()

    def choose(self, **kwargs):
        return choose_gemini(self.repos, "key", instructions=self.content.gemini_prompt, **kwargs)

    def test_configured_prompt_model_and_json_response(self):
        report = fallback_report(self.repos, self.content.categories, self.content.fallback)
        text = json.dumps(report)
        response = {"candidates": [{"content": {"parts": [{"text": text[:50]}, {"text": text[50:]}]}}]}
        with patch("ai_digest.gemini.request_json", return_value=response) as request:
            actual = self.choose(model="test-model")
        self.assertEqual(actual, report)
        self.assertIn("/test-model:generateContent", request.call_args.args[1])
        payload = request.call_args.kwargs["data"]
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], self.content.gemini_prompt)
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")

    def test_invalid_model_fails_before_request(self):
        with patch("ai_digest.gemini.request_json") as request:
            with self.assertRaisesRegex(ValueError, "Invalid Gemini model"):
                self.choose(model="../model")
            request.assert_not_called()

    def test_empty_malformed_and_unknown_repository_responses_are_rejected(self):
        report = fallback_report(self.repos, self.content.categories, self.content.fallback)
        report["items"][0]["name"] = "unknown/repo"
        for response in ({}, {"candidates": [{"content": {"parts": [{"text": "bad JSON"}]}}]},
                         {"candidates": [{"content": {"parts": [{"text": json.dumps(report)}]}}]}):
            with self.subTest(response=response), patch("ai_digest.gemini.request_json", return_value=response):
                with self.assertRaises(ValueError):
                    self.choose(model="test-model")
