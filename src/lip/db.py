import os
import logging
from contextlib import contextmanager
from typing import Optional

import mysql.connector
from mysql.connector import Error

logger = logging.getLogger("lip")

DB_CONFIG = {
    "host": os.getenv("LIP_DB_HOST", "localhost"),
    "user": os.getenv("LIP_DB_USER", "root"),
    "password": os.getenv("LIP_DB_PASSWORD", ""),
    "database": os.getenv("LIP_DB_NAME", "lip"),
    "charset": "utf8mb4",
}


@contextmanager
def get_cursor(dictionary: bool = True):
    """Context manager for safe MySQL connections."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def insert_url(url: str, title: Optional[str] = None) -> Optional[int]:
    """Insert URL (ignore duplicates) and return id."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT IGNORE INTO url (url, title) VALUES (%s, %s)",
            (url, title),
        )
        if cur.lastrowid:
            return cur.lastrowid
        # already existed – fetch id
        cur.execute("SELECT id FROM url WHERE url = %s", (url,))
        row = cur.fetchone()
        return row["id"] if row else None


def insert_keyword(keyword: str) -> Optional[int]:
    """Insert keyword (ignore duplicates) and return id."""
    keyword = keyword.strip().lower()
    if not keyword or len(keyword) < 2:
        return None
    with get_cursor() as cur:
        cur.execute(
            "INSERT IGNORE INTO keyword (keyword) VALUES (%s)",
            (keyword,),
        )
        if cur.lastrowid:
            return cur.lastrowid
        cur.execute("SELECT id FROM keyword WHERE keyword = %s", (keyword,))
        row = cur.fetchone()
        return row["id"] if row else None


def link_keyword_to_url(keyword_id: int, url_id: int) -> None:
    """Create many-to-many link."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT IGNORE INTO keyword2url (keyword_id, url_id) VALUES (%s, %s)",
            (keyword_id, url_id),
        )


def insert_image(url_id: int, image_url: str, alt_text: str = "") -> Optional[int]:
    """Store an image linked to a URL."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO image (url_id, image_url, alt_text) VALUES (%s, %s, %s)",
            (url_id, image_url, alt_text[:500] if alt_text else None),
        )
        return cur.lastrowid
