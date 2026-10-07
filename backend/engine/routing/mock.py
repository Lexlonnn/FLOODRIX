"""Mock routing provider generating realistic candidate routes across Kerala without network calls."""

import math
from typing import Any, List, Optional, Tuple
import numpy as np

from engine.geometry import haversine_distance_m
from engine.models import Coordinate
from engine.routing.base import RoutingProvider, RoutingResult, deduplicate_routes


class MockRoutingProvider(RoutingProvider):
    """Provides deterministic, geometrically diverse candidate routes for offline testing and benchmarking."""

    def __init__(self, num_points_per_route: int = 40):
        self.num_points = num_points_per_route

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        alternatives: int = 3,
        avoid_polygons: Optional[List[Any]] = None,
    ) -> List[RoutingResult]:
        """Generate up to 3 distinct routes: Primary Highway, Midland Bypass, and Coastal Alternate."""
        lat1, lon1 = origin.lat, origin.lon
        lat2, lon2 = destination.lat, destination.lon

        direct_dist = haversine_distance_m(lat1, lon1, lat2, lon2)
        base_dist = max(direct_dist * 1.15, 10000.0)  # Road distance vs straight-line
        # Base speed approx 45 km/h (12.5 m/s) in Kerala traffic
        base_duration = base_dist / 12.5

        t_vals = np.linspace(0.0, 1.0, self.num_points)

        # 1. Primary Highway (direct with subtle sinuous road curvature)
        r1_coords: List[Tuple[float, float]] = []
        for t in t_vals:
            # Sinuous curve with 3 oscillations
            wobble = 0.008 * math.sin(3 * math.pi * t)
            la = lat1 + t * (lat2 - lat1) + wobble * math.cos(math.pi * t)
            lo = lon1 + t * (lon2 - lon1) + wobble * math.sin(math.pi * t)
            r1_coords.append((round(la, 6), round(lo, 6)))

        # 2. Midland Bypass (arcs eastward into foothills/higher elevation)
        r2_coords: List[Tuple[float, float]] = []
        for t in t_vals:
            arc_east = 0.055 * math.sin(math.pi * t)
            la = lat1 + t * (lat2 - lat1)
            lo = lon1 + t * (lon2 - lon1) + arc_east
            r2_coords.append((round(la, 6), round(lo, 6)))

        # 3. Coastal Corridor (arcs westward towards coastal belt)
        r3_coords: List[Tuple[float, float]] = []
        for t in t_vals:
            arc_west = -0.045 * math.sin(math.pi * t)
            la = lat1 + t * (lat2 - lat1)
            lo = lon1 + t * (lon2 - lon1) + arc_west
            r3_coords.append((round(la, 6), round(lo, 6)))

        candidates = [
            RoutingResult(
                route_id="route_primary",
                label="Primary Highway (NH)",
                geometry=r1_coords,
                distance_m=round(base_dist, 1),
                duration_s=round(base_duration, 1),
                step_durations=[base_duration / (self.num_points - 1)] * (self.num_points - 1),
                step_distances=[base_dist / (self.num_points - 1)] * (self.num_points - 1),
            ),
            RoutingResult(
                route_id="route_midland",
                label="Midland Bypass (Higher Elevation)",
                geometry=r2_coords,
                distance_m=round(base_dist * 1.14, 1),
                duration_s=round(base_duration * 1.18, 1),
                step_durations=[(base_duration * 1.18) / (self.num_points - 1)] * (self.num_points - 1),
                step_distances=[(base_dist * 1.14) / (self.num_points - 1)] * (self.num_points - 1),
            ),
            RoutingResult(
                route_id="route_coastal",
                label="Coastal Corridor",
                geometry=r3_coords,
                distance_m=round(base_dist * 1.08, 1),
                duration_s=round(base_duration * 1.11, 1),
                step_durations=[(base_duration * 1.11) / (self.num_points - 1)] * (self.num_points - 1),
                step_distances=[(base_dist * 1.08) / (self.num_points - 1)] * (self.num_points - 1),
            ),
        ]

        # Apply requested number of alternatives and deduplication
        deduped = deduplicate_routes(candidates[: max(1, alternatives)], overlap_threshold=0.90)
        return deduped
