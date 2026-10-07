"""Unit tests for engine/geometry.py."""

import math
import pytest

from engine.geometry import (
    compute_route_overlap,
    decode_polyline,
    haversine_distance_m,
    interpolate_cumulative_times,
    resample_route,
    snap_to_route,
    to_geojson_linestring,
)


def test_haversine_distance():
    # Kochi to Alappuzha (~54 km)
    dist = haversine_distance_m(9.9816, 76.2999, 9.4981, 76.3388)
    assert 53000.0 <= dist <= 56000.0

    # Same point distance is zero
    assert haversine_distance_m(10.0, 76.0, 10.0, 76.0) == 0.0


def test_decode_polyline():
    # Standard encoded polyline from Google docs: "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    # [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    coords = decode_polyline(encoded)
    assert len(coords) == 3
    assert math.isclose(coords[0][0], 38.5, abs_tol=1e-4)
    assert math.isclose(coords[0][1], -120.2, abs_tol=1e-4)
    assert math.isclose(coords[1][0], 40.7, abs_tol=1e-4)
    assert math.isclose(coords[2][0], 43.252, abs_tol=1e-4)


def test_resample_route():
    # Route from Kochi to Thrissur (~70 km) with 3 vertices
    coords = [
        (9.98, 76.28),
        (10.25, 76.35),
        (10.52, 76.21),
    ]
    sampled = resample_route(coords, step_m=500.0)

    # For ~70 km at 500m intervals, expect around 130 - 150 points
    assert len(sampled) >= 120
    assert math.isclose(sampled[0][0], 9.98, abs_tol=1e-4)
    assert math.isclose(sampled[0][1], 76.28, abs_tol=1e-4)
    # End point should be near destination
    assert math.isclose(sampled[-1][0], 10.52, abs_tol=0.01)
    assert math.isclose(sampled[-1][1], 76.21, abs_tol=0.01)


def test_interpolate_cumulative_times():
    sampled = [
        (9.98, 76.28, 500.0),
        (10.05, 76.30, 500.0),
        (10.12, 76.32, 500.0),
        (10.20, 76.34, 500.0),
    ]
    total_dist_m = 25000.0
    total_duration_s = 1800.0  # 30 min

    cum_metrics = interpolate_cumulative_times(
        sampled, total_dist_m, total_duration_s, speed_factor=1.25
    )

    assert len(cum_metrics) == len(sampled)
    assert cum_metrics[0] == (0.0, 0.0)

    # Monotonic increasing distance and time
    for i in range(1, len(cum_metrics)):
        assert cum_metrics[i][0] > cum_metrics[i - 1][0]
        assert cum_metrics[i][1] > cum_metrics[i - 1][1]


def test_snap_to_route():
    route_points = [
        (10.0, 76.0),
        (10.1, 76.1),
        (10.2, 76.2),
    ]

    # Query point very close to middle vertex
    query = (10.099, 76.101)
    idx, dist_m, snapped = snap_to_route(query, route_points)
    assert idx == 1
    assert dist_m < 200.0
    assert snapped == (10.1, 76.1)


def test_route_overlap():
    route1 = [(10.0, 76.0), (10.1, 76.1), (10.2, 76.2)]
    # Exactly overlapping
    assert compute_route_overlap(route1, route1) == 1.0

    # Distant route
    route2 = [(11.0, 77.0), (11.1, 77.1), (11.2, 77.2)]
    assert compute_route_overlap(route1, route2) == 0.0


def test_to_geojson_linestring():
    coords = [(10.0, 76.0), (10.1, 76.1)]
    geojson = to_geojson_linestring(coords)
    assert geojson["type"] == "LineString"
    assert geojson["coordinates"] == [[76.0, 10.0], [76.1, 10.1]]
