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
from app.progress import (
    init_progress_db,
    progress_summary,
    record_action_completion,
    record_checkin,
)


APP_NAME = os.getenv("APP_NAME", "Joyverse")
APP_TAGLINE = os.getenv("APP_TAGLINE", "Your daily happiness companion")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")

st.set_page_config(
    page_title=f"{APP_NAME} | Daily Happiness Companion",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


init_auth_db()
init_progress_db()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-start: #fff8ef;
            --bg-end: #eef9f1;
            --surface: rgba(255, 255, 255, 0.86);
            --surface-solid: #ffffff;
            --surface-soft: #fff4e6;
            --surface-green: #edf9f1;
            --surface-blue: #eef6ff;
            --border: rgba(39, 73, 58, 0.14);
            --text: #17251f;
            --muted: #65746c;
            --accent: #1f9d68;
            --accent-dark: #0f7048;
            --accent-warm: #f08a5d;
            --shadow: 0 16px 48px rgba(31, 73, 52, 0.10);
            --radius-lg: 28px;
            --radius-md: 18px;
            --radius-sm: 12px;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 211, 145, 0.38), transparent 34rem),
                radial-gradient(circle at top right, rgba(109, 213, 154, 0.28), transparent 32rem),
                linear-gradient(135deg, var(--bg-start), var(--bg-end));
            color: var(--text);
        }

        .block-container {
            max-width: 1160px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.82);
            border-right: 1px solid var(--border);
            backdrop-filter: blur(16px);
        }

        [data-testid="stSidebar"] * { color: var(--text); }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.035em;
        }

        h1 {
            font-size: clamp(2rem, 6vw, 4.6rem) !important;
            line-height: 0.98 !important;
            margin-bottom: 0.75rem !important;
        }

        h2 { font-size: clamp(1.45rem, 3vw, 2.1rem) !important; }
        h3 { font-size: clamp(1.15rem, 2.4vw, 1.45rem) !important; }
        p, span, label, [data-testid="stMarkdownContainer"] { color: var(--text); }
        small, [data-testid="stCaptionContainer"] { color: var(--muted); }
        a { color: var(--accent-dark); }

        [data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow);
        }

        [data-testid="stForm"] { padding: 1.1rem; }

        [data-testid="stMetric"] {
            padding: 1rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--accent-dark);
            font-weight: 800;
        }

        .stButton > button,
        .stLinkButton > a {
            border-radius: 999px !important;
            border: 1px solid var(--border) !important;
            background: var(--surface-solid) !important;
            color: var(--text) !important;
            font-weight: 750 !important;
            min-height: 2.8rem;
            box-shadow: 0 8px 22px rgba(31, 73, 52, 0.08);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            border-color: rgba(31, 157, 104, 0.48) !important;
            color: var(--accent-dark) !important;
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(31, 73, 52, 0.12);
        }

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #1f9d68, #76c893) !important;
            color: #ffffff !important;
            border: none !important;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea,
        [data-testid="stTextInput"] input,
        [data-baseweb="input"] input {
            background-color: rgba(255,255,255,0.96) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
            border-radius: 14px !important;
        }

        [role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.65rem;
        }

        [role="radiogroup"] label {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.7rem 0.8rem;
            min-height: 3rem;
            box-shadow: 0 6px 18px rgba(31, 73, 52, 0.06);
        }

        [data-testid="stAlert"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            color: var(--text);
        }

        .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.12fr) minmax(280px, 0.88fr);
            gap: 2rem;
            align-items: center;
            min-height: min(720px, calc(100vh - 7rem));
        }

        .hero-card, .soft-card, .plan-card, .article-card, .step-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
        }

        .hero-card { padding: clamp(1.4rem, 4vw, 3rem); }
        .soft-card, .plan-card, .article-card, .step-card { padding: 1.2rem; }

        .kicker {
            color: var(--accent-dark);
            font-weight: 850;
            letter-spacing: .10em;
            text-transform: uppercase;
            font-size: .78rem;
            margin-bottom: .75rem;
        }

        .subtitle {
            color: var(--muted);
            font-size: clamp(1rem, 2.2vw, 1.18rem);
            line-height: 1.65;
            max-width: 44rem;
        }

        .hero-visual {
            min-height: 360px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 50% 32%, rgba(255, 186, 112, 0.52), transparent 9rem),
                radial-gradient(circle at 56% 58%, rgba(63, 184, 122, 0.42), transparent 12rem),
                linear-gradient(145deg, rgba(255,255,255,0.74), rgba(238,249,241,0.8));
        }

        .hero-emoji { font-size: clamp(7rem, 16vw, 12rem); }
        .feature-grid, .journey-grid, .plan-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
        }

        .plan-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: .4rem;
            padding: .42rem .72rem;
            border-radius: 999px;
            background: rgba(31, 157, 104, 0.10);
            color: var(--accent-dark);
            font-weight: 800;
            font-size: .84rem;
            margin: .2rem .25rem .2rem 0;
        }

        .muted { color: var(--muted); }
        .big-emoji { font-size: 2rem; line-height: 1; }
        .progress-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: .55rem;
            margin: .8rem 0 1.25rem;
        }
        .progress-dot {
            height: .45rem;
            border-radius: 999px;
            background: rgba(31, 157, 104, 0.16);
        }
        .progress-dot.active { background: linear-gradient(90deg, #1f9d68, #76c893); }

        .mobile-note {
            background: rgba(255, 244, 230, 0.76);
            border: 1px solid rgba(240, 138, 93, 0.20);
            border-radius: var(--radius-md);
            padding: 1rem;
        }

        .stTabs [data-baseweb="tab-list"] { gap: .45rem; }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,.72);
            border-radius: 999px;
            border: 1px solid var(--border);
            padding: .55rem 1rem;
        }
        .stTabs [aria-selected="true"] { color: var(--accent-dark) !important; }
        [data-baseweb="tab-highlight"] { background-color: transparent !important; }

        hr { border-color: var(--border); }

        @media (max-width: 900px) {
            .block-container {
                padding: 1rem 1rem 4rem;
            }
            [data-testid="stSidebar"] {
                width: 100% !important;
            }
            .hero {
                grid-template-columns: 1fr;
                min-height: auto;
                gap: 1rem;
            }
            .hero-visual {
                order: -1;
                min-height: 220px;
            }
            .feature-grid, .journey-grid, .plan-grid {
                grid-template-columns: 1fr;
            }
            [role="radiogroup"] {
                grid-template-columns: 1fr !important;
            }
            .stButton > button,
            .stLinkButton > a {
                width: 100%;
            }
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    defaults = {
        "landing_seen": False,
        "authenticated": False,
        "user_id": None,
        "user_email": "",
        "user_avatar": "",
        "reset_token": "",
        "active_view": "Today",
        "onboarding_step": "welcome",
        "wellness_answers": {},
        "recommendation": {},
        "selected_article": None,
        "done_articles": set(),
        "progress_summary": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def logout() -> None:
    for key in [
        "landing_seen", "authenticated", "user_id", "user_email", "user_avatar",
        "reset_token", "onboarding_step", "wellness_answers", "recommendation",
        "selected_article", "progress_summary",
    ]:
        st.session_state.pop(key, None)
    init_session_state()
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
            "Backend returned an error. Check the FastAPI terminal. "
            f"Status: {response.status_code} {response.reason}"
        )
    else:
        st.error(
            "Backend is not reachable. Start it with: "
            "`python -m uvicorn app.main:app --reload --port 8010`"
        )


def display_name() -> str:
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


def action_key_for_group(group: dict) -> str:
    return f"{group.get('dimension', 'general')}:{group.get('action_title', 'action')}"


def appreciation_message(summary: dict) -> str:
    user_label = display_name()
    streak = summary.get("current_streak", 0)
    total_days = summary.get("total_action_days", 0)
    if total_days <= 1:
        return f"Nice start, {user_label}. One small action today is enough to begin."
    if streak > 1:
        return f"Beautiful consistency, {user_label}. You are on a {streak}-day happiness habit streak."
    return f"Well done, {user_label}. You showed up for yourself today."


def mark_action_done(group: dict) -> None:
    summary = record_action_completion(
        int(st.session_state["user_id"]),
        action_key_for_group(group),
        group.get("action_title", "Happiness action"),
    )
    st.session_state["progress_summary"] = summary
    st.success(appreciation_message(summary))


def markdown_card(title: str, body: str, emoji: str = "🌿") -> None:
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="big-emoji">{emoji}</div>
            <h3>{title}</h3>
            <p class="muted">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    st.markdown(
        f"""
        <section class="hero" aria-label="{APP_NAME} landing page">
            <div class="hero-card">
                <div class="kicker">Built for everyday India</div>
                <h1>{APP_NAME}</h1>
                <h2>{APP_TAGLINE}</h2>
                <p class="subtitle">
                    Start with a quick emotional and physical check-in. Get one simple happiness plan,
                    trusted positive reading, and tiny actions you can actually complete today.
                </p>
                <div>
                    <span class="pill">🧠 Mental calm</span>
                    <span class="pill">💪 Physical energy</span>
                    <span class="pill">📰 Positive stories</span>
                    <span class="pill">❤️ Simple actions</span>
                </div>
            </div>
            <div class="hero-card hero-visual">
                <div class="hero-emoji" aria-hidden="true">🌞</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### What you get in 2 minutes")
    c1, c2, c3 = st.columns(3)
    with c1:
        markdown_card("Check in", "Tell the app how your mind, body, sleep, stress, and time feel today.", "✅")
    with c2:
        markdown_card("Get clarity", "Receive a simple plan: one mind action, one body action, and one positive story.", "✨")
    with c3:
        markdown_card("Feel progress", "Mark actions done and build a gentle streak without scores or pressure.", "🌱")

    if st.button(f"Start {APP_NAME}", type="primary", use_container_width=True):
        st.session_state["landing_seen"] = True
        st.rerun()


def render_auth_screen() -> None:
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown(f"<div class='kicker'>Private daily happiness space</div>", unsafe_allow_html=True)
        st.title(f"Welcome to {APP_NAME}")
        st.write(
            "Create a simple account so your saved articles, check-ins, and action streak stay with you."
        )
        st.markdown(
            """
            <div class="mobile-note">
            <strong>Good to know:</strong> This app supports everyday wellbeing. It does not diagnose,
            treat, or replace medical, mental-health, or financial professionals.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        login_tab, register_tab, reset_tab = st.tabs(["Login", "Register", "Reset"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login", type="primary")
            if submitted:
                success, message, user = authenticate_user(email, password)
                if success and user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_email"] = user["email"]
                    st.session_state["user_avatar"] = user["avatar"]
                    st.session_state["progress_summary"] = progress_summary(user["id"])
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with register_tab:
            with st.form("register_form"):
                email = st.text_input("Email", key="register_email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", key="register_password")
                confirm_password = st.text_input("Confirm password", type="password", key="register_confirm_password")
                submitted = st.form_submit_button("Create account", type="primary")
            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(email, password)
                    st.success(message) if success else st.error(message)

        with reset_tab:
            st.caption("In local development, reset code is shown here if SMTP is not configured.")
            with st.form("request_reset_form"):
                email = st.text_input("Registered email", key="reset_request_email")
                submitted = st.form_submit_button("Generate reset code")
            if submitted:
                success, message, token = create_password_reset_token(email)
                if success:
                    st.success(message)
                    if token:
                        st.session_state["reset_token"] = token
                        st.code(token)
                else:
                    st.error(message)

            with st.form("reset_password_form"):
                email = st.text_input("Email", key="reset_email")
                token = st.text_input("Reset code", value=st.session_state.get("reset_token", ""), key="reset_code")
                new_password = st.text_input("New password", type="password", key="reset_new_password")
                confirm_password = st.text_input("Confirm new password", type="password", key="reset_confirm_password")
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


def render_welcome_screen() -> None:
    st.markdown("<div class='progress-strip'><div class='progress-dot active'></div><div class='progress-dot'></div><div class='progress-dot'></div><div class='progress-dot'></div></div>", unsafe_allow_html=True)
    st.title("Create today’s happiness plan")
    st.write(
        "You’ll answer a few simple questions. No scores, no diagnosis, no pressure. "
        "The goal is only to help you choose one useful next step today."
    )
    st.info(
        "If you feel unsafe, may harm yourself, have severe symptoms, or have a medical condition, "
        "please contact emergency services, a trusted person, or a qualified professional."
    )
    if st.button("I understand — start my check-in", type="primary", use_container_width=True):
        st.session_state["onboarding_step"] = "questions"
        st.rerun()


def render_wellness_questions() -> None:
    st.markdown("<div class='progress-strip'><div class='progress-dot active'></div><div class='progress-dot active'></div><div class='progress-dot active'></div><div class='progress-dot'></div></div>", unsafe_allow_html=True)
    st.title("Quick Daily Check-In")
    st.caption("Designed for mobile. Choose what feels closest today; you can retake it anytime.")

    with st.form("wellness_check_form"):
        st.subheader("1. Mind")
        mental_support = st.radio(
            "What would support your mind right now?",
            ["Calm my thoughts", "Feel a little uplifted", "Improve focus", "Wind down for rest", "Not sure"],
            index=1,
        )
        mental_effort = st.radio(
            "How much effort feels realistic?",
            ["Tiny action", "Short action", "Reading only", "Prefer not to say"],
            index=0,
        )

        st.subheader("2. Body")
        physical_state = st.radio(
            "How does your body feel today?",
            ["Okay", "Tired", "Stiff", "Restless", "Prefer not to say"],
            index=0,
        )
        movement_comfort = st.radio(
            "What movement feels safe and comfortable?",
            ["No movement today", "Seated stretch", "Short walk", "Either is fine"],
            index=3,
        )

        st.subheader("3. Energy & Boundaries")
        sleep_quality = st.radio(
            "How was your sleep or rest?",
            ["Good", "Average", "Poor", "Very poor", "Prefer not to say"],
            index=1,
        )
        stress_level = st.radio(
            "How heavy does today feel?",
            ["Light", "Manageable", "Heavy", "Overwhelming"],
            index=1,
        )
        time_available = st.radio(
            "How much time can you give yourself today?",
            ["2 minutes", "5 minutes", "10 minutes", "20+ minutes"],
            index=0,
        )

        st.subheader("4. Optional life-area focus")
        life_focus = st.radio(
            "Would you like one extra happiness angle today?",
            ["Keep it health-only", "Social connection", "Spiritual grounding", "Financial peace"],
            index=0,
        )

        st.subheader("5. Avoid today")
        avoid_today = st.radio(
            "What should the app avoid recommending today?",
            ["Deep reflection", "Breathing exercises", "Journaling", "Physical activity", "Money decisions", "No preference"],
            index=5,
        )

        submitted = st.form_submit_button("Create my happiness plan", type="primary")

    if submitted:
        answers = map_simple_answers_to_recommendation_rules(
            mental_support=mental_support,
            mental_effort=mental_effort,
            physical_state=physical_state,
            movement_comfort=movement_comfort,
            sleep_quality=sleep_quality,
            stress_level=stress_level,
            time_available=time_available,
            life_focus=life_focus,
            avoid_today=avoid_today,
        )
        try:
            checkin = record_checkin(int(st.session_state["user_id"]), answers)
            recommendation_answers = {**answers, "_same_response_days": str(checkin["same_response_days"])}
            st.session_state["recommendation"] = fetch_recommendation(recommendation_answers)
            st.session_state["wellness_answers"] = recommendation_answers
            st.session_state["onboarding_step"] = "home"
            st.rerun()
        except (requests.RequestException, ValueError) as exc:
            show_api_error(exc)


def map_simple_answers_to_recommendation_rules(**kwargs) -> dict:
    life_focus = kwargs["life_focus"]
    avoid_today = kwargs["avoid_today"]
    stress_level = kwargs["stress_level"]
    sleep_quality = kwargs["sleep_quality"]
    time_available = kwargs["time_available"]

    mental_avoid = "No preference"
    physical_boundary = "No preference"
    money_boundary = "No preference"
    if avoid_today in {"Deep reflection", "Breathing exercises", "Journaling"}:
        mental_avoid = avoid_today
    elif avoid_today == "Physical activity":
        physical_boundary = "Avoid physical activity"
    elif avoid_today == "Money decisions":
        money_boundary = "No decisions today"

    money_support = "Not sure"
    money_action = "No task today"
    connection_need = "Not sure"
    social_comfort = "No social task today"
    privacy_preference = "Simple action ideas are okay"
    grounding_need = "Not sure"
    spiritual_practice = "No practice today"
    spiritual_boundary = "No preference"

    if life_focus == "Social connection":
        connection_need = "Send a kind message" if stress_level != "Overwhelming" else "Appreciate someone privately"
        social_comfort = "Send a simple message" if time_available != "2 minutes" else "Private reflection"
        privacy_preference = "Keep this private" if stress_level == "Overwhelming" else "Simple action ideas are okay"
    elif life_focus == "Spiritual grounding":
        grounding_need = "Nature or quiet" if stress_level in {"Heavy", "Overwhelming"} else "Gratitude"
        spiritual_practice = "Short silence" if time_available in {"5 minutes", "10 minutes", "20+ minutes"} else "One sentence reflection"
    elif life_focus == "Financial peace":
        money_support = "Reduce money anxiety"
        money_action = "Read only" if avoid_today == "Money decisions" else "Check one bill date"
        money_boundary = money_boundary if money_boundary != "No preference" else "No decisions today"

    if sleep_quality in {"Poor", "Very poor"}:
        mental_support = "Wind down for rest"
    elif stress_level == "Overwhelming":
        mental_support = "Calm my thoughts"
    else:
        mental_support = kwargs["mental_support"]

    return {
        "mental_support": mental_support,
        "mental_effort": kwargs["mental_effort"],
        "mental_avoid": mental_avoid,
        "physical_state": kwargs["physical_state"],
        "movement_comfort": kwargs["movement_comfort"],
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
        "sleep_quality": sleep_quality,
        "stress_level": stress_level,
        "time_available": time_available,
        "life_focus": life_focus,
    }


def save_or_unsave_button(article: dict, saved_urls: set[str], key_prefix: str) -> None:
    if article["url"] in saved_urls:
        if st.button("Saved ✓", key=f"{key_prefix}_unsave_{article['url']}", use_container_width=True):
            unsave_article_for_user(int(st.session_state["user_id"]), article["url"])
            st.success("Removed from saved articles.")
            st.rerun()
    elif st.button("Save", key=f"{key_prefix}_save_{article['url']}", use_container_width=True):
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

    if st.button("← Back to today’s plan"):
        st.session_state["selected_article"] = None
        st.rerun()

    st.title(article["title"])
    meta = [f"Source: {article['source']}", f"Area: {article['category'].title()}"]
    published = format_date(article.get("published_at", ""))
    if published:
        meta.append(f"Published: {published}")
    st.caption(" • ".join(meta))

    with st.container(border=True):
        st.subheader("Why this is recommended")
        st.write(group.get("reason", "This article matches your check-in and boundaries for today."))
        st.subheader("Quick summary")
        st.write(article.get("summary") or "This resource offers a practical wellness idea you can explore today.")

    with st.container(border=True):
        st.subheader("Try this now")
        st.markdown(f"**{group.get('action_title', 'Take one small idea from this article today.')}**")
        if group.get("activity_minutes"):
            st.caption(f"Estimated effort: {group['activity_minutes']} minutes")
        for step in group.get("action_steps", []):
            st.write(f"- {step}")
        if group.get("progress_note"):
            st.info(group["progress_note"])
        if st.button("Mark action done", type="primary", use_container_width=True):
            st.session_state["done_articles"].add(article["url"])
            mark_action_done(group)

    st.subheader("Reflection")
    st.radio("How do you feel after this?", ["A little better", "Same", "Worse", "Not sure"], horizontal=True, key=f"reflection_{article['url']}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        save_or_unsave_button(article, saved_urls, "detail")
    with col_b:
        st.link_button("Open full article", article["url"], use_container_width=True)
    with col_c:
        st.link_button("Share link", article["url"], use_container_width=True)


def render_article_card(article: dict, saved_urls: set[str], key_prefix: str) -> None:
    with st.container(border=True):
        st.markdown(f"<span class='pill'>📰 {article.get('category', 'Wellness').title()}</span>", unsafe_allow_html=True)
        st.subheader(article["title"])
        if article.get("summary"):
            st.write(summarize_words(article["summary"], 52))
        meta = [f"Source: {article['source']}"]
        published = format_date(article.get("published_at", ""))
        if published:
            meta.append(f"Published: {published}")
        st.caption(" • ".join(meta))
        col_a, col_b, col_c = st.columns([1.2, 0.8, 1])
        if col_a.button("Action page", key=f"{key_prefix}_open_{article['url']}", type="primary", use_container_width=True):
            st.session_state["selected_article"] = article
            st.rerun()
        with col_b:
            save_or_unsave_button(article, saved_urls, key_prefix)
        col_c.link_button("Read", article["url"], use_container_width=True)


def render_recommendation_group(group: dict, saved_urls: set[str]) -> None:
    dimension_emoji = {
        "mental": "🧠",
        "physical": "💪",
        "social": "❤️",
        "financial": "₹",
        "spiritual": "🌿",
    }.get(group.get("dimension"), "✨")

    with st.container(border=True):
        st.markdown(f"<span class='pill'>{dimension_emoji} {group.get('title', 'Recommended action')}</span>", unsafe_allow_html=True)
        st.markdown(f"### {group.get('action_title', 'Suggested action')}")
        if group.get("activity_minutes"):
            st.caption(f"Estimated effort: {group['activity_minutes']} minutes")
        for step in group.get("action_steps", []):
            st.write(f"- {step}")
        if group.get("progress_note"):
            st.info(group["progress_note"])
        st.caption(group.get("reason", "Matched to your check-in."))
        st.markdown(f"**Small insight:** {group.get('insight', 'Small actions count.')}" )
        if st.button("I did this", key=f"done_{action_key_for_group(group)}", type="primary", use_container_width=True):
            mark_action_done(group)

        articles = group.get("articles", [])[:2]
        if articles:
            st.markdown("#### Positive reading matched to this action")
            for article in articles:
                render_article_card(article, saved_urls, f"{group.get('dimension', 'group')}_trusted")


def render_today_dashboard() -> None:
    recommendation = st.session_state.get("recommendation", {})
    groups = recommendation.get("groups", [])
    saved_urls = get_saved_article_urls(int(st.session_state["user_id"]))
    summary = st.session_state.get("progress_summary") or progress_summary(int(st.session_state["user_id"]))
    st.session_state["progress_summary"] = summary

    st.markdown("<div class='progress-strip'><div class='progress-dot active'></div><div class='progress-dot active'></div><div class='progress-dot active'></div><div class='progress-dot active'></div></div>", unsafe_allow_html=True)
    st.title(f"{greeting()}, {display_name()}")
    st.write("Here is your simple happiness plan for today. Start with just one action.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Action streak", f"{summary.get('current_streak', 0)} days")
    col2.metric("Action days", summary.get("total_action_days", 0))
    col3.metric("Today", "Done" if summary.get("today_completed") else "Open")

    if summary.get("today_completed"):
        st.success("Today is marked. Small progress is still real progress.")
    else:
        st.info("Choose one action below and mark it done. No perfection needed.")

    with st.container(border=True):
        st.subheader("Today’s happiness focus")
        st.write(recommendation.get("today_focus", "Choose one gentle next step"))
        for item in recommendation.get("plan", [])[:4]:
            st.markdown(f"<span class='pill'>✓ {item}</span>", unsafe_allow_html=True)

    st.subheader("Your recommended actions")
    st.caption(recommendation.get("source_policy", "Recommendations use trusted wellness sources."))

    if not groups:
        st.info("No recommendations are available yet. Refresh feeds or retake your check-in.")
        return

    for group in groups[:4]:
        render_recommendation_group(group, saved_urls)


def render_saved_articles() -> None:
    saved_articles = list_saved_articles(int(st.session_state["user_id"]))
    st.title("Saved Articles")
    st.write("Your personal library of positive and useful resources.")
    if not saved_articles:
        st.info("You have not saved any articles yet.")
        return
    for article in saved_articles:
        with st.container(border=True):
            st.subheader(article["title"])
            if article["summary"]:
                st.write(summarize_words(article["summary"], 90))
            saved = format_date(article.get("saved_at", ""))
            st.caption(" • ".join(item for item in [f"Source: {article['source']}", f"Area: {article['category'].title()}", f"Saved: {saved}" if saved else ""] if item))
            col_a, col_b = st.columns([1, 1])
            col_a.link_button("Read full article", article["url"], use_container_width=True)
            if col_b.button("Remove saved", key=f"remove_{article['url']}", use_container_width=True):
                unsave_article_for_user(int(st.session_state["user_id"]), article["url"])
                st.success("Removed from saved articles.")
                st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## 🌿 {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.markdown(f"### {st.session_state['user_avatar']} {st.session_state['user_email']}")
        st.session_state["active_view"] = st.radio("Go to", ["Today", "Saved Articles", "Retake Check-In"])
        st.button("Logout", on_click=logout, use_container_width=True)
        st.divider()
        st.header("Tools")
        if st.button("Refresh positive resources", type="primary", use_container_width=True):
            with st.spinner("Fetching practical wellness content..."):
                try:
                    result = refresh_feed()
                    st.success(f"Saved {result['articles_saved']} new articles from {result['feeds_checked']} feeds.")
                    if result["errors"]:
                        st.warning("Some sources were unavailable or rate-limited.")
                    if st.session_state.get("wellness_answers"):
                        st.session_state["recommendation"] = fetch_recommendation(st.session_state["wellness_answers"])
                except (requests.RequestException, ValueError) as exc:
                    show_api_error(exc)
        st.caption(f"Backend: {API_BASE_URL}")


def main() -> None:
    apply_theme()
    init_session_state()

    if not st.session_state["landing_seen"] and not st.session_state["authenticated"]:
        render_landing_page()
        st.stop()

    if not st.session_state["authenticated"]:
        render_auth_screen()
        st.stop()

    render_sidebar()

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
        render_saved_articles()
        st.stop()

    if st.session_state.get("selected_article"):
        render_article_action_page(st.session_state["selected_article"])
    else:
        if not st.session_state.get("recommendation"):
            try:
                st.session_state["recommendation"] = fetch_recommendation(st.session_state.get("wellness_answers", {}))
            except (requests.RequestException, ValueError) as exc:
                show_api_error(exc)
                st.stop()
        render_today_dashboard()


if __name__ == "__main__":
    main()
