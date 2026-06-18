from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Property:
    id: str
    source: str          # spain_boe | italy_astalegale | france_licitor | portugal_eleiloes
    title: str
    location: str
    region: str          # sicily | south_france | lisbon | madrid
    country: str
    price_eur: Optional[float]
    area_m2: Optional[float]
    property_type: str   # masseria | palazzo | quinta | chateau | cortijo | casale | other
    auction_date: Optional[str]
    auction_end_date: Optional[str]
    description: str
    url: str
    image_url: Optional[str]
    is_historical: bool
    needs_refurbishment: bool
    payment_conditions: Optional[str]
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_new: bool = True
    is_favourite: bool = False
    notes: str = ""
