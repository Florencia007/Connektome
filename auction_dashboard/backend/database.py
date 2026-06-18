import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from .models import Property

DB_PATH = Path(__file__).parent.parent / "data" / "properties.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                region TEXT,
                country TEXT,
                price_eur REAL,
                area_m2 REAL,
                property_type TEXT,
                auction_date TEXT,
                auction_end_date TEXT,
                description TEXT,
                url TEXT,
                image_url TEXT,
                is_historical INTEGER DEFAULT 0,
                needs_refurbishment INTEGER DEFAULT 0,
                payment_conditions TEXT,
                scraped_at TEXT,
                is_new INTEGER DEFAULT 1,
                is_favourite INTEGER DEFAULT 0,
                notes TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at TEXT NOT NULL,
                source TEXT NOT NULL,
                new_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                error TEXT
            )
        """)


def upsert_property(prop: Property) -> bool:
    """Returns True if this is a newly inserted property."""
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM properties WHERE id = ?", (prop.id,)).fetchone()
        if existing:
            return False
        conn.execute("""
            INSERT INTO properties
            (id, source, title, location, region, country, price_eur, area_m2,
             property_type, auction_date, auction_end_date, description, url, image_url,
             is_historical, needs_refurbishment, payment_conditions, scraped_at, is_new,
             is_favourite, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, '')
        """, (
            prop.id, prop.source, prop.title, prop.location, prop.region,
            prop.country, prop.price_eur, prop.area_m2, prop.property_type,
            prop.auction_date, prop.auction_end_date, prop.description, prop.url,
            prop.image_url, int(prop.is_historical), int(prop.needs_refurbishment),
            prop.payment_conditions, prop.scraped_at,
        ))
        return True


def get_properties(
    region: Optional[str] = None,
    max_price: Optional[float] = None,
    is_new: Optional[bool] = None,
    is_favourite: Optional[bool] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[dict]:
    query = "SELECT * FROM properties WHERE 1=1"
    params = []
    if region:
        query += " AND region = ?"
        params.append(region)
    if max_price is not None:
        query += " AND (price_eur IS NULL OR price_eur <= ?)"
        params.append(max_price)
    if is_new is not None:
        query += " AND is_new = ?"
        params.append(int(is_new))
    if is_favourite is not None:
        query += " AND is_favourite = ?"
        params.append(int(is_favourite))
    if source:
        query += " AND source = ?"
        params.append(source)
    if search:
        query += " AND (title LIKE ? OR location LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    query += " ORDER BY is_new DESC, scraped_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def count_properties(**kwargs) -> int:
    kwargs.pop("limit", None)
    kwargs.pop("offset", None)
    query = "SELECT COUNT(*) FROM properties WHERE 1=1"
    params = []
    if kwargs.get("region"):
        query += " AND region = ?"
        params.append(kwargs["region"])
    if kwargs.get("max_price") is not None:
        query += " AND (price_eur IS NULL OR price_eur <= ?)"
        params.append(kwargs["max_price"])
    if kwargs.get("is_new") is not None:
        query += " AND is_new = ?"
        params.append(int(kwargs["is_new"]))
    if kwargs.get("is_favourite") is not None:
        query += " AND is_favourite = ?"
        params.append(int(kwargs["is_favourite"]))
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()[0]


def mark_seen(property_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE properties SET is_new = 0 WHERE id = ?", (property_id,))


def toggle_favourite(property_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT is_favourite FROM properties WHERE id = ?", (property_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["is_favourite"] else 1
        conn.execute("UPDATE properties SET is_favourite = ? WHERE id = ?", (new_val, property_id))
        return bool(new_val)


def save_note(property_id: str, notes: str):
    with get_conn() as conn:
        conn.execute("UPDATE properties SET notes = ? WHERE id = ?", (notes, property_id))


def log_scrape_run(source: str, new_count: int, total_count: int, error: Optional[str] = None):
    from datetime import datetime
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO scrape_runs (ran_at, source, new_count, total_count, error) VALUES (?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), source, new_count, total_count, error),
        )


def get_scrape_history(limit: int = 20) -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scrape_runs ORDER BY ran_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
