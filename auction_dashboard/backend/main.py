from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from .database import (
    init_db, get_properties, count_properties, mark_seen,
    toggle_favourite, save_note, get_scrape_history,
)
from .scheduler import run_scrape

app = FastAPI(title="Auction Dashboard")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.on_event("startup")
def startup():
    init_db()


# ── Properties ────────────────────────────────────────────────────────────────

@app.get("/api/properties")
def list_properties(
    region: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    is_new: Optional[bool] = Query(None),
    is_favourite: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    props = get_properties(
        region=region, max_price=max_price, is_new=is_new,
        is_favourite=is_favourite, source=source, search=search,
        limit=limit, offset=offset,
    )
    total = count_properties(
        region=region, max_price=max_price, is_new=is_new,
        is_favourite=is_favourite,
    )
    return {"properties": props, "total": total, "offset": offset, "limit": limit}


@app.post("/api/properties/{property_id}/seen")
def mark_property_seen(property_id: str):
    mark_seen(property_id)
    return {"ok": True}


@app.post("/api/properties/{property_id}/favourite")
def toggle_property_favourite(property_id: str):
    is_fav = toggle_favourite(property_id)
    return {"is_favourite": is_fav}


@app.post("/api/properties/{property_id}/notes")
def update_notes(property_id: str, body: dict):
    notes = body.get("notes", "")
    save_note(property_id, notes)
    return {"ok": True}


# ── Scraper ───────────────────────────────────────────────────────────────────

@app.post("/api/scrape")
def trigger_scrape():
    """Manually trigger a scrape run (also runs automatically weekly via cron)."""
    new_props = run_scrape()
    return {"new_count": len(new_props), "new_properties": [p.id for p in new_props]}


@app.get("/api/scrape/history")
def scrape_history():
    return {"runs": get_scrape_history()}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    from .database import get_conn
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM properties WHERE is_new = 1").fetchone()[0]
        favs = conn.execute("SELECT COUNT(*) FROM properties WHERE is_favourite = 1").fetchone()[0]
        by_region = conn.execute(
            "SELECT region, COUNT(*) as cnt FROM properties GROUP BY region ORDER BY cnt DESC"
        ).fetchall()
        last_run = conn.execute(
            "SELECT ran_at, new_count FROM scrape_runs ORDER BY ran_at DESC LIMIT 1"
        ).fetchone()
    return {
        "total": total,
        "new": new,
        "favourites": favs,
        "by_region": [dict(r) for r in by_region],
        "last_scrape": dict(last_run) if last_run else None,
    }


# ── Frontend ──────────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/{path:path}")
def serve_spa(path: str):
    file_path = FRONTEND_DIR / path
    if file_path.exists():
        return FileResponse(str(file_path))
    return FileResponse(str(FRONTEND_DIR / "index.html"))
