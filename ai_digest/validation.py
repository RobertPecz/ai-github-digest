"""Report schema and repository reference validation."""
from .models import Repository


def validate_report(report, repos: list[Repository]) -> dict[str, Repository]:
    lookup = {repo["name"]: repo for repo in repos}
    if not isinstance(report, dict) or not isinstance(report.get("intro"), str):
        raise ValueError("Missing report intro")
    items = report.get("items")
    if not isinstance(items, list) or not 10 <= len(items) <= 15:
        raise ValueError("Expected 10–15 items")
    names = []
    for item in items:
        if not isinstance(item, dict) or any(
            not isinstance(item.get(k), str)
            for k in ("name", "why", "use_case", "business", "risk", "difficulty")
        ):
            raise ValueError("Invalid item fields")
        names.append(item["name"])
    if len(names) != len(set(names)) or any(name not in lookup for name in names):
        raise ValueError("Unknown or duplicate repositories")
    top = report.get("top_three")
    if (
        not isinstance(top, list)
        or len(top) != 3
        or any(
            not isinstance(t, dict)
            or not isinstance(t.get("first_step"), str)
            or t.get("name") not in names
            for t in top
        )
    ):
        raise ValueError("Invalid top three")
    if len({t["name"] for t in top}) != 3:
        raise ValueError("Duplicate top three")
    return lookup
