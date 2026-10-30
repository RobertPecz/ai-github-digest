"""GitHub search and repository metadata normalization."""
from datetime import datetime, timedelta, timezone

from .http import request_json
from .models import Repository
from .selection import rank_repos

GITHUB_API = "https://api.github.com/search/repositories"


def normalize_repo(item: dict, category: str, query: str) -> Repository:
    """Map a GitHub payload to the application's repository data contract."""
    return {
        "name": item["full_name"],
        "url": item["html_url"],
        "description": (item.get("description") or "")[:280],
        "stars": item.get("stargazers_count", 0),
        "last_push": item.get("pushed_at", ""),
        "created_at": item.get("created_at", ""),
        "language": item.get("language"),
        "license": (item.get("license") or {}).get("spdx_id") or "unknown",
        "topics": item.get("topics") or [],
        "category": category,
        "signals": [query],
    }


def search_repos(token: str, categories: dict[str, list[str]]) -> tuple[list[Repository], list[str]]:
    start = (datetime.now(timezone.utc) - timedelta(days=8)).date().isoformat()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "weekly-ai-digest",
    }
    found, warnings = {}, []
    for category, queries in categories.items():
        for query in queries:
            try:
                payload = request_json(
                    "GET",
                    GITHUB_API,
                    headers=headers,
                    params={
                        "q": f"{query} archived:false fork:false pushed:>={start}",
                        "sort": "updated",
                        "order": "desc",
                        "per_page": 18,
                    },
                )
                if payload.get("incomplete_results"):
                    warnings.append(f"Incomplete results: {category}, {query}")
            except Exception as exc:
                warnings.append(f"Search failed: {category}, {query}: {exc}")
                continue
            for item in payload.get("items", []):
                if item.get("disabled") or item.get("private"):
                    continue
                key = item["full_name"].lower()
                if key not in found:
                    found[key] = normalize_repo(item, category, query)
                elif query not in found[key]["signals"]:
                    found[key]["signals"].append(query)
    if len(found) < 10:
        raise RuntimeError(
            f"Only {len(found)} unique repos found; warnings: {warnings}"
        )
    return rank_repos(found.values())[:100], warnings
