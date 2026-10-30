import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from ai_digest.configuration import load_categories, load_content
from ai_digest.settings import ROOT, load_settings


class TestConfiguration(unittest.TestCase):
    def test_existing_categories_file_loads(self):
        content = load_content()
        self.assertEqual(len(content.categories), 4)
        self.assertEqual(content.categories["AI agents / MCP"][0], "topic:mcp-server")
        self.assertIn("UNTRUSTED DATA", content.gemini_prompt)

    def test_categories_are_loaded_in_order_and_bad_shapes_are_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "categories.json"
            path.write_text(json.dumps({"CATEGORIES": {"B": ["b"], "A": ["a"]}}))
            self.assertEqual(list(load_categories(path)), ["B", "A"])
            for categories in (None, [], {}, {"A": "query"}, {"": ["q"]}, {"A": [1]}, {"A": []}):
                with self.subTest(categories=categories):
                    path.write_text(json.dumps({"CATEGORIES": categories}))
                    with self.assertRaises(ValueError):
                        load_categories(path)

    def test_custom_content_is_read_and_invalid_sections_fail_early(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "config", root, dirs_exist_ok=True)
            path = root / "report_content.json"
            original = json.loads(path.read_text())
            original["fallback"]["business"] = "Custom business copy"
            path.write_text(json.dumps(original))
            self.assertEqual(load_content(root).fallback["business"], "Custom business copy")
            for section, field, value in (
                ("fallback", "why", None), ("fallback", "examples", []),
                ("rendering", "fields", [["unknown", "Label"]]),
                ("rendering", "subject", ""),
            ):
                with self.subTest(field=field):
                    content = json.loads(json.dumps(original))
                    content[section][field] = value
                    path.write_text(json.dumps(content))
                    with self.assertRaises(ValueError):
                        load_content(root)

    def test_settings_use_only_supplied_environment(self):
        settings = load_settings({"GITHUB_TOKEN": " token ", "FORCE_FALLBACK": "TRUE", "DRY_RUN": "true"})
        self.assertEqual(settings.github_token, "token")
        self.assertTrue(settings.force_fallback)
        self.assertTrue(settings.dry_run)
        self.assertEqual(settings.gemini_api_key, "")
        self.assertEqual(settings.reports_dir, ROOT / "reports")
        with self.assertRaisesRegex(RuntimeError, "Missing GITHUB_TOKEN"):
            load_settings({})

    def test_secrets_are_not_in_settings_repr(self):
        settings = load_settings({"GITHUB_TOKEN": "github-secret", "GEMINI_API_KEY": "ai-secret",
                                  "GMAIL_CLIENT_SECRET": "gmail-secret", "GMAIL_REFRESH_TOKEN": "refresh-secret"})
        for secret in ("github-secret", "ai-secret", "gmail-secret", "refresh-secret"):
            self.assertNotIn(secret, repr(settings))
