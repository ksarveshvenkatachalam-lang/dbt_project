"""Build the local analytical warehouse."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from ingest import fetch_releases, load_fixture, normalise

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "ocds_sample.json"
DB_PATH = ROOT / "data" / "warehouse" / "procurement.duckdb"
SQL_PATH = ROOT / "sql" / "warehouse.sql"


def run(live: bool = False) -> Path:
    package = fetch_releases() if live else load_fixture(FIXTURE)
    awards = normalise(package)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as connection:
        connection.register("awards_input", awards)
        connection.execute(SQL_PATH.read_text(encoding="utf-8"))
        failures = connection.execute("SELECT COUNT(*) FROM quality_failures").fetchone()[0]
        if failures:
            raise ValueError(f"Warehouse validation failed with {failures} invalid records")
    return DB_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Fetch current API data")
    parser.add_argument("--fixture", action="store_true", help="Use deterministic fixture data")
    arguments = parser.parse_args()
    print(run(live=arguments.live))

