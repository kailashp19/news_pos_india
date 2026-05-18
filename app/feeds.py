from __future__ import annotations

import json

from app.config import FEEDS_PATH
from app.models import FeedSource


def load_feeds() -> list[FeedSource]:
    with FEEDS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        FeedSource(
            name=item["name"],
            url=item["url"],
            category=item.get("category", "general"),
        )
        for item in data
    ]
