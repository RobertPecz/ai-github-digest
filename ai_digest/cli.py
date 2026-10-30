"""Composition root: load configuration and wire concrete service adapters."""
from functools import partial
import os
import sys

from dotenv import load_dotenv

from .application import run_digest
from .configuration import load_content
from .gemini import choose_gemini
from .github import search_repos
from .gmail import send_gmail
from .settings import ROOT, load_settings


def main():
    load_dotenv(ROOT / ".env")
    settings = load_settings(os.environ)
    content = load_content()
    ai_generator = None
    if settings.gemini_api_key:
        ai_generator = partial(
            choose_gemini,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            instructions=content.gemini_prompt,
        )
    run_digest(
        settings, content,
        repository_source=search_repos,
        ai_generator=ai_generator,
        mail_sender=partial(send_gmail, config=settings.gmail),
    )


def entrypoint():
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0
