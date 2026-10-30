import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from ai_digest.application import run_digest
from ai_digest.configuration import load_content
from ai_digest.fallback import fallback_report
from ai_digest.settings import ROOT, Settings
from tests.support import sample_repos


class TestDigest(unittest.TestCase):
    def setUp(self):
        self.content = load_content()
        self.repos = sample_repos()
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.reports = Path(self.directory.name) / "reports"
        self.source = Mock(return_value=(self.repos, []))
        self.sender = Mock(return_value="message-id")

    def run_digest(self, *, dry_run=False, force_fallback=False, ai_generator=None):
        return run_digest(
            Settings("fake-token", dry_run=dry_run, force_fallback=force_fallback,
                     reports_dir=self.reports),
            self.content, repository_source=self.source,
            ai_generator=ai_generator, mail_sender=self.sender,
        )

    def test_dry_run_writes_all_artifacts_without_sending(self):
        self.assertEqual(self.run_digest(dry_run=True), "python")
        self.sender.assert_not_called()
        self.source.assert_called_once_with("fake-token", self.content.categories)
        selected = json.loads((self.reports / "selected.json").read_text())
        self.assertEqual(selected["engine"], "python")
        self.assertEqual(len(selected["report"]["items"]), 12)
        self.assertIn("org/repo-0", (self.reports / "digest.txt").read_text())
        self.assertIn("&lt;script&gt;", (self.reports / "digest.html").read_text())

    def test_forced_fallback_still_sends_email(self):
        generator = Mock(side_effect=AssertionError("AI must not run"))
        self.assertEqual(self.run_digest(force_fallback=True, ai_generator=generator), "python")
        generator.assert_not_called()
        self.sender.assert_called_once()
        _, plain, rich = self.sender.call_args.args
        self.assertEqual(plain, (self.reports / "digest.txt").read_text())
        self.assertEqual(rich, (self.reports / "digest.html").read_text())

    def test_gemini_success_is_persisted(self):
        report = fallback_report(self.repos, self.content.categories, self.content.fallback)
        generator = Mock(return_value=report)
        self.assertEqual(self.run_digest(dry_run=True, ai_generator=generator), "gemini")
        generator.assert_called_once_with(self.repos)
        self.assertEqual(
            json.loads((self.reports / "selected.json").read_text()),
            {"engine": "gemini", "report": report},
        )

    def test_delivery_failure_preserves_artifacts_and_propagates(self):
        self.sender.side_effect = RuntimeError("OAuth failed")
        with self.assertRaisesRegex(RuntimeError, "OAuth failed"):
            self.run_digest()
        self.assertEqual(len(list(self.reports.iterdir())), 3)

    def test_invalid_report_is_not_written_or_sent(self):
        self.source.return_value = (self.repos[:3], [])
        with self.assertRaisesRegex(ValueError, "10–15"):
            self.run_digest()
        self.assertFalse(self.reports.exists())
        self.sender.assert_not_called()

    def test_storage_failure_prevents_sending(self):
        self.reports.write_text("not a directory")
        with self.assertRaises(FileExistsError):
            self.run_digest()
        self.sender.assert_not_called()

    def test_cli_wires_loaded_settings_and_adapters(self):
        from ai_digest.cli import main
        env = {"GITHUB_TOKEN": "token", "GEMINI_API_KEY": "key", "GEMINI_MODEL": "model"}
        with patch.dict(os.environ, env, clear=True), \
             patch("ai_digest.cli.load_dotenv"), \
             patch("ai_digest.cli.run_digest") as run, \
             patch("ai_digest.cli.choose_gemini", return_value={}) as choose, \
             patch("ai_digest.cli.send_gmail", return_value="id") as send:
            main()
            settings, content = run.call_args.args
            self.assertEqual(settings.github_token, "token")
            run.call_args.kwargs["ai_generator"](self.repos)
            choose.assert_called_once_with(
                self.repos, api_key="key", model="model", instructions=content.gemini_prompt,
            )
            run.call_args.kwargs["mail_sender"]("subject", "plain", "html")
            send.assert_called_once_with("subject", "plain", "html", config=settings.gmail)

    def test_both_entrypoints_report_missing_token(self):
        env = dict(os.environ, GITHUB_TOKEN="", PYTHON_DOTENV_DISABLED="1")
        commands = [
            ([sys.executable, str(ROOT / "scripts/digest.py")], self.directory.name),
            ([sys.executable, "-m", "ai_digest"], ROOT),
        ]
        for command, cwd in commands:
            with self.subTest(command=command):
                result = subprocess.run(command, cwd=cwd, env=env, text=True,
                                        capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 1)
                self.assertIn("ERROR: Missing GITHUB_TOKEN", result.stderr)
