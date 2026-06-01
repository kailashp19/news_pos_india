from __future__ import annotations

from app.config import MIN_POSITIVITY_SCORE
from app.curated import TRUSTED_RECOMMENDATION_SOURCES, load_curated_resources
from app.db import list_articles


INTEREST_TO_DIMENSION = {
    "Mental calm": "mental",
    "Physical energy": "physical",
    "Relationships": "social",
    "Money habits": "financial",
    "Purpose and meaning": "spiritual",
    "General positivity": "all",
}

ENERGY_SCORE = {
    "Very low": 8,
    "Low": 14,
    "Medium": 22,
    "High": 30,
}

MOOD_SCORE = {
    "Calm": 24,
    "Okay": 20,
    "Tired": 14,
    "Stressed": 12,
    "Low energy": 10,
    "Prefer not to say": 18,
}

TIME_SCORE = {
    "1 minute": 10,
    "3 minutes": 14,
    "5 minutes": 18,
    "10 minutes": 24,
    "Just reading today": 16,
}

SUPPORT_FOCUS = {
    "Something calming": "Reduce stress",
    "Something motivating": "Build momentum",
    "Something reflective": "Create clarity",
    "Something practical": "Take one useful step",
    "Something light and easy": "Keep wellness simple",
    "Not sure": "Choose a gentle starting point",
}

INTEREST_FOCUS = {
    "Mental calm": "mental calm",
    "Physical energy": "physical energy",
    "Relationships": "stronger relationships",
    "Money habits": "financial clarity",
    "Purpose and meaning": "purpose and meaning",
    "General positivity": "daily positivity",
}

ACTION_COPY = {
    "Reading": "Read one short article",
    "Reflection": "Notice one thing that helped you today",
    "Breathing": "Take five slow, comfortable breaths",
    "Journaling": "Write one sentence about what you need today",
    "Light movement": "Try one minute of easy stretching if it feels okay",
    "Social connection": "Send one kind message",
    "Financial awareness": "Check one small money habit",
}

AVOIDANCE_TO_ACTION = {
    "Physical activity": "Light movement",
    "Emotional reflection": "Reflection",
    "Breathing exercises": "Breathing",
    "Financial tasks": "Financial awareness",
    "Social tasks": "Social connection",
}

TRUSTED_SOURCE_SET = set(TRUSTED_RECOMMENDATION_SOURCES)


def normalize_answers(answers: dict) -> dict:
    return {str(key): str(value) for key, value in answers.items() if value is not None}


def wellness_score(answers: dict) -> int:
    score = 28
    score += MOOD_SCORE.get(answers.get("feeling"), 18)
    score += ENERGY_SCORE.get(answers.get("energy"), 18)
    score += TIME_SCORE.get(answers.get("time"), 16)
    if answers.get("no_movement") == "Yes":
        score -= 4
    if answers.get("avoid") and answers.get("avoid") != "No preference":
        score -= 2
    return max(35, min(score, 92))


def action_allowed(action_type: str, answers: dict) -> bool:
    avoid = answers.get("avoid", "No preference")
    if AVOIDANCE_TO_ACTION.get(avoid) == action_type:
        return False
    if answers.get("no_movement") == "Yes" and action_type == "Light movement":
        return False
    return True


def choose_small_action(answers: dict) -> str:
    preferred = answers.get("action", "Reading")
    if action_allowed(preferred, answers):
        return ACTION_COPY.get(preferred, ACTION_COPY["Reading"])

    for action_type in ("Reading", "Journaling", "Reflection", "Financial awareness"):
        if action_allowed(action_type, answers):
            return ACTION_COPY[action_type]
    return ACTION_COPY["Reading"]


def recommendation_reason(answers: dict) -> str:
    feeling = answers.get("feeling", "your current state").lower()
    time = answers.get("time", "a short amount of time").lower()
    action = answers.get("action", "reading").lower()
    avoid = answers.get("avoid", "No preference")

    reason = (
        f"Matched to your {feeling} mood, {time} window, and preference for {action}."
    )
    if avoid != "No preference":
        reason += f" It avoids {avoid.lower()} today."
    return reason


def article_action(answers: dict) -> str:
    if answers.get("time") == "Just reading today":
        return "Read the quick summary and stop there if that feels like enough."
    if answers.get("energy") in {"Very low", "Low"}:
        return "Take one tiny step from this article for one minute."
    return choose_small_action(answers)


def article_to_dict(article) -> dict:
    return {
        "id": None,
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "summary": article.summary,
        "category": article.category,
        "image_url": article.image_url,
        "published_at": article.published_at,
        "positivity_score": article.positivity_score,
        "created_at": "",
    }


def trusted_articles(limit: int, dimension: str) -> list[dict]:
    articles = [
        article
        for article in list_articles(
            limit=max(limit * 4, 24),
            min_score=MIN_POSITIVITY_SCORE,
            dimension=dimension,
        )
        if article.get("source") in TRUSTED_SOURCE_SET
    ]

    curated = [
        article_to_dict(article)
        for article in load_curated_resources()
        if article.source in TRUSTED_SOURCE_SET
        and (dimension == "all" or article.category == dimension)
    ]

    seen = {article["url"] for article in articles}
    articles.extend(article for article in curated if article["url"] not in seen)
    return sorted(
        articles,
        key=lambda article: (
            article.get("positivity_score", 0),
            article.get("published_at", ""),
            article.get("title", ""),
        ),
        reverse=True,
    )[:limit]


def recommend(answers: dict, limit: int = 6) -> dict:
    answers = normalize_answers(answers)
    interest = answers.get("interest", "General positivity")
    dimension = INTEREST_TO_DIMENSION.get(interest, "all")
    focus_a = SUPPORT_FOCUS.get(answers.get("support"), "Choose a gentle starting point")
    focus_b = INTEREST_FOCUS.get(interest, "daily positivity")

    articles = trusted_articles(max(limit * 2, 12), dimension)
    if len(articles) < limit and dimension != "all":
        seen = {article["url"] for article in articles}
        articles.extend(
            article
            for article in trusted_articles(limit * 2, "all")
            if article["url"] not in seen
        )

    action = choose_small_action(answers)
    no_physical = (
        answers.get("no_movement") == "Yes"
        or answers.get("avoid") == "Physical activity"
        or answers.get("energy") in {"Very low", "Low"}
    )
    plan = [
        "Read one article",
        action,
        "Reflect for 30 seconds",
    ]
    if no_physical:
        plan[1] = action if "stretching" not in action.lower() else "Complete one non-physical small action"

    return {
        "today_focus": f"{focus_a} and build {focus_b}",
        "wellness_score": wellness_score(answers),
        "plan": plan,
        "reason": recommendation_reason(answers),
        "article_action": article_action(answers),
        "dimension": dimension,
        "source_policy": "Only trusted sources such as WHO, United Nations, UNICEF, NIMHANS, IIMs, Art of Living, RBI, and SEBI are used for recommendations.",
        "articles": articles[:limit],
    }
