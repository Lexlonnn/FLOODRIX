"""FLOODRIX app.api.v1 package."""
from api.v1 import (
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
    api_v1_router,
)

__all__ = [
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
