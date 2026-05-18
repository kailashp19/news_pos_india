from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

from app.config import MIN_POSITIVITY_SCORE
from app.db import init_db, list_articles, stats
from app.ingest import ingest_all


try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ModuleNotFoundError:
    BackgroundScheduler = None


scheduler = BackgroundScheduler() if BackgroundScheduler else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if scheduler and not scheduler.running:
        scheduler.add_job(
            ingest_all,
            "interval",
            minutes=30,
            id="feed_ingest",
            replace_existing=True,
        )
        scheduler.start()
    try:
        yield
    finally:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Positive News Feed", version="0.1.0", lifespan=lifespan)


@app.get("/")
def home() -> dict:
    return {
        "name": "Positive News Feed API",
        "docs": "/docs",
        "articles": "/api/articles",
        "refresh": "/api/refresh",
    }


@app.get("/api/articles")
def articles(
    limit: int = Query(default=50, ge=1, le=100),
    min_score: float = Query(default=MIN_POSITIVITY_SCORE, ge=-1, le=1),
) -> dict:
    return {"items": list_articles(limit=limit, min_score=min_score)}


@app.get("/api/stats")
def api_stats() -> dict:
    return stats()


@app.post("/api/refresh")
def refresh() -> dict:
    return ingest_all()
