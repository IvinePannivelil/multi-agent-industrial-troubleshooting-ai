"""
Agent Tools Interface
======================
Live tool functions that query the local SQLite database populated by scrapers.

Data flow:
  scripts/update_scraped_data.py -> SQLite DB -> tools.py -> Agents

Fallback:
  If the DB is empty (scrapers not yet run), returns seed data from scrapers
  so agents always have something to work with.

Tool functions:
  product_search(query)   -> List[ProductResult]
  training_search(query)  -> List[CourseResult]
  engineer_search(query)  -> List[TalentResult]

To populate the DB, run:
  python scripts/update_scraped_data.py
"""

import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result data types  (unchanged — agents depend on these)
# ---------------------------------------------------------------------------

@dataclass
class ProductResult:
    name:         str
    sku:          str
    description:  str
    vendor:       str
    price_range:  str
    in_stock:     bool
    alternatives: List[str] = field(default_factory=list)


@dataclass
class CourseResult:
    title:       str
    course_id:   str
    description: str
    level:       str
    duration:    str
    topics:      List[str] = field(default_factory=list)


@dataclass
class TalentResult:
    name:             str
    engineer_id:      str
    specialisms:      List[str]
    experience_years: int
    availability:     str
    location:         str


# ---------------------------------------------------------------------------
# DB-backed tool functions
# ---------------------------------------------------------------------------

def product_search(query: str) -> List[ProductResult]:
    """
    Search the Goose Mart product catalog from the scraped SQLite database.

    Falls back to scraper seed data if DB is empty.

    Args:
        query: Natural-language product search query.

    Returns:
        List of ProductResult objects.
    """
    logger.info("[Tools] product_search('%s') — querying DB", query)
    try:
        from services.scrapers.db import search_products
        rows = search_products(query, limit=5)

        if rows:
            logger.info("[Tools] product_search -> %d DB results", len(rows))
            return [_row_to_product(r) for r in rows]
    except Exception as e:
        logger.warning("[Tools] product_search DB query failed: %s", e)

    # Fallback: return scraper seed data
    logger.info("[Tools] product_search -> using seed data fallback")
    from services.scrapers.goose_mart_scraper import GooseMartScraper
    seed = GooseMartScraper()._seed_data()
    return [_seed_to_product(s) for s in seed[:5]]


def training_search(query: str) -> List[CourseResult]:
    """
    Search Goose Elevate training catalog from the scraped SQLite database.

    Args:
        query: Natural-language training topic query.

    Returns:
        List of CourseResult objects.
    """
    logger.info("[Tools] training_search('%s') — querying DB", query)
    try:
        from services.scrapers.db import search_courses
        rows = search_courses(query, limit=5)

        if rows:
            logger.info("[Tools] training_search -> %d DB results", len(rows))
            return [_row_to_course(r) for r in rows]
    except Exception as e:
        logger.warning("[Tools] training_search DB query failed: %s", e)

    logger.info("[Tools] training_search -> using seed data fallback")
    from services.scrapers.goose_elevate_scraper import GooseElevateScraper
    seed = GooseElevateScraper()._seed_data()
    return [_seed_to_course(s) for s in seed[:5]]


def engineer_search(query: str) -> List[TalentResult]:
    """
    Search HireMyEngineer talent database from the scraped SQLite database.

    Args:
        query: Natural-language expertise or skill query.

    Returns:
        List of TalentResult objects.
    """
    logger.info("[Tools] engineer_search('%s') — querying DB", query)
    try:
        from services.scrapers.db import search_engineers
        rows = search_engineers(query, limit=5)

        if rows:
            logger.info("[Tools] engineer_search -> %d DB results", len(rows))
            return [_row_to_talent(r) for r in rows]
    except Exception as e:
        logger.warning("[Tools] engineer_search DB query failed: %s", e)

    logger.info("[Tools] engineer_search -> using seed data fallback")
    from services.scrapers.hiremyengineer_scraper import HireMyEngineerScraper
    seed = HireMyEngineerScraper()._seed_data()
    return [_seed_to_talent(s) for s in seed[:5]]


# ---------------------------------------------------------------------------
# Row -> dataclass converters
# ---------------------------------------------------------------------------

def _row_to_product(row: dict) -> ProductResult:
    """Convert a DB products row to ProductResult."""
    specs = row.get("specifications", "")
    # Extract vendor from source label (e.g. "goose_mart" -> "Goose Mart")
    vendor = row.get("source", "Goose Mart").replace("_", " ").title()
    return ProductResult(
        name=row.get("product_name", ""),
        sku=f"{row.get('source','GM').upper()[:3]}-{row.get('id', 0):04d}",
        description=specs or row.get("category", ""),
        vendor=vendor,
        price_range=row.get("price", "Price on request"),
        in_stock=True,
        alternatives=[],
    )


def _seed_to_product(seed: dict) -> ProductResult:
    """Convert a scraper seed dict to ProductResult."""
    return ProductResult(
        name=seed.get("product_name", ""),
        sku="SEED-0000",
        description=seed.get("specifications", seed.get("category", "")),
        vendor="Goose Mart",
        price_range="Price on request",
        in_stock=True,
        alternatives=[],
    )


def _row_to_course(row: dict) -> CourseResult:
    """Convert a DB courses row to CourseResult."""
    name = row.get("course_name", "")
    # Generate a stable slug-based course ID
    slug = name.lower().replace(" ", "-")[:20]
    return CourseResult(
        title=name,
        course_id=f"GE-{slug}-{row.get('id', 0):03d}",
        description=f"Level: {row.get('level', '')} | Duration: {row.get('duration', '')}",
        level=row.get("level", ""),
        duration=row.get("duration", ""),
        topics=[],
    )


def _seed_to_course(seed: dict) -> CourseResult:
    """Convert a scraper seed dict to CourseResult."""
    name = seed.get("course_name", "")
    slug = name.lower().replace(" ", "-")[:20]
    return CourseResult(
        title=name,
        course_id=f"GE-{slug}-000",
        description=f"Level: {seed.get('level', '')} | Duration: {seed.get('duration', '')}",
        level=seed.get("level", ""),
        duration=seed.get("duration", ""),
        topics=[],
    )


def _row_to_talent(row: dict) -> TalentResult:
    """Convert a DB engineers row to TalentResult."""
    skills_str = row.get("skills", "")
    specialisms = [s.strip() for s in skills_str.split(",") if s.strip()]
    exp_str = row.get("experience", "")
    # Try to extract year count from "N years | Title" format
    years = 0
    try:
        years = int(exp_str.split("year")[0].strip().split()[-1])
    except Exception:
        pass
    return TalentResult(
        name=row.get("engineer_name", ""),
        engineer_id=f"HME-{row.get('id', 0):05d}",
        specialisms=specialisms[:5],
        experience_years=years,
        availability="Available",
        location="See profile",
    )


def _seed_to_talent(seed: dict) -> TalentResult:
    """Convert a scraper seed dict to TalentResult."""
    skills_str = seed.get("skills", "")
    specialisms = [s.strip() for s in skills_str.split(",") if s.strip()]
    exp_str = seed.get("experience", "")
    years = 0
    try:
        years = int(exp_str.split("year")[0].strip().split()[-1])
    except Exception:
        pass
    return TalentResult(
        name=seed.get("engineer_name", ""),
        engineer_id="HME-SEED",
        specialisms=specialisms[:5],
        experience_years=years,
        availability="Available",
        location="See profile",
    )
