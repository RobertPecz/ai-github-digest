from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from ai_digest.github import search_repos


def github_item(i, **fields):
    return {"full_name": f"org/repo-{i}", "html_url": f"https://github.com/org/repo-{i}",
            "stargazers_count": i, "pushed_at": "2026-10-30T00:00:00Z", **fields}


class TestGitHub(unittest.TestCase):
    def test_queries_normalization_deduplication_and_ranking(self):
        categories = {"First": ["query-a"], "Second": ["query-b"]}
        first = [github_item(i) for i in range(10)]
        first[0]["description"] = "x" * 300
        first += [github_item(10, private=True), github_item(11, disabled=True)]
        duplicate = github_item(0, full_name="ORG/REPO-0")
        with patch("ai_digest.github.request_json", side_effect=[
            {"items": first}, {"items": [duplicate], "incomplete_results": True},
        ]) as request, patch("ai_digest.github.datetime") as clock:
            clock.now.return_value = datetime(2026, 10, 30, tzinfo=timezone.utc)
            repos, warnings = search_repos("token", categories)
        self.assertEqual(len(repos), 10)
        self.assertEqual(repos[0]["name"], "org/repo-0")
        self.assertEqual(repos[0]["category"], "First")
        self.assertEqual(repos[0]["signals"], ["query-a", "query-b"])
        self.assertEqual(repos[0]["license"], "unknown")
        self.assertEqual(len(repos[0]["description"]), 280)
        self.assertEqual(repos[1]["stars"], 9)
        self.assertIn("Incomplete results: Second", warnings[0])
        self.assertEqual(request.call_args_list[0].kwargs["params"]["q"],
                         "query-a archived:false fork:false pushed:>=2026-10-22")

    def test_partial_failure_keeps_successful_results(self):
        with patch("ai_digest.github.request_json", side_effect=[
            RuntimeError("unavailable"), {"items": [github_item(i) for i in range(10)]},
        ]):
            repos, warnings = search_repos("token", {"Category": ["bad", "good"]})
        self.assertEqual(len(repos), 10)
        self.assertIn("Search failed: Category, bad", warnings[0])

    def test_too_few_repositories_fail(self):
        with patch("ai_digest.github.request_json", return_value={"items": []}):
            with self.assertRaisesRegex(RuntimeError, "Only 0 unique repos"):
                search_repos("token", {"Category": ["query"]})

    def test_candidate_limit_is_preserved(self):
        with patch("ai_digest.github.request_json", return_value={
            "items": [github_item(i) for i in range(110)],
        }):
            repos, _ = search_repos("token", {"Category": ["query"]})
        self.assertEqual(len(repos), 100)
        self.assertEqual(repos[0]["stars"], 109)
