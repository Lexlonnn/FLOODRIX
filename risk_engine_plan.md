# Risk Engine & Route Recommender: Implementation Plan

Builds on `plan.md` (ML flood model, FastAPI). Language: Python 3.11. All code lives inside `backend/`.

## 1. Goal

User picks origin + destination. Engine:

1. Gets candidate routes.
2. Scores flood risk per road segment.
3. Ranks routes by travel time + risk (cargo and deadline aware).
4. Recommends best route, or advises delay.
5. During the trip, re-scores the road ahead and re-routes only when worth it.

## 2. Two Modes (core requirement)

| | PLANNING (before trip) | LIVE (during trip) |
|---|---|---|
| Rain input | Forecast at the time vehicle will reach each segment | Current rain + short forecast (next 1–3 h) |
| Historic data | YES: `historical_flood_frequency`, `flood_zone` | NO. Weather + terrain only |
| Model | `model.joblib` (full, from plan.md) | `model_live.joblib` (weather-only, see 3) |
| Scope | Whole route, all alternatives | Remaining route ahead + alternatives from current position |
| Trigger | User request | GPS update every 60–120 s |
| Output | Ranked routes, ETA, risk, GO / CAUTION / DELAY / DO_NOT_GO | Alerts, reroute offer, updated ETA |

Elevation is static terrain, not flood history, so live mode still uses it.

## 3. Live Model (weather-only)

Needed because the full model expects history features.

- Train second XGBoost + calibration with same pipeline, `--feature-set live`.
- Features: latitude, longitude (optional, test without), rainfall_1h/6h/24h, elevation, rain_intensity_ratio, rain_6h_share, low_elev_rain. Drop `historical_flood_frequency`, `flood_zone`, `rain_x_freq`.
- Artifacts: `ml/artifacts/model_live.joblib` + `metadata_live.json` (own feature order).
- Expect lower accuracy than full model. Report both metrics.
- **Fallback if not trained yet:** rule-based nowcast `engine/risk/rules.py`: logistic of weighted normalised rain_1h (÷30 mm), rain_24h (÷115 mm), rain-rise trend, low-elevation factor. Deterministic, documented, flagged `source: "rules"` in output.
- `app/predictor.py` extended: `predict(df, model="full"|"live")`. Same `build_features(feature_set=...)` used in training and serving.

## 4. Architecture

```
Flutter  ->  FastAPI routers (route, trip, closures)
                 |
        engine/planner.py        engine/monitor.py
                 |                      |
   routing provider (alternatives)   trip state store
   geometry: resample into segments + per-segment ETA
   terrain (elevation) | static lookup (history) | weather (time-aware)
   risk scorer (ml predictor, full or live)
   aggregate -> cost -> rank -> advisory
```

Everything external sits behind an interface with a mock, so tests need no network.

## 5. Folder Structure (inside `backend/`)

```
backend/
  engine/
    __init__.py
    config.py              # all tunables (section 13)
    models.py              # pydantic: Route, Segment, RiskResult, Advisory, TripState
    geometry.py            # polyline decode, resample, snap, cumulative dist/time, haversine
    routing/
      base.py              # RoutingProvider interface
      osrm.py              # default
      ors.py               # optional, avoid-polygons support
      mock.py
    terrain.py             # elevation lookup + disk cache
    static_lookup.py       # grid cell -> historical_flood_frequency, flood_zone
    weather/
      base.py
      open_meteo.py
      cache.py             # TTL cache keyed by grid cell + hour
      mock.py
    risk/
      scorer.py            # builds feature frame per segment, calls predictor
      rules.py             # rule-based fallback
      aggregate.py         # segment -> cell -> route metrics
      cost.py              # effective time, hard filters, ranking
    planner.py             # PLANNING mode orchestration
    monitor.py             # LIVE mode orchestration + hysteresis
    closures.py            # active closure store + corridor query
    trips.py               # trip state store (SQLite)
  app/routers/route.py trip.py closures.py
  scripts/build_static_lookup.py
  data/static/             # lookup tables, hazard polygons, elevation cache
  tests/engine/
```

## 6. Pipeline Steps

### 6.1 Candidate routes
- `RoutingProvider.routes(origin, dest, alternatives=3, avoid=None)` returns geometry, distance, duration, per-step durations.
- Default OSRM (`alternatives` param). Self-host Kerala extract if public server rate-limits. ORS optional for `avoid_polygons`. Verify param names against current docs before coding.
- Alternatives from routers are often near-duplicates. Dedupe: drop route if >90% of its segments overlap another.
- **Avoidance re-route (v2):** take best route, find segments with p >= high threshold, request route avoiding a buffer polygon (ORS) or forcing a via-point (OSRM). Add result to candidates.
- Truck factor: multiply durations by `VEHICLE_SPEED_FACTOR` (config).

### 6.2 Segmentation and per-segment ETA
- Resample geometry every `SEGMENT_LEN_M` (default 500 m). Each sample point = one scored segment.
- Cumulative distance, then cumulative time by interpolating step durations. `eta_i = depart_time + cum_time_i`.
- Planning mode needs `eta_i` (forecast at arrival time). Live mode uses "now".

### 6.3 Feature assembly per segment
- **elevation:** DEM lookup (Open-Meteo elevation batch, 100 points per call, or local SRTM). Cache by ~100 m cell on disk.
- **historical_flood_frequency, flood_zone (planning only):** nearest value from `static_lookup` (grid 0.01 deg, built by `scripts/build_static_lookup.py` from events + hazard GeoJSON + station dataset, IDW within max 5 km). If no data: zone `low`, freq 0, mark segment `static_missing=true`, widen reported uncertainty.
- **rainfall_1h/6h/24h:** from hourly precipitation series per weather cell (0.1 deg grid, batched multi-point request to Open-Meteo, params for past hours + forecast hours). For segment i: window sums ending at hour(`eta_i`). Planning = past+forecast series. Live = last 24 h + next 1–3 h only, evaluated at now (and near-future for look-ahead).
- Guarantee 1h <= 6h <= 24h (reuse validator from `ml.data_prep`).
- Forecast is noisier than the gauge data the model trained on. Option `RAIN_SAFETY_FACTOR` (default 1.0, try 1.2) to be risk-averse.

### 6.4 Risk scoring
- One DataFrame for all segments of all candidate routes, single `predict_proba` call. No loops.
- Output p_i in [0,1] plus band (Low <0.3, Medium 0.3–0.6, High >0.6, same as ML plan).
- Active closure on segment (within `CLOSURE_SNAP_M`) forces p=1, `closed=true`.

### 6.5 Aggregation (fixing the independence trap)
Plain `1 - prod(1 - p_i)` over many points punishes long routes just because they have more sample points, and ignores that neighbouring segments flood together.

- Collapse to **risk cells**: 1 km grid key, `p_cell = max(p_i in cell)`.
- Per route metrics:
  - `expected_disruptions = sum(p_cell)`
  - `p_any = 1 - prod(1 - p_cell)` (shown to user as "chance of disruption", state independence assumption)
  - `max_p`, `high_risk_km`, `n_high_cells`, `worst_segments` (top 5 with coordinates)
  - `closed_segments` count

### 6.6 Cost and ranking
Cost in minutes ("effective time"):

```
effective_time = eta_min
               + risk_aversion(cargo) * delay_penalty_min(cargo) * expected_disruptions
               + lateness_weight * max(0, eta_min - minutes_to_deadline)
```

- Cargo profile (config): `general`, `perishable`, `fragile`, `hazardous` set `delay_penalty_min` and `risk_aversion`. Perishable: high delay penalty. Hazardous: very high risk aversion.
- **Hard filters:** drop route if any closed segment, or `max_p >= P_BLOCK` (default 0.7), unless every route fails. Then return least bad with `DO_NOT_GO` advisory.
- Rank by `effective_time`. Return reasons list, e.g. "Avoids 3 high-risk cells near X, +14 min".
- Ties: prefer lower `max_p`.

### 6.7 Advisory
- `GO`: best route max_p < 0.3.
- `GO_WITH_CAUTION`: 0.3 <= max_p < 0.6.
- `DELAY`: risk now is medium/high, and a later departure (scan offsets 0, 30, ..., 360 min, reusing the one forecast fetch, only model calls repeat) lowers effective_time by >= 30%. Return `suggested_departure`.
- `DO_NOT_GO`: all routes hard-filtered and no better departure window.

## 7. LIVE Trip Monitoring

State per trip (SQLite, TTL 24 h): trip_id, current route (segments), progress index, last scores, last reroute time, cargo, deadline, destination.

On each GPS update `POST /trip/{id}/update`:

1. Snap position to route. Off-route by > `OFF_ROUTE_M` (e.g. 150 m) for 2 updates -> treat as deviation, fetch fresh routes.
2. Take remaining route. Look-ahead window = min(`LOOKAHEAD_MIN` 60 min, `LOOKAHEAD_KM` 40 km).
3. Fetch current weather + next 1–3 h forecast for cells in window (cached, TTL 10 min).
4. Score with **live model** (no history features). Aggregate as in 6.5.
5. Check triggers:
   - `max_p` ahead >= `LIVE_WARN_P` (0.5), or jump >= 0.15 since last check
   - new closure within 2 km corridor of remaining route
   - rain_1h at current/ahead cell >= `HEAVY_RAIN_1H` (e.g. 15 mm)
6. If triggered: request alternatives **from current position** to destination, score all in live mode, compute effective_time.
7. **Hysteresis (no flip-flopping):** switch only if
   `best_alt.effective_time <= current.effective_time - max(10 min, 15%)` and last reroute > `MIN_REROUTE_GAP_MIN` (5 min). If current route risk is critical (max_p >= 0.7 ahead) skip the margin rule.
8. Response: alerts (`INFO`, `WARNING`, `REROUTE`, `HOLD`), `reroute` object if recommended (user confirms in app, no silent switch), updated ETA, risk ahead profile.
   - `HOLD`: critical risk ahead, no viable alternative. Suggest stopping at nearest higher-elevation point (stretch goal).
9. Poll interval hint returned in response (`next_poll_s`), shorter when risk high.

Cost control: weather and routing calls only when trigger fires or every N minutes (config), not every ping.

## 8. API (FastAPI, `backend/app/routers/`)

- `POST /route/plan`
  ```json
  {"origin": {"lat": 10.78, "lon": 76.65}, "destination": {"lat": 9.93, "lon": 76.27},
   "depart_time": "2026-10-08T06:00:00+05:30", "cargo": "perishable",
   "deadline": "2026-10-08T14:00:00+05:30", "avoid_tolls": false}
  ```
  Response: `advisory`, `recommended_route_id`, `routes[]` (id, distance_km, eta, duration_min, effective_time, metrics from 6.5, `reasons`, `geometry` GeoJSON LineString, `segments[]` with index range, p, band, closed, static_missing), `suggested_departure`, `generated_at`, `data_sources`, `degraded`.
- `POST /trip/start` body: chosen route_id (or full route) + cargo + deadline. Returns `trip_id`.
- `POST /trip/{trip_id}/update` body: lat, lon, speed, timestamp. Returns section 7 response.
- `GET /trip/{trip_id}`, `DELETE /trip/{trip_id}`.
- `POST /closures` (lat, lon, radius_m, reason, expires_at), `GET /closures?bbox=`, `DELETE /closures/{id}`. Admin or crowd-reported. Optional API key.
- `GET /engine/health`: provider status (routing, weather, elevation), model versions.

Flutter gets GeoJSON geometry and per-segment bands to colour polyline. OpenAPI at `/docs` is the contract.

## 9. Caching, Performance, Degradation

- Weather: cell + hour keyed TTL cache (planning 30 min, live 10 min). Elevation: permanent disk cache.
- Targets: planning, 3 routes x ~300 points, warm cache < 3 s excluding routing provider time. Live update < 1.5 s. Model inference < 10 ms per batch.
- Weather down: use stale cache, set `degraded: true`, `weather_age_min`. No cache: planning falls back to static-only history risk, live falls back to `rules.py` with a warning to driver, never silent.
- Routing down: HTTP 503 with clear error. Live mode keeps current route.
- Every response states data sources and timestamps.

## 10. Data to Prepare

- `data/static/flood_zones.geojson` + `flood_events.csv` (same files used for model dataset) -> `scripts/build_static_lookup.py` -> `static_lookup.parquet`.
- Optional: closure feed from KSDMA/PWD/police if accessible, else manual `/closures`.
- Stretch: blend live rain with CWC/Kerala telemetry station rainfall (IDW) when a feed is available. Same source as training data, closes forecast-vs-gauge gap.

## 11. Testing

- Unit: polyline resample lengths, cumulative ETA interpolation, cell collapse, aggregation math (monotonic: more risk never lowers cost), cost function with cargo profiles, hard filters, advisory thresholds, hysteresis (no switch inside margin, switch outside), off-route detection.
- Contract: in LIVE mode, history columns (`historical_flood_frequency`, `flood_zone`) must never reach the scorer. Test that live path uses `model_live` and static lookup is not called.
- Integration with mocks: fixed route + fixed weather -> expected ranking. Rain spike scenario triggers reroute, repeated updates do not flip-flop.
- Simulation harness `scripts/simulate_trip.py`: replay a GPS trace on a route with a synthetic rain front, print alert timeline.
- Golden scenario: Palakkad -> Kochi corridor, main road vs alternative, with heavy rain on main.
- API tests: 422 on bad payloads, unknown trip 404, closure effect on ranking.

## 12. Milestones

1. Config, models, geometry (resample, ETA), mock providers
2. Routing provider (OSRM) + route dedupe
3. Terrain + static lookup build script
4. Weather provider + cache, time-aware rainfall windows
5. Scorer (full model) + aggregation + cost + `/route/plan`
6. Advisory + delay scan
7. Live model training (`--feature-set live`) + rules fallback
8. Trip store + monitor + hysteresis + `/trip/*`
9. Closures
10. Tests, simulator, README section, API contract for Flutter
11. Stretch: avoidance re-route, HOLD suggestion, telemetry blend, forecast ensemble quantiles

## 13. Config Defaults (`engine/config.py`)

SEGMENT_LEN_M=500, CELL_KM=1, P_BLOCK=0.7, bands 0.3/0.6, LIVE_WARN_P=0.5, HEAVY_RAIN_1H=15, LOOKAHEAD_MIN=60, LOOKAHEAD_KM=40, OFF_ROUTE_M=150, MIN_REROUTE_GAP_MIN=5, reroute margin max(10 min, 15%), VEHICLE_SPEED_FACTOR=1.25, RAIN_SAFETY_FACTOR=1.0, cargo profiles (delay_penalty_min / risk_aversion): general 90/1.0, perishable 180/1.5, fragile 150/1.5, hazardous 240/2.5, DELAY scan 0–360 min step 30, lateness_weight=3. Tune with data. All env-overridable.

## 14. Risks and Honest Limits

- Probability = flood occurrence in training data at station-hour, not guaranteed road closure. State in API docs and UI copy.
- Forecast rain vs gauge-trained model: distribution shift. Mitigate with safety factor, later telemetry blend.
- Live model has no history, so weaker at known hotspots. Accepted per requirement. Could add optional blend later.
- Public routing and weather APIs: rate limits, terms of use for commercial use. Self-host or swap provider for production.
- Alternative routes from router may be too few or too similar. Avoidance re-route (v2) fixes.
- Delay and risk-aversion numbers are assumptions. Expose in config, tune with operators.
- Independence assumption in `p_any`. Cell collapse reduces but does not remove it.
- Do not auto-switch route silently while driving. Always prompt driver.
