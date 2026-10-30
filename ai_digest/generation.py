"""Choose AI generation or the deterministic fallback."""
from collections.abc import Callable, Iterable
import sys

import requests

from .fallback import fallback_report
from .models import FallbackContent, Report, Repository
from .validation import validate_report


def generate_report(
    repos: list[Repository], categories: Iterable[str], content: FallbackContent, *,
    ai_generator: Callable[[list[Repository]], Report] | None = None,
    force_fallback: bool = False,
) -> tuple[Report, str]:
    """The AI generator accepts repositories; credentials belong to its adapter."""
    if force_fallback or ai_generator is None:
        return (
            fallback_report(
                repos, categories, content,
                "forced fallback" if force_fallback else "missing GEMINI_API_KEY"
            ),
            "python",
        )
    try:
        report = ai_generator(repos)
        validate_report(report, repos)
        return report, "gemini"
    except (
        requests.RequestException,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(
            f"WARNING: Gemini failed; using Python fallback: {type(exc).__name__}: {str(exc)[:180]}",
            file=sys.stderr,
        )
        return fallback_report(repos, categories, content, type(exc).__name__), "python"
