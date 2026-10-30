"""Load and validate editable search queries, editorial copy and AI instructions."""
import json
from pathlib import Path

from .models import DigestContent
from .settings import ROOT


def load_categories(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    categories = payload.get("CATEGORIES") if isinstance(payload, dict) else None
    if not isinstance(categories, dict) or not categories:
        raise ValueError("CATEGORIES must be a non-empty object")
    for name, queries in categories.items():
        if (
            not name.strip()
            or not isinstance(queries, list)
            or not queries
            or any(not isinstance(q, str) or not q.strip() for q in queries)
        ):
            raise ValueError(f"Invalid search category: {name!r}")
    return categories


def _require_strings(section, keys, name):
    if not isinstance(section, dict) or any(
        not isinstance(section.get(key), str) or not section[key].strip()
        for key in keys
    ):
        raise ValueError(f"Invalid {name} content")


def load_content(directory: Path = ROOT / "config") -> DigestContent:
    categories = load_categories(directory / "categories.json")
    content = json.loads((directory / "report_content.json").read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("Report content must be an object")
    fallback = content.get("fallback")
    _require_strings(
        fallback,
        ("default_use_case", "why", "business", "risk", "difficulty", "intro"),
        "fallback",
    )
    examples = fallback.get("examples")
    if not isinstance(examples, dict) or any(
        not isinstance(value, str) for value in examples.values()
    ):
        raise ValueError("Fallback examples must map categories to strings")
    rendering = content.get("rendering")
    _require_strings(
        rendering,
        ("subject", "source", "missing_description", "top_three", "plain_warning",
         "html_warning", "disclaimer"),
        "rendering",
    )
    fields = rendering.get("fields")
    expected = {"why", "use_case", "business", "risk", "difficulty"}
    if (
        not isinstance(fields, list)
        or len(fields) != len(expected)
        or any(
            not isinstance(pair, list) or len(pair) != 2
            or any(not isinstance(value, str) or not value.strip() for value in pair)
            for pair in fields
        )
        or {pair[0] for pair in fields} != expected
    ):
        raise ValueError("Rendering fields must label each report item field exactly once")
    prompt = (directory / "gemini_prompt.txt").read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError("Gemini prompt must not be empty")
    return DigestContent(categories, fallback, rendering, prompt)
