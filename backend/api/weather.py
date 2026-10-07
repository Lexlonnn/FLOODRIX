"""Weather endpoints re-export."""
from api.v1.weather import get_current_weather, get_weather_forecast, router

__all__ = ["router", "get_current_weather", "get_weather_forecast"]
