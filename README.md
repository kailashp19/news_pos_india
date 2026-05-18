# Positive India News Feed

A Python-first MVP that fetches latest India-focused RSS/news feeds, classifies positive stories with scikit-learn, stores them in SQLite, serves them through FastAPI, and displays 100-word summaries in Streamlit.

## Setup

Use Python 3.11 or 3.12. This project already has a working Python 3.12 environment in `.venv312`; prefer that over `.venv`, which may point at Python 3.14.

```bash
cd /Users/kailashpatel/Documents/positive_news_feed
source .venv312/bin/activate
pip install -r requirements.txt
```

## Run Once To Fetch Latest India Articles

```bash
python -m app.ingest
```

## Start The FastAPI Backend

Keep this terminal open:

```bash
cd /Users/kailashpatel/Documents/positive_news_feed
source .venv312/bin/activate
python -m uvicorn app.main:app --reload --port 8010
```

API docs:

```text
http://127.0.0.1:8010/docs
```

## Start The Streamlit Frontend

Open a second terminal and keep the FastAPI terminal running:

```bash
cd /Users/kailashpatel/Documents/positive_news_feed
source .venv312/bin/activate
streamlit run streamlit_app.py
```

Frontend:

```text
http://localhost:8501
```

If you decide to run FastAPI on a different port, pass that URL to Streamlit:

```bash
API_BASE_URL=http://127.0.0.1:8002 streamlit run streamlit_app.py
```

## Important Files

- `feeds.json`: India-focused RSS/Google News sources to fetch.
- `app/ingest.py`: fetch, normalize, score, and save articles.
- `app/classifier.py`: scikit-learn classifier.
- `app/scoring.py`: shared text cleanup helper.
- `app/db.py`: SQLite schema and queries.
- `app/main.py`: FastAPI backend.
- `streamlit_app.py`: Streamlit frontend.

## Notes

This app uses RSS and public URL endpoints that do not require authentication. Check each publisher's terms before using their content in a public or commercial product.
