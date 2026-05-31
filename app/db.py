from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import (
    DATA_DIR,
    DB_PATH,
    MAX_ARTICLES_PER_SOURCE,
    MAX_SUMMARY_WORDS,
    MIN_POSITIVITY_SCORE,
    WELLNESS_DIMENSIONS,
    WELLNESS_KEYWORDS,
)
from app.curated import curated_source_names
from app.feeds import load_feeds
from app.models import Article
from app.scoring import summarize_words
from app.wellness import practical_wellness_score


def wellness_filter_sql() -> tuple[str, list[str]]:
    category_filters = " OR ".join("LOWER(category) = ?" for _ in WELLNESS_DIMENSIONS)
    keyword_filters = " OR ".join(
        ["LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(source) LIKE ?"]
        * len(WELLNESS_KEYWORDS)
    )
    params = [
        *WELLNESS_DIMENSIONS,
        *[
        f"%{keyword}%"
        for keyword in WELLNESS_KEYWORDS
        for _ in range(3)
        ],
    ]
    return f"{category_filters} OR {keyword_filters}", params


def current_sources_sql() -> tuple[str, list[str]]:
    sources = [feed.name for feed in load_feeds()] + curated_source_names()
    placeholders = ", ".join("?" for _ in sources)
    return f"source IN ({placeholders})", sources


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'general',
                image_url TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                positivity_score REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_articles_score_created
            ON articles (positivity_score DESC, created_at DESC)
            """
        )


def save_articles(articles: list[Article]) -> int:
    if not articles:
        return 0

    with connect() as connection:
        before = connection.total_changes
        connection.executemany(
            """
            INSERT OR IGNORE INTO articles (
                title,
                url,
                source,
                summary,
                category,
                image_url,
                published_at,
                positivity_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                source = excluded.source,
                summary = excluded.summary,
                category = excluded.category,
                image_url = excluded.image_url,
                published_at = excluded.published_at,
                positivity_score = excluded.positivity_score
            """,
            [
                (
                    article.title,
                    article.url,
                    article.source,
                    article.summary,
                    article.category,
                    article.image_url,
                    article.published_at,
                    article.positivity_score,
                )
                for article in articles
            ],
        )
        return connection.total_changes - before


def list_articles(
    limit: int = 50,
    min_score: float = 0.0,
    dimension: str = "all",
) -> list[dict]:
    with connect() as connection:
        wellness_filters, wellness_params = wellness_filter_sql()
        source_filters, source_params = current_sources_sql()
        dimension_filter = ""
        dimension_params: tuple[str, ...] = ()
        if dimension in WELLNESS_DIMENSIONS:
            dimension_filter = "AND LOWER(category) = ?"
            dimension_params = (dimension,)
        rows = connection.execute(
            f"""
            SELECT *
            FROM (
                SELECT
                    id,
                    title,
                    url,
                    source,
                    summary,
                    category,
                    image_url,
                    published_at,
                    positivity_score,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY source
                        ORDER BY published_at DESC, created_at DESC
                    ) AS source_rank
                FROM articles
                WHERE ({wellness_filters})
                  AND {source_filters}
                  {dimension_filter}
            )
            WHERE source_rank <= ?
            ORDER BY published_at DESC, created_at DESC
            LIMIT ?
            """,
            (
                *wellness_params,
                *source_params,
                *dimension_params,
                MAX_ARTICLES_PER_SOURCE,
                limit * 4,
            ),
        ).fetchall()
        articles = [dict(row) for row in rows]
        for article in articles:
            article["summary"] = summarize_words(
                article.get("summary", ""),
                MAX_SUMMARY_WORDS,
            )
            article["positivity_score"] = practical_wellness_score(
                article.get("title", ""),
                article.get("summary", ""),
                article.get("category", ""),
            )

        return [
            article
            for article in articles
            if article["positivity_score"] >= min_score
        ][:limit]


def stats(dimension: str = "all") -> dict:
    with connect() as connection:
        wellness_filters, wellness_params = wellness_filter_sql()
        source_filters, source_params = current_sources_sql()
        dimension_filter = ""
        dimension_params: tuple[str, ...] = ()
        if dimension in WELLNESS_DIMENSIONS:
            dimension_filter = "AND LOWER(category) = ?"
            dimension_params = (dimension,)
        rows = connection.execute(
            f"""
            SELECT
                title,
                summary,
                category,
                created_at
            FROM articles
            WHERE {wellness_filters}
              AND {source_filters}
              {dimension_filter}
            """,
            (*wellness_params, *source_params, *dimension_params),
        ).fetchall()
        scores = [
            practical_wellness_score(row["title"], row["summary"], row["category"])
            for row in rows
        ]
        scores = [score for score in scores if score >= MIN_POSITIVITY_SCORE]
        last_saved_at = max((row["created_at"] for row in rows), default=None)
        average_score = round(sum(scores) / len(scores), 3) if scores else None
        return {
            "total_articles": len(scores),
            "average_score": average_score,
            "last_saved_at": last_saved_at,
        }
