from __future__ import annotations

import os
from datetime import datetime

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")


st.set_page_config(
    page_title="Positive India News Feed",
    layout="wide",
)


def format_date(value: str) -> str:
    if not value:
        return ""

    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return value


def summarize_words(value: str, max_words: int = 100) -> str:
    words = (value or "").split()
    if len(words) <= max_words:
        return " ".join(words)

    return " ".join(words[:max_words]).rstrip(" ,;:") + "..."


def api_get(url: str, **kwargs) -> dict:
    response = requests.get(url, timeout=20, **kwargs)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=120)
def fetch_articles(min_score: float, limit: int) -> list[dict]:
    response = api_get(
        f"{API_BASE_URL}/api/articles",
        params={"min_score": min_score, "limit": limit},
    )
    return response.get("items", [])


@st.cache_data(ttl=120)
def fetch_stats() -> dict:
    return api_get(f"{API_BASE_URL}/api/stats")


def refresh_feed() -> dict:
    response = requests.post(f"{API_BASE_URL}/api/refresh", timeout=60)
    response.raise_for_status()
    fetch_articles.clear()
    fetch_stats.clear()
    return response.json()


def show_api_error(exc: Exception) -> None:
    response = getattr(exc, "response", None)
    if response is not None:
        st.error(
            "FastAPI returned an error. Check the backend terminal for the "
            f"traceback. Status: {response.status_code} {response.reason}"
        )
        return

    st.error(
        "FastAPI is not reachable. Start it with: "
        "`.venv312/bin/python -m uvicorn app.main:app --reload --port 8010`"
    )


st.title("Positive India News Feed")

with st.sidebar:
    st.header("Filters")
    min_score = st.slider(
        "Minimum positive probability",
        min_value=0.5,
        max_value=0.95,
        value=0.55,
        step=0.05,
    )
    limit = st.slider("Articles", min_value=10, max_value=100, value=50, step=10)

    if st.button("Refresh feeds", type="primary", use_container_width=True):
        with st.spinner("Fetching and classifying news..."):
            try:
                result = refresh_feed()
                st.success(
                    f"Saved {result['articles_saved']} new articles from "
                    f"{result['feeds_checked']} feeds."
                )
                if result["errors"]:
                    st.warning("Some sources were unavailable or rate-limited.")
            except (requests.RequestException, ValueError) as exc:
                show_api_error(exc)

try:
    stats = fetch_stats()
    articles = fetch_articles(min_score=min_score, limit=limit)
except (requests.RequestException, ValueError) as exc:
    show_api_error(exc)
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Saved articles", stats.get("total_articles") or 0)
col2.metric("Average positive probability", stats.get("average_score") or 0)
col3.metric("Showing", len(articles))
st.caption(f"Backend: {API_BASE_URL}")

st.divider()

if not articles:
    st.info("No India-focused articles match this score yet. Try lowering the threshold or refreshing feeds.")
else:
    for article in articles:
        with st.container(border=True):
            st.subheader(article["title"])

            if article["summary"]:
                st.write(summarize_words(article["summary"], 100))

            meta = [
                f"Source: {article['source']}",
                f"Category: {article['category']}",
                f"Positive probability: {article['positivity_score']:.2f}",
            ]
            published = format_date(article["published_at"])
            if published:
                meta.append(f"Published: {published}")

            st.caption(" | ".join(meta))
            st.link_button("Read full article", article["url"])
