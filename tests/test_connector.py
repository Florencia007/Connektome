from pathlib import Path

from src.letterboxd_imdb_connector import _imdb_to_letterboxd_rating, parse_imdb, parse_letterboxd, run_sync


def test_run_sync_generates_imdb_import(tmp_path: Path) -> None:
    letterboxd_csv = tmp_path / "letterboxd.csv"
    imdb_csv = tmp_path / "imdb.csv"
    output_dir = tmp_path / "output"

    letterboxd_csv.write_text(
        "Name,Year,IMDb ID\nInception,2010,tt1375666\nAlien,1979,tt0078748\n",
        encoding="utf-8",
    )
    imdb_csv.write_text(
        "Const,Title,Year,Your Rating,Review,Date Rated\n"
        "tt1375666,Inception,2010,9,Masterpiece,2026-01-01\n"
        "tt0090605,Aliens,1986,10,All-time favorite,2026-01-02\n",
        encoding="utf-8",
    )

    diff = run_sync(letterboxd_csv, imdb_csv, output_dir)

    assert len(diff.add_to_imdb) == 1
    assert diff.add_to_imdb[0].title == "Alien"
    assert (output_dir / "imdb_import_from_letterboxd.csv").exists()
    assert (output_dir / "letterboxd_import_from_imdb.csv").exists()
    assert (output_dir / "sync_report.json").exists()

    letterboxd_import = (output_dir / "letterboxd_import_from_imdb.csv").read_text(encoding="utf-8")
    assert "Aliens" in letterboxd_import
    assert "All-time favorite" in letterboxd_import


def test_parsers_handle_alternative_headers(tmp_path: Path) -> None:
    letterboxd_csv = tmp_path / "lb_alt.csv"
    imdb_csv = tmp_path / "imdb_alt.csv"

    letterboxd_csv.write_text(
        "Title,Year,imdbID\nHeat,1995,tt0113277\n",
        encoding="utf-8",
    )
    imdb_csv.write_text(
        "IMDb ID,Name,Year\ntt0113277,Heat,1995\n",
        encoding="utf-8",
    )

    lb_records = parse_letterboxd(letterboxd_csv)
    imdb_records = parse_imdb(imdb_csv)

    assert lb_records[0].imdb_id == "tt0113277"
    assert imdb_records[0].title == "Heat"


def test_rating_conversion_for_letterboxd() -> None:
    assert _imdb_to_letterboxd_rating("10") == "5"
    assert _imdb_to_letterboxd_rating("9") == "4.5"
    assert _imdb_to_letterboxd_rating("7") == "3.5"
