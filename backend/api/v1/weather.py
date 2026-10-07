"""FLOODRIX API v1 - Weather integration endpoints."""

from fastapi import APIRouter, Query
from app.schemas import WeatherCurrentResponse, WeatherForecastResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather Integration"])


@router.get("/current", response_model=WeatherCurrentResponse)
def get_current_weather(
    latitude: float = Query(..., ge=8.0, le=13.0, description="Latitude in Kerala"),
    longitude: float = Query(..., ge=74.5, le=77.5, description="Longitude in Kerala"),
) -> WeatherCurrentResponse:
    """Return current rainfall (1h, 6h, 24h) and weather observations needed by the prediction layer."""
    return WeatherService.get_current_weather(latitude, longitude)


@router.get("/forecast", response_model=WeatherForecastResponse)
def get_weather_forecast(
    latitude: float = Query(..., ge=8.0, le=13.0, description="Latitude in Kerala"),
    longitude: float = Query(..., ge=74.5, le=77.5, description="Longitude in Kerala"),
) -> WeatherForecastResponse:
    """Return short-term hourly rainfall forecast used for route-time prediction."""
    return WeatherService.get_forecast(latitude, longitude)
