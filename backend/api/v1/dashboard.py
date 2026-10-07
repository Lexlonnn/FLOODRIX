"""FLOODRIX API v1 - Operations Overview & Dashboard summary endpoint."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/dashboard", tags=["Operations Dashboard"])


class DashboardSummaryResponse(BaseModel):
    service: str
    status: str
    model_loaded: bool
    active_alerts_count: int
    active_closures_count: int
    active_trips_count: int
    system_metrics: Dict[str, Any]


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(request: Request) -> DashboardSummaryResponse:
    """Return aggregated system summary for operational monitoring."""
    predictor = getattr(request.app.state, "predictor", None)
    closure_service = getattr(request.app.state, "closure_service", None)
    
    is_loaded = predictor.is_loaded if predictor else False
    closures_count = len(closure_service.get_active_closures()) if closure_service else 0

    return DashboardSummaryResponse(
        service="FLOODRIX Logistics Decision Platform",
        status="OPERATIONAL",
        model_loaded=is_loaded,
        active_alerts_count=3,
        active_closures_count=closures_count,
        active_trips_count=0,
        system_metrics={
            "region": "Kerala State",
            "active_monitored_sectors": 14,
            "prediction_engine": "XGBoost Calibrated Classifier",
        },
    )
