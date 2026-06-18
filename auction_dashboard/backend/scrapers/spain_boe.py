"""
Spain BOE (Boletín Oficial del Estado) — official judicial auction portal.
API docs: https://subastas.boe.es/api.php
Free, no key required.
"""
import hashlib
import httpx
from typing import List
from ..models import Property
from .base import BaseScraper


class SpainBOEScraper(BaseScraper):
    source_id = "spain_boe"
    country = "ES"
    API_BASE = "https://subastas.boe.es/api.php"

    # Madrid-area provinces + their BOE province codes
    TARGET_PROVINCES = {
        "TO": "Toledo",
        "GU": "Guadalajara",
        "SG": "Segovia",
        "AV": "Ávila",
        "CU": "Cuenca",
        "M":  "Madrid",
    }

    def fetch(self) -> List[Property]:
        results = []
        for code, name in self.TARGET_PROVINCES.items():
            try:
                batch = self._fetch_province(code, name)
                results.extend(batch)
            except Exception as e:
                print(f"[spain_boe] Error fetching {name}: {e}")
        return results

    def _fetch_province(self, province_code: str, province_name: str) -> List[Property]:
        params = {
            "accion": "SEARCH_SUBASTA",
            "provincia_subasta": province_code,
            "tipo_bien": "INM",       # inmueble = real estate
            "estado_subasta": "EJE",  # en ejecución = active
            "pagina": 1,
        }
        try:
            resp = httpx.get(self.API_BASE, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[spain_boe] HTTP error for {province_name}: {e}")
            return []

        properties = []
        auctions = data.get("subastas", {}).get("subasta", [])
        if isinstance(auctions, dict):
            auctions = [auctions]

        for item in auctions:
            prop = self._parse_auction(item, province_name)
            if prop and self._matches_profile(prop):
                properties.append(prop)

        return properties

    def _parse_auction(self, item: dict, province_name: str) -> Property | None:
        try:
            ref = item.get("idSubasta", "")
            uid = hashlib.md5(f"spain_boe_{ref}".encode()).hexdigest()

            title = item.get("descripcionBien", "Propiedad en subasta")
            location = f"{item.get('municipio', '')}, {province_name}, España".strip(", ")
            region = self._detect_region(f"{location} {title}")

            price_raw = item.get("valorBien") or item.get("precioSalida") or ""
            price = self._parse_price(str(price_raw)) if price_raw else None

            desc_parts = [
                item.get("descripcionBien", ""),
                item.get("situacion", ""),
                item.get("cargas", ""),
            ]
            description = " | ".join(p for p in desc_parts if p)

            prop_type, is_hist, needs_refurb = self._detect_property_type(f"{title} {description}")
            area = self._parse_area(description)

            auction_start = item.get("fechaInicio", "")
            auction_end = item.get("fechaFin", "")

            payment = item.get("condicionesPago") or item.get("forma_pago", "")

            url = f"https://subastas.boe.es/detalleSubasta.php?idSub={ref}"

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
                auction_date=auction_start,
                auction_end_date=auction_end,
                description=description,
                url=url,
                image_url=None,
                is_historical=is_hist,
                needs_refurbishment=needs_refurb,
                payment_conditions=payment,
            )
        except Exception as e:
            print(f"[spain_boe] Parse error: {e}")
            return None
