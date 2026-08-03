from src.metrics import composite_risk, dependency_ratio, hhi


def test_hhi_equal_market():
    assert hhi([25, 25, 25, 25]) == 2500.0


def test_dependency_ratio():
    assert dependency_ratio([80, 20]) == 0.8


def test_composite_risk_is_bounded():
    assert composite_risk(10000, 2, 2) == 100.0

