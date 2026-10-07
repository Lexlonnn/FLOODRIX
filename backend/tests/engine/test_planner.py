"""Unit tests for engine/planner.py (RoutePlanner and departure scan)."""

from datetime import datetime, timezone
import pytest

from engine.models import AdvisoryType, Coordinate, PlanRouteRequest
from engine.planner import RoutePlanner
from engine.routing.mock import MockRoutingProvider
from engine.weather.mock import MockWeatherProvider


def test_route_planner_basic_flow():
    routing = MockRoutingProvider()
    weather = MockWeatherProvider(base_rain_mm=2.0)
    planner = RoutePlanner(routing_provider=routing, weather_provider=weather, predictor=None)

    req = PlanRouteRequest(
        origin=Coordinate(lat=10.78, lon=76.65),
        destination=Coordinate(lat=9.93, lon=76.27),
        depart_time="2026-10-08T06:00:00Z",
        cargo="general",
    )

    res = planner.plan(req)
    assert res.recommended_route_id is not None
    assert len(res.routes) > 0
    assert res.advisory in [AdvisoryType.GO, AdvisoryType.GO_WITH_CAUTION, AdvisoryType.DELAY, AdvisoryType.DO_NOT_GO]
    assert len(res.data_sources) >= 4

    best = res.routes[0]
    assert best.geometry.type == "LineString"
    assert len(best.geometry.coordinates) > 0
    assert len(best.segments) > 0
    assert best.segments[0].elevation is not None
    assert best.segments[0].rainfall_24h is not None


def test_route_planner_delay_scan():
    routing = MockRoutingProvider()
    # High storm at 06:00 UTC (10.0, 76.3) that moves away or subsides
    weather = MockWeatherProvider(
        base_rain_mm=1.0,
        storm_center=(10.0, 76.3),
        storm_radius_deg=0.5,
        storm_spike_mm=80.0,
        storm_peak_hour=6,
    )
    planner = RoutePlanner(routing_provider=routing, weather_provider=weather, predictor=None)

    req = PlanRouteRequest(
        origin=Coordinate(lat=10.78, lon=76.65),
        destination=Coordinate(lat=9.93, lon=76.27),
        depart_time="2026-10-08T06:00:00Z",
        cargo="hazardous",  # very sensitive to high risk
    )

    res = planner.plan(req)
    # At 06:00, severe storm spike creates high disruption; later departure scan should recommend delay or caution
    assert res.advisory in [AdvisoryType.DELAY, AdvisoryType.GO_WITH_CAUTION, AdvisoryType.DO_NOT_GO]
    if res.advisory == AdvisoryType.DELAY:
        assert res.suggested_departure is not None
