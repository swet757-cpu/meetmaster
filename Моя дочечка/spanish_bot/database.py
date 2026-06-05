from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "words.db"
WORDS_SOURCE_PATH = BASE_DIR / "words_source.json"

INTERVAL_STEPS = (1, 3, 7, 14, 30)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                association TEXT NOT NULL,
                example TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                interval INTEGER DEFAULT 1,
                next_review TEXT NOT NULL,
                PRIMARY KEY (user_id, word_id),
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_progress_user_next_review
            ON progress (user_id, next_review)
            """
        )
        conn.commit()

    load_words_once()


def load_words_once() -> None:
    if not WORDS_SOURCE_PATH.exists():
        raise FileNotFoundError(f"Не найден файл словаря: {WORDS_SOURCE_PATH}")

    with get_connection() as conn:
        words_count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        if words_count:
            return

        words = json.loads(WORDS_SOURCE_PATH.read_text(encoding="utf-8"))
        rows = [
            (
                item["word"].strip(),
                item["translation"].strip(),
                item["association"].strip(),
                item["example"].strip(),
            )
            for item in words
        ]
        conn.executemany(
            """
            INSERT INTO words (word, translation, association, example)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def ensure_user_progress(user_id: int) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO progress (user_id, word_id, interval, next_review)
            SELECT ?, id, 1, ?
            FROM words
            """,
            (user_id, now),
        )
        conn.commit()


def get_next_word_for_review(user_id: int) -> Optional[sqlite3.Row]:
    ensure_user_progress(user_id)
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                w.id,
                w.word,
                w.translation,
                w.association,
                w.example,
                p.interval,
                p.next_review
            FROM progress p
            JOIN words w ON w.id = p.word_id
            WHERE p.user_id = ?
              AND p.next_review <= ?
            ORDER BY p.next_review ASC, w.id ASC
            LIMIT 1
            """,
            (user_id, now),
        ).fetchone()


def update_progress(user_id: int, word_id: int, remembered: bool) -> int:
    ensure_user_progress(user_id)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT interval
            FROM progress
            WHERE user_id = ? AND word_id = ?
            """,
            (user_id, word_id),
        ).fetchone()

        current_interval = int(row["interval"]) if row else 1
        new_interval = _next_interval(current_interval) if remembered else 1
        next_review_at = datetime.now() + timedelta(days=new_interval) if remembered else datetime.now()
        next_review = next_review_at.isoformat(timespec="seconds")

        conn.execute(
            """
            UPDATE progress
            SET interval = ?, next_review = ?
            WHERE user_id = ? AND word_id = ?
            """,
            (new_interval, next_review, user_id, word_id),
        )
        conn.commit()

    return new_interval


def get_stats(user_id: int) -> dict[str, int]:
    ensure_user_progress(user_id)
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM progress WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        due = conn.execute(
            """
            SELECT COUNT(*)
            FROM progress
            WHERE user_id = ? AND next_review <= ?
            """,
            (user_id, now),
        ).fetchone()[0]
        learned = conn.execute(
            """
            SELECT COUNT(*)
            FROM progress
            WHERE user_id = ? AND interval >= 30
            """,
            (user_id,),
        ).fetchone()[0]

    return {"total": total, "due": due, "learned": learned}


def _next_interval(current_interval: int) -> int:
    for step in INTERVAL_STEPS:
        if current_interval < step:
            return step

    current_index = INTERVAL_STEPS.index(current_interval) if current_interval in INTERVAL_STEPS else 0
    next_index = min(current_index + 1, len(INTERVAL_STEPS) - 1)
    return INTERVAL_STEPS[next_index]
