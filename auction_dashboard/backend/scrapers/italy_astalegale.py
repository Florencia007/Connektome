"""
AstaLegale.net — Italy's main judicial auction aggregator.
Covers all Italian courts including Sicily (Siracusa, Noto area = Tribunale di Siracusa).
"""
import hashlib
import httpx
from bs4 import BeautifulSoup
from typing import List
from ..models import Property
from .base import BaseScraper


class ItalyAstaLegaleScraper(BaseScraper):
    source_id = "italy_astalegale"
    country = "IT"
    BASE_URL = "https://www.astalegale.net"

    # Tribunali covering Noto/Val di Noto area in Sicily
    TARGET_COURTS = [
        "siracusa",
        "ragusa",
        "catania",
        "caltagirone",
    ]

    def fetch(self) -> List[Property]:
        results = []
        for court in self.TARGET_COURTS:
            try:
                batch = self._fetch_court(court)
                results.extend(batch)
            except Exception as e:
                print(f"[italy_astalegale] Error fetching court {court}: {e}")
        return results

    def _fetch_court(self, court: str) -> List[Property]:
        url = f"{self.BASE_URL}/immobili/tribunale/{court}/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AuctionBot/1.0)"}
        try:
            resp = httpx.get(url, headers=headers, timeout=25, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"[italy_astalegale] HTTP error {court}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        properties = []

        for card in soup.select(".listing-item, .immobile-card, article.property"):
            prop = self._parse_card(card, court)
            if prop and self._matches_profile(prop):
                properties.append(prop)

        # Fallback: try generic item containers
        if not properties:
            for card in soup.select(".item, .result-item, .annuncio"):
                prop = self._parse_card(card, court)
                if prop and self._matches_profile(prop):
                    properties.append(prop)

        return properties

    def _parse_card(self, card, court: str) -> Property | None:
        try:
            title_el = card.select_one("h2, h3, .title, .titolo")
            title = title_el.get_text(strip=True) if title_el else "Immobile in asta"

            link_el = card.select_one("a[href]")
            relative_url = link_el["href"] if link_el else ""
            full_url = relative_url if relative_url.startswith("http") else f"{self.BASE_URL}{relative_url}"

            location_el = card.select_one(".location, .luogo, .comune, .address")
            location = location_el.get_text(strip=True) if location_el else f"Tribunale di {court.title()}"

            price_el = card.select_one(".price, .prezzo, .base-asta")
            price = self._parse_price(price_el.get_text()) if price_el else None

            desc_el = card.select_one(".description, .descrizione, p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            date_el = card.select_one(".date, .data-asta, .data")
            auction_date = date_el.get_text(strip=True) if date_el else None

            img_el = card.select_one("img[src]")
            image_url = img_el["src"] if img_el else None
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.BASE_URL}{image_url}"

            area = self._parse_area(f"{title} {description}")
            prop_type, is_hist, needs_refurb = self._detect_property_type(f"{title} {description}")
            region = self._detect_region(f"{location} {title} {description}")

            uid = hashlib.md5(f"italy_astalegale_{full_url}".encode()).hexdigest()

            return Property(
                id=uid,
                source=self.source_id,
                title=title,
                location=location,
                region=region,
                country=self.country,
                price_eur=price,
                area_m2=area,
                property_type=prop_type,
                auction_date=auction_date,
                auction_end_date=None,
                description=description,
                url=full_url,
                image_url=image_url,
                is_historical=is_hist,
                needs_refurbishment=needs_refurb,
                payment_conditions=None,
            )
        except Exception as e:
            print(f"[italy_astalegale] Card parse error: {e}")
            return None
