"""
Scraper Database Layer
=======================
Local SQLite database for all scraped Goose Ecosystem data.

Tables:
  products   — Goose Mart industrial hardware catalog
  engineers  — HireMyEngineer talent profiles
  courses    — Goose Elevate training catalog
  services   — Goose Solutions service offerings

Design decisions:
  - SQLite (stdlib sqlite3) — no extra dependencies, sense-api is Python
  - Upsert deduplication on (name, link) composite key
  - source + last_updated tracked for every row
  - Full-text LIKE search on name, category/skills/level/industry fields
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Dict, Any

from core.config import SCRAPER_DB_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS products (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name   TEXT    NOT NULL,
    category       TEXT    DEFAULT '',
    specifications TEXT    DEFAULT '',
    price          TEXT    DEFAULT '',
    product_link   TEXT    DEFAULT '',
    source         TEXT    DEFAULT '',
    scraped_at     TIMESTAMP,
    last_updated   TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_products_dedup
    ON products(product_name, product_link);

CREATE TABLE IF NOT EXISTS engineers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    engineer_name  TEXT    NOT NULL,
    skills         TEXT    DEFAULT '',
    experience     TEXT    DEFAULT '',
    profile_link   TEXT    DEFAULT '',
    source         TEXT    DEFAULT '',
    scraped_at     TIMESTAMP,
    last_updated   TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_engineers_dedup
    ON engineers(engineer_name, profile_link);

CREATE TABLE IF NOT EXISTS courses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name    TEXT    NOT NULL,
    duration       TEXT    DEFAULT '',
    level          TEXT    DEFAULT '',
    course_link    TEXT    DEFAULT '',
    source         TEXT    DEFAULT '',
    scraped_at     TIMESTAMP,
    last_updated   TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_courses_dedup
    ON courses(course_name, course_link);

CREATE TABLE IF NOT EXISTS services (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name   TEXT    NOT NULL,
    industry       TEXT    DEFAULT '',
    description    TEXT    DEFAULT '',
    service_link   TEXT    DEFAULT '',
    source         TEXT    DEFAULT '',
    scraped_at     TIMESTAMP,
    last_updated   TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_services_dedup
    ON services(service_name, service_link);
"""


# ---------------------------------------------------------------------------
# Connection context manager
# ---------------------------------------------------------------------------

@contextmanager
def _conn():
    """Thread-safe SQLite connection with WAL mode for concurrent reads."""
    con = sqlite3.connect(SCRAPER_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables and indexes if they don't exist."""
    with _conn() as con:
        con.executescript(_DDL)
    logger.info("[DB] Initialized SQLite database at %s", SCRAPER_DB_PATH)


# ---------------------------------------------------------------------------
# Upsert helpers  (INSERT or UPDATE last_updated on conflict)
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(sep=" ")


def upsert_products(rows: List[Dict[str, Any]]) -> int:
    """
    Upsert rows into products table.
    Dedup key: (product_name, product_link)
    Returns number of rows affected.
    """
    sql = """
    INSERT INTO products (product_name, category, specifications, price,
                          product_link, source, scraped_at, last_updated)
    VALUES (:product_name, :category, :specifications, :price,
            :product_link, :source, :scraped_at, :last_updated)
    ON CONFLICT(product_name, product_link) DO UPDATE SET
        category       = excluded.category,
        specifications = excluded.specifications,
        price          = excluded.price,
        source         = excluded.source,
        last_updated   = excluded.last_updated
    """
    ts = _now()
    enriched = [{**r, "scraped_at": ts, "last_updated": ts} for r in rows]
    with _conn() as con:
        con.executemany(sql, enriched)
    logger.info("[DB] upsert_products: %d rows", len(enriched))
    return len(enriched)


def upsert_engineers(rows: List[Dict[str, Any]]) -> int:
    """
    Upsert rows into engineers table.
    Dedup key: (engineer_name, profile_link)
    """
    sql = """
    INSERT INTO engineers (engineer_name, skills, experience,
                           profile_link, source, scraped_at, last_updated)
    VALUES (:engineer_name, :skills, :experience,
            :profile_link, :source, :scraped_at, :last_updated)
    ON CONFLICT(engineer_name, profile_link) DO UPDATE SET
        skills       = excluded.skills,
        experience   = excluded.experience,
        source       = excluded.source,
        last_updated = excluded.last_updated
    """
    ts = _now()
    enriched = [{**r, "scraped_at": ts, "last_updated": ts} for r in rows]
    with _conn() as con:
        con.executemany(sql, enriched)
    logger.info("[DB] upsert_engineers: %d rows", len(enriched))
    return len(enriched)


def upsert_courses(rows: List[Dict[str, Any]]) -> int:
    """
    Upsert rows into courses table.
    Dedup key: (course_name, course_link)
    """
    sql = """
    INSERT INTO courses (course_name, duration, level,
                         course_link, source, scraped_at, last_updated)
    VALUES (:course_name, :duration, :level,
            :course_link, :source, :scraped_at, :last_updated)
    ON CONFLICT(course_name, course_link) DO UPDATE SET
        duration     = excluded.duration,
        level        = excluded.level,
        source       = excluded.source,
        last_updated = excluded.last_updated
    """
    ts = _now()
    enriched = [{**r, "scraped_at": ts, "last_updated": ts} for r in rows]
    with _conn() as con:
        con.executemany(sql, enriched)
    logger.info("[DB] upsert_courses: %d rows", len(enriched))
    return len(enriched)


def upsert_services(rows: List[Dict[str, Any]]) -> int:
    """
    Upsert rows into services table.
    Dedup key: (service_name, service_link)
    """
    sql = """
    INSERT INTO services (service_name, industry, description,
                          service_link, source, scraped_at, last_updated)
    VALUES (:service_name, :industry, :description,
            :service_link, :source, :scraped_at, :last_updated)
    ON CONFLICT(service_name, service_link) DO UPDATE SET
        industry     = excluded.industry,
        description  = excluded.description,
        source       = excluded.source,
        last_updated = excluded.last_updated
    """
    ts = _now()
    enriched = [{**r, "scraped_at": ts, "last_updated": ts} for r in rows]
    with _conn() as con:
        con.executemany(sql, enriched)
    logger.info("[DB] upsert_services: %d rows", len(enriched))
    return len(enriched)


# ---------------------------------------------------------------------------
# Search helpers  (fuzzy LIKE across text fields)
# ---------------------------------------------------------------------------

def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def search_products(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text LIKE search over product_name, category, specifications."""
    q = f"%{query}%"
    sql = """
    SELECT * FROM products
    WHERE product_name LIKE ? OR category LIKE ? OR specifications LIKE ?
    ORDER BY last_updated DESC LIMIT ?
    """
    with _conn() as con:
        rows = con.execute(sql, (q, q, q, limit)).fetchall()
    return _rows_to_dicts(rows)


def search_engineers(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text LIKE search over engineer_name, skills, experience."""
    q = f"%{query}%"
    sql = """
    SELECT * FROM engineers
    WHERE engineer_name LIKE ? OR skills LIKE ? OR experience LIKE ?
    ORDER BY last_updated DESC LIMIT ?
    """
    with _conn() as con:
        rows = con.execute(sql, (q, q, q, limit)).fetchall()
    return _rows_to_dicts(rows)


def search_courses(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text LIKE search over course_name, level."""
    q = f"%{query}%"
    sql = """
    SELECT * FROM courses
    WHERE course_name LIKE ? OR level LIKE ?
    ORDER BY last_updated DESC LIMIT ?
    """
    with _conn() as con:
        rows = con.execute(sql, (q, q, limit)).fetchall()
    return _rows_to_dicts(rows)


def search_services(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text LIKE search over service_name, industry, description."""
    q = f"%{query}%"
    sql = """
    SELECT * FROM services
    WHERE service_name LIKE ? OR industry LIKE ? OR description LIKE ?
    ORDER BY last_updated DESC LIMIT ?
    """
    with _conn() as con:
        rows = con.execute(sql, (q, q, q, limit)).fetchall()
    return _rows_to_dicts(rows)


def get_stats() -> Dict[str, int]:
    """Return row counts for all tables."""
    with _conn() as con:
        return {
            "products":  con.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "engineers": con.execute("SELECT COUNT(*) FROM engineers").fetchone()[0],
            "courses":   con.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
            "services":  con.execute("SELECT COUNT(*) FROM services").fetchone()[0],
        }


# ---------------------------------------------------------------------------
# Auto-initialise on import
# ---------------------------------------------------------------------------
init_db()
