"""
Goose Elevate Scraper
======================
Scrapes training course listings from the Goose Elevate app (port 3002).

Targets:
  http://localhost:3002  — course listing page

Parsed fields:
  course_name, duration, level, course_link

Fallback:
  Realistic industrial training course seed data.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any

from services.scrapers.base_scraper import BaseScraper
from core.config import GOOSE_ELEVATE_URL


class GooseElevateScraper(BaseScraper):
    name     = "Goose Elevate"
    source   = "goose_elevate"
    base_url = GOOSE_ELEVATE_URL

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Parse course cards from the Goose Elevate listing page.

        Expected HTML conventions:
          .course-card, [data-course]  — course container
          .course-name, h2, h3         — course title
          .duration, .course-duration  — duration string
          .level, .course-level        — difficulty level
          a[href]                      — course detail link
        """
        html = self.fetch_page(self.base_url)
        if not html:
            return []

        soup    = BeautifulSoup(html, "html.parser")
        courses = []

        cards = soup.select(".course-card, [data-course], article.course")
        for card in cards:
            name     = self._text(card, ".course-name, h2, h3")
            duration = self._text(card, ".duration, .course-duration, [data-duration]")
            level    = self._text(card, ".level, .course-level, [data-level]")
            link     = self._href(card, "a", self.base_url)

            if name:
                courses.append({
                    "course_name": name,
                    "duration":    duration,
                    "level":       level,
                    "course_link": link,
                    "source":      self.source,
                })

        return courses

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _seed_data(self) -> List[Dict[str, Any]]:
        items = [
            ("Industrial Pump Systems — Operation & Maintenance",
             "16 hours", "Intermediate",
             f"{self.base_url}/courses/pump-systems-201"),
            ("PLC Programming Fundamentals (Siemens S7-1500)",
             "24 hours", "Beginner",
             f"{self.base_url}/courses/plc-siemens-101"),
            ("Predictive Maintenance with IIoT Sensors",
             "20 hours", "Advanced",
             f"{self.base_url}/courses/predictive-maintenance-301"),
            ("SCADA System Design and Configuration",
             "18 hours", "Intermediate",
             f"{self.base_url}/courses/scada-design-202"),
            ("Hazardous Area Classification & ATEX",
             "12 hours", "Intermediate",
             f"{self.base_url}/courses/atex-hazardous-203"),
            ("Lean Manufacturing & OEE Optimisation",
             "14 hours", "Beginner",
             f"{self.base_url}/courses/lean-oee-101"),
            ("Industrial Robotics — ABB & FANUC Programming",
             "30 hours", "Advanced",
             f"{self.base_url}/courses/robotics-abb-fanuc-302"),
            ("Electrical Safety — LV/HV Systems & LOTO",
             "8 hours", "Beginner",
             f"{self.base_url}/courses/electrical-safety-loto-101"),
            ("P&ID Reading and Interpretation",
             "10 hours", "Beginner",
             f"{self.base_url}/courses/pid-reading-102"),
            ("Vibration Analysis for Rotating Machinery",
             "16 hours", "Advanced",
             f"{self.base_url}/courses/vibration-analysis-301"),
        ]
        return [
            {
                "course_name": i[0],
                "duration":    i[1],
                "level":       i[2],
                "course_link": i[3],
                "source":      self.source,
            }
            for i in items
        ]

    # ------------------------------------------------------------------
    # HTML parsing helpers
    # ------------------------------------------------------------------

    def _text(self, el, selector: str) -> str:
        found = el.select_one(selector)
        return found.get_text(strip=True) if found else ""

    def _href(self, el, selector: str, base: str) -> str:
        found = el.select_one(selector)
        if found and found.get("href"):
            href = found["href"]
            return href if href.startswith("http") else f"{base.rstrip('/')}/{href.lstrip('/')}"
        return base
