"""Active emergency flood alerts and weather disruption notifications."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter
from app.schemas import AlertItem, AlertsResponse

router = APIRouter(prefix="/alerts", tags=["Emergency Alerts"])

SAMPLE_ALERTS = [
    AlertItem(
        id="ALT001",
        type="FLOOD_RISK",
        severity="HIGH",
        title="Critical Flood Probability on NH 66",
        message="High flood probability detected 8 km ahead in Edappally sector. Reroute recommended.",
        latitude=9.985,
        longitude=76.289,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
    AlertItem(
        id="ALT002",
        type="ROAD_CLOSURE",
        severity="CRITICAL",
        title="Alappuzha-Changanassery Road Submerged",
        message="Road traffic suspended at Km 12 due to Pampa river overflow.",
        latitude=9.442,
        longitude=76.438,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
    AlertItem(
        id="ALT003",
        type="MONSOON_WARNING",
        severity="MEDIUM",
        title="IMD Red Alert Warning: Idukki & Wayanad",
        message="Extremely heavy rainfall predicted over the next 6 hours. Expect waterlogging.",
        latitude=10.02,
        longitude=76.95,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
]


@router.get("/active", response_model=AlertsResponse)
def get_active_alerts() -> AlertsResponse:
    """Return active flood, road-closure, and route-risk alerts."""
    return AlertsResponse(alerts=SAMPLE_ALERTS)
