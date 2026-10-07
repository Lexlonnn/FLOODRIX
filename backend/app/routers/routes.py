"""Logistics route planning router matching FLOODRIX Mobile API Specification."""

from fastapi import APIRouter, HTTPException, Request, status
from app.schemas import PlanRouteRequest, PlanRouteResponse, EvaluateRoutesRequest
from app.services.routing_service import RoutingService

router = APIRouter(prefix="/routes", tags=["Route Planning"])

@router.post("/evaluate", response_model=PlanRouteResponse)
def evaluate_routes(payload: EvaluateRoutesRequest, request: Request) -> PlanRouteResponse:
    """Evaluate externally provided routes and select safest practical route considering predicted flood risk."""
    predictor = getattr(request.app.state, "predictor", None)
    closure_service = getattr(request.app.state, "closure_service", None)

    if not predictor or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor model is not loaded.",
        )

    routing_svc = RoutingService(predictor, closure_service)
    return routing_svc.evaluate_routes(payload)

@router.post("/plan", response_model=PlanRouteResponse)
def plan_route(payload: PlanRouteRequest, request: Request) -> PlanRouteResponse:
    """Plan shipment and select safest practical route considering predicted flood risk."""
    predictor = getattr(request.app.state, "predictor", None)
    closure_service = getattr(request.app.state, "closure_service", None)

    if not predictor or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor model is not loaded.",
        )

    routing_svc = RoutingService(predictor, closure_service)
    return routing_svc.plan_shipment(payload)
