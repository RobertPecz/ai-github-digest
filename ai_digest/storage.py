"""Persist report artifacts independently of generation and delivery."""
import json
from pathlib import Path

from .models import Report


def write_reports(directory: Path, report: Report, engine: str, plain: str, rich: str):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "digest.txt").write_text(plain, encoding="utf-8")
    (directory / "digest.html").write_text(rich, encoding="utf-8")
    (directory / "selected.json").write_text(
        json.dumps({"engine": engine, "report": report}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
