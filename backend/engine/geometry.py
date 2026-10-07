"""Geometrical operations: polyline decoding, equidistant resampling, cumulative distance/time interpolation, and route snapping."""

import math
from typing import Any, Dict, List, Tuple

from engine.config import SEGMENT_LEN_M, VEHICLE_SPEED_FACTOR

EARTH_RADIUS_M = 6371000.0


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in meters."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c


def decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """Decode a Google-encoded polyline string into a list of (lat, lon) coordinates."""
    if not encoded:
        return []

    coordinates: List[Tuple[float, float]] = []
    index = 0
    lat = 0
    lon = 0
    length = len(encoded)

    while index < length:
        # Decode Latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Decode Longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlon = ~(result >> 1) if (result & 1) else (result >> 1)
        lon += dlon

        coordinates.append((lat / 1e5, lon / 1e5))

    return coordinates


def resample_route(
    coordinates: List[Tuple[float, float]],
    step_m: float = SEGMENT_LEN_M,
) -> List[Tuple[float, float, float]]:
    """Resample polyline coordinates into equidistant intervals of step_m.

    Returns:
    List of (lat, lon, segment_len_m) for each sampled point.
    """
    if not coordinates:
        return []
    if len(coordinates) == 1:
        return [(coordinates[0][0], coordinates[0][1], 0.0)]

    # Compute total distances between consecutive vertices
    seg_lengths = []
    total_dist = 0.0
    for i in range(len(coordinates) - 1):
        d = haversine_distance_m(
            coordinates[i][0], coordinates[i][1],
            coordinates[i + 1][0], coordinates[i + 1][1]
        )
        seg_lengths.append(d)
        total_dist += d

    if total_dist <= step_m:
        # Route is very short: return start and end
        return [
            (coordinates[0][0], coordinates[0][1], total_dist / 2.0),
            (coordinates[-1][0], coordinates[-1][1], total_dist / 2.0),
        ]

    # Walk along the path and sample at target distances
    sampled: List[Tuple[float, float, float]] = []
    curr_target = 0.0
    curr_vert_idx = 0
    dist_into_curr_seg = 0.0

    while curr_target <= total_dist:
        # Advance through vertices until we find the segment containing curr_target
        while curr_vert_idx < len(seg_lengths) and (dist_into_curr_seg + seg_lengths[curr_vert_idx] < curr_target):
            dist_into_curr_seg += seg_lengths[curr_vert_idx]
            curr_vert_idx += 1

        if curr_vert_idx >= len(seg_lengths):
            # Reached end
            sampled.append((coordinates[-1][0], coordinates[-1][1], step_m))
            break

        seg_len = seg_lengths[curr_vert_idx]
        fraction = (curr_target - dist_into_curr_seg) / seg_len if seg_len > 0 else 0.0
        fraction = max(0.0, min(1.0, fraction))

        lat1, lon1 = coordinates[curr_vert_idx]
        lat2, lon2 = coordinates[curr_vert_idx + 1]

        interp_lat = lat1 + fraction * (lat2 - lat1)
        interp_lon = lon1 + fraction * (lon2 - lon1)

        sampled.append((interp_lat, interp_lon, step_m))
        curr_target += step_m

    # Ensure final destination is explicitly represented
    last_p = sampled[-1]
    dest_d = haversine_distance_m(last_p[0], last_p[1], coordinates[-1][0], coordinates[-1][1])
    if dest_d > (step_m * 0.35):
        sampled.append((coordinates[-1][0], coordinates[-1][1], dest_d))

    return sampled


def interpolate_cumulative_times(
    sampled_points: List[Tuple[float, float, float]],
    total_distance_m: float,
    total_duration_s: float,
    speed_factor: float = VEHICLE_SPEED_FACTOR,
) -> List[Tuple[float, float]]:
    """Compute cumulative distance and interpolated arrival times for sampled points.

    Returns:
    List of (cum_dist_m, cum_time_s) matching each sampled point.
    """
    if not sampled_points:
        return []

    adjusted_total_duration_s = total_duration_s * speed_factor
    n = len(sampled_points)
    if n == 1:
        return [(0.0, 0.0)]

    cum_metrics: List[Tuple[float, float]] = []
    running_dist = 0.0

    for i in range(n):
        if i == 0:
            cum_metrics.append((0.0, 0.0))
        else:
            prev_p = sampled_points[i - 1]
            curr_p = sampled_points[i]
            d = haversine_distance_m(prev_p[0], prev_p[1], curr_p[0], curr_p[1])
            running_dist += d
            frac = min(running_dist / total_distance_m, 1.0) if total_distance_m > 0 else (i / (n - 1))
            cum_time = frac * adjusted_total_duration_s
            cum_metrics.append((round(running_dist, 1), round(cum_time, 1)))

    return cum_metrics


def snap_to_route(
    point: Tuple[float, float],
    route_points: List[Tuple[float, float]],
) -> Tuple[int, float, Tuple[float, float]]:
    """Find the closest point on the route to the given coordinates.

    Returns:
    (closest_index, distance_to_route_m, (snapped_lat, snapped_lon))
    """
    if not route_points:
        return 0, 0.0, point

    best_idx = 0
    min_dist = float("inf")

    for i, p in enumerate(route_points):
        d = haversine_distance_m(point[0], point[1], p[0], p[1])
        if d < min_dist:
            min_dist = d
            best_idx = i

    snapped_point = route_points[best_idx]
    return best_idx, min_dist, snapped_point


def compute_route_overlap(
    route1_points: List[Tuple[float, float]],
    route2_points: List[Tuple[float, float]],
    overlap_threshold_m: float = 200.0,
) -> float:
    """Calculate the overlap ratio: fraction of points in route1 within threshold distance of route2."""
    if not route1_points or not route2_points:
        return 0.0

    overlapping_count = 0
    for p1 in route1_points:
        _, dist, _ = snap_to_route(p1, route2_points)
        if dist <= overlap_threshold_m:
            overlapping_count += 1

    return overlapping_count / len(route1_points)


def to_geojson_linestring(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Convert list of (lat, lon) into GeoJSON LineString format [[lon, lat], ...]."""
    return {
        "type": "LineString",
        "coordinates": [[round(lon, 6), round(lat, 6)] for lat, lon in coords],
    }
