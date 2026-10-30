"""Deterministic repository selection without I/O."""
from collections.abc import Iterable

from .models import Repository


def rank_repos(repos: Iterable[Repository]) -> list[Repository]:
    """Rank by matching queries, capped popularity, then most recent activity."""
    return sorted(
        repos,
        key=lambda r: (len(r["signals"]), min(r["stars"], 4000), r["last_push"]),
        reverse=True,
    )


def balanced_selection(
    repos: list[Repository], categories: Iterable[str], count: int = 12,
) -> list[Repository]:
    """Visit categories in order, preserving repository rank within each category."""
    groups = {category: [] for category in categories}
    for repo in repos:
        groups.setdefault(repo["category"], []).append(repo)
    selected, seen = [], set()
    while len(selected) < count:
        changed = False
        for group in groups.values():
            while group and group[0]["name"] in seen:
                group.pop(0)
            if group and len(selected) < count:
                repo = group.pop(0)
                selected.append(repo)
                seen.add(repo["name"])
                changed = True
        if not changed:
            break
    return selected
