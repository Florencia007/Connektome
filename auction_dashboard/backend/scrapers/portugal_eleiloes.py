"""
e-leiloes.pt — Portugal's official Ministry of Justice electronic auction platform.
Covers all judicial auctions in Portugal including Lisbon area.
"""
import hashlib
import httpx
from bs4 import BeautifulSoup
from typing import List
from ..models import Property
from .base import BaseScraper


class PortugalELeiloesScraper(BaseScraper):
    source_id = "portugal_eleiloes"
    country = "PT"
    BASE_URL = "https://www.e-leiloes.pt"

    TARGET_DISTRICTS = [
        "Lisboa",
        "Setúbal",
        "Sintra",
        "Cascais",
        "Almada",
    ]

    def fetch(self) -> List[Property]:
        results = []
        try:
            batch = self._fetch_listings()
            results.extend(batch)
        except Exception as e:
            print(f"[portugal_eleiloes] Error: {e}")
        return results

    def _fetch_listings(self) -> List[Property]:
        # Search for real estate in Lisbon region
        url = f"{self.BASE_URL}/leiloes/pesquisa?categoria=imoveis&distrito=Lisboa"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AuctionBot/1.0)"}
        try:
            resp = httpx.get(url, headers=headers, timeout=25, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"[portugal_eleiloes] HTTP error: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        properties = []

        for card in soup.select(".lote-item, .property-item, .leilao-card, article, .item-leilao"):
            prop = self._parse_card(card)
            if prop and self._matches_profile(prop):
                properties.append(prop)

        return properties

    def _parse_card(self, card) -> Property | None:
        try:
            title_el = card.select_one("h2, h3, .title, .titulo, .designacao")
            title = title_el.get_text(strip=True) if title_el else "Imóvel em leilão"

            link_el = card.select_one("a[href]")
            relative_url = link_el["href"] if link_el else ""
            full_url = relative_url if relative_url.startswith("http") else f"{self.BASE_URL}{relative_url}"

            location_el = card.select_one(".location, .localizacao, .morada, .address")
            location = location_el.get_text(strip=True) if location_el else "Lisboa, Portugal"

            price_el = card.select_one(".price, .valor-base, .preco, .vr-base")
            price = self._parse_price(price_el.get_text()) if price_el else None

            desc_el = card.select_one(".description, .descricao, p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            date_el = card.select_one(".date, .data-leilao, .data, time")
            auction_date = date_el.get_text(strip=True) if date_el else None

            img_el = card.select_one("img[src]")
            image_url = img_el["src"] if img_el else None
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.BASE_URL}{image_url}"

            area = self._parse_area(f"{title} {description}")
            prop_type, is_hist, needs_refurb = self._detect_property_type(f"{title} {description}")
            region = self._detect_region(f"{location} {title} {description}")

            uid = hashlib.md5(f"portugal_eleiloes_{full_url}".encode()).hexdigest()

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
            print(f"[portugal_eleiloes] Card parse error: {e}")
            return None
