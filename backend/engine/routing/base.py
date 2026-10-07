"""Abstract RoutingProvider interface and route deduplication."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel

from engine.geometry import compute_route_overlap
from engine.models import Coordinate


class RoutingResult(BaseModel):
    route_id: str
    label: str
    geometry: List[Tuple[float, float]]  # [(lat, lon), ...]
    distance_m: float
    duration_s: float
    step_durations: List[float] = []
    step_distances: List[float] = []


class RoutingProvider(ABC):
    """Abstract interface for route generation providers."""

    @abstractmethod
    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        alternatives: int = 3,
        avoid_polygons: Optional[List[Any]] = None,
    ) -> List[RoutingResult]:
        """Fetch candidate routes from origin to destination."""
        pass


def deduplicate_routes(
    routes: List[RoutingResult],
    overlap_threshold: float = 0.90,
) -> List[RoutingResult]:
    """Filter out candidate routes that have > 90% spatial overlap with an existing route."""
    if not routes:
        return []

    unique_routes: List[RoutingResult] = [routes[0]]

    for candidate in routes[1:]:
        is_duplicate = False
        for accepted in unique_routes:
            overlap = compute_route_overlap(candidate.geometry, accepted.geometry)
            if overlap >= overlap_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_routes.append(candidate)

    return unique_routes
