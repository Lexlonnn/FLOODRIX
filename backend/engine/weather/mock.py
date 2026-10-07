"""Deterministic Mock Weather Provider for offline execution, unit tests, and simulations."""

from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Tuple

from engine.weather.base import WeatherProvider


class MockWeatherProvider(WeatherProvider):
    """Provides synthetic deterministic hourly rainfall for testing and reproducible simulation."""

    def __init__(self, rain_spike_corridor: Optional[Tuple[float, float, float, float]] = None, spike_intensity: float = 35.0):
        """
        Optional rain_spike_corridor: (min_lat, max_lat, min_lon, max_lon)
        where precipitation will be artificially elevated to simulate an active monsoon front.
        """
        self.spike_corridor = rain_spike_corridor
        self.spike_intensity = spike_intensity

    def get_hourly_precipitation(
        self,
        locations: List[Tuple[float, float]],
        ref_time: datetime,
        past_hours: int = 24,
        forecast_hours: int = 48,
    ) -> Dict[Tuple[float, float], Dict[int, float]]:
        """Generate smooth sinusoidal precipitation curves with optional localized storm spikes."""
        ref_epoch_hour = int(ref_time.timestamp()) // 3600
        start_hour = ref_epoch_hour - past_hours
        end_hour = ref_epoch_hour + forecast_hours

        result: Dict[Tuple[float, float], Dict[int, float]] = {}

        for lat, lon in locations:
            # Deterministic base rainfall cycle per location
            loc_seed = int((lat * 100 + lon * 50) % 100)
            hourly_map: Dict[int, float] = {}

            # Check if this coordinate falls inside the synthetic rain spike front
            in_spike_zone = False
            if self.spike_corridor:
                min_la, max_la, min_lo, max_lo = self.spike_corridor
                if min_la <= lat <= max_la and min_lo <= lon <= max_lo:
                    in_spike_zone = True

            for h in range(start_hour, end_hour + 1):
                offset = h - ref_epoch_hour
                # Diurnal pattern (monsoon rains often peak afternoon / evening)
                diurnal = math.sin(2 * math.pi * ((h % 24) - 14) / 24.0)
                base_rain = max(0.0, 5.0 + 4.0 * diurnal + 3.0 * math.sin(h / 6.0 + loc_seed))

                if in_spike_zone and (-4 <= offset <= 18):
                    # Storm front active between past 4h and next 18h
                    peak_factor = math.exp(-((offset - 2) ** 2) / 16.0)
                    rain_val = base_rain + self.spike_intensity * peak_factor
                else:
                    rain_val = base_rain

                hourly_map[h] = round(float(rain_val), 2)

            result[(lat, lon)] = hourly_map

        return result
