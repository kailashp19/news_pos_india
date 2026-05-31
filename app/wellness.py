from __future__ import annotations

from app.config import WELLNESS_DIMENSIONS, WELLNESS_KEYWORDS


DIMENSION_KEYWORDS = {
    "mental": (
        "mental health",
        "stress",
        "anxiety",
        "depression",
        "mindfulness",
        "therapy",
        "counselling",
        "emotional",
        "burnout",
        "sleep",
        "habit",
    ),
    "physical": (
        "fitness",
        "physical activity",
        "exercise",
        "workout",
        "walking",
        "cycling",
        "sedentary",
        "active",
        "preventive health",
        "nutrition",
        "diet",
        "food",
        "health",
        "wellness",
        "ayurveda",
        "medicine",
        "diabetes",
        "heart",
        "walking",
    ),
    "spiritual": (
        "spiritual",
        "meditation",
        "yoga",
        "pranayama",
        "mindfulness",
        "inner",
        "purpose",
        "gratitude",
        "wisdom",
        "consciousness",
    ),
    "social": (
        "community",
        "relationship",
        "family",
        "social",
        "volunteer",
        "support group",
        "rural",
        "livelihood",
        "self-help group",
        "women",
        "youth",
    ),
    "financial": (
        "personal finance",
        "money",
        "saving",
        "investment",
        "mutual fund",
        "insurance",
        "tax",
        "budget",
        "retirement",
        "financial planning",
        "sip",
        "income",
    ),
}

ACTIONABLE_KEYWORDS = (
    "how to",
    "guide",
    "tips",
    "ways",
    "steps",
    "learn",
    "practice",
    "apply",
    "scheme",
    "checklist",
    "strategy",
    "plan",
)


def dimension_from_category(category: str) -> str:
    category_lower = category.lower()
    for dimension in WELLNESS_DIMENSIONS:
        if dimension in category_lower:
            return dimension
    return "general"


def detect_dimension(title: str, summary: str, fallback_category: str) -> str:
    category_dimension = dimension_from_category(fallback_category)
    if category_dimension != "general":
        return category_dimension

    text = f"{title} {summary}".lower()
    matches = {
        dimension: sum(keyword in text for keyword in keywords)
        for dimension, keywords in DIMENSION_KEYWORDS.items()
    }
    best_dimension = max(matches, key=matches.get)
    if matches[best_dimension] > 0:
        return best_dimension
    return "general"


def is_wellness_content(title: str, summary: str, category: str) -> bool:
    if dimension_from_category(category) != "general":
        return True

    text = f"{title} {summary}".lower()
    return any(keyword in text for keyword in WELLNESS_KEYWORDS)


def practical_wellness_score(title: str, summary: str, category: str) -> float:
    text = f"{title} {summary}".lower()
    wellness_hits = sum(keyword in text for keyword in WELLNESS_KEYWORDS)
    action_hits = sum(keyword in text for keyword in ACTIONABLE_KEYWORDS)
    dimension = detect_dimension(title, summary, category)

    score = 0.25
    if dimension != "general":
        score += 0.2
    score += min(wellness_hits, 5) * 0.03
    score += min(action_hits, 3) * 0.12
    return round(min(score, 0.99), 3)
