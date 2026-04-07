# Sync IMDB and Letterboxd

Connector utility to sync Letterboxd and IMDb exports.

## What it does

- Reads a Letterboxd CSV export (`watched.csv` or `watchlist.csv`).
- Reads an IMDb CSV export.
- Computes what is missing in each side.
- Generates an IMDb-compatible import file for titles found in Letterboxd but missing in IMDb.
- Generates a Letterboxd-compatible import file for titles rated/reviewed in IMDb but missing in Letterboxd.
- Writes a JSON report with totals and previews.

## Usage

```bash
python -m src.letterboxd_imdb_connector \
  --letterboxd /path/to/letterboxd.csv \
  --imdb /path/to/imdb.csv \
  --output ./output
```

### Output files

- `output/imdb_import_from_letterboxd.csv`
- `output/letterboxd_import_from_imdb.csv`
- `output/sync_report.json`

## Notes

Letterboxd and IMDb do not provide equivalent write APIs for personal lists, so this connector focuses on export/import workflow compatibility.
