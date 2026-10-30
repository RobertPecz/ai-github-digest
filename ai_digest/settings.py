"""Read runtime settings once at the application boundary."""
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


@dataclass(frozen=True)
class GmailSettings:
    client_id: str = ""
    client_secret: str = field(default="", repr=False)
    refresh_token: str = field(default="", repr=False)
    email_from: str = ""
    email_to: str = ""


@dataclass(frozen=True)
class Settings:
    github_token: str = field(repr=False)
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = DEFAULT_GEMINI_MODEL
    force_fallback: bool = False
    dry_run: bool = False
    reports_dir: Path = ROOT / "reports"
    gmail: GmailSettings = field(default_factory=GmailSettings)


def load_settings(env: Mapping[str, str]) -> Settings:
    """Accept an explicit environment so imports and tests have no side effects."""
    token = env.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    return Settings(
        github_token=token,
        gemini_api_key=env.get("GEMINI_API_KEY", "").strip(),
        gemini_model=env.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        force_fallback=env.get("FORCE_FALLBACK", "").lower() == "true",
        dry_run=env.get("DRY_RUN", "").lower() == "true",
        gmail=GmailSettings(
            client_id=env.get("GMAIL_CLIENT_ID", "").strip(),
            client_secret=env.get("GMAIL_CLIENT_SECRET", "").strip(),
            refresh_token=env.get("GMAIL_REFRESH_TOKEN", "").strip(),
            email_from=env.get("EMAIL_FROM", "").strip(),
            email_to=env.get("EMAIL_TO", "").strip(),
        ),
    )
