from copy import deepcopy
from datetime import date
import unittest
from unittest.mock import Mock

import requests

from ai_digest.configuration import load_content
from ai_digest.fallback import fallback_report
from ai_digest.generation import generate_report
from ai_digest.rendering import render
from ai_digest.selection import balanced_selection
from ai_digest.validation import validate_report
from tests.support import sample_repos


class TestReports(unittest.TestCase):
    def setUp(self):
        self.content = load_content()
        self.repos = sample_repos()

    def fallback(self):
        return fallback_report(self.repos, self.content.categories, self.content.fallback)

    def generate(self, **kwargs):
        return generate_report(self.repos, self.content.categories, self.content.fallback, **kwargs)

    def test_fallback_is_balanced_valid_and_deterministic(self):
        report = self.fallback()
        lookup = validate_report(report, self.repos)
        self.assertEqual(report, self.fallback())
        self.assertEqual(len(report["items"]), 12)
        categories = [lookup[item["name"]]["category"] for item in report["items"]]
        self.assertEqual({category: categories.count(category) for category in categories},
                         dict.fromkeys(self.content.categories, 3))

    def test_selection_preserves_input_and_handles_duplicates_and_unknown_categories(self):
        self.repos[0]["category"] = "New category"
        self.repos.insert(0, deepcopy(self.repos[1]))
        before = deepcopy(self.repos)
        selected = balanced_selection(self.repos, self.content.categories, count=30)
        self.assertEqual(len(selected), 16)
        self.assertEqual(len({r["name"] for r in selected}), 16)
        self.assertEqual(self.repos, before)
        self.assertTrue(any(r["category"] == "New category" for r in selected))

    def test_selection_obeys_configured_category_order(self):
        selected = balanced_selection(self.repos, ["Game dev", "AI agents / MCP"], count=2)
        self.assertEqual([r["category"] for r in selected], ["Game dev", "AI agents / MCP"])
        self.assertEqual(balanced_selection([], self.content.categories), [])

    def test_missing_key_uses_fallback(self):
        report, engine = self.generate()
        self.assertEqual(engine, "python")
        self.assertIn("missing GEMINI_API_KEY", report["intro"])
        self.assertEqual(len(report["top_three"]), 3)

    def test_gemini_errors_and_invalid_response_trigger_fallback(self):
        for error in (RuntimeError("429"), requests.Timeout(), ValueError("bad JSON")):
            with self.subTest(error=error):
                report, engine = self.generate(ai_generator=Mock(side_effect=error))
                self.assertEqual(engine, "python")
                validate_report(report, self.repos)
        report, engine = self.generate(ai_generator=lambda repos: {})
        self.assertEqual(engine, "python")
        validate_report(report, self.repos)

    def test_valid_gemini_response_is_used(self):
        report = self.fallback()
        actual, engine = self.generate(ai_generator=lambda repos: report)
        self.assertEqual(engine, "gemini")
        self.assertEqual(actual, report)

    def test_invalid_repositories_and_fields_are_rejected(self):
        for mutate in (
            lambda r: r["items"][0].update(name="unknown/repo"),
            lambda r: r["items"][0].update(name=r["items"][1]["name"]),
            lambda r: r["items"][0].update(why=None),
            lambda r: r.update(items=r["items"][:9]),
            lambda r: r["top_three"][0].update(name=r["top_three"][1]["name"]),
            lambda r: r["top_three"][0].update(name="unknown/repo"),
        ):
            report = self.fallback()
            mutate(report)
            with self.assertRaises(ValueError):
                validate_report(report, self.repos)

    def test_render_escapes_untrusted_data_and_uses_configured_copy(self):
        report = self.fallback()
        self.content.rendering["source"] = "<Source>"
        subject, plain, rich = render(
            report, validate_report(report, self.repos), ["incomplete"], "python",
            self.content.rendering, today=date(2026, 10, 30),
        )
        self.assertEqual(subject, "Heti AI GitHub válogatás – 2026-10-30")
        self.assertIn("&lt;script&gt;", rich)
        self.assertNotIn("<script>", rich)
        self.assertIn("&lt;Source&gt;: python", rich)
        self.assertIn("https://github.com/org/repo-0", plain)
        self.assertIn(self.content.rendering["plain_warning"], plain)
        self.assertIn(self.content.rendering["disclaimer"], rich)

    def test_new_category_uses_default_example(self):
        self.repos[0]["category"] = "New category"
        report = self.fallback()
        item = next(item for item in report["items"] if item["name"] == "org/repo-0")
        self.assertEqual(item["use_case"], self.content.fallback["default_use_case"])
