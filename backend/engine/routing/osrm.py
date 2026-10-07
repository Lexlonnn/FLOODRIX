"""OSRM routing provider with automatic fallback to mock provider on network failure."""

import json
import logging
import urllib.request
from typing import Any, List, Optional
import httpx

from engine.config import OSRM_URL
from engine.geometry import decode_polyline
from engine.models import Coordinate
from engine.routing.base import RoutingProvider, RoutingResult, deduplicate_routes
from engine.routing.mock import MockRoutingProvider

logger = logging.getLogger("floodrix.routing.osrm")


class OSRMRoutingProvider(RoutingProvider):
    """Integrates with OSRM HTTP API for real routing geometry and step durations."""

    def __init__(self, base_url: str = OSRM_URL, timeout_sec: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.mock_fallback = MockRoutingProvider()

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        alternatives: int = 3,
        avoid_polygons: Optional[List[Any]] = None,
    ) -> List[RoutingResult]:
        """Fetch routes from OSRM server, decoding geometries and steps with fallback."""
        url = (
            f"{self.base_url}/route/v1/driving/"
            f"{origin.lon:.6f},{origin.lat:.6f};{destination.lon:.6f},{destination.lat:.6f}"
            f"?overview=full&geometries=polyline&alternatives={min(alternatives, 3)}&steps=true"
        )

        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"OSRM returned status {resp.status_code}. Falling back to mock routing.")
                    return self.mock_fallback.get_routes(origin, destination, alternatives, avoid_polygons)
                data = resp.json()
        except Exception as e:
            logger.warning(f"OSRM connection failed ({e}). Falling back to mock routing.")
            return self.mock_fallback.get_routes(origin, destination, alternatives, avoid_polygons)

        raw_routes = data.get("routes", [])
        if not raw_routes:
            return self.mock_fallback.get_routes(origin, destination, alternatives, avoid_polygons)

        results: List[RoutingResult] = []
        for i, r in enumerate(raw_routes):
            geom = decode_polyline(r.get("geometry", ""))
            dist_m = float(r.get("distance", 0.0))
            dur_s = float(r.get("duration", 0.0))

            step_durations = []
            step_distances = []
            for leg in r.get("legs", []):
                for step in leg.get("steps", []):
                    step_durations.append(float(step.get("duration", 0.0)))
                    step_distances.append(float(step.get("distance", 0.0)))

            results.append(
                RoutingResult(
                    route_id=f"osrm_route_{i+1}",
                    label=f"Route Option {i+1}",
                    geometry=geom,
                    distance_m=dist_m,
                    duration_s=dur_s,
                    step_durations=step_durations,
                    step_distances=step_distances,
                )
            )

        return deduplicate_routes(results, overlap_threshold=0.90)
