from __future__ import annotations

from app.config import MIN_POSITIVITY_SCORE
from app.curated import TRUSTED_RECOMMENDATION_SOURCES, load_curated_resources
from app.db import list_articles


DIMENSIONS = ("mental", "physical", "social", "financial", "spiritual")

DIMENSION_LABELS = {
    "mental": "Mental wellness",
    "physical": "Physical wellness",
    "social": "Social wellness",
    "financial": "Financial wellness",
    "spiritual": "Spiritual wellness",
}

TRUSTED_SOURCE_SET = set(TRUSTED_RECOMMENDATION_SOURCES)

INSIGHTS = {
    "mental": [
        "Tiny, repeatable calming habits are often easier to keep than ambitious routines.",
        "A short pause can be useful even when you do not feel ready for deeper reflection.",
    ],
    "physical": [
        "Gentle movement can include seated stretches, household movement, or a short walk if it feels comfortable.",
        "Rest is also a valid wellness action when energy is low.",
    ],
    "social": [
        "Connection does not need to be intense; a small kind message can be enough for today.",
        "Choosing quiet time is still a social boundary, not a failure to connect.",
    ],
    "financial": [
        "Financial clarity can start with one tiny task, such as reading one trusted resource or checking one due date.",
        "Good money habits are usually built through small, repeatable decisions rather than big one-time changes.",
    ],
    "spiritual": [
        "Grounding can be secular, reflective, spiritual, or values-based depending on what feels safe to you.",
        "A brief moment of gratitude or quiet can count as a complete practice.",
    ],
}

FOCUS_COPY = {
    "mental": "make the day feel calmer",
    "physical": "support your body gently",
    "social": "keep connection manageable",
    "financial": "build a little money clarity",
    "spiritual": "feel more grounded",
}


def normalize_answers(answers: dict) -> dict:
    return {str(key): str(value) for key, value in answers.items() if value is not None}


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


def dimension_priority(answers: dict, dimension: str) -> int:
    priority = 1

    if dimension == "mental":
        if answers.get("mental_support") != "Not sure":
            priority += 2
        if answers.get("mental_effort") in {"Tiny action", "Short action"}:
            priority += 1
    elif dimension == "physical":
        if answers.get("physical_state") in {"Tired", "Stiff", "Restless"}:
            priority += 2
        if answers.get("movement_comfort") != "No movement today":
            priority += 1
    elif dimension == "social":
        if answers.get("connection_need") not in {"Quiet time alone", "Not sure"}:
            priority += 2
        if answers.get("social_comfort") != "No social task today":
            priority += 1
    elif dimension == "financial":
        if answers.get("money_support") == "Avoid money today":
            return 0
        if answers.get("money_support") != "Not sure":
            priority += 2
        if answers.get("money_action") != "Read only":
            priority += 1
    elif dimension == "spiritual":
        if answers.get("grounding_need") != "Not sure":
            priority += 2
        if answers.get("spiritual_practice") != "Read an insight":
            priority += 1

    return priority


def action_for_dimension(answers: dict, dimension: str) -> str:
    if dimension == "mental":
        avoid = answers.get("mental_avoid")
        effort = answers.get("mental_effort")
        if avoid == "Breathing exercises":
            return "Read one calming paragraph and name one thing that feels manageable."
        if avoid == "Journaling":
            return "Take a quiet 30-second pause without writing anything down."
        if effort == "Reading only":
            return "Read one trusted mental wellness tip and stop there."
        return "Do one tiny calming action: pause, unclench your jaw, and soften your shoulders."

    if dimension == "physical":
        boundary = answers.get("physical_boundary")
        movement = answers.get("movement_comfort")
        if boundary in {"Avoid physical activity", "Keep it seated"} or movement == "No movement today":
            return "Choose a body-friendly rest action: sit comfortably and relax your shoulders for 30 seconds."
        if boundary == "Avoid standing":
            return "Try one seated stretch if it feels comfortable."
        if movement == "Short walk":
            return "Take a very short easy walk, then stop before it becomes effortful."
        return "Try one minute of gentle movement only if it feels comfortable."

    if dimension == "social":
        comfort = answers.get("social_comfort")
        privacy = answers.get("privacy_preference")
        if comfort == "No social task today" or privacy == "Keep this private":
            return "Do a private connection action: think of one person you appreciate without messaging them."
        if comfort == "Send a simple message":
            return "Send one low-pressure message, such as 'thinking of you today'."
        if comfort == "Talk to a trusted person":
            return "Plan one short check-in with someone you trust."
        return "Notice one relationship that feels supportive, without needing to act on it."

    if dimension == "financial":
        boundary = answers.get("money_boundary")
        action = answers.get("money_action")
        if answers.get("money_support") == "Avoid money today":
            return "Skip money tasks today and read one neutral financial education insight only if you want to."
        if boundary in {"No numbers today", "No decisions today"} or action == "Read only":
            return "Read one trusted financial education tip without making any money decision."
        if boundary == "No investment content":
            return "Check one simple money admin item, such as a bill date or account notification."
        if action == "List recent spending":
            return "List only three recent spends, without judging them."
        if action == "Save a small amount":
            return "Set aside a small amount only if it already fits your budget."
        return "Do one tiny financial clarity task that does not require a big decision."

    if dimension == "spiritual":
        boundary = answers.get("spiritual_boundary")
        practice = answers.get("spiritual_practice")
        if boundary == "Avoid religious content":
            return "Use a secular grounding action: name one value you want to carry today."
        if boundary == "Avoid meditation":
            return "Read one grounding insight and take a normal, comfortable pause."
        if boundary == "Avoid deep purpose questions":
            return "Notice one small thing you are grateful for right now."
        if practice == "Short silence":
            return "Sit quietly for 30 seconds, with no need to meditate."
        if practice == "One sentence reflection":
            return "Write one sentence: 'Today, I want to move gently toward...'"
        return "Read one grounding insight and choose one word for your day."

    return "Read one trusted wellness tip and choose the smallest useful next step."


def reason_for_dimension(answers: dict, dimension: str) -> str:
    if dimension == "mental":
        return (
            f"Matched to your preference for {answers.get('mental_support', 'gentle support').lower()} "
            f"with {answers.get('mental_effort', 'a manageable action').lower()}."
        )
    if dimension == "physical":
        return (
            f"Matched to your body feeling {answers.get('physical_state', 'okay').lower()} "
            f"and your movement comfort: {answers.get('movement_comfort', 'either is fine').lower()}."
        )
    if dimension == "social":
        return (
            f"Matched to your connection preference: {answers.get('connection_need', 'not sure').lower()} "
            f"and privacy preference: {answers.get('privacy_preference', 'keep this private').lower()}."
        )
    if dimension == "financial":
        return (
            f"Matched to your money support preference: {answers.get('money_support', 'not sure').lower()} "
            f"with boundary: {answers.get('money_boundary', 'no preference').lower()}."
        )
    if dimension == "spiritual":
        return (
            f"Matched to what feels grounding: {answers.get('grounding_need', 'not sure').lower()} "
            f"and boundary: {answers.get('spiritual_boundary', 'no preference').lower()}."
        )
    return "Matched to your stated preferences and boundaries."


def recommendation_groups(answers: dict, limit: int) -> list[dict]:
    ranked = sorted(
        DIMENSIONS,
        key=lambda dimension: dimension_priority(answers, dimension),
        reverse=True,
    )
    ranked = [dimension for dimension in ranked if dimension_priority(answers, dimension) > 0]

    groups = []
    for dimension in ranked:
        articles = trusted_articles(1, dimension)
        groups.append(
            {
                "dimension": dimension,
                "title": DIMENSION_LABELS[dimension],
                "action": action_for_dimension(answers, dimension),
                "insight": INSIGHTS[dimension][0],
                "reason": reason_for_dimension(answers, dimension),
                "articles": articles,
            }
        )
        if len(groups) >= limit:
            break
    return groups


def recommend(answers: dict, limit: int = 5) -> dict:
    answers = normalize_answers(answers)
    groups = recommendation_groups(answers, limit=max(3, min(limit, 5)))
    focus_parts = [FOCUS_COPY[group["dimension"]] for group in groups[:2]]
    today_focus = " and ".join(focus_parts) if focus_parts else "choose one gentle next step"
    plan = [group["action"] for group in groups[:3]]
    articles = []
    seen_urls = set()
    for group in groups:
        for article in group["articles"]:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

    return {
        "today_focus": today_focus,
        "plan": plan,
        "groups": groups,
        "articles": articles[:6],
        "source_policy": "Only trusted sources such as WHO, United Nations, UNICEF, NIMHANS, IIMs, Art of Living, RBI, and SEBI are used for recommendations.",
    }
