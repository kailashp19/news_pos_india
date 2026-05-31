from __future__ import annotations

from app.models import Article


CURATED_RESOURCES = [
    Article(
        title="WHO: How to manage stress",
        url="https://www.who.int/en/news-room/questions-and-answers/item/stress",
        source="WHO",
        summary=(
            "WHO explains how stress affects mental and physical health and recommends "
            "practical self-help techniques that can be practised for a few minutes each "
            "day, while also encouraging people to seek professional help when distress "
            "continues to interfere with daily life."
        ),
        category="mental",
        positivity_score=0.9,
    ),
    Article(
        title="WHO: Mental health tips for everyday well-being",
        url="https://www.who.int/campaigns/connecting-the-world-to-combat-coronavirus/healthyathome/healthyathome---mental-health",
        source="WHO",
        summary=(
            "WHO's mental health guidance includes keeping daily routines, regular "
            "exercise, healthy sleep, social connection, limiting distressing news, "
            "avoiding alcohol and tobacco as coping tools, and continuing prescribed "
            "mental-health treatment when applicable."
        ),
        category="mental",
        positivity_score=0.9,
    ),
    Article(
        title="WHO: Physical activity recommendations for adults",
        url="https://www.who.int/news-room/fact-sheets/detail/physical-activity",
        source="WHO",
        summary=(
            "WHO recommends that adults do regular moderate or vigorous physical "
            "activity each week and reduce sedentary time. Activity can include walking, "
            "cycling, sports, household chores, gardening, or other movement that fits "
            "daily life."
        ),
        category="physical",
        positivity_score=0.92,
    ),
    Article(
        title="WHO India: Physical activity in South-East Asia",
        url="https://www.who.int/india/health-topics/physical-activity",
        source="WHO India",
        summary=(
            "WHO India describes physical activity as any movement that uses energy, "
            "including walking, cycling, sport, recreation, work, and household activity. "
            "It notes that being active supports mental well-being and lowers risk from "
            "major noncommunicable diseases."
        ),
        category="physical",
        positivity_score=0.92,
    ),
    Article(
        title="WHO: Keeping well in adulthood",
        url="https://www.who.int/tools/your-life-your-health/life-phase/early-and-middle-adulthood/keeping-well-in-adulthood",
        source="WHO",
        summary=(
            "WHO's adult well-being guidance gives practical reminders to stay active, "
            "care for mental health through relaxing and enjoyable activities, maintain "
            "healthy relationships, avoid tobacco, limit alcohol, and keep up with "
            "preventive health checks."
        ),
        category="physical",
        positivity_score=0.88,
    ),
    Article(
        title="NIMHANS: Build healthy sleep routines",
        url="https://nimhansonline.in/sleep-and-mental-health-how-to-build-healthy-routines/",
        source="NIMHANS",
        summary=(
            "NIMHANS explains the connection between sleep and mental health and gives "
            "practical routine-building tips, such as gradually shifting bedtime, calming "
            "racing thoughts, and creating habits that train the body and mind to rest."
        ),
        category="mental",
        positivity_score=0.88,
    ),
    Article(
        title="UNICEF India: Seven tips to take care of your mental health",
        url="https://www.unicef.org/india/tips-take-care-your-mental-health",
        source="UNICEF India",
        summary=(
            "UNICEF India recommends talking to someone trusted, being kind to yourself, "
            "using positive self-talk, taking breaks for refreshing activities, and "
            "asking for help as a strong step when emotions feel difficult to carry."
        ),
        category="mental",
        positivity_score=0.86,
    ),
    Article(
        title="IIM Bangalore: Student Welfare Office holistic support",
        url="https://www.iimb.ac.in/about-institute/life-iimb/swo",
        source="IIM Bangalore",
        summary=(
            "IIM Bangalore describes a holistic approach to student well-being across "
            "physical, emotional, social, community, and spiritual spheres, including "
            "wellness activities, life-skills workshops, and access to mental-health "
            "support."
        ),
        category="social",
        positivity_score=0.78,
    ),
    Article(
        title="IIMA Emotional Wellness Services",
        url="https://ews.iima.ac.in/",
        source="IIM Ahmedabad",
        summary=(
            "IIMA's Emotional Wellness Services describe confidential counselling, "
            "stress-management support, mindfulness, resilience-building, interpersonal "
            "connection, self-care, and relationship-care resources for emotional "
            "well-being."
        ),
        category="mental",
        positivity_score=0.82,
    ),
]


def load_curated_resources() -> list[Article]:
    return CURATED_RESOURCES.copy()


def curated_source_names() -> list[str]:
    return sorted({article.source for article in CURATED_RESOURCES})
