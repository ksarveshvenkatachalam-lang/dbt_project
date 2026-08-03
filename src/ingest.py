"""Contracts Finder ingestion and OCDS release normalisation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API_URL = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"


def fetch_releases(limit: int = 100) -> dict[str, Any]:
    response = requests.get(API_URL, params={"limit": limit}, timeout=60)
    response.raise_for_status()
    return response.json()


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _party_name(parties: list[dict[str, Any]], party_id: str | None) -> str | None:
    return next((p.get("name") for p in parties if p.get("id") == party_id), None)


def normalise(package: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for release in package.get("releases", []):
        parties = release.get("parties", [])
        buyer = release.get("buyer", {})
        tender = release.get("tender", {})
        category = (tender.get("items") or [{}])[0].get("classification", {})
        for award in release.get("awards", []):
            suppliers = award.get("suppliers") or [{}]
            value = award.get("value", {})
            for supplier in suppliers:
                rows.append(
                    {
                        "ocid": release.get("ocid"),
                        "award_id": award.get("id"),
                        "award_date": award.get("date"),
                        "buyer_id": buyer.get("id"),
                        "buyer_name": buyer.get("name") or _party_name(parties, buyer.get("id")),
                        "supplier_id": supplier.get("id"),
                        "supplier_name": supplier.get("name") or _party_name(parties, supplier.get("id")),
                        "category_code": category.get("id", "UNCLASSIFIED"),
                        "category_name": category.get("description", "Unclassified"),
                        "award_value": value.get("amount"),
                        "currency": value.get("currency", "GBP"),
                        "title": tender.get("title"),
                    }
                )
    frame = pd.DataFrame(rows)
    required = {"ocid", "award_id", "buyer_name", "supplier_name", "award_value"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    frame["award_value"] = pd.to_numeric(frame["award_value"], errors="coerce")
    frame["award_date"] = pd.to_datetime(frame["award_date"], errors="coerce", utc=True)
    return frame.dropna(subset=["award_id", "buyer_name", "supplier_name", "award_value"])

