from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    category: str = "general"


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    source: str
    summary: str = ""
    category: str = "general"
    image_url: str = ""
    published_at: str = ""
    positivity_score: float = 0.0
