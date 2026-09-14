"""
Goose Mart Scraper
===================
Scrapes industrial product listings from the Goose Mart app (port 3000).

Targets:
  http://localhost:3000  — product listing page

Parsed fields:
  product_name, category, specifications, price, product_link

Fallback:
  Realistic industrial hardware seed data when live scrape fails.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any

from services.scrapers.base_scraper import BaseScraper
from core.config import GOOSE_MART_URL


class GooseMartScraper(BaseScraper):
    name     = "Goose Mart"
    source   = "goose_mart"
    base_url = GOOSE_MART_URL

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Parse product cards from the Goose Mart storefront.

        Expected HTML conventions (update selectors as the app develops):
          .product-card          — product container
          .product-name          — product title
          .product-category      — category tag
          .product-spec          — specifications text
          .product-price         — price string
          a[href]                — product detail link
        """
        html = self.fetch_page(self.base_url)
        if not html:
            return []

        soup     = BeautifulSoup(html, "html.parser")
        products = []

        # Try data-driven structured selectors first
        cards = soup.select(".product-card, [data-product], article.product")
        for card in cards:
            name  = self._text(card, ".product-name, h2, h3")
            cat   = self._text(card, ".product-category, .category")
            spec  = self._text(card, ".product-spec, .specifications, p")
            price = self._text(card, ".product-price, .price, [data-price]")
            link  = self._href(card, "a", self.base_url)

            if name:
                products.append({
                    "product_name":   name,
                    "category":       cat,
                    "specifications": spec,
                    "price":          price,
                    "product_link":   link,
                    "source":         self.source,
                })

        return products

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _seed_data(self) -> List[Dict[str, Any]]:
        items = [
            ("Grundfos CM5-8 Centrifugal Pump",
             "Pumps & Fluid Handling",
             "Flow: 5 m³/h | Head: 75m | Power: 1.1kW | IP55 | ATEX certified",
             "Price on request",
             f"{self.base_url}/products/grundfos-cm5-8"),
            ("Mechanical Seal Kit — GF-CM Series",
             "Spare Parts",
             "OEM seal kit: O-rings, spring, seat. Compatible: Grundfos CM5-CM10",
             "Price on request",
             f"{self.base_url}/products/gf-seal-cm5-kit"),
            ("Siemens S7-1500 PLC CPU 1511-1 PN",
             "PLCs & Automation",
             "Work memory: 150KB | Interfaces: 1x PROFINET | DI/DQ: 6/4 | Display: Yes",
             "Price on request",
             f"{self.base_url}/products/siemens-s7-1511"),
            ("Phoenix Contact FLUKE 287 Multimeter",
             "Measurement & Testing",
             "True RMS | 1000V CAT IV | Logging: 10,000 readings | USB",
             "Price on request",
             f"{self.base_url}/products/fluke-287"),
            ("Schneider Electric Altivar ATV320 VFD",
             "Drives & Motion",
             "Power: 0.18–15kW | Supply: 3ph 380-500V | MODBUS RTU / CANopen",
             "Price on request",
             f"{self.base_url}/products/altivar-320"),
            ("Endress+Hauser Promag 300 Flowmeter",
             "Instrumentation",
             "DN15–DN2000 | ±0.2% accuracy | HART / PROFIBUS PA | IP68",
             "Price on request",
             f"{self.base_url}/products/promag-300"),
            ("Bearing SKF 6205-2RS Deep Groove",
             "Rotating Machinery",
             "Bore: 25mm | OD: 52mm | Width: 15mm | Sealed | Max RPM: 17,000",
             "Price on request",
             f"{self.base_url}/products/skf-6205-2rs"),
            ("Parker Hannifin P1D Pneumatic Cylinder",
             "Pneumatics",
             "Bore: 32–125mm | Stroke: up to 2000mm | ISO 15552 | Double-acting",
             "Price on request",
             f"{self.base_url}/products/parker-p1d"),
        ]
        return [
            dict(zip(
                ["product_name","category","specifications","price","product_link","source"],
                (*item, self.source)
            ))
            for item in items
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
