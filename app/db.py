from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import (
    DATA_DIR,
    DB_PATH,
    INDIA_KEYWORDS,
    MAX_ARTICLES_PER_SOURCE,
    MAX_SUMMARY_WORDS,
)
from app.feeds import load_feeds
from app.models import Article
from app.scoring import summarize_words


def india_filter_sql() -> tuple[str, list[str]]:
    filters = "LOWER(category) LIKE '%india%' OR " + " OR ".join(
        ["LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(source) LIKE ?"]
        * len(INDIA_KEYWORDS)
    )
    params = [
        f"%{keyword}%"
        for keyword in INDIA_KEYWORDS
        for _ in range(3)
    ]
    return filters, params


def current_sources_sql() -> tuple[str, list[str]]:
    sources = [feed.name for feed in load_feeds()]
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


def list_articles(limit: int = 50, min_score: float = 0.0) -> list[dict]:
    with connect() as connection:
        india_filters, keyword_params = india_filter_sql()
        source_filters, source_params = current_sources_sql()
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
                WHERE positivity_score >= ?
                  AND ({india_filters})
                  AND {source_filters}
            )
            WHERE source_rank <= ?
            ORDER BY published_at DESC, created_at DESC
            LIMIT ?
            """,
            (
                min_score,
                *keyword_params,
                *source_params,
                MAX_ARTICLES_PER_SOURCE,
                limit,
            ),
        ).fetchall()
        articles = [dict(row) for row in rows]
        for article in articles:
            article["summary"] = summarize_words(
                article.get("summary", ""),
                MAX_SUMMARY_WORDS,
            )
        return articles


def stats() -> dict:
    with connect() as connection:
        india_filters, keyword_params = india_filter_sql()
        source_filters, source_params = current_sources_sql()
        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_articles,
                ROUND(AVG(positivity_score), 3) AS average_score,
                MAX(created_at) AS last_saved_at
            FROM articles
            WHERE {india_filters}
              AND {source_filters}
            """,
            (*keyword_params, *source_params),
        ).fetchone()
        return dict(row)
