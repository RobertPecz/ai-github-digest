"""Backward-compatible script entry point for the digest application."""
from pathlib import Path
import sys

# Direct script execution places scripts/, not the repository root, on sys.path.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_digest.cli import entrypoint


if __name__ == "__main__":
    raise SystemExit(entrypoint())
