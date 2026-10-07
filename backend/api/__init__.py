"""FLOODRIX Backend API package."""

from fastapi import APIRouter
from api.v1 import (
    api_v1_router,
    alerts_router,
    closures_router,
    dashboard_router,
    health_router,
    map_risk_router,
    prediction_router,
    routes_router,
    simulation_router,
    trips_router,
    weather_router,
)

# Root API router mounting /api/v1 prefix
api_router = APIRouter()
api_router.include_router(api_v1_router, prefix="/api/v1")

__all__ = [
    "api_router",
    "api_v1_router",
    "alerts_router",
    "closures_router",
    "dashboard_router",
    "health_router",
    "map_risk_router",
    "prediction_router",
    "routes_router",
    "simulation_router",
    "trips_router",
    "weather_router",
]
