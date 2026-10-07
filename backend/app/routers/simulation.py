"""What-If Scenario Simulation engine using live model inference pipeline."""

import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Request, status
import numpy as np
from app.schemas import (
    DecisionActionEnum,
    LatLng,
    SegmentInput,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.services.routing_service import RoutingService
from ml.config import RISK_HIGH_THRESHOLD, RISK_LOW_THRESHOLD

router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])


@router.post("/run", response_model=SimulationRunResponse)
def run_simulation(payload: SimulationRunRequest, request: Request) -> SimulationRunResponse:
    """Run dynamic what-if simulation modifying weather multiplier and injected closures."""
    predictor = getattr(request.app.state, "predictor", None)
    closure_service = getattr(request.app.state, "closure_service", None)

    if not predictor or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded for simulation.",
        )

    # Base test route segments across Ernakulam - Thrissur corridor
    base_lats = [9.98, 10.05, 10.15, 10.28, 10.40, 10.52]
    base_lons = [76.28, 76.32, 76.30, 76.25, 76.22, 76.21]

    original_segments: List[SegmentInput] = []
    simulated_segments: List[SegmentInput] = []

    for i, (lat, lon) in enumerate(zip(base_lats, base_lons)):
        seg_id = f"SIM_SEG_{i+1:02d}"
        r1 = 15.0
        r6 = 40.0
        r24 = 90.0

        # Baseline
        original_segments.append(
            SegmentInput(
                segment_id=seg_id,
                latitude=lat,
                longitude=lon,
                rainfall_1h=r1,
                rainfall_6h=r6,
                rainfall_24h=r24,
                elevation=6.0 if i < 3 else 14.0,
                historical_flood_frequency=3 if i < 3 else 1,
                flood_zone="high" if i < 3 else "medium",
            )
        )

        # Multiplier applied to simulated scenario
        sim_r24 = min(r24 * payload.rainfall_multiplier, 450.0)
        sim_r6 = min(r6 * payload.rainfall_multiplier, sim_r24)
        sim_r1 = min(r1 * payload.rainfall_multiplier, sim_r6)

        simulated_segments.append(
            SegmentInput(
                segment_id=seg_id,
                latitude=lat,
                longitude=lon,
                rainfall_1h=round(sim_r1, 2),
                rainfall_6h=round(sim_r6, 2),
                rainfall_24h=round(sim_r24, 2),
                elevation=6.0 if i < 3 else 14.0,
                historical_flood_frequency=3 if i < 3 else 1,
                flood_zone="high" if i < 3 else "medium",
            )
        )

    # Predict baseline
    orig_res = predictor.predict_route(payload.route_id, original_segments)
    sim_res = predictor.predict_route(payload.route_id, simulated_segments)

    sim_decision = sim_res.recommended_action
    if payload.inject_closure:
        sim_decision = DecisionActionEnum.REROUTE

    summary = (
        f"Simulated {payload.rainfall_multiplier}x rainfall surge. "
        f"Route flood risk escalated from {orig_res.route_risk:.1%} to {sim_res.route_risk:.1%}. "
        f"Operational decision changed from {orig_res.recommended_action.value} to {sim_decision.value}."
    )

    return SimulationRunResponse(
        simulation_id=f"SIM_{uuid.uuid4().hex[:6].upper()}",
        original_risk=orig_res.route_risk,
        simulated_risk=sim_res.route_risk,
        original_decision=orig_res.recommended_action,
        simulated_decision=sim_decision,
        impact_summary=summary,
    )
