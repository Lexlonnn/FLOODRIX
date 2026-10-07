"""Pydantic v2 schemas for Flood-Aware Logistics Planner."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from ml.config import (
    KERALA_LAT_MAX,
    KERALA_LAT_MIN,
    KERALA_LON_MAX,
    KERALA_LON_MIN,
)


class FloodZoneEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    MED = "med"
    HIGH = "high"
    EXTREME = "extreme"
    VERY_HIGH = "very_high"


class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionActionEnum(str, Enum):
    GO = "GO"
    REROUTE = "REROUTE"
    WAIT = "WAIT"


class LatLng(BaseModel):
    latitude: float = Field(..., ge=KERALA_LAT_MIN - 0.1, le=KERALA_LAT_MAX + 0.1, description="Latitude in Kerala")
    longitude: float = Field(..., ge=KERALA_LON_MIN - 0.1, le=KERALA_LON_MAX + 0.1, description="Longitude in Kerala")


class SegmentInput(BaseModel):
    segment_id: Optional[str] = Field(default="seg_001", description="Identifier for road segment")
    latitude: float = Field(..., ge=KERALA_LAT_MIN, le=KERALA_LAT_MAX, description="Midpoint latitude")
    longitude: float = Field(..., ge=KERALA_LON_MIN, le=KERALA_LON_MAX, description="Midpoint longitude")
    rainfall_1h: float = Field(..., ge=0.0, le=500.0, description="1-hour cumulative rainfall (mm)")
    rainfall_6h: float = Field(..., ge=0.0, le=1000.0, description="6-hour cumulative rainfall (mm)")
    rainfall_24h: float = Field(..., ge=0.0, le=2000.0, description="24-hour cumulative rainfall (mm)")
    elevation: float = Field(..., ge=-5.0, le=3000.0, description="Elevation above sea level (m)")
    historical_flood_frequency: float = Field(..., ge=0.0, le=100.0, description="Past flood occurrence count/rate")
    flood_zone: str = Field(default="medium", description="Designated flood risk zone (low, medium, high)")

    @model_validator(mode="after")
    def validate_rainfall_ordering(self) -> "SegmentInput":
        tol = 1e-3
        if self.rainfall_1h > (self.rainfall_6h + tol):
            raise ValueError(
                f"Rainfall ordering violated: rainfall_1h ({self.rainfall_1h}) > rainfall_6h ({self.rainfall_6h})"
            )
        if self.rainfall_6h > (self.rainfall_24h + tol):
            raise ValueError(
                f"Rainfall ordering violated: rainfall_6h ({self.rainfall_6h}) > rainfall_24h ({self.rainfall_24h})"
            )
        return self


class SegmentPrediction(BaseModel):
    segment_id: str
    latitude: float
    longitude: float
    flood_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevelEnum


class BatchSegmentsRequest(BaseModel):
    segments: List[SegmentInput] = Field(..., min_length=1, max_length=1000, description="Batch of road segments")


class BatchSegmentsResponse(BaseModel):
    segments: List[SegmentPrediction]
    total_segments: int
    latency_ms: float


class RoutePredictRequest(BaseModel):
    route_id: str = Field(default="route_001", description="Unique route identifier")
    segments: List[SegmentInput] = Field(..., min_length=1, max_length=1000, description="Ordered road segments along route")


class WorstSegment(BaseModel):
    segment_id: str
    latitude: float
    longitude: float
    flood_probability: float
    risk_level: RiskLevelEnum


class RoutePredictResponse(BaseModel):
    route_id: str
    segments: List[SegmentPrediction]
    route_risk: float = Field(..., ge=0.0, le=1.0, description="Aggregated route flood risk: 1 - prod(1 - p_i)")
    max_segment_risk: float = Field(..., ge=0.0, le=1.0, description="Highest individual segment probability")
    high_risk_segment_count: int
    worst_segments: List[WorstSegment]
    recommended_action: DecisionActionEnum
    risk_independence_note: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    model_name: str
    version: str
    feature_columns: List[str]
    risk_bands: Dict[str, str]
    test_metrics: Dict[str, Any]
    frameworks: Dict[str, str]
    calibration_note: str


# =========================================================================
# Additional schemas supporting the FLOODRIX Mobile API Specification (v1)
# =========================================================================

class PlanRouteRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    cargo_type: Optional[str] = Field(default="GENERAL", description="GENERAL, MEDICINE, PERISHABLE, HAZMAT")
    vehicle_type: Optional[str] = Field(default="TRUCK")
    departure_time: Optional[str] = None
    max_acceptable_risk: Optional[float] = Field(default=0.40)


class RouteOption(BaseModel):
    route_id: str
    label: str
    distance_km: float
    eta_minutes: float
    route_risk: float
    max_segment_risk: float
    decision: DecisionActionEnum
    is_recommended: bool
    high_risk_segments: int
    warning_message: Optional[str] = None
    waypoints: List[LatLng] = []


class PlanRouteResponse(BaseModel):
    recommended_route: RouteOption
    alternative_routes: List[RouteOption]
    plan_timestamp: str


class WeatherCurrentResponse(BaseModel):
    latitude: float
    longitude: float
    rainfall_1h: float
    rainfall_6h: float
    rainfall_24h: float
    temperature_c: float
    condition: str


class HourlyForecastItem(BaseModel):
    time: str
    rainfall: float
    risk_indicator: str


class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    forecast: List[HourlyForecastItem]


class MapRiskSegment(BaseModel):
    id: str
    latitude: float
    longitude: float
    flood_probability: float
    risk_level: RiskLevelEnum


class MapRiskResponse(BaseModel):
    segments: List[MapRiskSegment]


class RoadClosure(BaseModel):
    id: str
    latitude: float
    longitude: float
    road_name: str
    district: str
    reason: str
    is_active: bool


class ClosuresResponse(BaseModel):
    closures: List[RoadClosure]


class CreateTripRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    route_id: str
    cargo_type: Optional[str] = "GENERAL"
    driver_name: Optional[str] = "Driver"


class TripResponse(BaseModel):
    trip_id: str
    status: str
    route_id: str
    created_at: str


class LiveLocationRequest(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = 0.0
    heading: Optional[float] = 0.0


class LiveLocationResponse(BaseModel):
    trip_id: str
    status: str
    current_segment_risk: float
    current_risk_level: RiskLevelEnum
    alert_triggered: bool
    recommended_action: DecisionActionEnum


class AlertItem(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    message: str
    latitude: float
    longitude: float
    created_at: str


class AlertsResponse(BaseModel):
    alerts: List[AlertItem]


class SimulationRunRequest(BaseModel):
    route_id: str = "route_001"
    rainfall_multiplier: float = Field(default=2.0, ge=0.1, le=10.0)
    inject_closure: bool = False
    closure_segment_id: Optional[str] = None


class SimulationRunResponse(BaseModel):
    simulation_id: str
    original_risk: float
    simulated_risk: float
    original_decision: DecisionActionEnum
    simulated_decision: DecisionActionEnum
    impact_summary: str
