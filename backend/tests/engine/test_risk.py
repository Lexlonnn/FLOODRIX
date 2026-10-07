"""Unit tests for time-aware rainfall, risk rules, aggregation, and cost functions."""

from datetime import datetime, timezone
import pytest

from engine.models import (
    GeoJSONGeometry,
    RiskBand,
    RouteMetrics,
    RouteOption,
    Segment,
    WorstSegment,
)
from engine.risk.aggregate import aggregate_route_risk
from engine.risk.cost import calculate_effective_time, rank_and_explain_routes
from engine.risk.rules import score_segment_rules
from engine.weather.time_aware import calculate_time_aware_rainfall


def test_time_aware_rainfall_monotonicity():
    hourly = {1000 + i: float(i % 5) for i in range(50)}
    arr_dt = datetime.fromtimestamp(1030 * 3600, tz=timezone.utc)

    r1, r6, r24 = calculate_time_aware_rainfall(hourly, arr_dt)
    assert 0.0 <= r1 <= r6 <= r24


def test_rules_fallback_sanity():
    # Low rain, high elevation
    p_safe = score_segment_rules(rainfall_1h=0.0, rainfall_6h=2.0, rainfall_24h=5.0, elevation=200.0)
    # Severe rain, low coastal elevation
    p_danger = score_segment_rules(rainfall_1h=25.0, rainfall_6h=65.0, rainfall_24h=140.0, elevation=2.0)

    assert p_safe < 0.15
    assert p_danger > 0.60
    assert p_danger > p_safe


def test_aggregate_route_risk_cell_collapse():
    # 4 segments within the same 500m area (should collapse to 1 cell)
    segments = [
        Segment(
            index=i,
            lat=10.000 + i * 0.0001,
            lon=76.002 + i * 0.0001,
            length_m=500.0,
            cum_dist_m=float(i * 500),
            cum_time_s=float(i * 40),
            eta="2026-10-08T06:00:00Z",
            p=0.4 if i == 0 else 0.2,
            band=RiskBand.MEDIUM if i == 0 else RiskBand.LOW,
        )
        for i in range(4)
    ]

    metrics = aggregate_route_risk(segments)
    # Max p in this single cell is 0.4
    assert metrics.max_p == 0.4
    # Expected disruptions across 1 cell is max_p = 0.4
    assert metrics.expected_disruptions == 0.4
    assert metrics.p_any == 0.4
    assert metrics.n_high_cells == 0


def test_effective_time_cost_monotonicity():
    # More risk should strictly increase effective_time
    metrics_low = RouteMetrics(expected_disruptions=0.5, p_any=0.3, max_p=0.3, high_risk_km=0.0, n_high_cells=0, closed_segments=0)
    metrics_high = RouteMetrics(expected_disruptions=2.0, p_any=0.8, max_p=0.8, high_risk_km=5.0, n_high_cells=3, closed_segments=0)

    cost_low = calculate_effective_time(duration_min=60.0, metrics=metrics_low, cargo="general")
    cost_high = calculate_effective_time(duration_min=60.0, metrics=metrics_high, cargo="general")

    assert cost_high > cost_low

    # Hazardous cargo should penalize risk much more than general
    cost_haz = calculate_effective_time(duration_min=60.0, metrics=metrics_high, cargo="hazardous")
    assert cost_haz > cost_high


def test_rank_and_explain_hard_filters():
    # Route 1: fast but has closure
    r1 = RouteOption(
        route_id="r1",
        label="Route 1",
        distance_km=50.0,
        duration_min=60.0,
        eta="2026-10-08T07:00:00Z",
        effective_time=60.0,
        metrics=RouteMetrics(expected_disruptions=0.2, p_any=0.2, max_p=0.2, high_risk_km=0.0, n_high_cells=0, closed_segments=1),
        geometry=GeoJSONGeometry(coordinates=[[76.0, 10.0], [76.1, 10.1]]),
        segments=[],
    )

    # Route 2: slightly slower but safe
    r2 = RouteOption(
        route_id="r2",
        label="Route 2",
        distance_km=55.0,
        duration_min=70.0,
        eta="2026-10-08T07:10:00Z",
        effective_time=70.0,
        metrics=RouteMetrics(expected_disruptions=0.1, p_any=0.1, max_p=0.15, high_risk_km=0.0, n_high_cells=0, closed_segments=0),
        geometry=GeoJSONGeometry(coordinates=[[76.0, 10.0], [76.2, 10.2]]),
        segments=[],
    )

    ranked, rec = rank_and_explain_routes([r1, r2], cargo="general", p_block_threshold=0.7)
    assert rec.route_id == "r2"
    assert rec.is_recommended is True
    assert r1.is_hard_filtered is True
