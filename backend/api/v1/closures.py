"""FLOODRIX API v1 - Road closures and disruptions endpoint."""

from fastapi import APIRouter, Request
from app.schemas import ClosuresResponse
from app.services.closure_service import ClosureService

router = APIRouter(prefix="/closures", tags=["Road Closures"])


@router.get("", response_model=ClosuresResponse)
def get_active_closures(request: Request) -> ClosuresResponse:
    """Return currently known active road closures and disruptions."""
    closure_service: ClosureService = getattr(request.app.state, "closure_service", ClosureService())
    return ClosuresResponse(closures=closure_service.get_active_closures())
