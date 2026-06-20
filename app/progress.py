from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from app.db import connect


QUESTION_KEYS = (
    "mental_support",
    "mental_effort",
    "mental_avoid",
    "physical_state",
    "movement_comfort",
    "physical_boundary",
    "connection_need",
    "social_comfort",
    "privacy_preference",
    "money_support",
    "money_action",
    "money_boundary",
    "grounding_need",
    "spiritual_practice",
    "spiritual_boundary",
)


def init_progress_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS wellness_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                response_signature TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, checkin_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_checkins_user_signature_date
            ON wellness_checkins (user_id, response_signature, checkin_date)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                completion_date TEXT NOT NULL,
                action_key TEXT NOT NULL,
                action_title TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, completion_date, action_key),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_actions_user_date
            ON recommendation_actions (user_id, completion_date)
            """
        )


def canonical_answers(answers: dict) -> dict:
    return {key: str(answers.get(key, "")) for key in QUESTION_KEYS}


def response_signature(answers: dict) -> str:
    payload = json.dumps(canonical_answers(answers), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def today_iso() -> str:
    return date.today().isoformat()


def record_checkin(user_id: int, answers: dict) -> dict:
    init_progress_db()
    checkin_date = today_iso()
    signature = response_signature(answers)
    answers_json = json.dumps(canonical_answers(answers), sort_keys=True)

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO wellness_checkins (
                user_id,
                checkin_date,
                response_signature,
                answers_json
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, checkin_date) DO UPDATE SET
                response_signature = excluded.response_signature,
                answers_json = excluded.answers_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, checkin_date, signature, answers_json),
        )

    return {
        "response_signature": signature,
        "same_response_days": same_response_days(user_id, signature, date.today()),
    }


def same_response_days(user_id: int, signature: str, start: date | None = None) -> int:
    init_progress_db()
    cursor = start or date.today()
    days = 0
    with connect() as connection:
        while True:
            row = connection.execute(
                """
                SELECT 1
                FROM wellness_checkins
                WHERE user_id = ?
                  AND checkin_date = ?
                  AND response_signature = ?
                """,
                (user_id, cursor.isoformat(), signature),
            ).fetchone()
            if not row:
                break
            days += 1
            cursor -= timedelta(days=1)
    return days


def action_completion_dates(user_id: int) -> set[str]:
    init_progress_db()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT completion_date
            FROM recommendation_actions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
    return {row["completion_date"] for row in rows}


def streak_from_dates(dates: set[str], start: date) -> int:
    cursor = start
    streak = 0
    while cursor.isoformat() in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def progress_summary(user_id: int) -> dict:
    dates = action_completion_dates(user_id)
    today = date.today()
    today_completed = today.isoformat() in dates
    streak_start = today if today_completed else today - timedelta(days=1)
    return {
        "today_completed": today_completed,
        "current_streak": streak_from_dates(dates, streak_start),
        "total_action_days": len(dates),
        "last_completed": max(dates) if dates else "",
    }


def record_action_completion(
    user_id: int,
    action_key: str,
    action_title: str,
) -> dict:
    init_progress_db()
    with connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO recommendation_actions (
                user_id,
                completion_date,
                action_key,
                action_title
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, today_iso(), action_key, action_title),
        )
    return progress_summary(user_id)
