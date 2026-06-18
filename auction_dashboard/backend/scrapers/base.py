import re
import sys
import os
from typing import List, Tuple
from ..models import Property

# Add parent to path so config is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BaseScraper:
    source_id: str = ""
    country: str = ""

    def fetch(self) -> List[Property]:
        raise NotImplementedError

    def _detect_region(self, text: str) -> str:
        from ..config import SEARCH_PROFILE
        text_lower = text.lower()
        for region, cfg in SEARCH_PROFILE["regions"].items():
            for kw in cfg["keywords"]:
                if kw.lower() in text_lower:
                    return region
        return "other"

    def _detect_property_type(self, text: str) -> Tuple[str, bool, bool]:
        """Returns (property_type_label, is_historical, needs_refurbishment)."""
        from ..config import SEARCH_PROFILE
        text_lower = text.lower()
        type_map = {
            "masseria": "masseria", "palazzo": "palazzo", "casale": "casale",
            "castello": "castello", "convento": "convento", "monastero": "monastero",
            "château": "chateau", "chateau": "chateau", "manoir": "manoir",
            "mas": "mas", "bastide": "bastide",
            "quinta": "quinta", "solar": "solar",
            "cortijo": "cortijo", "hacienda": "hacienda", "finca": "finca",
        }
        prop_type = "residential"
        for kw, label in type_map.items():
            if kw in text_lower:
                prop_type = label
                break

        historical_keywords = ["storica", "storico", "historic", "heritage", "period",
                                 "ancien", "ancienne", "antigo", "antigua", "antiguo",
                                 "xv", "xvi", "xvii", "xviii", "xix", "century", "secolo"]
        refurb_keywords = ["restauro", "ristrutturare", "ristrutturazione", "rudere",
                           "restauration", "rénovation", "renovation", "rénover",
                           "reabilitação", "reabilitacao", "rehabilitación",
                           "restore", "renovate", "refurbish", "ruins", "ruin",
                           "da ristrutturare", "à rénover", "para restaurar"]

        is_historical = any(kw in text_lower for kw in historical_keywords)
        needs_refurb = any(kw in text_lower for kw in refurb_keywords)
        return prop_type, is_historical, needs_refurb

    def _matches_profile(self, prop: Property) -> bool:
        from ..config import SEARCH_PROFILE
        if prop.price_eur and prop.price_eur > SEARCH_PROFILE["max_price_eur"]:
            return False
        if prop.region == "other":
            return False
        text = f"{prop.title} {prop.description} {prop.location}".lower()
        kws = SEARCH_PROFILE["property_type_keywords"]
        return any(kw.lower() in text for kw in kws)

    def _parse_price(self, text: str) -> float | None:
        text = text.replace(".", "").replace(",", ".").replace("€", "").replace("EUR", "").strip()
        m = re.search(r"[\d]+\.?\d*", text)
        if m:
            try:
                return float(m.group())
            except ValueError:
                pass
        return None

    def _parse_area(self, text: str) -> float | None:
        m = re.search(r"([\d]+[\.,]?\d*)\s*m[²2]", text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except ValueError:
                pass
        return None
