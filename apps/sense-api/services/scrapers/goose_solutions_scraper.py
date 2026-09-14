"""
Goose Solutions Scraper
========================
Scrapes service offerings from the Goose Digital / Goose Solutions app (port 3001).

Targets:
  http://localhost:3001  — services listing page

Parsed fields:
  service_name, industry, description, service_link

Fallback:
  Realistic industrial solutions seed data.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any

from services.scrapers.base_scraper import BaseScraper
from core.config import GOOSE_SOLUTIONS_URL


class GooseSolutionsScraper(BaseScraper):
    name     = "Goose Solutions"
    source   = "goose_solutions"
    base_url = GOOSE_SOLUTIONS_URL

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Parse service cards from the Goose Solutions / Digital listing page.

        Expected HTML conventions:
          .service-card, [data-service]  — service container
          .service-name, h2, h3          — service title
          .industry, .sector             — industry tag
          .description, p               — description text
          a[href]                        — service detail link
        """
        html = self.fetch_page(self.base_url)
        if not html:
            return []

        soup     = BeautifulSoup(html, "html.parser")
        services = []

        cards = soup.select(".service-card, [data-service], article.service")
        for card in cards:
            name     = self._text(card, ".service-name, h2, h3")
            industry = self._text(card, ".industry, .sector, [data-industry]")
            desc     = self._text(card, ".description, p")
            link     = self._href(card, "a", self.base_url)

            if name:
                services.append({
                    "service_name": name,
                    "industry":     industry,
                    "description":  desc,
                    "service_link": link,
                    "source":       self.source,
                })

        return services

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _seed_data(self) -> List[Dict[str, Any]]:
        items = [
            ("Predictive Maintenance Programme",
             "Manufacturing, Oil & Gas",
             "End-to-end IIoT sensor deployment, ML model training, and dashboard integration for predictive failure detection.",
             f"{self.base_url}/services/predictive-maintenance"),
            ("SCADA System Integration",
             "Utilities, Water Treatment",
             "Design, migration, and commissioning of SCADA systems with PROFINET/MODBUS connectivity and historian setup.",
             f"{self.base_url}/services/scada-integration"),
            ("Plant Automation Audit",
             "Food & Beverage, Pharmaceuticals",
             "Comprehensive audit of existing automation systems against IEC 62443 cybersecurity and ISO 9001 quality standards.",
             f"{self.base_url}/services/automation-audit"),
            ("Digital Twin Development",
             "Aerospace, Heavy Industry",
             "3D simulation of production lines and equipment using real-time SCADA data for scenario planning and optimisation.",
             f"{self.base_url}/services/digital-twin"),
            ("Energy Optimisation Consulting",
             "Steel, Cement, Chemical",
             "Power factor correction, load scheduling, and motor efficiency audits targeting 15–30% energy cost reduction.",
             f"{self.base_url}/services/energy-optimisation"),
            ("Remote Monitoring & NOC Services",
             "Oil & Gas, Renewables",
             "24/7 remote monitoring of distributed assets with alarm triage, escalation workflows, and SLA reporting.",
             f"{self.base_url}/services/remote-monitoring"),
        ]
        return [
            {
                "service_name": i[0],
                "industry":     i[1],
                "description":  i[2],
                "service_link": i[3],
                "source":       self.source,
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
