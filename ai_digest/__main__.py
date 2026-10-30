"""Support python -m ai_digest."""
from .cli import entrypoint

if __name__ == "__main__":
    raise SystemExit(entrypoint())
