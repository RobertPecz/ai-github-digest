"""Render a validated report as plain text and escaped HTML."""
import html
from datetime import date, datetime, timezone

from .models import RenderingContent, Report, Repository


def render(
    report: Report, lookup: dict[str, Repository], warnings: list[str],
    engine: str, content: RenderingContent, *, today: date | None = None,
) -> tuple[str, str, str]:
    now = today or datetime.now(timezone.utc).date()
    subject = content["subject"].format(date=now.isoformat())
    source = f'{content["source"]}: {engine}'
    lines = [subject, source, "", report["intro"], ""]
    chunks = [
        f"<h1>{html.escape(subject)}</h1>",
        f"<p>{html.escape(source)}</p>",
        f'<p>{html.escape(report["intro"])}</p>',
    ]
    for index, item in enumerate(report["items"], 1):
        repo = lookup[item["name"]]
        desc = repo["description"] or content["missing_description"]
        meta = (
            f"{repo['category']} · ★ {repo['stars']} · {repo['language'] or 'n/a'} · "
            f"license: {repo['license']} · last push: {repo['last_push'][:10]}"
        )
        fields = [(label, item[key]) for key, label in content["fields"]]
        lines.extend([f"{index}. {repo['name']}", repo["url"], desc, meta])
        lines.extend(f"{label}: {value}" for label, value in fields)
        lines.append("")
        chunks.append(
            f'<h2>{index}. <a href="{html.escape(repo["url"], quote=True)}">{html.escape(repo["name"])}</a></h2>'
        )
        chunks.extend(
            [
                f"<p>{html.escape(desc)}</p>",
                f"<p><small>{html.escape(meta)}</small></p>",
            ]
        )
        chunks.append(
            "<ul>"
            + "".join(
                f"<li><b>{html.escape(k)}:</b> {html.escape(v)}</li>" for k, v in fields
            )
            + "</ul>"
        )
    lines += [content["top_three"]]
    chunks += [f'<h2>{html.escape(content["top_three"])}</h2><ol>']
    for recommendation in report["top_three"]:
        lines.append(f"{recommendation['name']}: {recommendation['first_step']}")
        chunks.append(
            f'<li><b>{html.escape(recommendation["name"])}</b>: '
            f'{html.escape(recommendation["first_step"])}</li>'
        )
    chunks.append("</ol>")
    if warnings:
        lines.extend(["", content["plain_warning"]])
        chunks.append(f'<p><i>{html.escape(content["html_warning"])}</i></p>')
    disclaimer = content["disclaimer"]
    lines.extend(["", disclaimer])
    chunks.append(f"<p><small>{html.escape(disclaimer)}</small></p>")
    return (
        subject,
        "\n".join(lines),
        "<html><body>" + "\n".join(chunks) + "</body></html>",
    )
