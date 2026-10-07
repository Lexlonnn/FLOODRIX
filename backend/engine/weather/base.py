"""Abstract WeatherProvider interface for hourly precipitation series."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple
from pydantic import BaseModel


class WeatherSeries(BaseModel):
    latitude: float
    longitude: float
    # Maps integer epoch hour (timestamp // 3600) -> precipitation mm
    hourly_precipitation: Dict[int, float]
    updated_at: float  # Unix timestamp


class WeatherProvider(ABC):
    """Abstract interface for weather providers supplying past and forecast hourly precipitation."""

    @abstractmethod
    def get_hourly_precipitation(
        self,
        locations: List[Tuple[float, float]],
        ref_time: datetime,
        past_hours: int = 24,
        forecast_hours: int = 48,
    ) -> Dict[Tuple[float, float], Dict[int, float]]:
        """Fetch hourly precipitation keyed by (lat, lon) and epoch hour (timestamp // 3600)."""
        pass
