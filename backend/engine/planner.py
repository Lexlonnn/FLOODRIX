"""PlanRoute orchestration engine for FLOODRIX (PLANNING mode)."""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional
import pandas as pd

from engine.config import (
    BAND_HIGH,
    BAND_LOW,
    CLOSURE_SNAP_M,
    DELAY_SCAN_MAX_MIN,
    DELAY_SCAN_STEP_MIN,
    ROUTE_OVERLAP_DEDUPE_THRESH,
    SEGMENT_LEN_M,
    VEHICLE_SPEED_FACTOR,
)
from engine.geometry import (
    interpolate_cumulative_times,
    resample_route,
    to_geojson_linestring,
)
from engine.models import (
    AdvisoryType,
    GeoJSONGeometry,
    PlanRouteRequest,
    PlanRouteResponse,
    RiskBand,
    RouteOption,
    Segment,
)
from engine.closures import closure_store
from engine.routing.base import RoutingProvider, deduplicate_routes
from engine.routing.osrm import OSRMRoutingProvider
from engine.weather.base import WeatherProvider
from engine.weather.open_meteo import OpenMeteoWeatherProvider
from engine.weather.time_aware import calculate_time_aware_rainfall
from engine.terrain import TerrainService, terrain_service as default_terrain_service
from engine.static_lookup import query_static_lookup
from engine.risk.scorer import score_segments
from engine.risk.aggregate import aggregate_route_risk
from engine.risk.cost import rank_and_explain_routes

logger = logging.getLogger("floodrix.planner")


def parse_iso_datetime(dt_str: Optional[str]) -> datetime:
    """Parse ISO datetime string, defaulting to current UTC time."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


class RoutePlanner:
    """Orchestrates candidate routing, feature assembly, risk inference, cost ranking,

    and departure scan advisories.
    """

    def __init__(
        self,
        routing_provider: Optional[RoutingProvider] = None,
        weather_provider: Optional[WeatherProvider] = None,
        terrain_service_instance: Optional[TerrainService] = None,
        predictor=None,
    ):
        self.routing = routing_provider or OSRMRoutingProvider()
        self.weather = weather_provider or OpenMeteoWeatherProvider(use_fallback_mock=True)
        self.terrain = terrain_service_instance or default_terrain_service
        self.predictor = predictor

    def plan(self, req: PlanRouteRequest) -> PlanRouteResponse:
        depart_dt = parse_iso_datetime(req.depart_time)
        deadline_dt = parse_iso_datetime(req.deadline) if req.deadline else None

        # 1. Fetch Candidate Routes from Routing Provider
        routes_raw = self.routing.get_routes(
            origin=req.origin,
            destination=req.destination,
            alternatives=3,
        )
        if not routes_raw:
            raise RuntimeError("No routes available from routing provider.")

        # Deduplicate routes (>90% overlap removed)
        routes_deduped = deduplicate_routes(routes_raw, overlap_threshold=ROUTE_OVERLAP_DEDUPE_THRESH)
        if not routes_deduped:
            routes_deduped = routes_raw[:1]

        # 2. Resample and segment routes
        routes_segments: List[List[Segment]] = []
        all_coords_for_terrain: List[tuple[float, float]] = []

        for r in routes_deduped:
            # Resample geometry to SEGMENT_LEN_M
            sampled = resample_route(r.polyline, segment_len_m=SEGMENT_LEN_M)
            cum_metrics = interpolate_cumulative_times(
                sampled,
                total_distance_m=r.distance_m,
                total_duration_s=r.duration_s,
                speed_factor=VEHICLE_SPEED_FACTOR,
            )

            route_segs: List[Segment] = []
            for i, ((lat, lon, length_m), (cum_dist, cum_time)) in enumerate(zip(sampled, cum_metrics)):
                seg_eta = depart_dt + timedelta(seconds=cum_time)
                route_segs.append(
                    Segment(
                        index=i,
                        lat=lat,
                        lon=lon,
                        length_m=length_m,
                        cum_dist_m=cum_dist,
                        cum_time_s=cum_time,
                        eta=seg_eta.isoformat(),
                    )
                )
                all_coords_for_terrain.append((lat, lon))
            routes_segments.append(route_segs)

        # 3. Terrain batch lookup
        elevations = self.terrain.get_elevations_batch(all_coords_for_terrain)
        elev_idx = 0
        for route_segs in routes_segments:
            for seg in route_segs:
                seg.elevation = elevations[elev_idx]
                elev_idx += 1

        # 4. Static Lookup & Closures
        for route_segs in routes_segments:
            for seg in route_segs:
                freq, zone, missing = query_static_lookup(seg.lat, seg.lon)
                seg.historical_flood_frequency = freq
                seg.flood_zone = zone
                seg.static_missing = missing

                # Check road closures
                is_closed, _ = closure_store.is_point_closed(seg.lat, seg.lon, snap_distance_m=CLOSURE_SNAP_M)
                if is_closed:
                    seg.closed = True

        # 5. Weather Series Multi-Point Fetch
        # Collect unique coordinates rounded to 0.1 deg
        unique_weather_cells: List[tuple[float, float]] = []
        seen_cells = set()
        for route_segs in routes_segments:
            for seg in route_segs:
                cell = (round(seg.lat, 1), round(seg.lon, 1))
                if cell not in seen_cells:
                    seen_cells.add(cell)
                    unique_weather_cells.append(cell)

        # Fetch weather series for unique weather cells
        weather_series_map = self.weather.get_hourly_precipitation(
            locations=unique_weather_cells,
            ref_time=depart_dt,
            past_hours=25,
            forecast_hours=48,
        )

        # Compute time-aware rainfall for departure at depart_dt
        self._populate_segment_rainfall(routes_segments, weather_series_map, depart_dt)

        # 6. Risk Scoring (single batch DataFrame across all segments of all routes)
        self._score_all_routes_segments(routes_segments)

        # 7. Route Aggregation & Metrics
        route_options: List[RouteOption] = []
        for r_raw, route_segs in zip(routes_deduped, routes_segments):
            metrics = aggregate_route_risk(route_segs)
            adj_duration_min = round((r_raw.duration_s * VEHICLE_SPEED_FACTOR) / 60.0, 1)
            eta_str = (depart_dt + timedelta(seconds=r_raw.duration_s * VEHICLE_SPEED_FACTOR)).isoformat()
            geojson_geom = GeoJSONGeometry(**to_geojson_linestring(r_raw.polyline))

            route_options.append(
                RouteOption(
                    route_id=r_raw.route_id,
                    label=r_raw.label,
                    distance_km=round(r_raw.distance_m / 1000.0, 2),
                    duration_min=adj_duration_min,
                    eta=eta_str,
                    effective_time=adj_duration_min,
                    metrics=metrics,
                    geometry=geojson_geom,
                    segments=route_segs,
                )
            )

        # 8. Cost & Ranking
        ranked_options = rank_and_explain_routes(
            route_options,
            cargo=req.cargo,
            deadline=deadline_dt,
        )

        best_route = ranked_options[0]

        # 9. Advisory & Departure Scan
        advisory = AdvisoryType.GO
        suggested_departure = None

        # Check if best route has risk >= BAND_LOW (0.3) or is hard-filtered
        if best_route.metrics.max_p >= BAND_LOW or best_route.is_hard_filtered:
            best_scan_offset, scan_improved_eff_time = self._scan_departures(
                routes_deduped,
                routes_segments,
                weather_series_map,
                depart_dt,
                deadline_dt,
                req.cargo,
                best_route.effective_time,
            )

            # If departure scan lowers effective_time by >= 30%
            if best_scan_offset and scan_improved_eff_time <= (0.70 * best_route.effective_time):
                advisory = AdvisoryType.DELAY
                suggested_departure = (depart_dt + timedelta(minutes=best_scan_offset)).isoformat()
            elif all(r.is_hard_filtered for r in ranked_options):
                advisory = AdvisoryType.DO_NOT_GO
            elif best_route.metrics.max_p < BAND_LOW:
                advisory = AdvisoryType.GO
            else:
                advisory = AdvisoryType.GO_WITH_CAUTION
        else:
            advisory = AdvisoryType.GO

        # Check degradation
        degraded = getattr(self.weather, "is_degraded", False)

        data_sources = [
            f"routing:{getattr(self.routing, 'name', 'provider')}",
            f"weather:{getattr(self.weather, 'name', 'provider')}",
            "terrain:srtm_elevation_cache",
            "static:kerala_hazard_grid",
        ]
        if self.predictor:
            data_sources.append("model:calibrated_gbdt")
        else:
            data_sources.append("model:rules_fallback")
            degraded = True

        return PlanRouteResponse(
            advisory=advisory,
            recommended_route_id=best_route.route_id,
            routes=ranked_options,
            suggested_departure=suggested_departure,
            generated_at=datetime.now(timezone.utc).isoformat(),
            data_sources=data_sources,
            degraded=degraded,
        )

    def _populate_segment_rainfall(
        self,
        routes_segments: List[List[Segment]],
        weather_series_map,
        depart_dt: datetime,
    ):
        for route_segs in routes_segments:
            for seg in route_segs:
                seg_eta = depart_dt + timedelta(seconds=seg.cum_time_s)
                seg.eta = seg_eta.isoformat()
                cell = (round(seg.lat, 1), round(seg.lon, 1))
                series = weather_series_map.get(cell)
                if series:
                    r1, r6, r24 = calculate_time_aware_rainfall(series, seg_eta)
                    seg.rainfall_1h = r1
                    seg.rainfall_6h = r6
                    seg.rainfall_24h = r24
                else:
                    seg.rainfall_1h = 0.0
                    seg.rainfall_6h = 0.0
                    seg.rainfall_24h = 0.0

    def _score_all_routes_segments(self, routes_segments: List[List[Segment]]):
        rows = []
        for route_segs in routes_segments:
            for s in route_segs:
                rows.append({
                    "latitude": s.lat,
                    "longitude": s.lon,
                    "rainfall_1h": s.rainfall_1h or 0.0,
                    "rainfall_6h": s.rainfall_6h or 0.0,
                    "rainfall_24h": s.rainfall_24h or 0.0,
                    "elevation": s.elevation or 10.0,
                    "historical_flood_frequency": s.historical_flood_frequency or 0.0,
                    "flood_zone": s.flood_zone or 0.0,
                })

        df = pd.DataFrame(rows)
        probs, bands = score_segments(df, predictor=self.predictor, mode="full")

        idx = 0
        for route_segs in routes_segments:
            for s in route_segs:
                if s.closed:
                    s.p = 1.0
                    s.band = RiskBand.HIGH
                else:
                    s.p = round(float(probs[idx]), 4)
                    s.band = bands[idx]
                idx += 1

    def _scan_departures(
        self,
        routes_deduped,
        routes_segments: List[List[Segment]],
        weather_series_map,
        base_depart_dt: datetime,
        deadline_dt: Optional[datetime],
        cargo: str,
        current_best_effective_time: float,
    ) -> tuple[Optional[int], float]:
        """Scan departure delays every 30 min up to 360 min reusing weather forecast."""
        best_offset: Optional[int] = None
        min_effective_time = current_best_effective_time

        offsets = list(range(DELAY_SCAN_STEP_MIN, DELAY_SCAN_MAX_MIN + 1, DELAY_SCAN_STEP_MIN))

        for offset_min in offsets:
            scan_depart_dt = base_depart_dt + timedelta(minutes=offset_min)
            # Recompute rainfall for each segment
            self._populate_segment_rainfall(routes_segments, weather_series_map, scan_depart_dt)
            # Re-score
            self._score_all_routes_segments(routes_segments)

            # Evaluate options
            scan_options: List[RouteOption] = []
            for r_raw, route_segs in zip(routes_deduped, routes_segments):
                metrics = aggregate_route_risk(route_segs)
                adj_duration_min = round((r_raw.duration_s * VEHICLE_SPEED_FACTOR) / 60.0, 1)
                scan_options.append(
                    RouteOption(
                        route_id=r_raw.route_id,
                        label=r_raw.label,
                        distance_km=round(r_raw.distance_m / 1000.0, 2),
                        duration_min=adj_duration_min,
                        eta=(scan_depart_dt + timedelta(seconds=r_raw.duration_s * VEHICLE_SPEED_FACTOR)).isoformat(),
                        effective_time=adj_duration_min,
                        metrics=metrics,
                        geometry=GeoJSONGeometry(**to_geojson_linestring(r_raw.polyline)),
                        segments=route_segs,
                    )
                )

            ranked = rank_and_explain_routes(scan_options, cargo=cargo, deadline=deadline_dt)
            best_scan = ranked[0]

            if not best_scan.is_hard_filtered and best_scan.effective_time < min_effective_time:
                min_effective_time = best_scan.effective_time
                best_offset = offset_min

        # Restore original departure times & scores
        self._populate_segment_rainfall(routes_segments, weather_series_map, base_depart_dt)
        self._score_all_routes_segments(routes_segments)

        return best_offset, min_effective_time
