"""FLOODRIX API v1 - Active trip management and live GPS location tracking."""

from datetime import datetime, timezone
import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas import (
    CreateTripRequest,
    DecisionActionEnum,
    LiveLocationRequest,
    LiveLocationResponse,
    RiskLevelEnum,
    SegmentInput,
    TripResponse,
)
from app.services.weather_service import WeatherService
from ml.config import RISK_HIGH_THRESHOLD, RISK_LOW_THRESHOLD

router = APIRouter(prefix="/trips", tags=["Live Trips"])

# In-memory active trips store
TRIPS_DB: Dict[str, Dict] = {}


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(payload: CreateTripRequest) -> TripResponse:
    """Create a new trip after the operator selects a route."""
    trip_id = f"TRP_{uuid.uuid4().hex[:6].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()
    TRIPS_DB[trip_id] = {
        "trip_id": trip_id,
        "route_id": payload.route_id,
        "origin": payload.origin.model_dump(),
        "destination": payload.destination.model_dump(),
        "cargo_type": payload.cargo_type,
        "status": "PLANNED",
        "created_at": now_str,
    }

    return TripResponse(
        trip_id=trip_id,
        status="PLANNED",
        route_id=payload.route_id,
        created_at=now_str,
    )


@router.post("/{trip_id}/location", response_model=LiveLocationResponse)
def update_trip_location(
    trip_id: str,
    payload: LiveLocationRequest,
    request: Request,
) -> LiveLocationResponse:
    """Send periodic GPS updates from Flutter during an active trip."""
    if trip_id not in TRIPS_DB:
        TRIPS_DB[trip_id] = {"trip_id": trip_id, "status": "IN_PROGRESS"}

    predictor = getattr(request.app.state, "predictor", None)
    weather = WeatherService.get_current_weather(payload.latitude, payload.longitude)

    seg = SegmentInput(
        segment_id=f"{trip_id}_curr",
        latitude=payload.latitude,
        longitude=payload.longitude,
        rainfall_1h=weather.rainfall_1h,
        rainfall_6h=weather.rainfall_6h,
        rainfall_24h=weather.rainfall_24h,
        elevation=12.0,
        historical_flood_frequency=2,
        flood_zone="medium",
    )

    if predictor and predictor.is_loaded:
        preds, _ = predictor.predict_segments([seg])
        prob = preds[0].flood_probability
        risk_level = preds[0].risk_level
    else:
        prob = 0.2
        risk_level = RiskLevelEnum.LOW

    alert_triggered = prob > RISK_HIGH_THRESHOLD
    if prob > RISK_HIGH_THRESHOLD:
        action = DecisionActionEnum.REROUTE
    elif prob > RISK_LOW_THRESHOLD:
        action = DecisionActionEnum.WAIT
    else:
        action = DecisionActionEnum.GO

    return LiveLocationResponse(
        trip_id=trip_id,
        status="IN_PROGRESS",
        current_segment_risk=round(prob, 4),
        current_risk_level=risk_level,
        alert_triggered=alert_triggered,
        recommended_action=action,
    )
