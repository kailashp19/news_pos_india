from __future__ import annotations

from collections import Counter, defaultdict

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

SOURCE_PRIORITY = {
    "WHO": 1.0,
    "WHO India": 1.0,
    "United Nations": 0.96,
    "UNICEF India": 0.94,
    "NIMHANS": 0.92,
    "IIM Ahmedabad": 0.9,
    "IIM Bangalore": 0.9,
    "Reserve Bank of India": 0.88,
    "SEBI": 0.88,
    "Art of Living": 0.84,
}

TAG_KEYWORDS = {
    "calm": ("stress", "calm", "relax", "breath", "mindfulness", "mental"),
    "uplift": ("happiness", "positive", "kind", "self-talk", "well-being"),
    "focus": ("focus", "routine", "habit", "mindfulness", "attention"),
    "sleep": ("sleep", "rest", "routine", "bedtime", "wind down"),
    "tiny": ("few minutes", "short", "simple", "daily", "habit"),
    "read-only": ("guide", "tips", "education", "awareness", "learn"),
    "seated": ("seated", "rest", "gentle", "comfortable", "activity"),
    "movement": ("activity", "walking", "movement", "exercise", "active"),
    "rest": ("rest", "sleep", "relax", "recover", "routine"),
    "private": ("private", "self", "reflect", "relationship", "support"),
    "connection": ("connection", "relationship", "support", "family", "community"),
    "message": ("talk", "message", "support", "trusted", "connection"),
    "money-calm": ("financial", "money", "safe", "awareness", "education"),
    "money-admin": ("banking", "bill", "account", "awareness", "education"),
    "budget": ("budget", "spending", "saving", "financial", "decision"),
    "investor-education": ("investor", "investment", "education", "awareness"),
    "gratitude": ("gratitude", "happiness", "positive", "well-being"),
    "purpose": ("purpose", "meaning", "values", "life"),
    "meditation": ("meditation", "mindfulness", "silence", "inner"),
    "secular-grounding": ("well-being", "values", "happiness", "quality of life"),
}

ANSWER_RULES = {
    "mental_support": {
        "Calm my thoughts": {"weights": {"mental": 5}, "tags": ("calm", "tiny")},
        "Feel a little uplifted": {"weights": {"mental": 4, "social": 1}, "tags": ("uplift", "tiny")},
        "Improve focus": {"weights": {"mental": 4}, "tags": ("focus", "habit")},
        "Wind down for rest": {"weights": {"mental": 4, "physical": 2}, "tags": ("sleep", "rest")},
        "Not sure": {"weights": {"mental": 1}, "tags": ("read-only",)},
    },
    "mental_effort": {
        "Tiny action": {"weights": {"mental": 2}, "tags": ("tiny",)},
        "Short action": {"weights": {"mental": 2}, "tags": ("tiny", "habit")},
        "Reading only": {"weights": {"mental": 1}, "tags": ("read-only",), "avoid": ("deep-reflection",)},
        "Prefer not to say": {"weights": {"mental": 1}, "tags": ("read-only",)},
    },
    "mental_avoid": {
        "Deep reflection": {"tags": ("tiny",), "avoid": ("deep-reflection", "journaling")},
        "Breathing exercises": {"tags": ("read-only",), "avoid": ("breathing",)},
        "Journaling": {"tags": ("calm",), "avoid": ("journaling",)},
        "No preference": {"tags": ()},
    },
    "physical_state": {
        "Okay": {"weights": {"physical": 1}, "tags": ("movement",)},
        "Tired": {"weights": {"physical": 4, "mental": 1}, "tags": ("rest", "seated")},
        "Stiff": {"weights": {"physical": 4}, "tags": ("seated", "movement")},
        "Restless": {"weights": {"physical": 3, "mental": 1}, "tags": ("movement", "calm")},
        "Prefer not to say": {"weights": {"physical": 1}, "tags": ("read-only",)},
    },
    "movement_comfort": {
        "No movement today": {"weights": {"physical": 1}, "tags": ("seated", "rest"), "avoid": ("movement",)},
        "Seated stretch": {"weights": {"physical": 3}, "tags": ("seated", "movement")},
        "Short walk": {"weights": {"physical": 3}, "tags": ("movement", "tiny")},
        "Either is fine": {"weights": {"physical": 2}, "tags": ("movement", "tiny")},
    },
    "physical_boundary": {
        "Avoid physical activity": {"tags": ("rest", "read-only"), "avoid": ("movement",)},
        "Avoid standing": {"tags": ("seated",), "avoid": ("standing",)},
        "Keep it seated": {"tags": ("seated",), "avoid": ("standing",)},
        "No preference": {"tags": ()},
    },
    "connection_need": {
        "Quiet time alone": {"weights": {"social": 1, "mental": 1}, "tags": ("private",)},
        "Send a kind message": {"weights": {"social": 5}, "tags": ("message", "connection")},
        "Feel more connected": {"weights": {"social": 4}, "tags": ("connection",)},
        "Appreciate someone privately": {"weights": {"social": 3, "spiritual": 1}, "tags": ("private", "gratitude")},
        "Not sure": {"weights": {"social": 1}, "tags": ("read-only",)},
    },
    "social_comfort": {
        "No social task today": {"weights": {"social": 1}, "tags": ("private",), "avoid": ("outreach",)},
        "Private reflection": {"weights": {"social": 2}, "tags": ("private",)},
        "Send a simple message": {"weights": {"social": 4}, "tags": ("message",)},
        "Talk to a trusted person": {"weights": {"social": 4}, "tags": ("connection", "message")},
    },
    "privacy_preference": {
        "Keep this private": {"tags": ("private",), "avoid": ("outreach",)},
        "Anonymous/general content only": {"tags": ("read-only", "private")},
        "Simple action ideas are okay": {"tags": ("connection", "tiny")},
    },
    "money_support": {
        "Reduce money anxiety": {"weights": {"financial": 5, "mental": 1}, "tags": ("money-calm", "read-only")},
        "Organize one small task": {"weights": {"financial": 5}, "tags": ("money-admin", "tiny")},
        "Learn basics": {"weights": {"financial": 4}, "tags": ("read-only", "investor-education")},
        "Avoid money today": {"weights": {"financial": -3, "mental": 1}, "tags": ("read-only",), "avoid": ("money-action",)},
        "Not sure": {"weights": {"financial": 1}, "tags": ("read-only",)},
    },
    "money_action": {
        "Read only": {"weights": {"financial": 1}, "tags": ("read-only",), "avoid": ("money-action",)},
        "Check one bill date": {"weights": {"financial": 3}, "tags": ("money-admin",)},
        "List recent spending": {"weights": {"financial": 3}, "tags": ("budget",)},
        "Save a small amount": {"weights": {"financial": 3}, "tags": ("budget",)},
        "No task today": {"weights": {"financial": 0}, "tags": ("read-only",), "avoid": ("money-action",)},
    },
    "money_boundary": {
        "No numbers today": {"tags": ("read-only",), "avoid": ("numbers", "money-action")},
        "No investment content": {"tags": ("money-admin",), "avoid": ("investor-education",)},
        "No decisions today": {"tags": ("read-only",), "avoid": ("money-decision", "money-action")},
        "No preference": {"tags": ()},
    },
    "grounding_need": {
        "Gratitude": {"weights": {"spiritual": 4, "social": 1}, "tags": ("gratitude",)},
        "Purpose": {"weights": {"spiritual": 4}, "tags": ("purpose",)},
        "Meditation": {"weights": {"spiritual": 4, "mental": 1}, "tags": ("meditation", "calm")},
        "Values or prayer": {"weights": {"spiritual": 4}, "tags": ("purpose", "gratitude")},
        "Nature or quiet": {"weights": {"spiritual": 3, "mental": 1}, "tags": ("secular-grounding", "calm")},
        "Not sure": {"weights": {"spiritual": 1}, "tags": ("read-only",)},
    },
    "spiritual_practice": {
        "Read an insight": {"weights": {"spiritual": 1}, "tags": ("read-only",)},
        "One sentence reflection": {"weights": {"spiritual": 2}, "tags": ("purpose", "tiny")},
        "Short silence": {"weights": {"spiritual": 2}, "tags": ("meditation", "tiny")},
        "Breathing optional": {"weights": {"spiritual": 2, "mental": 1}, "tags": ("calm", "meditation")},
        "No practice today": {"weights": {"spiritual": 0}, "tags": ("read-only",)},
    },
    "spiritual_boundary": {
        "Avoid religious content": {"tags": ("secular-grounding",), "avoid": ("religious",)},
        "Avoid meditation": {"tags": ("read-only", "gratitude"), "avoid": ("meditation",)},
        "Avoid deep purpose questions": {"tags": ("gratitude", "tiny"), "avoid": ("purpose",)},
        "No preference": {"tags": ()},
    },
}

INSIGHTS = {
    "calm": "A small calming action is more useful when it feels easy enough to repeat tomorrow.",
    "uplift": "Uplift can be gentle: one kind thought, one lighter article, or one small pause.",
    "focus": "Focus often improves when the next step is made smaller and clearer.",
    "sleep": "A wind-down routine works best when it is predictable and low effort.",
    "rest": "Rest can be a valid wellness action, especially when energy is already low.",
    "seated": "A seated action can still support physical well-being without pushing the body.",
    "movement": "Gentle movement should feel optional and comfortable, not like a test.",
    "private": "Private reflection can protect your energy while still supporting connection.",
    "connection": "Connection does not need to be intense; a small low-pressure action can be enough.",
    "message": "A short message can maintain connection without turning into a long conversation.",
    "money-calm": "Financial calm often starts with neutral information, not a big decision.",
    "money-admin": "One tiny money-admin task can reduce background mental load.",
    "budget": "A useful money habit can begin with noticing, not judging.",
    "investor-education": "Trusted financial education helps separate learning from personal advice.",
    "gratitude": "Gratitude works well when it stays specific and small.",
    "purpose": "Purpose does not have to be grand; one values-based action counts.",
    "meditation": "A short quiet pause can be complete even when the mind wanders.",
    "secular-grounding": "Grounding can be values-based, practical, and fully non-religious.",
    "read-only": "Reading-only is still action when it helps you choose a safer next step.",
    "tiny": "Tiny steps are easier to start, easier to stop, and easier to repeat.",
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


def build_profile(answers: dict) -> dict:
    weights = defaultdict(float)
    tags = Counter()
    avoid = Counter()
    matched = defaultdict(list)

    for key, value in answers.items():
        rule = ANSWER_RULES.get(key, {}).get(value, {})
        for dimension, weight in rule.get("weights", {}).items():
            weights[dimension] += weight
            matched[dimension].append(value)
        for tag in rule.get("tags", ()):
            tags[tag] += 1
        for tag in rule.get("avoid", ()):
            avoid[tag] += 1

    for dimension in DIMENSIONS:
        weights[dimension] += 0.25

    return {
        "weights": dict(weights),
        "tags": tags,
        "avoid": avoid,
        "matched": dict(matched),
    }


def trusted_candidates(dimension: str) -> list[dict]:
    articles = [
        article
        for article in list_articles(
            limit=80,
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

    seen = set()
    merged = []
    for article in [*curated, *articles]:
        url = article.get("url", "")
        if url and url not in seen:
            seen.add(url)
            merged.append(article)
    return merged


def article_match_score(article: dict, profile: dict, dimension: str) -> float:
    text = " ".join(
        [
            article.get("title", ""),
            article.get("summary", ""),
            article.get("source", ""),
            article.get("category", ""),
        ]
    ).lower()
    score = float(article.get("positivity_score") or 0)
    score += SOURCE_PRIORITY.get(article.get("source", ""), 0.7)
    if article.get("category") == dimension:
        score += 1.5

    for tag, count in profile["tags"].items():
        keywords = TAG_KEYWORDS.get(tag, (tag,))
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits:
            score += min(hits, 3) * (0.55 + 0.15 * count)

    for tag, count in profile["avoid"].items():
        keywords = TAG_KEYWORDS.get(tag, (tag,))
        if any(keyword in text for keyword in keywords):
            score -= 1.2 * count

    return round(score, 3)


def ranked_articles(profile: dict, dimension: str, limit: int = 3) -> list[dict]:
    scored = []
    for article in trusted_candidates(dimension):
        item = dict(article)
        item["match_score"] = article_match_score(item, profile, dimension)
        scored.append(item)
    scored.sort(
        key=lambda article: (
            article["match_score"],
            SOURCE_PRIORITY.get(article.get("source", ""), 0),
            article.get("title", ""),
        ),
        reverse=True,
    )
    return scored[:limit]


def top_tags(profile: dict, dimension: str) -> list[str]:
    relevant = []
    for tag, _count in profile["tags"].most_common():
        if tag in profile["avoid"]:
            continue
        if dimension == "mental" and tag in {
            "calm",
            "uplift",
            "focus",
            "sleep",
            "tiny",
            "read-only",
            "meditation",
        }:
            relevant.append(tag)
        elif dimension == "physical" and tag in {"rest", "seated", "movement", "sleep", "tiny", "read-only"}:
            relevant.append(tag)
        elif dimension == "social" and tag in {"private", "connection", "message", "gratitude", "read-only"}:
            relevant.append(tag)
        elif dimension == "financial" and tag in {
            "money-calm",
            "money-admin",
            "budget",
            "investor-education",
            "read-only",
            "tiny",
        }:
            relevant.append(tag)
        elif dimension == "spiritual" and tag in {
            "gratitude",
            "purpose",
            "meditation",
            "secular-grounding",
            "calm",
            "read-only",
            "tiny",
        }:
            relevant.append(tag)
    return relevant[:3] or ["tiny", "read-only"]


def action_for_dimension(answers: dict, profile: dict, dimension: str) -> dict:
    tags = set(top_tags(profile, dimension))
    avoid = set(profile["avoid"])

    if dimension == "mental":
        if "breathing" in avoid:
            title = "Calm without breathing exercises"
            steps = [
                "Read one short calming paragraph.",
                "Look around and name one thing that feels manageable.",
                "Stop there if that is enough.",
            ]
        elif "sleep" in tags:
            title = "Create a tiny wind-down cue"
            steps = [
                "Dim one screen or light for a minute.",
                "Relax your jaw and shoulders.",
                "Choose one repeatable cue for bedtime.",
            ]
        elif "focus" in tags:
            title = "Make the next step smaller"
            steps = [
                "Pick one task you can start in two minutes.",
                "Write or say the first visible step.",
                "Do only that step.",
            ]
        else:
            title = "Use a one-minute reset"
            steps = [
                "Pause for 10 seconds.",
                "Unclench your jaw and soften your shoulders.",
                "Choose one gentle next action.",
            ]
    elif dimension == "physical":
        if "movement" in avoid or "seated" in tags:
            title = "Support your body without pushing it"
            steps = [
                "Sit comfortably with both feet supported.",
                "Relax your shoulders for 30 seconds.",
                "Skip movement if anything feels uncomfortable.",
            ]
        elif answers.get("movement_comfort") == "Short walk":
            title = "Take a low-pressure walk"
            steps = [
                "Walk for one to three minutes.",
                "Keep the pace easy.",
                "Stop before it becomes effortful.",
            ]
        else:
            title = "Try gentle movement"
            steps = [
                "Do one easy stretch or movement.",
                "Keep it below effort level.",
                "Stop if your body says no.",
            ]
    elif dimension == "social":
        if "outreach" in avoid or "private" in tags:
            title = "Stay private but connected"
            steps = [
                "Think of one person you appreciate.",
                "Name the quality you value in them.",
                "No message is required today.",
            ]
        elif "message" in tags:
            title = "Send one low-pressure message"
            steps = [
                "Pick one safe person.",
                "Send a short note, such as 'thinking of you today'.",
                "Do not turn it into a long conversation unless you want to.",
            ]
        else:
            title = "Notice one supportive connection"
            steps = [
                "Name one relationship that feels steady.",
                "Notice what makes it supportive.",
                "Let that be enough for today.",
            ]
    elif dimension == "financial":
        if "money-action" in avoid or "read-only" in tags:
            title = "Learn without making a money decision"
            steps = [
                "Read one trusted financial education tip.",
                "Do not enter numbers or make changes.",
                "Save one useful idea for later.",
            ]
        elif "budget" in tags:
            title = "Notice spending without judgment"
            steps = [
                "List three recent spends.",
                "Mark only whether each was planned or unplanned.",
                "Do not judge or fix anything today.",
            ]
        else:
            title = "Clear one small money admin item"
            steps = [
                "Check one due date, reminder, or account notification.",
                "Write down only the next tiny action.",
                "Stop before it becomes a bigger task.",
            ]
    else:
        if "religious" in avoid or "secular-grounding" in tags:
            title = "Use secular grounding"
            steps = [
                "Choose one value for today, such as patience or steadiness.",
                "Name one tiny action that expresses it.",
                "Keep it practical and non-religious.",
            ]
        elif "meditation" in avoid:
            title = "Ground without meditation"
            steps = [
                "Read one grounding insight.",
                "Notice one thing you are grateful for.",
                "No silence practice is needed.",
            ]
        elif "gratitude" in tags:
            title = "Use one specific gratitude cue"
            steps = [
                "Name one small thing you appreciate.",
                "Make it specific.",
                "Let that be the full practice.",
            ]
        else:
            title = "Choose one word for the day"
            steps = [
                "Read one grounding insight.",
                "Choose one word you want to carry today.",
                "Return to it once later.",
            ]

    return {
        "title": title,
        "steps": steps,
        "text": f"{title}: {steps[0]}",
    }


def insight_for_dimension(profile: dict, dimension: str) -> str:
    tags = top_tags(profile, dimension)
    for tag in tags:
        if tag in INSIGHTS:
            return INSIGHTS[tag]
    return "A useful wellness action can be small, private, and complete in under a minute."


def reason_for_dimension(answers: dict, profile: dict, dimension: str) -> str:
    matched = profile["matched"].get(dimension, [])
    if matched:
        shown = ", ".join(dict.fromkeys(matched[:3]))
        return f"Recommended because you selected: {shown}."
    if dimension == "financial" and answers.get("money_support") == "Avoid money today":
        return "Kept light because you preferred to avoid money tasks today."
    return "Recommended as a gentle fallback based on your current boundaries."


def recommendation_groups(answers: dict, limit: int) -> list[dict]:
    profile = build_profile(answers)
    ranked = sorted(
        DIMENSIONS,
        key=lambda dimension: profile["weights"].get(dimension, 0),
        reverse=True,
    )

    groups = []
    for dimension in ranked:
        if profile["weights"].get(dimension, 0) <= 0:
            continue
        action = action_for_dimension(answers, profile, dimension)
        articles = ranked_articles(profile, dimension, limit=3)
        groups.append(
            {
                "dimension": dimension,
                "title": DIMENSION_LABELS[dimension],
                "priority": round(profile["weights"].get(dimension, 0), 2),
                "tags": top_tags(profile, dimension),
                "action": action["text"],
                "action_title": action["title"],
                "action_steps": action["steps"],
                "insight": insight_for_dimension(profile, dimension),
                "reason": reason_for_dimension(answers, profile, dimension),
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
        "articles": articles[:12],
        "source_policy": "Only trusted sources such as WHO, United Nations, UNICEF, NIMHANS, IIMs, Art of Living, RBI, and SEBI are used for recommendations.",
    }
