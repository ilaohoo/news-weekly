import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List

from src.config import DB_PATH
from src.models import NewsItem


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                published TEXT,
                summary TEXT,
                category TEXT,
                collected_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collected ON news(collected_at)")


def save_items(items: List[NewsItem]) -> int:
    saved = 0
    with _conn() as conn:
        for it in items:
            try:
                conn.execute(
                    """INSERT INTO news (title, url, source, published, summary, category, collected_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (it.title, it.url, it.source, it.published,
                     it.summary, it.category, it.collected_at),
                )
                saved += 1
            except sqlite3.IntegrityError:
                continue
    return saved


def get_recent_items(days: int = 7) -> List[NewsItem]:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM news WHERE collected_at >= ? ORDER BY collected_at DESC",
            (cutoff,),
        ).fetchall()
    return [
        NewsItem(
            title=r["title"], url=r["url"], source=r["source"],
            published=r["published"], summary=r["summary"] or "",
            category=r["category"] or "", collected_at=r["collected_at"],
        )
        for r in rows
    ]


def cleanup_old(days: int = 30) -> None:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        conn.execute("DELETE FROM news WHERE collected_at < ?", (cutoff,))
