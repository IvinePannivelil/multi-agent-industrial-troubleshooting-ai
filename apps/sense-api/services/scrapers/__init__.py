"""
Goose Sense Scraper Package
============================
Exports all scraper classes for use in the update script.
"""

from services.scrapers.goose_mart_scraper     import GooseMartScraper
from services.scrapers.hiremyengineer_scraper import HireMyEngineerScraper
from services.scrapers.goose_elevate_scraper  import GooseElevateScraper
from services.scrapers.goose_solutions_scraper import GooseSolutionsScraper

ALL_SCRAPERS = [
    GooseMartScraper,
    HireMyEngineerScraper,
    GooseElevateScraper,
    GooseSolutionsScraper,
]

__all__ = [
    "GooseMartScraper",
    "HireMyEngineerScraper",
    "GooseElevateScraper",
    "GooseSolutionsScraper",
    "ALL_SCRAPERS",
]
