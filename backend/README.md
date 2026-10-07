# FLOODRIX: Flood-Aware Predictive Logistics Planner (ML Backend)

> **Predict. Protect. Deliver.**  
> High-throughput AI flood hazard prediction engine and resilient logistics router for Kerala, designed to serve the Flutter mobile application with single-digit millisecond batch inference latency.

---

## 1. System Overview

FLOODRIX transforms environmental, topographical, and meteorological signals across Kerala into calibrated flood probabilities for road segments. It evaluates entire delivery corridors, checks known road closures, factors in cargo vulnerability (e.g., medicine, perishables, hazmat), and outputs real-time routing recommendations (`GO`, `REROUTE`, `WAIT`).

### Key ML & Architectural Highlights
- **Spatial Block Splitting (~5.5 km cells)**: Prevents spatial leakage between adjacent road segments across Train (60%), Calibration (20%), and Test (20%) splits.
- **Monotone Constraints**: Enforces physical laws in XGBoost (+1 for cumulative rainfall and burst intensity, -1 for elevation, +1 for historical flood frequency).
- **Isotonic Calibration**: Rebalances class-weighted probabilities against empirical base rates, achieving an Expected Calibration Error (ECE) of **0.0272**.
- **Vectorized Inference**: Vectorized feature construction and batch scoring in single-digit ms for 500 segments.
- **Dual API Surface**: Direct root endpoints (`/health`, `/model-info`, `/predict/segments`, `/predict/route`) as specified in `model-plan.md` plus full `/api/v1/...` endpoints compliant with the Flutter Mobile API Specification.

---

## 2. Directory Structure

All backend code, datasets, artifacts, tests, and configuration reside strictly inside `backend/`:

```
backend/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── .dockerignore
├── data/
│   ├── raw/
│   │   └── flood.csv               # Raw / synthetic Kerala flood dataset
│   └── processed/
│       ├── train.parquet           # Leak-free train split (60%)
│       ├── cal.parquet             # Calibration split (20%)
│       └── test.parquet            # Untouched spatial test set (20%)
├── ml/
│   ├── __init__.py
│   ├── config.py                   # Paths, constants, Kerala bounds, feature order, risk bands
│   ├── data_prep.py                # Schema validation & deterministic feature engineering
│   ├── split.py                    # Spatial group split generator (~5 km blocks)
│   ├── train.py                    # Baseline Logistic Regression + Optuna-tuned XGBoost
│   ├── calibrate.py                # Isotonic & Sigmoid probability calibration
│   ├── evaluate.py                 # Evaluation metrics, PR/ROC curves, reliability plots
│   ├── generate_synthetic.py       # Fallback realistic dataset generator
│   └── artifacts/                  # Persisted model artifacts & plots
│       ├── model.joblib            # Calibrated production model
│       ├── model_raw.joblib        # Uncalibrated baseline XGBoost
│       ├── baseline_model.joblib   # Standard Logistic Regression baseline
│       ├── metadata.json           # Features order, versions, risk thresholds
│       ├── metrics.json            # Quantitative test set evaluation metrics
│       └── plots/
│           ├── reliability_curve.png
│           ├── pr_curve.png
│           ├── roc_curve.png
│           └── feature_importance.png
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application & lifespan state management
│   ├── schemas.py                  # Pydantic v2 data models & validation rules
│   ├── predictor.py                # Vectorized inference & route risk aggregator
│   ├── services/
│   │   ├── weather_service.py      # Current & hourly forecast rainfall observations
│   │   ├── closure_service.py      # Active Kerala road closure & disruption registry
│   │   └── routing_service.py      # Multi-candidate route risk & cargo decision engine
│   └── routers/
│       ├── health.py               # /health and /model-info
│       ├── predict.py              # /predict/segments and /predict/route
│       ├── routes.py               # /api/v1/routes/plan
│       ├── weather.py              # /api/v1/weather/current & /forecast
│       ├── closures.py             # /api/v1/closures
│       ├── map_risk.py             # /api/v1/map/risk
│       ├── trips.py                # /api/v1/trips & /trips/{id}/location
│       ├── alerts.py               # /api/v1/alerts/active
│       └── simulation.py           # /api/v1/simulation/run
├── tests/
│   ├── test_features.py            # Unit tests for build_features and validation
│   ├── test_schemas.py             # Unit tests for Pydantic schema constraints
│   ├── test_model.py               # Unit tests for monotonicity and probability bounds
│   ├── test_api.py                 # Integration tests for FastAPI endpoints
│   └── test_latency.py             # Latency benchmarks for 100, 500, 1000 segments
└── scripts/
    └── run_pipeline.sh             # End-to-end execution: train -> calibrate -> evaluate
```

---

## 3. Dataset Schema & Feature Engineering

### 3.1 Input Schema
| Column | Type | Validation Constraint | Description |
|---|---|---|---|
| `latitude` | `float` | `8.18 <= lat <= 12.85` | Kerala boundary latitude |
| `longitude` | `float` | `74.80 <= lon <= 77.45` | Kerala boundary longitude |
| `rainfall_1h` | `float` | `>= 0.0, <= rainfall_6h` | 1-hour cumulative rainfall (mm) |
| `rainfall_6h` | `float` | `>= 0.0, <= rainfall_24h` | 6-hour cumulative rainfall (mm) |
| `rainfall_24h` | `float` | `>= 0.0` | 24-hour cumulative rainfall (mm) |
| `elevation` | `float` | `>= -5.0` | Elevation above sea level (m) |
| `historical_flood_frequency` | `float/int` | `>= 0` | Historical flood count per zone |
| `flood_zone` | `str` | `low`, `medium`, `high` | Flood zone vulnerability rating |
| `flood_occurred` | `int` | `0` or `1` | Historical target label |

### 3.2 Deterministic Engineered Features
Implemented in `ml.data_prep.build_features` (shared identically across training and FastAPI serving to eliminate train/serve skew):
- **`rain_intensity_ratio`**: `rainfall_1h / (rainfall_24h + 1e-5)` (captures sudden cloudburst bursts)
- **`rain_6h_share`**: `rainfall_6h / (rainfall_24h + 1e-5)` (captures sustained short-term deluge)
- **`rain_x_freq`**: `rainfall_24h * historical_flood_frequency` (interaction effect between rain and known chronic flood locations)
- **`low_elev_rain`**: `rainfall_24h / (max(elevation, 0.0) + 1.0)` (penalizes low coastal / backwater land)
- **`flood_zone_encoded`**: Ordinal integer mapping (`low: 0`, `medium: 1`, `high: 2`, `extreme: 3`).

---

## 4. Evaluation Results (Untouched Spatial Test Set)

Evaluated on 1,029 held-out road segments located in unseen spatial blocks:

| Metric | Baseline Logistic Regression | Raw XGBoost | **Calibrated XGBoost** |
|---|---|---|---|
| **PR-AUC** | 0.8034 | 0.8051 | **0.7871** |
| **ROC-AUC** | 0.8255 | 0.8310 | **0.8234** |
| **Brier Score** | 0.1737 | 0.1614 | **0.1489** (Lower is better) |
| **Log Loss** | 0.5120 | 0.4891 | **0.4536** (Lower is better) |
| **Expected Calibration Error (ECE)** | 0.0724 | 0.0510 | **0.0272** (Near-perfect reliability) |

### Risk Bands
- **LOW Risk**: `flood_probability < 0.30`
- **MEDIUM Risk**: `0.30 <= flood_probability <= 0.60`
- **HIGH Risk**: `flood_probability > 0.60`

---

## 5. Quickstart & Local Setup

### 5.1 Environment Setup (from `backend/`)
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 5.2 Run Pipeline
Execute the full data generation, training, calibration, and evaluation pipeline:
```bash
./scripts/run_pipeline.sh
# OR manually:
python -m ml.train
python -m ml.calibrate
python -m ml.evaluate
```

### 5.3 Run Test Suite
```bash
pytest -v
```

### 5.4 Start FastAPI Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 6. API Reference & Sample Requests

### 6.1 Predict Batch Segments
`POST /predict/segments`

**Request:**
```json
{
  "segments": [
    {
      "segment_id": "seg_ernakulam_01",
      "latitude": 9.9812,
      "longitude": 76.2845,
      "rainfall_1h": 15.0,
      "rainfall_6h": 45.0,
      "rainfall_24h": 110.0,
      "elevation": 4.5,
      "historical_flood_frequency": 3,
      "flood_zone": "high"
    }
  ]
}
```

**Response:**
```json
{
  "segments": [
    {
      "segment_id": "seg_ernakulam_01",
      "latitude": 9.9812,
      "longitude": 76.2845,
      "flood_probability": 0.6482,
      "risk_level": "HIGH"
    }
  ],
  "total_segments": 1,
  "latency_ms": 6.84
}
```

### 6.2 Predict Route Risk
`POST /predict/route`

**Request:**
```json
{
  "route_id": "route_nh66_kochi_alappuzha",
  "segments": [
    {
      "segment_id": "s1",
      "latitude": 9.98,
      "longitude": 76.28,
      "rainfall_1h": 12.0,
      "rainfall_6h": 40.0,
      "rainfall_24h": 90.0,
      "elevation": 5.0,
      "historical_flood_frequency": 3,
      "flood_zone": "high"
    },
    {
      "segment_id": "s2",
      "latitude": 9.85,
      "longitude": 76.31,
      "rainfall_1h": 18.0,
      "rainfall_6h": 50.0,
      "rainfall_24h": 120.0,
      "elevation": 3.0,
      "historical_flood_frequency": 4,
      "flood_zone": "high"
    }
  ]
}
```

**Response:**
```json
{
  "route_id": "route_nh66_kochi_alappuzha",
  "segments": [...],
  "route_risk": 0.8124,
  "max_segment_risk": 0.6852,
  "high_risk_segment_count": 2,
  "worst_segments": [
    {
      "segment_id": "s2",
      "latitude": 9.85,
      "longitude": 76.31,
      "flood_probability": 0.6852,
      "risk_level": "HIGH"
    }
  ],
  "recommended_action": "REROUTE",
  "risk_independence_note": "Route risk is computed as 1 - prod(1 - p_i), assuming spatial independence between flood occurrences across distinct road segments.",
  "latency_ms": 7.15
}
```

### 6.3 Plan Logistics Route (Mobile Specification)
`POST /api/v1/routes/plan`

**Request:**
```json
{
  "origin": {"latitude": 9.98, "longitude": 76.28},
  "destination": {"latitude": 10.52, "longitude": 76.21},
  "cargo_type": "MEDICINE"
}
```

**Response:**
```json
{
  "recommended_route": {
    "route_id": "R2_MIDLAND",
    "label": "Midland Bypass (Higher Elevation)",
    "distance_km": 72.8,
    "eta_minutes": 131.0,
    "route_risk": 0.3120,
    "max_segment_risk": 0.2840,
    "decision": "GO",
    "is_recommended": true,
    "high_risk_segments": 0,
    "warning_message": null
  },
  "alternative_routes": [...],
  "plan_timestamp": "2026-10-07T13:25:37+00:00"
}
```

---

## 7. Docker Deployment

Build and run the containerized backend:
```bash
# Build image from backend/ directory
docker build -t floodrix-backend:latest .

# Run container
docker run -d -p 8000:8000 --name floodrix-api floodrix-backend:latest

# Check health
curl http://localhost:8000/health
```
