from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from app.db import connect


EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"^[A-Z0-9]+$", re.IGNORECASE)
PBKDF2_ITERATIONS = 260_000
RESET_TOKEN_MINUTES = 20
AVATAR_PALETTE = (
    "🧘",
    "🌿",
    "☀️",
    "🏃",
    "📚",
    "💪",
    "🪷",
    "✨",
    "🧠",
    "💰",
)


def init_auth_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                avatar_seed TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(connection, "users", "username", "TEXT NOT NULL DEFAULT ''")
        ensure_column(connection, "users", "avatar_seed", "TEXT NOT NULL DEFAULT ''")
        backfill_usernames(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique
            ON users (username)
            WHERE username != ''
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used_at TEXT DEFAULT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                article_url TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, article_url),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )


def ensure_column(connection, table: str, column: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_username(username: str) -> str:
    return username.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(normalize_email(email)))


def is_valid_username(username: str) -> bool:
    username = normalize_username(username)
    return 3 <= len(username) <= 24 and bool(USERNAME_PATTERN.fullmatch(username))


def username_from_email(email: str, fallback_id: int) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", email.split("@", 1)[0]).lower()
    return base[:18] or f"user{fallback_id}"


def backfill_usernames(connection) -> None:
    rows = connection.execute(
        """
        SELECT id, email, username
        FROM users
        WHERE username = ''
        ORDER BY id
        """
    ).fetchall()
    used = {
        row["username"]
        for row in connection.execute(
            "SELECT username FROM users WHERE username != ''"
        ).fetchall()
    }
    for row in rows:
        candidate = username_from_email(row["email"], row["id"])
        username = candidate
        suffix = 2
        while username in used:
            username = f"{candidate[:18]}{suffix}"
            suffix += 1
        used.add(username)
        connection.execute(
            """
            UPDATE users
            SET username = ?, avatar_seed = ?
            WHERE id = ?
            """,
            (username, username, row["id"]),
        )


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations),
    ).hex()
    return hmac.compare_digest(actual_hash, expected_hash)


def get_user_by_email(email: str) -> dict | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, email, password_hash, avatar_seed, created_at
            FROM users
            WHERE email = ?
            """,
            (normalize_email(email),),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_username(username: str) -> dict | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, email, password_hash, avatar_seed, created_at
            FROM users
            WHERE username = ?
            """,
            (normalize_username(username),),
        ).fetchone()
        return dict(row) if row else None


def avatar_for_seed(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    emoji = AVATAR_PALETTE[int(digest[:8], 16) % len(AVATAR_PALETTE)]
    return f"{emoji} {digest[:6].upper()}"


def send_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    host = os.getenv("SMTP_HOST", "")
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM", username)
    port = int(os.getenv("SMTP_PORT", "587"))

    if not host or not username or not password or not from_email:
        return False, "SMTP is not configured, so the code is shown in the app."

    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
    except OSError as exc:
        return False, f"Could not send email: {exc}"
    except smtplib.SMTPException as exc:
        return False, f"Could not send email: {exc}"

    return True, "Email sent."


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    username = normalize_username(username)
    email = normalize_email(email)
    if not is_valid_username(username):
        return False, "Username must be 3-24 letters or numbers only."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if get_user_by_username(username):
        return False, "This username is already registered."
    if get_user_by_email(email):
        return False, "This email is already registered."

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO users (username, email, password_hash, avatar_seed)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, hash_password(password), username),
        )

    return True, "Registration successful. You can now log in."


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    if not is_valid_username(username):
        return False, "Username must be 3-24 letters or numbers only.", None
    user = get_user_by_username(username)
    if not user:
        return False, "Username is not registered.", None
    if not verify_password(password, user["password_hash"]):
        return False, "Password does not match.", None
    return True, "Login successful.", {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "avatar": avatar_for_seed(user["username"]),
    }


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(email: str) -> tuple[bool, str, str | None]:
    user = get_user_by_email(email)
    if not user:
        return False, "Email is not registered.", None

    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_MINUTES)
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
            """,
            (user["id"], hash_token(token), expires_at.isoformat()),
        )
    subject = "Reset your Joyverse password"
    body = (
        "Use this code to reset your password:\n\n"
        f"{token}\n\n"
        f"This code expires in {RESET_TOKEN_MINUTES} minutes."
    )
    email_sent, delivery_message = send_email(user["email"], subject, body)
    message = (
        f"Reset code sent to {user['email']}."
        if email_sent
        else delivery_message
    )
    return True, message, token if not email_sent else None


def reset_password(email: str, token: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long."

    user = get_user_by_email(email)
    if not user:
        return False, "Email is not registered."

    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, expires_at, used_at
            FROM password_reset_tokens
            WHERE user_id = ? AND token_hash = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user["id"], hash_token(token.strip())),
        ).fetchone()

        if not row or row["used_at"]:
            return False, "Reset code is invalid."

        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at < datetime.now(timezone.utc):
            return False, "Reset code has expired."

        connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (hash_password(new_password), user["id"]),
        )
        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), row["id"]),
        )

    return True, "Password reset successful. You can now log in."


def save_article_for_user(user_id: int, article: dict) -> tuple[bool, str]:
    with connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO saved_articles (
                user_id,
                article_url,
                title,
                source,
                summary,
                category,
                published_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                article.get("url", ""),
                article.get("title", ""),
                article.get("source", ""),
                article.get("summary", ""),
                article.get("category", ""),
                article.get("published_at", ""),
            ),
        )
    return True, "Article saved."


def unsave_article_for_user(user_id: int, article_url: str) -> None:
    with connect() as connection:
        connection.execute(
            """
            DELETE FROM saved_articles
            WHERE user_id = ? AND article_url = ?
            """,
            (user_id, article_url),
        )


def get_saved_article_urls(user_id: int) -> set[str]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT article_url
            FROM saved_articles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        return {row["article_url"] for row in rows}


def list_saved_articles(user_id: int) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT article_url AS url,
                   title,
                   source,
                   summary,
                   category,
                   published_at,
                   saved_at
            FROM saved_articles
            WHERE user_id = ?
            ORDER BY saved_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
