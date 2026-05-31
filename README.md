# India Holistic Wellness Feed

A Python-first MVP that fetches practical India-focused holistic wellness resources, classifies them into mental, physical, spiritual, social, and financial wellness, stores them in SQLite, serves them through FastAPI, and displays 100-word summaries in Streamlit.

## Setup

Use Python 3.11 or 3.12. This project already has a working Python 3.12 environment in `.venv312`; prefer that over `.venv`, which may point at Python 3.14.

```bash
cd /Users/kailashpatel/Documents/positive_news_feed
source .venv312/bin/activate
pip install -r requirements.txt
```

## Run Once To Fetch Latest Wellness Resources

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

## User Accounts

The Streamlit app now includes local account management:

- Register with a valid email address and password.
- Log in with the registered email and password.
- Wrong passwords show `Password does not match.`
- Forgot Password generates a short-lived reset code.
- Each user gets a stable avatar at registration.
- Logged-in users can save articles and revisit them later from Saved Articles.

For local development, password reset codes are displayed in the app when SMTP is not configured. To send real password reset emails, set these environment variables before starting Streamlit:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=your-smtp-username
export SMTP_PASSWORD=your-smtp-password
export SMTP_FROM=no-reply@example.com
```

In production, use an email provider such as SendGrid, Amazon SES, Mailgun, Postmark, or your SMTP provider. Keep these values in environment variables or a secrets manager, not in source code.

Passwords are not stored directly. They are salted and hashed with Python's standard `hashlib.pbkdf2_hmac`, and user records are stored in the same SQLite database as the articles.

If you decide to run FastAPI on a different port, pass that URL to Streamlit:

```bash
API_BASE_URL=http://127.0.0.1:8002 streamlit run streamlit_app.py
```

## Important Files

- `feeds.json`: India-focused wellness RSS/Google News sources for mental, physical, spiritual, social, and financial health.
- `app/curated.py`: credible static wellness resources from WHO, WHO India, NIMHANS, UNICEF India, and IIM wellness pages.
- `app/ingest.py`: fetch, normalize, categorize, score, and save resources.
- `app/wellness.py`: wellness dimension detection and practical relevance scoring.
- `app/auth.py`: registration, login, password hashing, reset-code logic, avatars, and saved articles.
- `app/classifier.py`: older scikit-learn positive-news classifier retained for reference.
- `app/scoring.py`: shared text cleanup helper.
- `app/db.py`: SQLite schema and queries.
- `app/main.py`: FastAPI backend.
- `streamlit_app.py`: Streamlit frontend.

## Notes

This app uses RSS and public URL endpoints that do not require authentication. Check each publisher's terms before using their content in a public or commercial product.
