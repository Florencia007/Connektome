from .spain_boe import SpainBOEScraper
from .italy_astalegale import ItalyAstaLegaleScraper
from .france_licitor import FranceLicitorScraper
from .portugal_eleiloes import PortugalELeiloesScraper

ALL_SCRAPERS = [
    SpainBOEScraper,
    ItalyAstaLegaleScraper,
    FranceLicitorScraper,
    PortugalELeiloesScraper,
]
