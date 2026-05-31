from __future__ import annotations

from email.utils import parsedate_to_datetime

import httpx
import feedparser

from app.config import (
    INDIA_KEYWORDS,
    MAX_ARTICLES_PER_FEED,
    MAX_SUMMARY_WORDS,
    MIN_POSITIVITY_SCORE,
)
from app.curated import load_curated_resources
from app.db import init_db, save_articles
from app.feeds import load_feeds
from app.models import Article, FeedSource
from app.scoring import clean_text, summarize_words
from app.wellness import (
    detect_dimension,
    is_wellness_content,
    practical_wellness_score,
)


REQUEST_HEADERS = {
    "User-Agent": "PositiveNewsFeed/0.1 (+local development; RSS reader)"
}


def normalize_date(entry: dict) -> str:
    published = entry.get("published") or entry.get("updated") or ""
    if not published:
        return ""

    try:
        return parsedate_to_datetime(published).isoformat()
    except (TypeError, ValueError):
        return published


def find_image_url(entry: dict) -> str:
    media_content = entry.get("media_content") or []
    if media_content and isinstance(media_content, list):
        first_media = media_content[0]
        if isinstance(first_media, dict):
            return first_media.get("url", "")

    media_thumbnail = entry.get("media_thumbnail") or []
    if media_thumbnail and isinstance(media_thumbnail, list):
        first_thumb = media_thumbnail[0]
        if isinstance(first_thumb, dict):
            return first_thumb.get("url", "")

    return ""


def is_india_article(title: str, summary: str, source: FeedSource) -> bool:
    if "india" in source.category.lower():
        return True

    text = f"{title} {summary}".lower()
    return any(keyword in text for keyword in INDIA_KEYWORDS)


def fetch_feed(source: FeedSource) -> list[Article]:
    response = httpx.get(
        source.url,
        headers=REQUEST_HEADERS,
        follow_redirects=True,
        timeout=20,
    )
    response.raise_for_status()

    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"Could not parse feed: {parsed.bozo_exception}")

    articles: list[Article] = []

    for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
        title = clean_text(entry.get("title", ""))
        url = entry.get("link", "")
        summary = clean_text(entry.get("summary", ""))

        if not title or not url:
            continue

        if not is_india_article(title, summary, source):
            continue

        if not is_wellness_content(title, summary, source.category):
            continue

        score = practical_wellness_score(title, summary, source.category)
        if score < MIN_POSITIVITY_SCORE:
            continue

        dimension = detect_dimension(title, summary, source.category)

        articles.append(
            Article(
                title=title,
                url=url,
                source=source.name,
                summary=summarize_words(summary, MAX_SUMMARY_WORDS),
                category=dimension,
                image_url=find_image_url(entry),
                published_at=normalize_date(entry),
                positivity_score=score,
            )
        )

    return articles


def ingest_all() -> dict:
    init_db()
    feeds = load_feeds()
    all_articles: list[Article] = load_curated_resources()
    errors: list[dict] = []

    for source in feeds:
        try:
            all_articles.extend(fetch_feed(source))
        except Exception as exc:
            errors.append({"source": source.name, "error": str(exc)})

    saved_count = save_articles(all_articles)
    return {
        "feeds_checked": len(feeds),
        "articles_matched": len(all_articles),
        "articles_saved": saved_count,
        "errors": errors,
    }


if __name__ == "__main__":
    result = ingest_all()
    print(result)
