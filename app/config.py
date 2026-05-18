from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "positive_news.sqlite3"
FEEDS_PATH = BASE_DIR / "feeds.json"
STATIC_DIR = BASE_DIR / "static"

MIN_POSITIVITY_SCORE = 0.55
MAX_ARTICLES_PER_FEED = 30
MAX_SUMMARY_WORDS = 100

INDIA_KEYWORDS = (
    "india",
    "indian",
    "bharat",
    "new delhi",
    "delhi",
    "mumbai",
    "bengaluru",
    "bangalore",
    "chennai",
    "kolkata",
    "hyderabad",
    "pune",
    "ahmedabad",
    "kerala",
    "tamil nadu",
    "karnataka",
    "maharashtra",
    "gujarat",
    "rajasthan",
    "uttar pradesh",
    "madhya pradesh",
    "telangana",
    "andhra pradesh",
    "odisha",
    "punjab",
    "haryana",
    "bihar",
    "assam",
    "jharkhand",
    "uttarakhand",
    "himachal",
    "goa",
)
