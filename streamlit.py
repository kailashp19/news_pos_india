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
    page_title="India Holistic Wellness Feed",
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
            --bg: #151a1e;
            --surface: #1f262b;
            --surface-soft: #263038;
            --border: #3a454e;
            --text: #eef3f2;
            --muted: #aab7b7;
            --accent: #62d6a4;
            --accent-strong: #35b887;
            --accent-blue: #8fc7ff;
            --danger: #ff8d8d;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(98, 214, 164, 0.08), transparent 32rem),
                linear-gradient(180deg, #182026 0%, var(--bg) 42%, #12171a 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #202a30 0%, #1a2025 100%);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        [data-testid="stMetric"] {
            background: rgba(31, 38, 43, 0.92);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(31, 38, 43, 0.9);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 14px 34px rgba(0, 0, 0, 0.2);
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
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
            gap: 8px;
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
            background: #151b20 !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stTextInput"] div,
        [data-baseweb="input"],
        [data-baseweb="input"] input {
            background-color: #151b20 !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        [data-testid="stTextInput"] input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }

        [data-testid="stForm"] {
            background: rgba(31, 38, 43, 0.72);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }

        .stButton > button,
        .stLinkButton > a {
            border-radius: 8px;
            border: 1px solid var(--border);
            background: #253039;
            color: var(--text);
            font-weight: 600;
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            border-color: var(--accent);
            background: #2b3a42;
            color: var(--text);
        }

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, var(--accent-strong), #4fc3a1);
            border-color: transparent !important;
            color: #071512 !important;
        }

        button[data-baseweb="tab"] {
            color: var(--muted) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom-color: var(--accent) !important;
        }

        [data-baseweb="tab-highlight"] {
            background-color: var(--accent) !important;
        }

        [data-testid="stAlert"] {
            background: rgba(38, 48, 56, 0.96);
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
            background: #101518;
            color: var(--accent);
        }

        .stSlider [data-baseweb="slider"] {
            color: var(--accent);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("user_email", "")
    st.session_state.setdefault("user_avatar", "")
    st.session_state.setdefault("reset_token", "")
    st.session_state.setdefault("active_view", "Feed")


def logout() -> None:
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["user_email"] = ""
    st.session_state["user_avatar"] = ""
    st.session_state["reset_token"] = ""
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


def render_auth_screen() -> None:
    st.title("India Holistic Wellness Feed")

    login_tab, register_tab, reset_tab = st.tabs(
        ["Login", "Register", "Forgot Password"]
    )

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            success, message, user = authenticate_user(email, password)
            if success and user:
                st.session_state["authenticated"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_email"] = user["email"]
                st.session_state["user_avatar"] = user["avatar"]
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with register_tab:
        with st.form("register_form"):
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
                success, message = register_user(email, password)
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

if not st.session_state["authenticated"]:
    render_auth_screen()
    st.stop()


st.title("India Holistic Wellness Feed")

with st.sidebar:
    st.markdown(
        f"### {st.session_state['user_avatar']} {st.session_state['user_email']}"
    )
    st.session_state["active_view"] = st.radio(
        "View",
        ["Feed", "Saved Articles"],
    )
    st.button("Logout", on_click=logout, use_container_width=True)
    st.divider()

with st.sidebar:
    st.header("Filters")
    selected_dimension = st.selectbox(
        "Wellness area",
        options=list(DIMENSION_OPTIONS.keys()),
    )
    dimension = DIMENSION_OPTIONS[selected_dimension]
    min_score = st.slider(
        "Minimum practical relevance",
        min_value=0.3,
        max_value=0.95,
        value=0.55,
        step=0.05,
    )
    limit = st.slider("Articles", min_value=10, max_value=100, value=50, step=10)

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
            except (requests.RequestException, ValueError) as exc:
                show_api_error(exc)

try:
    stats = fetch_stats(dimension)
    articles = fetch_articles(min_score=min_score, limit=limit, dimension=dimension)
except (requests.RequestException, ValueError) as exc:
    show_api_error(exc)
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Saved resources", stats.get("total_articles") or 0)
col2.metric("Average relevance", stats.get("average_score") or 0)
col3.metric("Showing", len(articles))
st.caption(f"Backend: {API_BASE_URL}")

st.divider()

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

if not articles:
    st.info("No India-focused wellness resources match these filters yet. Try another wellness area, lowering the threshold, or refreshing feeds.")
else:
    saved_urls = get_saved_article_urls(int(st.session_state["user_id"]))
    for article in articles:
        with st.container(border=True):
            st.subheader(article["title"])

            if article["summary"]:
                st.write(summarize_words(article["summary"], 100))

            meta = [
                f"Source: {article['source']}",
                f"Wellness area: {article['category'].title()}",
                f"Practical relevance: {article['positivity_score']:.2f}",
            ]
            published = format_date(article["published_at"])
            if published:
                meta.append(f"Published: {published}")

            st.caption(" | ".join(meta))
            col_a, col_b = st.columns([1, 1])
            col_a.link_button("Read full article", article["url"])
            if article["url"] in saved_urls:
                if col_b.button(
                    "Saved",
                    key=f"unsave_{article['url']}",
                    use_container_width=True,
                ):
                    unsave_article_for_user(
                        int(st.session_state["user_id"]),
                        article["url"],
                    )
                    st.success("Removed from saved articles.")
                    st.rerun()
            elif col_b.button(
                "Save article",
                key=f"save_{article['url']}",
                use_container_width=True,
            ):
                save_article_for_user(int(st.session_state["user_id"]), article)
                st.success("Article saved.")
                st.rerun()
