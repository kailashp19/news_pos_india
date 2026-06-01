from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from app.config import MIN_POSITIVITY_SCORE, WELLNESS_DIMENSIONS
from app.db import init_db, list_articles, stats
from app.ingest import ingest_all
from app.recommendations import recommend


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


app = FastAPI(title="India Holistic Wellness Feed", version="0.2.0", lifespan=lifespan)


class WellnessRecommendationRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
    limit: int = Field(default=6, ge=1, le=12)


@app.get("/")
def home() -> dict:
    return {
        "name": "India Holistic Wellness Feed API",
        "docs": "/docs",
        "articles": "/api/articles",
        "refresh": "/api/refresh",
        "dimensions": WELLNESS_DIMENSIONS,
    }


@app.get("/api/articles")
def articles(
    limit: int = Query(default=50, ge=1, le=100),
    min_score: float = Query(default=MIN_POSITIVITY_SCORE, ge=-1, le=1),
    dimension: str = Query(default="all"),
) -> dict:
    dimension = dimension.lower()
    if dimension != "all" and dimension not in WELLNESS_DIMENSIONS:
        dimension = "all"
    return {"items": list_articles(limit=limit, min_score=min_score, dimension=dimension)}


@app.get("/api/stats")
def api_stats(dimension: str = Query(default="all")) -> dict:
    dimension = dimension.lower()
    if dimension != "all" and dimension not in WELLNESS_DIMENSIONS:
        dimension = "all"
    return stats(dimension=dimension)


@app.post("/api/recommendations")
def recommendations(payload: WellnessRecommendationRequest) -> dict:
    return recommend(payload.answers, limit=payload.limit)


@app.post("/api/refresh")
def refresh() -> dict:
    return ingest_all()
