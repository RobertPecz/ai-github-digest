"""Data contracts shared by configuration, services and report processing."""
from dataclasses import dataclass
from typing import TypedDict


class Repository(TypedDict):
    name: str
    url: str
    description: str
    stars: int
    last_push: str
    created_at: str
    language: str | None
    license: str
    topics: list[str]
    category: str
    signals: list[str]


class ReportItem(TypedDict):
    name: str
    why: str
    use_case: str
    business: str
    risk: str
    difficulty: str


class Recommendation(TypedDict):
    name: str
    first_step: str


class Report(TypedDict):
    intro: str
    items: list[ReportItem]
    top_three: list[Recommendation]


class FallbackContent(TypedDict):
    examples: dict[str, str]
    default_use_case: str
    why: str
    business: str
    risk: str
    difficulty: str
    intro: str


class RenderingContent(TypedDict):
    subject: str
    source: str
    missing_description: str
    fields: list[list[str]]
    top_three: str
    plain_warning: str
    html_warning: str
    disclaimer: str


@dataclass(frozen=True)
class DigestContent:
    categories: dict[str, list[str]]
    fallback: FallbackContent
    rendering: RenderingContent
    gemini_prompt: str
