"""
Weekly scrape runner.
Run manually:  python -m auction_dashboard.backend.scheduler
Or schedule via cron:  0 8 * * 1  python -m auction_dashboard.backend.scheduler
(Every Monday at 08:00)
"""
import sys
import os
from datetime import datetime
from .scrapers import ALL_SCRAPERS
from .database import init_db, upsert_property, log_scrape_run
from .notifier import send_new_properties_alert
from .config import SOURCES


def run_scrape():
    print(f"[scheduler] Starting scrape run — {datetime.utcnow().isoformat()}")
    init_db()
    all_new = []

    for ScraperClass in ALL_SCRAPERS:
        scraper = ScraperClass()
        if not SOURCES.get(scraper.source_id, True):
            print(f"[scheduler] Skipping {scraper.source_id} (disabled in config)")
            continue

        print(f"[scheduler] Running {scraper.source_id}...")
        error = None
        new_count = 0
        total_count = 0

        try:
            properties = scraper.fetch()
            total_count = len(properties)
            for prop in properties:
                is_new = upsert_property(prop)
                if is_new:
                    new_count += 1
                    all_new.append(prop)
            print(f"[scheduler] {scraper.source_id}: {total_count} matched, {new_count} new")
        except Exception as e:
            error = str(e)
            print(f"[scheduler] {scraper.source_id} failed: {e}")

        log_scrape_run(scraper.source_id, new_count, total_count, error)

    print(f"[scheduler] Done. {len(all_new)} new properties total.")

    if all_new:
        send_new_properties_alert(all_new)

    return all_new


if __name__ == "__main__":
    run_scrape()
