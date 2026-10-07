"""Thread-safe Weather Cache with TTL and stale data tracking for graceful degradation."""

import time
from typing import Dict, List, Optional, Tuple

from engine.config import WEATHER_CACHE_PLANNING_TTL_SEC


class WeatherCache:
    """Caches spatial weather grids (0.1 deg ~11 km) with time-to-live policies."""

    def __init__(self, default_ttl_sec: int = WEATHER_CACHE_PLANNING_TTL_SEC):
        self.default_ttl = default_ttl_sec
        # Store: (grid_lat, grid_lon) -> (fetch_time, Dict[epoch_hour, precipitation_mm])
        self._store: Dict[Tuple[float, float], Tuple[float, Dict[int, float]]] = {}

    @staticmethod
    def to_grid_key(lat: float, lon: float) -> Tuple[float, float]:
        """Discretize to 0.1 degree grid cell (~11 km)."""
        return round(lat, 1), round(lon, 1)

    def get(
        self,
        lat: float,
        lon: float,
        allow_stale: bool = True,
        ttl_sec: Optional[int] = None,
    ) -> Tuple[Optional[Dict[int, float]], bool, float]:
        """Retrieve cached hourly precipitation series.

        Returns:
        (data_dict_or_none, is_stale, age_minutes)
        """
        key = self.to_grid_key(lat, lon)
        entry = self._store.get(key)
        if not entry:
            return None, False, 0.0

        fetch_time, data = entry
        age_sec = time.time() - fetch_time
        age_min = age_sec / 60.0
        effective_ttl = ttl_sec if ttl_sec is not None else self.default_ttl

        if age_sec <= effective_ttl:
            return data, False, age_min
        elif allow_stale:
            return data, True, age_min
        else:
            return None, True, age_min

    def set(self, lat: float, lon: float, data: Dict[int, float]):
        """Store hourly precipitation series for grid key."""
        key = self.to_grid_key(lat, lon)
        self._store[key] = (time.time(), data)

    def clear(self):
        self._store.clear()
