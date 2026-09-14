"""
HireMyEngineer Scraper
========================
Scrapes engineer profiles from the HireMyEngineer app (port 3003).

Targets:
  http://localhost:3003  — engineer listing page

Parsed fields:
  engineer_name, skills, experience, profile_link

Fallback:
  Realistic engineer profile seed data when live scrape fails.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any

from services.scrapers.base_scraper import BaseScraper
from core.config import HIREMYENGINEER_URL


class HireMyEngineerScraper(BaseScraper):
    name     = "HireMyEngineer"
    source   = "hiremyengineer"
    base_url = HIREMYENGINEER_URL

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Parse engineer profile cards from the HireMyEngineer listing page.

        Expected HTML conventions:
          .engineer-card, .profile-card — profile container
          .engineer-name, h2, h3        — engineer name
          .skills, .tags                — comma-separated skill tags
          .experience, .exp             — years or experiece string
          a[href]                       — profile detail link
        """
        html = self.fetch_page(self.base_url)
        if not html:
            return []

        soup      = BeautifulSoup(html, "html.parser")
        engineers = []

        cards = soup.select(".engineer-card, .profile-card, [data-engineer], article.engineer")
        for card in cards:
            name  = self._text(card, ".engineer-name, h2, h3")
            skills = self._text(card, ".skills, .tags, [data-skills]")
            exp   = self._text(card, ".experience, .exp, [data-experience]")
            link  = self._href(card, "a", self.base_url)

            if name:
                engineers.append({
                    "engineer_name": name,
                    "skills":        skills,
                    "experience":    exp,
                    "profile_link":  link,
                    "source":        self.source,
                })

        return engineers

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _seed_data(self) -> List[Dict[str, Any]]:
        profiles = [
            ("Arjun Mehta",
             "Pump systems, SCADA, Predictive maintenance, Rotating machinery, Python",
             "12 years | Senior Mechanical Engineer",
             f"{self.base_url}/engineers/arjun-mehta"),
            ("Sarah Kowalski",
             "PLC programming, Siemens TIA Portal, PROFINET, HMI design, Automation",
             "8 years | Automation Engineer",
             f"{self.base_url}/engineers/sarah-kowalski"),
            ("Marcus Odhiambo",
             "IIoT, Edge computing, Vibration analysis, Python ML, AWS IoT",
             "6 years | IIoT Solutions Engineer",
             f"{self.base_url}/engineers/marcus-odhiambo"),
            ("Priya Nair",
             "Process engineering, P&ID, Piping design, HAZOP, Chemical plants",
             "10 years | Process Engineer",
             f"{self.base_url}/engineers/priya-nair"),
            ("David Antwi",
             "Electrical design, MCC panels, Power distribution, HV systems, AutoCAD",
             "14 years | Electrical Engineer",
             f"{self.base_url}/engineers/david-antwi"),
            ("Lena Fischer",
             "Quality systems, ISO 9001, Lean manufacturing, Six Sigma Black Belt",
             "9 years | Quality & Continuous Improvement Engineer",
             f"{self.base_url}/engineers/lena-fischer"),
            ("Ryo Tanaka",
             "Robotics, ABB/FANUC integration, Vision systems, Collaborative robots",
             "7 years | Robotics Engineer",
             f"{self.base_url}/engineers/ryo-tanaka"),
            ("Amina Hassan",
             "SCADA, DCS, Yokogawa, Emerson DeltaV, Alarm rationalisation",
             "11 years | Control Systems Engineer",
             f"{self.base_url}/engineers/amina-hassan"),
        ]
        return [
            {
                "engineer_name": p[0],
                "skills":        p[1],
                "experience":    p[2],
                "profile_link":  p[3],
                "source":        self.source,
            }
            for p in profiles
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
