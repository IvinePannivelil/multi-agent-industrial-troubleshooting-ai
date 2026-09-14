"""
Base Scraper
=============
Abstract foundation for all Goose Ecosystem scrapers.

Each scraper must implement:
  scrape()    -> List[dict]   — live web scraping logic
  _seed_data() -> List[dict]  — realistic fallback when scraping fails

The base class provides:
  fetch_page(url)      — requests (fast) -> Playwright fallback (JS pages)
  run()                — calls scrape(); falls back to _seed_data() on error
  _log(msg)            — structured [Scraper] prefixed logging

Error isolation:
  Any exception in scrape() is caught and logged.
  The pipeline always continues — seed data is returned, never a crash.
"""

import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default request timeout in seconds
_REQUEST_TIMEOUT = 8

# Common browser-like headers to avoid 403s from local Next.js servers
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseScraper(ABC):
    """
    Abstract base class for all Goose Ecosystem scrapers.

    Attributes:
        name        Human-readable scraper name (e.g. "Goose Mart")
        base_url    Root URL of the target app
        source      Source label stored in DB rows (e.g. "goose_mart")
    """

    name:     str = "BaseScraper"
    base_url: str = ""
    source:   str = ""

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Perform live scraping of the target app.

        Returns:
            List of dicts matching the DB table schema for this scraper.
        """

    @abstractmethod
    def _seed_data(self) -> List[Dict[str, Any]]:
        """
        Return realistic hardcoded seed data.
        Called when scraping fails or returns no results.
        """

    # ------------------------------------------------------------------
    # Public run() entry point
    # ------------------------------------------------------------------

    def run(self) -> tuple[List[Dict[str, Any]], bool]:
        """
        Execute the scraper with full error isolation.

        Returns:
            (data, used_seed)
              data      — list of scraped / seed dicts
              used_seed — True if seed data was used
        """
        try:
            data = self.scrape()
            if not data:
                self._log("No results from live scrape — using seed data")
                return self._seed_data(), True
            self._log(f"Live scrape successful: {len(data)} records")
            return data, False
        except Exception as e:
            self._log(f"Scrape failed ({e.__class__.__name__}: {e}) — using seed data")
            return self._seed_data(), True

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a URL and return the HTML body.

        Strategy:
          1. Try requests (fast)
          2. If requests returns non-HTML / empty / JS shell, try Playwright
          3. Return None on complete failure

        Args:
            url: Absolute URL to fetch.

        Returns:
            HTML string or None.
        """
        # Pass 1 — requests
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            html = resp.text
            # Detect JS-rendered shell (no meaningful body content)
            if len(html) > 500 and "<body" in html:
                return html
        except Exception as e:
            self._log(f"requests.get({url}) failed: {e}")

        # Pass 2 — Playwright (JS-rendered pages)
        return self._fetch_with_playwright(url)

    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Playwright fallback for JavaScript-rendered Next.js pages.
        Returns None if Playwright is not installed.
        """
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page    = browser.new_page()
                page.goto(url, timeout=15000, wait_until="networkidle")
                html = page.content()
                browser.close()
                self._log(f"Playwright fetched {url} ({len(html)} bytes)")
                return html
        except ImportError:
            self._log("Playwright not installed — skipping JS fallback")
            return None
        except Exception as e:
            self._log(f"Playwright failed for {url}: {e}")
            return None

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        """Emit a structured [Scraper] prefixed log line."""
        logger.info("[Scraper] %s — %s", self.name, msg)
