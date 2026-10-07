"""Logistics route planning, multi-candidate risk comparison, and decision engine."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import numpy as np

from app.schemas import (
    DecisionActionEnum,
    LatLng,
    PlanRouteRequest,
    PlanRouteResponse,
    EvaluateRoutesRequest,
    RouteCandidate,
    RiskLevelEnum,
    RouteOption,
    SegmentInput,
)
from app.services.closure_service import ClosureService
from app.services.weather_service import WeatherService
from ml.config import RISK_HIGH_THRESHOLD, RISK_LOW_THRESHOLD


class RoutingService:
    """Combines route topology, ML flood predictions, active road closures, and cargo constraints."""

    def __init__(self, predictor, closure_service: ClosureService):
        self.predictor = predictor
        self.closure_service = closure_service

    def _generate_candidate_waypoints(
        self, origin: LatLng, destination: LatLng, num_segments: int = 8
    ) -> List[List[LatLng]]:
        """Synthesize candidate route geometries between origin and destination."""
        t_vals = np.linspace(0.0, 1.0, num_segments)
        
        # Candidate 1: Direct Highway (NH Corridors)
        direct_wps = [
            LatLng(
                latitude=round(origin.latitude + t * (destination.latitude - origin.latitude), 5),
                longitude=round(origin.longitude + t * (destination.longitude - origin.longitude), 5),
            )
            for t in t_vals
        ]

        # Candidate 2: Midland Alternate (slight eastern arc)
        midland_wps = [
            LatLng(
                latitude=round(origin.latitude + t * (destination.latitude - origin.latitude), 5),
                longitude=round(origin.longitude + t * (destination.longitude - origin.longitude) + 0.04 * np.sin(np.pi * t), 5),
            )
            for t in t_vals
        ]

        # Candidate 3: Coastal / Western Alternate (slight western arc)
        coastal_wps = [
            LatLng(
                latitude=round(origin.latitude + t * (destination.latitude - origin.latitude), 5),
                longitude=round(origin.longitude + t * (destination.longitude - origin.longitude) - 0.04 * np.sin(np.pi * t), 5),
            )
            for t in t_vals
        ]

        return [direct_wps, midland_wps, coastal_wps]

    def _assemble_route_segments(self, waypoints: List[LatLng], route_id: str) -> List[SegmentInput]:
        """Fill environmental, weather, and topographical attributes for road segments."""
        segments: List[SegmentInput] = []
        for i, wp in enumerate(waypoints):
            weather = WeatherService.get_current_weather(wp.latitude, wp.longitude)
            # Estimate elevation from longitude (closer to 77.0 is Western Ghats, closer to 76.2 is coast)
            dist_to_coast = max(wp.longitude - 75.8, 0.0)
            elev = max(round(dist_to_coast * 120.0 + np.random.uniform(2.0, 15.0), 1), 1.0)
            hist_freq = 4 if elev < 8.0 else (2 if elev < 25.0 else 0)
            flood_zone = "high" if elev < 6.0 else ("medium" if elev < 20.0 else "low")

            segments.append(
                SegmentInput(
                    segment_id=f"{route_id}_seg_{i+1:02d}",
                    latitude=wp.latitude,
                    longitude=wp.longitude,
                    rainfall_1h=weather.rainfall_1h,
                    rainfall_6h=weather.rainfall_6h,
                    rainfall_24h=weather.rainfall_24h,
                    elevation=elev,
                    historical_flood_frequency=hist_freq,
                    flood_zone=flood_zone,
                )
            )
        return segments

    def plan_shipment(self, request: PlanRouteRequest) -> PlanRouteResponse:
        """Evaluate candidate routes against flood predictions and logistics constraints."""
        candidate_geometries = self._generate_candidate_waypoints(request.origin, request.destination)
        route_labels = [
            ("R1_DIRECT", "Primary NH Highway", 1.0, 1.0),
            ("R2_MIDLAND", "Midland Bypass (Higher Elevation)", 1.12, 1.15),
            ("R3_COASTAL", "Coastal Alternate Corridor", 1.08, 1.10),
        ]

        # Calculate approximate base distance
        d_lat = (request.destination.latitude - request.origin.latitude) * 111.0
        d_lon = (request.destination.longitude - request.origin.longitude) * 108.0
        base_dist_km = max(round(float(np.sqrt(d_lat**2 + d_lon**2)), 1), 15.0)

        # Cargo vulnerability penalties
        cargo_penalty = {
            "MEDICINE": 0.12,
            "PERISHABLE": 0.08,
            "HAZMAT": 0.15,
            "GENERAL": 0.0,
        }.get((request.cargo_type or "").upper(), 0.0)

        evaluated_options: List[RouteOption] = []

        for (r_id, r_label, dist_factor, time_factor), wps in zip(route_labels, candidate_geometries):
            segments = self._assemble_route_segments(wps, r_id)
            preds, _ = self.predictor.predict_segments(segments)

            probs = [p.flood_probability for p in preds]
            max_prob = max(probs) if probs else 0.0
            clipped = np.clip(probs, 0.0, 0.9999)
            raw_route_risk = 1.0 - float(np.exp(np.sum(np.log(1.0 - clipped))))

            # Effective logistics risk
            effective_risk = min(raw_route_risk + cargo_penalty, 1.0)
            high_risk_count = sum(1 for p in probs if p > RISK_HIGH_THRESHOLD)

            # Check for closures
            has_closure = False
            closure_warning = None
            for seg in segments:
                closure = self.closure_service.is_near_closure(seg.latitude, seg.longitude)
                if closure:
                    has_closure = True
                    closure_warning = f"Active Road Closure on segment: {closure.road_name} ({closure.reason})"
                    break

            dist_km = round(base_dist_km * dist_factor, 1)
            eta_mins = round(dist_km * 1.8 * time_factor + (30 if max_prob > 0.4 else 0), 1)

            # Route decision policy
            if has_closure or max_prob > RISK_HIGH_THRESHOLD or high_risk_count >= 2:
                decision = DecisionActionEnum.REROUTE
            elif effective_risk > (request.max_acceptable_risk or 0.40):
                decision = DecisionActionEnum.WAIT
            else:
                decision = DecisionActionEnum.GO

            evaluated_options.append(
                RouteOption(
                    route_id=r_id,
                    label=r_label,
                    distance_km=dist_km,
                    eta_minutes=eta_mins,
                    route_risk=round(effective_risk, 4),
                    max_segment_risk=round(max_prob, 4),
                    decision=decision,
                    is_recommended=False,
                    high_risk_segments=high_risk_count,
                    warning_message=closure_warning,
                    waypoints=wps,
                )
            )

        # Sort routes: viable GO first, then lowest risk, then shortest ETA
        sorted_routes = sorted(
            evaluated_options,
            key=lambda r: (
                0 if r.decision == DecisionActionEnum.GO else (1 if r.decision == DecisionActionEnum.WAIT else 2),
                r.route_risk,
                r.eta_minutes,
            )
        )

        recommended = sorted_routes[0]
        # Mark as recommended
        recommended.is_recommended = True
        alternatives = sorted_routes[1:]

        return PlanRouteResponse(
            recommended_route=recommended,
            alternative_routes=alternatives,
            plan_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_routes(self, request: EvaluateRoutesRequest) -> PlanRouteResponse:
        """Evaluate explicitly provided route geometries."""
        import logging
        logger = logging.getLogger("floodrix.backend.routing")
        logger.info(f"🚀 Received {len(request.routes)} routes from Frontend for evaluation.")

        cargo_penalty = {
            "MEDICINE": 0.12,
            "PERISHABLE": 0.08,
            "HAZMAT": 0.15,
            "GENERAL": 0.0,
        }.get((request.cargo_type or "").upper(), 0.0)

        evaluated_options: List[RouteOption] = []

        for idx, candidate in enumerate(request.routes):
            # Sample max 15 waypoints to avoid overloading model
            wps = candidate.waypoints
            if len(wps) > 15:
                step = len(wps) // 15
                wps = wps[::step][:15]

            segments = self._assemble_route_segments(wps, candidate.route_id)
            preds, _ = self.predictor.predict_segments(segments)

            probs = [p.flood_probability for p in preds]
            max_prob = max(probs) if probs else 0.0
            clipped = np.clip(probs, 0.0, 0.9999)
            raw_route_risk = 1.0 - float(np.exp(np.sum(np.log(1.0 - clipped))))

            effective_risk = min(raw_route_risk + cargo_penalty, 1.0)
            high_risk_count = sum(1 for p in probs if p > RISK_HIGH_THRESHOLD)

            has_closure = False
            closure_warning = None
            for seg in segments:
                closure = self.closure_service.is_near_closure(seg.latitude, seg.longitude)
                if closure:
                    has_closure = True
                    closure_warning = f"Active Road Closure on segment: {closure.road_name} ({closure.reason})"
                    break

            if has_closure or max_prob > RISK_HIGH_THRESHOLD or high_risk_count >= 2:
                decision = DecisionActionEnum.REROUTE
            elif effective_risk > (request.max_acceptable_risk or 0.40):
                decision = DecisionActionEnum.WAIT
            else:
                decision = DecisionActionEnum.GO

            evaluated_options.append(
                RouteOption(
                    route_id=candidate.route_id,
                    label=f"Route Option {idx + 1}",
                    distance_km=candidate.distance_km,
                    eta_minutes=candidate.eta_minutes,
                    route_risk=round(effective_risk, 4),
                    max_segment_risk=round(max_prob, 4),
                    decision=decision,
                    is_recommended=False,
                    high_risk_segments=high_risk_count,
                    warning_message=closure_warning,
                    waypoints=candidate.waypoints,
                )
            )
            logger.info(f"📊 Evaluated Route {candidate.route_id}: Risk={effective_risk:.4f}, Decision={decision.name}")

        if not evaluated_options:
            raise ValueError("No routes were evaluated")

        sorted_routes = sorted(
            evaluated_options,
            key=lambda r: (
                0 if r.decision == DecisionActionEnum.GO else (1 if r.decision == DecisionActionEnum.WAIT else 2),
                r.route_risk,
                r.eta_minutes,
            )
        )

        recommended = sorted_routes[0]
        recommended.is_recommended = True
        alternatives = sorted_routes[1:]

        return PlanRouteResponse(
            recommended_route=recommended,
            alternative_routes=alternatives,
            plan_timestamp=datetime.now(timezone.utc).isoformat(),
        )
