"""
Scraper Update Script
======================
CLI runner that executes all Goose Ecosystem scrapers and populates
the local SQLite database.

Usage:
  # Run all scrapers
  python scripts/update_scraped_data.py

  # Run a specific scraper only
  python scripts/update_scraped_data.py --scraper goose_mart
  python scripts/update_scraped_data.py --scraper hiremyengineer
  python scripts/update_scraped_data.py --scraper goose_elevate
  python scripts/update_scraped_data.py --scraper goose_solutions

Output format:
  [Scraper] Goose Mart        -> 24 products scraped
  [Scraper] Goose Elevate     -> using seed data (8 courses)
  [Scraper] HireMyEngineer    -> 12 engineers scraped
  [Scraper] Goose Solutions   -> using seed data (6 services)
  ─────────────────────────────────────────────────────
  [Summary] products=24  engineers=12  courses=8  services=6
  [Summary] Duration: 3.41s
"""

import sys
import io
import os
import time
import logging
import argparse

# Force UTF-8 on Windows stdout to handle any non-ASCII output
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Make sense-api modules importable when called from the project root
_SENSE_API_DIR = os.path.join(
    os.path.dirname(__file__), ".."
)
sys.path.insert(0, os.path.abspath(_SENSE_API_DIR))

# Now configure logging before importing scrapers
logging.basicConfig(
    level=logging.WARNING,   # suppress inner library noise
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
_logger = logging.getLogger("update_scraped_data")
_logger.setLevel(logging.INFO)

from services.scrapers.db import (
    init_db, upsert_products, upsert_engineers, upsert_courses, upsert_services, get_stats
)
from services.scrapers.goose_mart_scraper      import GooseMartScraper
from services.scrapers.hiremyengineer_scraper  import HireMyEngineerScraper
from services.scrapers.goose_elevate_scraper   import GooseElevateScraper
from services.scrapers.goose_solutions_scraper import GooseSolutionsScraper


# ---------------------------------------------------------------------------
# Scraper registry: name -> (ScraperClass, upsert_fn, entity_label)
# ---------------------------------------------------------------------------

REGISTRY = {
    "goose_mart":    (GooseMartScraper,      upsert_products,  "products"),
    "hiremyengineer":(HireMyEngineerScraper, upsert_engineers, "engineers"),
    "goose_elevate": (GooseElevateScraper,   upsert_courses,   "courses"),
    "goose_solutions":(GooseSolutionsScraper,upsert_services,  "services"),
}


# ---------------------------------------------------------------------------
# Pretty print helpers
# ---------------------------------------------------------------------------

_WIDTH = 52

def _banner(text: str) -> str:
    return f"\n{'=' * _WIDTH}\n  {text}\n{'=' * _WIDTH}"

def _row(label: str, count: int, used_seed: bool) -> str:
    src  = "seed data" if used_seed else "live scrape"
    note = f"using {src}" if used_seed else "scraped"
    return f"[Scraper] {label:<22} -> {count:>4} {note}"


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(selected: str = "all") -> None:
    print(_banner("Goose Sense — Scraper Update"))
    start = time.perf_counter()

    # Ensure DB is initialised
    init_db()

    # Select scrapers to run
    if selected == "all":
        targets = list(REGISTRY.items())
    elif selected in REGISTRY:
        targets = [(selected, REGISTRY[selected])]
    else:
        print(f"[Error] Unknown scraper '{selected}'. Choices: {', '.join(REGISTRY.keys())}")
        sys.exit(1)

    # Run each scraper with full error isolation
    for key, (ScraperCls, upsert_fn, label) in targets:
        scraper = ScraperCls()
        try:
            data, used_seed = scraper.run()
            if data:
                stored = upsert_fn(data)
            else:
                stored = 0
            print(_row(scraper.name, stored, used_seed))
        except Exception as e:
            # Should never reach here — BaseScraper.run() isolates errors
            print(f"[Scraper] {scraper.name:<22} -> ERROR: {e}")
            _logger.exception("Unexpected scraper error for %s", key)

    # Print final DB summary
    stats    = get_stats()
    elapsed  = time.perf_counter() - start
    stat_str = "  ".join(f"{k}={v}" for k, v in stats.items())
    print(f"\n[Summary] {stat_str}")
    print(f"[Summary] Duration: {elapsed:.2f}s\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Goose Sense scraper database")
    parser.add_argument(
        "--scraper",
        default="all",
        choices=["all"] + list(REGISTRY.keys()),
        help="Which scraper to run (default: all)",
    )
    args = parser.parse_args()
    run(args.scraper)
