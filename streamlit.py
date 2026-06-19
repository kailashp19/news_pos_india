from __future__ import annotations

import os
from datetime import datetime

import requests
import streamlit as st

from app.auth import (
    authenticate_user,
    create_password_reset_token,
    get_saved_article_urls,
    init_auth_db,
    list_saved_articles,
    register_user,
    reset_password,
    save_article_for_user,
    unsave_article_for_user,
)


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")


st.set_page_config(
    page_title="Joyverse",
    layout="wide",
)


DIMENSION_OPTIONS = {
    "All": "all",
    "Mental Health": "mental",
    "Physical Health": "physical",
    "Spiritual Health": "spiritual",
    "Social Health": "social",
    "Financial Health": "financial",
}


init_auth_db()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #1d2638;
            --surface: #222c40;
            --surface-soft: #2a354b;
            --surface-raised: #253048;
            --border: #36435a;
            --border-soft: #2f3a50;
            --text: #f5f7fb;
            --muted: #aeb8ca;
            --accent: #6ee7a8;
            --accent-strong: #35c985;
            --accent-blue: #89b7ff;
            --accent-warm: #ff6b5f;
            --danger: #ff8d8d;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 4rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: #182033;
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
            box-shadow: none;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: none;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #53617c;
            background: var(--surface-raised);
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
        }

        h1,
        h1 span,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h1 span {
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(2.15rem, 4vw, 3.5rem);
            line-height: 1.05;
            margin-bottom: 0.85rem;
        }

        h2, h3,
        h2 span, h3 span,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            font-family: Georgia, "Times New Roman", serif;
        }

        p, span, label, [data-testid="stMarkdownContainer"] {
            color: var(--text);
        }

        small, [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        a {
            color: var(--accent-blue);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-bottom: 0;
            border-radius: 8px 8px 0 0;
            color: var(--muted);
            padding: 10px 16px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--surface-soft);
            color: var(--text);
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea {
            background: var(--surface-soft) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stTextInput"] div,
        [data-baseweb="input"],
        [data-baseweb="input"] input {
            background-color: var(--surface-soft) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }

        [data-testid="stForm"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
        }

        .stButton > button,
        .stLinkButton > a {
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--surface-soft);
            color: var(--text);
            font-weight: 600;
            min-height: 2.75rem;
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            border-color: var(--accent);
            background: #303d56;
            color: var(--text);
        }

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: #ef5f54;
            border-color: transparent !important;
            color: #fffafa !important;
        }

        button[data-baseweb="tab"] {
            color: var(--muted) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom-color: var(--accent) !important;
        }

        [data-baseweb="tab-highlight"] {
            background-color: var(--accent-warm) !important;
        }

        [data-testid="stAlert"] {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            color: var(--text);
        }

        [role="radiogroup"] label,
        [data-testid="stWidgetLabel"] {
            color: var(--text);
        }

        hr {
            border-color: var(--border);
        }

        code {
            background: #12192a;
            color: var(--accent);
        }

        .stSlider [data-baseweb="slider"] {
            color: var(--accent);
        }

        [data-testid="stRadio"] label p {
            color: var(--text);
        }

        [role="radiogroup"] {
            gap: 0.5rem;
        }

        [role="radiogroup"] label {
            background: #202a3f;
            border: 1px solid var(--border-soft);
            border-radius: 8px;
            padding: 0.35rem 0.6rem;
            min-height: 2.25rem;
        }

        [data-testid="stMetricLabel"] p {
            color: var(--muted);
        }

        [data-testid="stMetricValue"] {
            color: var(--text);
            font-family: Georgia, "Times New Roman", serif;
        }

        .st-emotion-cache-1wmy9hl,
        .st-emotion-cache-ocqkz7 {
            gap: 1rem;
        }

        .joyverse-landing {
            min-height: min(760px, calc(100vh - 7rem));
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
            gap: 3rem;
            align-items: center;
        }

        .joyverse-kicker {
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin-bottom: 1rem;
            text-transform: uppercase;
        }

        .joyverse-title {
            color: var(--text);
            font-family: Georgia, "Times New Roman", serif !important;
            font-size: clamp(3.4rem, 7.5vw, 5.4rem) !important;
            line-height: 0.9 !important;
            margin: 0 0 1rem !important;
            white-space: nowrap;
        }

        .joyverse-tagline {
            color: var(--text);
            font-size: clamp(1.35rem, 2.6vw, 2.2rem);
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 1rem;
        }

        .joyverse-copy {
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.65;
            max-width: 42rem;
        }

        .joyverse-icon-card {
            align-items: center;
            aspect-ratio: 1 / 1;
            background:
                radial-gradient(circle at 50% 28%, rgba(110, 231, 168, 0.18), transparent 34%),
                linear-gradient(145deg, #25314a 0%, #1a2337 100%);
            border: 1px solid var(--border);
            border-radius: 8px;
            display: flex;
            justify-content: center;
            min-height: 280px;
            position: relative;
        }

        .joyverse-icon {
            color: var(--text);
            font-size: clamp(7rem, 18vw, 12rem);
            filter: drop-shadow(0 16px 30px rgba(0, 0, 0, 0.32));
            line-height: 1;
        }

        .joyverse-icon-caption {
            bottom: 1rem;
            color: var(--muted);
            font-size: 0.9rem;
            left: 1rem;
            position: absolute;
            right: 1rem;
            text-align: center;
        }

        .joyverse-feature-row {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 2rem;
        }

        .joyverse-feature {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.35;
            padding: 0.9rem;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1.25rem;
                padding-right: 1.25rem;
                padding-top: 2rem;
            }

            .joyverse-landing {
                grid-template-columns: 1fr;
                gap: 1.5rem;
                min-height: auto;
            }

            .joyverse-icon-card {
                min-height: 220px;
                order: -1;
            }

            .joyverse-feature-row {
                grid-template-columns: 1fr;
            }

            [role="radiogroup"] {
                align-items: stretch;
                flex-direction: column;
            }

            [role="radiogroup"] label {
                width: 100%;
            }
        }

        @media (max-width: 520px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.25rem;
            }

            .joyverse-title {
                font-size: 3rem !important;
            }

            .joyverse-tagline {
                font-size: 1.35rem;
            }

            .joyverse-copy {
                font-size: 1rem;
            }

            .stButton > button,
            .stLinkButton > a {
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    st.session_state.setdefault("landing_seen", False)
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("user_email", "")
    st.session_state.setdefault("user_avatar", "")
    st.session_state.setdefault("reset_token", "")
    st.session_state.setdefault("active_view", "Today")
    st.session_state.setdefault("onboarding_step", "welcome")
    st.session_state.setdefault("wellness_answers", {})
    st.session_state.setdefault("recommendation", {})
    st.session_state.setdefault("selected_article", None)
    st.session_state.setdefault("done_articles", set())


def logout() -> None:
    st.session_state["landing_seen"] = False
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = ""
    st.session_state["user_email"] = ""
    st.session_state["user_avatar"] = ""
    st.session_state["reset_token"] = ""
    st.session_state["onboarding_step"] = "welcome"
    st.session_state["wellness_answers"] = {}
    st.session_state["recommendation"] = {}
    st.session_state["selected_article"] = None
    st.rerun()


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
def fetch_articles(min_score: float, limit: int, dimension: str) -> list[dict]:
    response = api_get(
        f"{API_BASE_URL}/api/articles",
        params={"min_score": min_score, "limit": limit, "dimension": dimension},
    )
    return response.get("items", [])


@st.cache_data(ttl=120)
def fetch_stats(dimension: str) -> dict:
    return api_get(f"{API_BASE_URL}/api/stats", params={"dimension": dimension})


def refresh_feed() -> dict:
    response = requests.post(f"{API_BASE_URL}/api/refresh", timeout=60)
    response.raise_for_status()
    fetch_articles.clear()
    fetch_stats.clear()
    return response.json()


def fetch_recommendation(answers: dict, limit: int = 6) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/recommendations",
        json={"answers": answers, "limit": limit},
        timeout=20,
    )
    response.raise_for_status()
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


def display_name() -> str:
    username = st.session_state.get("username", "")
    if username:
        return username
    email = st.session_state.get("user_email", "")
    name = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return name.title() if name else "there"


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def render_landing_page() -> None:
    st.markdown(
        """
        <section class="joyverse-landing" aria-label="Joyverse landing page">
            <div>
                <div class="joyverse-kicker">Personal wellness for everyday India</div>
                <h1 class="joyverse-title">Joyverse</h1>
                <div class="joyverse-tagline">Helping India Smile Everyday</div>
                <p class="joyverse-copy">
                    A gentle wellness companion that turns your preferences into
                    small actions, trusted reading, and practical insights across
                    mental, physical, social, financial, and spiritual well-being.
                </p>
                <div class="joyverse-feature-row">
                    <div class="joyverse-feature">Private check-ins without medical or financial details.</div>
                    <div class="joyverse-feature">Small actions matched to your comfort and energy.</div>
                    <div class="joyverse-feature">Trusted sources like WHO, UN, IIMs, RBI, SEBI, and more.</div>
                </div>
            </div>
            <div class="joyverse-icon-card" aria-label="Person in a free and joyful state">
                <div class="joyverse-icon" aria-hidden="true">&#128588;</div>
                <div class="joyverse-icon-caption">A small daily lift for body, mind, money, people, and purpose.</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Start your Joyverse", type="primary", use_container_width=True):
        st.session_state["landing_seen"] = True
        st.rerun()


def render_welcome_screen() -> None:
    st.title("Let's build your personal wellness plan.")
    st.write(
        "This app is for general wellness education and gentle habit-building. "
        "It does not provide medical advice, diagnosis, or treatment."
    )
    st.info(
        "If you have a medical condition, are pregnant, have pain, feel unsafe, "
        "or are unsure, please consult a qualified healthcare professional before "
        "trying any activity."
    )
    if st.button("I understand", type="primary", use_container_width=True):
        st.session_state["onboarding_step"] = "questions"
        st.rerun()


def render_wellness_questions() -> None:
    st.title("Your Wellness Check-In")
    st.caption(
        "Fifteen quick choices. No diagnosis, no medical details, and no private "
        "financial numbers required."
    )

    with st.form("wellness_check_form"):
        st.subheader("Mental Health")
        mental_support = st.radio(
            "What would support your mind today?",
            [
                "Calm my thoughts",
                "Feel a little uplifted",
                "Improve focus",
                "Wind down for rest",
                "Not sure",
            ],
            index=1,
            horizontal=True,
        )
        mental_effort = st.radio(
            "How much mental effort feels okay?",
            [
                "Tiny action",
                "Short action",
                "Reading only",
                "Prefer not to say",
            ],
            horizontal=True,
        )
        mental_avoid = st.radio(
            "Anything you want to avoid mentally today?",
            [
                "Deep reflection",
                "Breathing exercises",
                "Journaling",
                "No preference",
            ],
            index=3,
            horizontal=True,
        )

        st.subheader("Physical Health")
        physical_state = st.radio(
            "How does your body feel today?",
            [
                "Okay",
                "Tired",
                "Stiff",
                "Restless",
                "Prefer not to say",
            ],
            horizontal=True,
        )
        movement_comfort = st.radio(
            "What kind of movement feels comfortable?",
            [
                "No movement today",
                "Seated stretch",
                "Short walk",
                "Either is fine",
            ],
            index=3,
            horizontal=True,
        )
        physical_boundary = st.radio(
            "Any physical boundary for today?",
            [
                "Avoid physical activity",
                "Avoid standing",
                "Keep it seated",
                "No preference",
            ],
            index=3,
            horizontal=True,
        )

        st.subheader("Social Health")
        connection_need = st.radio(
            "What kind of connection feels helpful?",
            [
                "Quiet time alone",
                "Send a kind message",
                "Feel more connected",
                "Appreciate someone privately",
                "Not sure",
            ],
            index=4,
            horizontal=True,
        )
        social_comfort = st.radio(
            "What social action feels comfortable?",
            [
                "No social task today",
                "Private reflection",
                "Send a simple message",
                "Talk to a trusted person",
            ],
            horizontal=True,
        )
        privacy_preference = st.radio(
            "How private should today's social suggestion be?",
            [
                "Keep this private",
                "Anonymous/general content only",
                "Simple action ideas are okay",
            ],
            horizontal=True,
        )

        st.subheader("Financial Health")
        money_support = st.radio(
            "What kind of money support would feel useful?",
            [
                "Reduce money anxiety",
                "Organize one small task",
                "Learn basics",
                "Avoid money today",
                "Not sure",
            ],
            index=4,
            horizontal=True,
        )
        money_action = st.radio(
            "What financial action feels safe today?",
            [
                "Read only",
                "Check one bill date",
                "List recent spending",
                "Save a small amount",
                "No task today",
            ],
            horizontal=True,
        )
        money_boundary = st.radio(
            "Any money boundary for today?",
            [
                "No numbers today",
                "No investment content",
                "No decisions today",
                "No preference",
            ],
            index=3,
            horizontal=True,
        )

        st.subheader("Spiritual Health")
        grounding_need = st.radio(
            "What feels grounding today?",
            [
                "Gratitude",
                "Purpose",
                "Meditation",
                "Values or prayer",
                "Nature or quiet",
                "Not sure",
            ],
            index=5,
            horizontal=True,
        )
        spiritual_practice = st.radio(
            "What kind of grounding practice feels comfortable?",
            [
                "Read an insight",
                "One sentence reflection",
                "Short silence",
                "Breathing optional",
                "No practice today",
            ],
            horizontal=True,
        )
        spiritual_boundary = st.radio(
            "Any spiritual boundary for today?",
            [
                "Avoid religious content",
                "Avoid meditation",
                "Avoid deep purpose questions",
                "No preference",
            ],
            index=3,
            horizontal=True,
        )

        submitted = st.form_submit_button("Create my plan", type="primary")

    if submitted:
        answers = {
            "mental_support": mental_support,
            "mental_effort": mental_effort,
            "mental_avoid": mental_avoid,
            "physical_state": physical_state,
            "movement_comfort": movement_comfort,
            "physical_boundary": physical_boundary,
            "connection_need": connection_need,
            "social_comfort": social_comfort,
            "privacy_preference": privacy_preference,
            "money_support": money_support,
            "money_action": money_action,
            "money_boundary": money_boundary,
            "grounding_need": grounding_need,
            "spiritual_practice": spiritual_practice,
            "spiritual_boundary": spiritual_boundary,
        }
        try:
            st.session_state["recommendation"] = fetch_recommendation(answers)
            st.session_state["wellness_answers"] = answers
            st.session_state["onboarding_step"] = "home"
            st.rerun()
        except (requests.RequestException, ValueError) as exc:
            show_api_error(exc)


def save_or_unsave_button(article: dict, saved_urls: set[str], key_prefix: str) -> None:
    if article["url"] in saved_urls:
        if st.button("Saved", key=f"{key_prefix}_unsave_{article['url']}"):
            unsave_article_for_user(int(st.session_state["user_id"]), article["url"])
            st.success("Removed from saved articles.")
            st.rerun()
    elif st.button("Save Article", key=f"{key_prefix}_save_{article['url']}"):
        save_article_for_user(int(st.session_state["user_id"]), article)
        st.success("Article saved.")
        st.rerun()


def group_for_article(article: dict) -> dict:
    recommendation = st.session_state.get("recommendation", {})
    for group in recommendation.get("groups", []):
        if article.get("category") == group.get("dimension"):
            return group
    return {}


def render_article_action_page(article: dict) -> None:
    group = group_for_article(article)
    saved_urls = get_saved_article_urls(int(st.session_state["user_id"]))

    if st.button("Back to today's plan"):
        st.session_state["selected_article"] = None
        st.rerun()

    st.title(article["title"])
    meta = [
        f"Source: {article['source']}",
        f"Wellness area: {article['category'].title()}",
    ]
    published = format_date(article.get("published_at", ""))
    if published:
        meta.append(f"Published: {published}")
    st.caption(" | ".join(meta))

    st.subheader("Quick Summary")
    st.write(
        article.get("summary")
        or "This resource offers a short wellness idea you can explore today."
    )

    st.subheader("Why This Matters For You")
    st.write(
        group.get(
            "reason",
            "This article is matched to the boundaries and preferences you chose today.",
        )
    )

    st.subheader("Today's Action")
    st.write(group.get("action_title", "Take one small idea from this article today."))
    for step in group.get("action_steps", []):
        st.write(f"- {step}")
    if st.button("Mark as Done", type="primary"):
        st.session_state["done_articles"].add(article["url"])
        st.success("Done. Small steps count.")

    st.subheader("Insight")
    st.write(
        group.get(
            "insight",
            "A useful wellness action can be small, private, and complete in under a minute.",
        )
    )

    st.subheader("Reflection")
    st.radio(
        "How do you feel after this?",
        ["Better", "Same", "Worse", "Not sure"],
        horizontal=True,
        key=f"reflection_{article['url']}",
    )

    st.subheader("Save / Share")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        save_or_unsave_button(article, saved_urls, "detail")
    with col_b:
        st.link_button("Share Insight", article["url"])
    with col_c:
        st.link_button("Open Full Article", article["url"])


def render_article_card(article: dict, saved_urls: set[str], key_prefix: str) -> None:
    with st.container(border=True):
        st.subheader(article["title"])
        if article.get("summary"):
            st.write(summarize_words(article["summary"], 60))

        meta = [
            f"Source: {article['source']}",
            f"Wellness area: {article['category'].title()}",
        ]
        if article.get("match_score") is not None:
            meta.append(f"Match: {article['match_score']:.1f}")
        published = format_date(article.get("published_at", ""))
        if published:
            meta.append(f"Published: {published}")
        st.caption(" | ".join(meta))

        col_a, col_b, col_c = st.columns([1, 1, 1])
        if col_a.button(
            "Open Action Page",
            key=f"{key_prefix}_open_{article['url']}",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["selected_article"] = article
            st.rerun()
        with col_b:
            save_or_unsave_button(article, saved_urls, key_prefix)
        col_c.link_button("Full Article", article["url"], use_container_width=True)


def render_recommendation_group(group: dict, saved_urls: set[str]) -> None:
    st.subheader(group.get("title", "Wellness recommendation"))
    st.markdown(f"**{group.get('action_title', 'Suggested action')}**")
    for step in group.get("action_steps", []):
        st.write(f"- {step}")
    st.caption(group.get("reason", "Matched to your preferences and boundaries."))
    if group.get("tags"):
        st.caption("Matched signals: " + ", ".join(group["tags"]))
    st.markdown(f"**Insight:** {group.get('insight', 'Small actions count.')}")

    articles = group.get("articles", [])
    if articles:
        st.markdown("**Trusted reading matched to this action:**")
        for article in articles:
            render_article_card(
                article,
                saved_urls,
                f"{group.get('dimension', 'group')}_trusted",
            )
    st.divider()


def render_today_dashboard() -> None:
    recommendation = st.session_state.get("recommendation", {})
    groups = recommendation.get("groups", [])
    saved_urls = get_saved_article_urls(int(st.session_state["user_id"]))

    st.title(f"{greeting()}, {display_name()}")
    st.caption("A gentle daily plan based on your preferences and boundaries.")

    st.subheader("Today's Focus")
    st.write(recommendation.get("today_focus", "Choose one gentle next step"))

    st.subheader("Suggested Actions")
    for index, item in enumerate(recommendation.get("plan", []), start=1):
        st.write(f"{index}. {item}")

    st.divider()
    st.subheader("Recommended For You")
    st.caption(
        recommendation.get(
            "source_policy",
            "Recommendations use only trusted wellness sources.",
        )
    )
    if not groups:
        st.info("No recommended articles are available yet. Try refreshing feeds or changing your check-in.")
        return

    for group in groups:
        render_recommendation_group(group, saved_urls)


def render_auth_screen() -> None:
    st.title("Joyverse")
    st.caption("Helping India Smile Everyday")

    login_tab, register_tab, reset_tab = st.tabs(
        ["Login", "Register", "Forgot Password"]
    )

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            success, message, user = authenticate_user(username, password)
            if success and user:
                st.session_state["authenticated"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["username"] = user["username"]
                st.session_state["user_email"] = user["email"]
                st.session_state["user_avatar"] = user["avatar"]
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with register_tab:
        with st.form("register_form"):
            username = st.text_input(
                "Username",
                help="Use 3-24 letters or numbers only. No spaces or special characters.",
                key="register_username",
            )
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="register_confirm_password",
            )
            submitted = st.form_submit_button("Create account", type="primary")

        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = register_user(username, email, password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with reset_tab:
        st.caption(
            "Reset codes are emailed when SMTP is configured. In local development, "
            "the code is shown here."
        )

        with st.form("request_reset_form"):
            email = st.text_input("Registered email", key="reset_request_email")
            submitted = st.form_submit_button("Generate reset code")

        if submitted:
            success, message, token = create_password_reset_token(email)
            if success:
                st.success(message)
                if token:
                    st.session_state["reset_token"] = token
                    st.info("SMTP is not configured, so use this local reset code:")
                    st.code(token)
            else:
                st.error(message)

        with st.form("reset_password_form"):
            email = st.text_input("Email", key="reset_email")
            token = st.text_input(
                "Reset code",
                value=st.session_state.get("reset_token", ""),
                key="reset_code",
            )
            new_password = st.text_input(
                "New password",
                type="password",
                key="reset_new_password",
            )
            confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="reset_confirm_password",
            )
            submitted = st.form_submit_button("Reset password", type="primary")

        if submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = reset_password(email, token, new_password)
                if success:
                    st.session_state["reset_token"] = ""
                    st.success(message)
                else:
                    st.error(message)


apply_theme()
init_session_state()

if not st.session_state["landing_seen"] and not st.session_state["authenticated"]:
    render_landing_page()
    st.stop()

if not st.session_state["authenticated"]:
    render_auth_screen()
    st.stop()


with st.sidebar:
    st.markdown("## Joyverse")
    st.caption("Helping India Smile Everyday")
    st.markdown(
        f"### {st.session_state['user_avatar']} {st.session_state['username']}"
    )
    st.session_state["active_view"] = st.radio(
        "View",
        ["Today", "Saved Articles", "Retake Check-In"],
    )
    st.button("Logout", on_click=logout, use_container_width=True)
    st.divider()

if st.session_state["active_view"] == "Retake Check-In":
    st.session_state["onboarding_step"] = "questions"
    st.session_state["selected_article"] = None

if st.session_state["onboarding_step"] == "welcome":
    render_welcome_screen()
    st.stop()

if st.session_state["onboarding_step"] == "questions":
    render_wellness_questions()
    st.stop()

if st.session_state["active_view"] == "Saved Articles":
    saved_articles = list_saved_articles(int(st.session_state["user_id"]))
    st.subheader("Saved Articles")
    if not saved_articles:
        st.info("You have not saved any articles yet.")
    else:
        for article in saved_articles:
            with st.container(border=True):
                st.subheader(article["title"])
                if article["summary"]:
                    st.write(summarize_words(article["summary"], 100))
                saved = format_date(article.get("saved_at", ""))
                st.caption(
                    " | ".join(
                        item
                        for item in [
                            f"Source: {article['source']}",
                            f"Wellness area: {article['category'].title()}",
                            f"Saved: {saved}" if saved else "",
                        ]
                        if item
                    )
                )
                col_a, col_b = st.columns([1, 1])
                col_a.link_button("Read full article", article["url"])
                if col_b.button(
                    "Remove saved",
                    key=f"remove_{article['url']}",
                    use_container_width=True,
                ):
                    unsave_article_for_user(
                        int(st.session_state["user_id"]),
                        article["url"],
                    )
                    st.success("Removed from saved articles.")
                    st.rerun()
    st.stop()

with st.sidebar:
    st.header("Tools")
    if st.button("Refresh feeds", type="primary", use_container_width=True):
        with st.spinner("Fetching practical wellness content..."):
            try:
                result = refresh_feed()
                st.success(
                    f"Saved {result['articles_saved']} new articles from "
                    f"{result['feeds_checked']} feeds."
                )
                if result["errors"]:
                    st.warning("Some sources were unavailable or rate-limited.")
                if st.session_state.get("wellness_answers"):
                    st.session_state["recommendation"] = fetch_recommendation(
                        st.session_state["wellness_answers"]
                    )
            except (requests.RequestException, ValueError) as exc:
                show_api_error(exc)
    st.caption(f"Backend: {API_BASE_URL}")

if st.session_state.get("selected_article"):
    render_article_action_page(st.session_state["selected_article"])
else:
    if not st.session_state.get("recommendation"):
        try:
            st.session_state["recommendation"] = fetch_recommendation(
                st.session_state.get("wellness_answers", {})
            )
        except (requests.RequestException, ValueError) as exc:
            show_api_error(exc)
            st.stop()
    render_today_dashboard()
