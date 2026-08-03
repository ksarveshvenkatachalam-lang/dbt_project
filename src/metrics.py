"""Reusable procurement-risk metrics."""

from __future__ import annotations


def hhi(shares: list[float]) -> float:
    """Return the Herfindahl-Hirschman Index on the conventional 0–10,000 scale."""
    if not shares:
        return 0.0
    total = sum(shares)
    if total <= 0:
        return 0.0
    return round(sum(((share / total) * 100) ** 2 for share in shares), 2)


def dependency_ratio(values: list[float]) -> float:
    """Return the proportion represented by the largest buyer relationship."""
    total = sum(values)
    return round(max(values) / total, 4) if values and total > 0 else 0.0


def composite_risk(concentration: float, dependency: float, anomaly_rate: float) -> float:
    """Combine normalised risk components into a transparent 0–100 score."""
    score = 0.40 * min(concentration / 2500, 1) + 0.35 * dependency + 0.25 * anomaly_rate
    return round(min(max(score * 100, 0), 100), 1)

