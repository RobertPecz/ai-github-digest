"""Build a metadata-only report using configured editorial content."""
from collections.abc import Iterable

from .selection import balanced_selection
from .models import FallbackContent, Report, Repository


def fallback_report(
    repos: list[Repository], categories: Iterable[str], content: FallbackContent,
    reason: str = "Gemini unavailable",
) -> Report:
    selected = balanced_selection(repos, categories)
    items = []
    for repo in selected:
        category = repo["category"]
        items.append(
            {
                "name": repo["name"],
                "why": content["why"].format(category=category),
                "use_case": content["examples"].get(
                    category, content["default_use_case"]
                ),
                "business": content["business"],
                "risk": content["risk"],
                "difficulty": content["difficulty"],
            }
        )
    return {
        "intro": content["intro"].format(reason=reason),
        "items": items,
        "top_three": [
            {"name": item["name"], "first_step": item["use_case"]} for item in items[:3]
        ],
    }
