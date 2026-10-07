"""FLOODRIX API v1 package assembly."""

from fastapi import APIRouter

from api.v1.alerts import router as alerts_router
from api.v1.closures import router as closures_router
from api.v1.dashboard import router as dashboard_router
from api.v1.health import router as health_router
from api.v1.map_risk import router as map_risk_router
from api.v1.prediction import router as prediction_router
from api.v1.routes import router as routes_router
from api.v1.simulation import router as simulation_router
from api.v1.trips import router as trips_router
from api.v1.weather import router as weather_router

# Aggregated v1 router
api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(prediction_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(map_risk_router)
api_v1_router.include_router(closures_router)
api_v1_router.include_router(trips_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(dashboard_router)

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
