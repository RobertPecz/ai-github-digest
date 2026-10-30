"""Coordinate the digest use case through injected service functions."""
from collections.abc import Callable

from .generation import generate_report
from .models import DigestContent, Report, Repository
from .rendering import render
from .storage import write_reports
from .validation import validate_report
from .settings import Settings

# Small callable contracts keep the use case independent of API implementations.
RepositorySource = Callable[[str, dict[str, list[str]]], tuple[list[Repository], list[str]]]
ReportGenerator = Callable[[list[Repository]], Report]
MailSender = Callable[[str, str, str], str]


def run_digest(
    settings: Settings,
    content: DigestContent,
    *,
    repository_source: RepositorySource,
    ai_generator: ReportGenerator | None = None,
    mail_sender: MailSender | None = None,
) -> str:
    repos, warnings = repository_source(settings.github_token, content.categories)
    report, engine = generate_report(
        repos, content.categories, content.fallback,
        ai_generator=ai_generator, force_fallback=settings.force_fallback,
    )
    lookup = validate_report(report, repos)
    subject, plain, rich = render(report, lookup, warnings, engine, content.rendering)
    write_reports(settings.reports_dir, report, engine, plain, rich)
    print(f'Digest generated with {engine}; {len(report["items"])} repositories.')
    if settings.dry_run:
        print("Dry run: report generated; email was not sent.")
    else:
        if mail_sender is None:
            raise RuntimeError("Missing mail sender")
        mail_sender(subject, plain, rich)
    return engine
