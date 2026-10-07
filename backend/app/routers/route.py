"""Route planning router supporting POST /route/plan and POST /routes/plan."""

from fastapi import APIRouter, HTTPException, Request, status
from engine.models import PlanRouteRequest, PlanRouteResponse
from engine.planner import RoutePlanner

router = APIRouter(tags=["Route Planning"])


@router.post("/route/plan", response_model=PlanRouteResponse)
@router.post("/routes/plan", response_model=PlanRouteResponse)
def plan_route(payload: PlanRouteRequest, request: Request) -> PlanRouteResponse:
    """Plan shipment and select safest practical route considering predicted flood risk."""
    predictor = getattr(request.app.state, "predictor", None)
    planner = RoutePlanner(predictor=predictor)

    try:
        return planner.plan(payload)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route planning failed: {str(e)}",
        )
