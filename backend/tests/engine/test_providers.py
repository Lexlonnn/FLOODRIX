"""Unit tests for routing and weather providers, deduplication, and cache."""

from datetime import datetime, timezone
import time
import pytest

from engine.models import Coordinate
from engine.routing.base import RoutingResult, deduplicate_routes
from engine.routing.mock import MockRoutingProvider
from engine.weather.cache import WeatherCache
from engine.weather.mock import MockWeatherProvider


def test_mock_routing_provider():
    provider = MockRoutingProvider(num_points_per_route=20)
    origin = Coordinate(lat=9.98, lon=76.28)
    destination = Coordinate(lat=10.52, lon=76.21)

    routes = provider.get_routes(origin, destination, alternatives=3)
    assert len(routes) == 3
    for r in routes:
        assert len(r.geometry) == 20
        assert r.distance_m > 40000.0
        assert r.duration_s > 1000.0


def test_route_deduplication():
    # Two identical routes and one distinct route
    geom1 = [(10.0, 76.0), (10.1, 76.1), (10.2, 76.2)]
    geom2 = [(10.0, 76.0), (10.1, 76.1), (10.2, 76.2)]  # exact duplicate
    geom3 = [(11.0, 77.0), (11.1, 77.1), (11.2, 77.2)]  # distinct

    r1 = RoutingResult(route_id="r1", label="R1", geometry=geom1, distance_m=1000, duration_s=100)
    r2 = RoutingResult(route_id="r2", label="R2", geometry=geom2, distance_m=1000, duration_s=100)
    r3 = RoutingResult(route_id="r3", label="R3", geometry=geom3, distance_m=2000, duration_s=200)

    deduped = deduplicate_routes([r1, r2, r3], overlap_threshold=0.90)
    assert len(deduped) == 2
    assert [r.route_id for r in deduped] == ["r1", "r3"]


def test_mock_weather_provider():
    provider = MockWeatherProvider()
    now = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    coords = [(9.98, 76.28), (10.52, 76.21)]

    weather = provider.get_hourly_precipitation(coords, now, past_hours=24, forecast_hours=24)
    assert len(weather) == 2
    for pt in coords:
        assert pt in weather
        # 24 past + now + 24 forecast = 49 hours
        assert len(weather[pt]) >= 48


def test_weather_cache():
    cache = WeatherCache(default_ttl_sec=1)  # 1 second TTL
    lat, lon = 9.981, 76.282
    test_data = {1000: 5.5, 1001: 12.0}

    cache.set(lat, lon, test_data)

    # Immediate lookup -> fresh
    data, is_stale, age_min = cache.get(lat, lon)
    assert data == test_data
    assert is_stale is False

    # Wait for TTL to expire
    time.sleep(1.1)
    data_stale, is_stale2, age_min2 = cache.get(lat, lon, allow_stale=True)
    assert data_stale == test_data
    assert is_stale2 is True
    assert age_min2 > 0.0

    # Deny stale
    data_no_stale, _, _ = cache.get(lat, lon, allow_stale=False)
    assert data_no_stale is None
