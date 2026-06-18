"""
Licitor.fr — France's main judicial auction platform (ventes aux enchères judiciaires).
Covers all French courts. South of France departments: 11, 12, 13, 30, 34, 66, 83, 84.
"""
import hashlib
import httpx
from bs4 import BeautifulSoup
from typing import List
from ..models import Property
from .base import BaseScraper


class FranceLicitorScraper(BaseScraper):
    source_id = "france_licitor"
    country = "FR"
    BASE_URL = "https://www.licitor.fr"

    # Department codes for south of France
    TARGET_DEPARTMENTS = {
        "11": "Aude",
        "12": "Aveyron",
        "13": "Bouches-du-Rhône",
        "30": "Gard",
        "34": "Hérault",
        "66": "Pyrénées-Orientales",
        "83": "Var",
        "84": "Vaucluse",
        "48": "Lozère",
        "81": "Tarn",
    }

    def fetch(self) -> List[Property]:
        results = []
        for dept_code, dept_name in self.TARGET_DEPARTMENTS.items():
            try:
                batch = self._fetch_department(dept_code, dept_name)
                results.extend(batch)
            except Exception as e:
                print(f"[france_licitor] Error fetching dept {dept_name}: {e}")
        return results

    def _fetch_department(self, dept_code: str, dept_name: str) -> List[Property]:
        url = f"{self.BASE_URL}/ventes/immobilier/?departement={dept_code}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AuctionBot/1.0)"}
        try:
            resp = httpx.get(url, headers=headers, timeout=25, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"[france_licitor] HTTP error {dept_name}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        properties = []

        for card in soup.select(".bien-item, .property-card, .annonce, article"):
            prop = self._parse_card(card, dept_name)
            if prop and self._matches_profile(prop):
                properties.append(prop)

        return properties

    def _parse_card(self, card, dept_name: str) -> Property | None:
        try:
            title_el = card.select_one("h2, h3, .bien-titre, .title")
            title = title_el.get_text(strip=True) if title_el else "Bien immobilier aux enchères"

            link_el = card.select_one("a[href]")
            relative_url = link_el["href"] if link_el else ""
            full_url = relative_url if relative_url.startswith("http") else f"{self.BASE_URL}{relative_url}"

            location_el = card.select_one(".location, .ville, .commune, .adresse")
            location = location_el.get_text(strip=True) if location_el else dept_name

            price_el = card.select_one(".price, .mise-a-prix, .prix")
            price = self._parse_price(price_el.get_text()) if price_el else None

            desc_el = card.select_one(".description, .desc, p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            date_el = card.select_one(".date-vente, .date, time")
            auction_date = date_el.get_text(strip=True) if date_el else None

            img_el = card.select_one("img[src]")
            image_url = img_el["src"] if img_el else None
            if image_url and not image_url.startswith("http"):
                image_url = f"{self.BASE_URL}{image_url}"

            area = self._parse_area(f"{title} {description}")
            prop_type, is_hist, needs_refurb = self._detect_property_type(f"{title} {description}")
            region = self._detect_region(f"{location} {dept_name} {title} {description}")

            uid = hashlib.md5(f"france_licitor_{full_url}".encode()).hexdigest()

            return Property(
                id=uid,
                source=self.source_id,
                title=title,
                location=f"{location}, {dept_name}",
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
            print(f"[france_licitor] Card parse error: {e}")
            return None
