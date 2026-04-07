from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FilmRecord:
    title: str
    year: str
    imdb_id: str = ""
    rating_10: str = ""
    review: str = ""
    watched_date: str = ""

    def normalized(self) -> "FilmRecord":
        return FilmRecord(
            title=" ".join(self.title.lower().split()),
            year=self.year.strip(),
            imdb_id=self.imdb_id.strip().lower(),
            rating_10=self.rating_10.strip(),
            review=self.review.strip(),
            watched_date=self.watched_date.strip(),
        )

    def key(self) -> tuple[str, str, str]:
        normalized = self.normalized()
        if normalized.imdb_id:
            return ("imdb", normalized.imdb_id, "")
        return ("title_year", normalized.title, normalized.year)


@dataclass
class SyncDiff:
    add_to_imdb: list[FilmRecord]
    add_to_letterboxd: list[FilmRecord]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def parse_letterboxd(path: Path) -> list[FilmRecord]:
    records: list[FilmRecord] = []
    for row in _read_csv(path):
        # Letterboxd exports typically use Name/Year/IMDb ID.
        title = (row.get("Name") or row.get("Title") or "").strip()
        if not title:
            continue
        year = (row.get("Year") or "").strip()
        imdb_id = (row.get("IMDb ID") or row.get("imdbID") or "").strip()
        rating = (row.get("Rating") or row.get("Rating10") or "").strip()
        review = (row.get("Review") or "").strip()
        watched_date = (row.get("Watched Date") or row.get("Date") or "").strip()
        records.append(
            FilmRecord(
                title=title,
                year=year,
                imdb_id=imdb_id,
                rating_10=rating,
                review=review,
                watched_date=watched_date,
            )
        )
    return records


def parse_imdb(path: Path) -> list[FilmRecord]:
    records: list[FilmRecord] = []
    for row in _read_csv(path):
        # IMDb exports commonly use Title/Year/Const.
        title = (row.get("Title") or row.get("Name") or "").strip()
        if not title:
            continue
        year = (row.get("Year") or "").strip()
        imdb_id = (row.get("Const") or row.get("IMDb ID") or "").strip()
        rating = (row.get("Your Rating") or row.get("Rating") or "").strip()
        review = (row.get("Review") or row.get("Comments") or "").strip()
        watched_date = (row.get("Date Rated") or row.get("Watched Date") or "").strip()
        records.append(
            FilmRecord(
                title=title,
                year=year,
                imdb_id=imdb_id,
                rating_10=rating,
                review=review,
                watched_date=watched_date,
            )
        )
    return records


def _index(records: Iterable[FilmRecord]) -> dict[tuple[str, str, str], FilmRecord]:
    return {record.key(): record for record in records}


def diff_records(letterboxd: list[FilmRecord], imdb: list[FilmRecord]) -> SyncDiff:
    letterboxd_index = _index(letterboxd)
    imdb_index = _index(imdb)

    add_to_imdb = [record for key, record in letterboxd_index.items() if key not in imdb_index]
    add_to_letterboxd = [record for key, record in imdb_index.items() if key not in letterboxd_index]

    return SyncDiff(add_to_imdb=sorted(add_to_imdb, key=lambda x: (x.title, x.year)), add_to_letterboxd=sorted(add_to_letterboxd, key=lambda x: (x.title, x.year)))


def write_imdb_import_csv(path: Path, records: list[FilmRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = ["Const", "Your Rating", "Date Rated", "Title", "URL", "Title Type", "IMDb Rating", "Runtime (mins)", "Year", "Genres", "Num Votes", "Release Date", "Directors"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Const": record.imdb_id,
                    "Your Rating": record.rating_10,
                    "Date Rated": record.watched_date,
                    "Title": record.title,
                    "URL": f"https://www.imdb.com/title/{record.imdb_id}/" if record.imdb_id else "",
                    "Title Type": "",
                    "IMDb Rating": "",
                    "Runtime (mins)": "",
                    "Year": record.year,
                    "Genres": "",
                    "Num Votes": "",
                    "Release Date": "",
                    "Directors": "",
                }
            )


def _imdb_to_letterboxd_rating(imdb_rating: str) -> str:
    if not imdb_rating:
        return ""
    try:
        value = float(imdb_rating)
    except ValueError:
        return ""
    # IMDb is 10-point; Letterboxd is 5-point (supports .5 steps).
    converted = round(value / 2 * 2) / 2
    return f"{converted:g}"


def write_letterboxd_import_csv(path: Path, records: list[FilmRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = ["Title", "Year", "IMDb ID", "Rating", "Watched Date", "Review"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Title": record.title,
                    "Year": record.year,
                    "IMDb ID": record.imdb_id,
                    "Rating": _imdb_to_letterboxd_rating(record.rating_10),
                    "Watched Date": record.watched_date,
                    "Review": record.review,
                }
            )


def run_sync(letterboxd_csv: Path, imdb_csv: Path, output_dir: Path) -> SyncDiff:
    output_dir.mkdir(parents=True, exist_ok=True)

    letterboxd_records = parse_letterboxd(letterboxd_csv)
    imdb_records = parse_imdb(imdb_csv)

    diff = diff_records(letterboxd_records, imdb_records)

    write_imdb_import_csv(output_dir / "imdb_import_from_letterboxd.csv", diff.add_to_imdb)
    write_letterboxd_import_csv(output_dir / "letterboxd_import_from_imdb.csv", diff.add_to_letterboxd)

    summary = {
        "letterboxd_total": len(letterboxd_records),
        "imdb_total": len(imdb_records),
        "missing_in_imdb": len(diff.add_to_imdb),
        "missing_in_letterboxd": len(diff.add_to_letterboxd),
        "missing_in_imdb_preview": [record.__dict__ for record in diff.add_to_imdb[:20]],
        "missing_in_letterboxd_preview": [record.__dict__ for record in diff.add_to_letterboxd[:20]],
    }

    with (output_dir / "sync_report.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    return diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Letterboxd and IMDb exports.")
    parser.add_argument("--letterboxd", required=True, type=Path, help="Path to a Letterboxd CSV export (watched or watchlist).")
    parser.add_argument("--imdb", required=True, type=Path, help="Path to an IMDb CSV export.")
    parser.add_argument("--output", default=Path("./output"), type=Path, help="Output folder for sync artifacts.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    diff = run_sync(args.letterboxd, args.imdb, args.output)

    print(f"Done. {len(diff.add_to_imdb)} titles can be imported into IMDb.")
    print(f"{len(diff.add_to_letterboxd)} titles can be imported into Letterboxd.")
    print(f"Artifacts written to: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
