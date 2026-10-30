"""Shared repository fixtures."""
def sample_repos(count=16):
    categories = [
        "AI agents / MCP", "QA / Test automation", "Game dev",
        "Monetization / RAG / Finance",
    ]
    return [
        {
            "name": f"org/repo-{i}", "url": f"https://github.com/org/repo-{i}",
            "description": "<script>alert(1)</script>" if i == 0 else "demo",
            "category": categories[i % 4], "stars": i, "language": "Python",
            "license": "MIT", "last_push": "2026-10-22T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z", "topics": [], "signals": ["ai"],
        }
        for i in range(count)
    ]
