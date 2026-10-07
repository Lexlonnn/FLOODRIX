"""Open-Meteo weather provider with batching, TTL caching, and graceful degradation."""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Tuple
import urllib.request
import httpx

from engine.weather.base import WeatherProvider
from engine.weather.cache import WeatherCache
from engine.weather.mock import MockWeatherProvider

logger = logging.getLogger("floodrix.weather.open_meteo")


class OpenMeteoWeatherProvider(WeatherProvider):
    """Fetches real hourly precipitation from Open-Meteo with caching and mock fallback."""

    def __init__(self, cache: WeatherCache, timeout_sec: float = 6.0):
        self.cache = cache
        self.timeout_sec = timeout_sec
        self.fallback = MockWeatherProvider()
        self.last_degraded = False

    def get_hourly_precipitation(
        self,
        locations: List[Tuple[float, float]],
        ref_time: datetime,
        past_hours: int = 24,
        forecast_hours: int = 48,
    ) -> Dict[Tuple[float, float], Dict[int, float]]:
        """Fetch precipitation for locations using cache first, then batched HTTP request."""
        result: Dict[Tuple[float, float], Dict[int, float]] = {}
        missing_locations: List[Tuple[float, float]] = []

        # 1. Check Cache
        for lat, lon in locations:
            cached_series, is_stale, _ = self.cache.get(lat, lon, allow_stale=True)
            if cached_series is not None and not is_stale:
                result[(lat, lon)] = cached_series
            else:
                missing_locations.append((lat, lon))

        if not missing_locations:
            self.last_degraded = False
            return result

        # 2. Query Open-Meteo for uncached locations in batches of 30
        batch_size = 30
        for i in range(0, len(missing_locations), batch_size):
            batch = missing_locations[i : i + batch_size]
            lats_str = ",".join(f"{p[0]:.4f}" for p in batch)
            lons_str = ",".join(f"{p[1]:.4f}" for p in batch)
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lats_str}&longitude={lons_str}&hourly=precipitation"
                f"&past_hours={past_hours}&forecast_hours={forecast_hours}&timezone=UTC"
            )

            try:
                with httpx.Client(timeout=self.timeout_sec) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        payload = resp.json()
                        responses = payload if isinstance(payload, list) else [payload]
                        for loc_pt, loc_data in zip(batch, responses):
                            hourly = loc_data.get("hourly", {})
                            times = hourly.get("time", [])
                            precips = hourly.get("precipitation", [])
                            loc_map: Dict[int, float] = {}
                            for t_str, pr in zip(times, precips):
                                dt = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
                                ep_h = int(dt.timestamp()) // 3600
                                loc_map[ep_h] = float(pr or 0.0)

                            self.cache.set(loc_pt[0], loc_pt[1], loc_map)
                            result[loc_pt] = loc_map
                        continue
            except Exception as e:
                logger.warning(f"Open-Meteo batch weather fetch failed ({e}). Degrading to fallback.")
                self.last_degraded = True

            # If HTTP call failed, check stale cache or mock
            for loc_pt in batch:
                cached_series, is_stale, _ = self.cache.get(loc_pt[0], loc_pt[1], allow_stale=True)
                if cached_series is not None:
                    result[loc_pt] = cached_series
                else:
                    mock_res = self.fallback.get_hourly_precipitation([loc_pt], ref_time, past_hours, forecast_hours)
                    result[loc_pt] = mock_res[loc_pt]
                    self.cache.set(loc_pt[0], loc_pt[1], mock_res[loc_pt])

        return result
