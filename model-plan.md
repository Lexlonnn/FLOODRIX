# Flood-Aware Logistics Planner: ML Backend Implementation Plan

## 1. Goal

Predict calibrated probability of road-segment flooding. Serve via FastAPI for Flutter app. Batch of hundreds of segments scored in single-digit ms.

## 2. Dataset Schema

| Column | Type | Note |
|---|---|---|
| Latitude, Longitude | float | Segment midpoint |
| Rainfall_1h, Rainfall_6h, Rainfall_24h | float (mm) | Cumulative, must satisfy 1h <= 6h <= 24h |
| Elevation | float (m) | |
| Historical_flood_frequency | float / int | Past flood count or rate per location |
| Flood_zone | categorical | Encode ordinal if risk levels (low/med/high), else one-hot |
| Flood_occurred | 0/1 | Target |

## 3. Language, Stack, Project Structure

**Language: Python 3.11.** Libraries: pandas, numpy, scikit-learn (>= 1.6), xgboost, optuna, shap, matplotlib, joblib, FastAPI, uvicorn, pydantic v2, pytest, httpx.

**Rule: everything backend lives inside `backend/`.** Data, training code, model artifacts, API, tests, Docker, README, env files. Nothing backend-related outside it. Flutter app lives in sibling folder (e.g. `frontend/`). All paths in code resolve relative to `backend/` (use `Path(__file__)` based `config.py`), so commands work when run from `backend/`.

```
project-root/
  frontend/                  # Flutter app (not part of this plan)
  backend/                   # ALL backend work here
    README.md
    requirements.txt
    .env.example
    .gitignore
    Dockerfile
    .dockerignore
    data/
      raw/                   # flood.csv (input)
      processed/             # cleaned + feature tables
    ml/
      __init__.py
      config.py              # paths, constants, seeds, risk bands
      data_prep.py           # load, validate, clean, build_features()
      split.py               # spatial group split
      train.py               # baseline + XGBoost + Optuna
      calibrate.py           # isotonic / sigmoid calibration
      evaluate.py            # metrics + plots
      generate_synthetic.py  # fallback dataset if no real CSV
      artifacts/             # model.joblib, metadata.json, metrics.json, plots/
    app/
      __init__.py
      main.py                # FastAPI app, lifespan model load
      schemas.py             # pydantic models
      predictor.py           # inference wrapper
      routers/
        predict.py
        health.py
    tests/
      test_features.py
      test_schemas.py
      test_model.py
      test_api.py
      test_latency.py
    scripts/
      run_pipeline.sh        # data -> train -> calibrate -> evaluate
```

Run commands (from `backend/`):

```
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m ml.train && python -m ml.calibrate && python -m ml.evaluate
uvicorn app.main:app --reload --port 8000
pytest
```

Use package-style imports (`from ml.data_prep import build_features`) so `app/` and `ml/` share one feature builder.

## 4. Data Preparation

1. Validate: nulls, duplicates, lat/lon within Kerala bounds (~8.2–12.8 N, 74.8–77.4 E), rainfall monotonic (1h <= 6h <= 24h), non-negative.
2. Check class balance. Record positive rate. Needed for `scale_pos_weight` = neg / pos.
3. Feature engineering (all derived deterministically so inference matches training):
   - `rain_intensity_ratio` = Rainfall_1h / (Rainfall_24h + eps)
   - `rain_6h_share` = Rainfall_6h / (Rainfall_24h + eps)
   - `rain_x_freq` = Rainfall_24h * Historical_flood_frequency
   - `low_elev_rain` = Rainfall_24h / (Elevation + 1)
   - Flood_zone encoding as above.
4. Keep raw Lat/Lon, but test model with and without. Raw coords can memorise location and inflate scores.
5. Save feature list and order in `metadata.json`. Inference must use same order.

## 5. Splitting (critical)

Random split leaks. Neighbouring points share labels.

- Build spatial blocks: round lat/lon into grid cells (e.g. ~5 km) -> `group_id`.
- Outer split: `StratifiedGroupKFold` or `GroupShuffleSplit`. Hold out test set of unseen cells (~20%).
- Remaining data: train (~60%) and calibration (~20%), also grouped. Calibration set must never be used for training.
- If time-stamped events exist, prefer split by time or event instead.

## 6. Model Training

- `XGBClassifier(objective="binary:logistic", tree_method="hist", scale_pos_weight=neg/pos, eval_metric="aucpr", early_stopping_rounds=50)`
- Tune with Optuna (or RandomizedSearch) using grouped CV, metric = PR-AUC. Params: `max_depth` 3–8, `learning_rate` 0.01–0.2, `n_estimators` (early stop), `subsample`, `colsample_bytree`, `min_child_weight`, `gamma`, `reg_lambda`.
- Optional `monotone_constraints`: rainfall features +1, elevation -1, historical frequency +1. Improves physical plausibility and generalisation.
- Save raw model as baseline.

## 7. Calibration

`scale_pos_weight` skews raw probabilities upward. Calibration repairs this.

- Calibrate on the held-out calibration set, which keeps the **true** class distribution (no resampling).
- sklearn >= 1.6 removed `cv="prefit"`. Use:
  ```python
  from sklearn.frozen import FrozenEstimator
  from sklearn.calibration import CalibratedClassifierCV
  cal = CalibratedClassifierCV(FrozenEstimator(model), method="isotonic")
  cal.fit(X_cal, y_cal)
  ```
- Isotonic needs enough positives (rule of thumb >= ~1000 total, in calibration set at least a few hundred). If fewer, use `method="sigmoid"` instead. Compare both.
- Honest claim: calibrated 0.85 means "about 85% of similar cases flooded in data". It holds only if the training data reflects real conditions. Document this. Predictions are of flood occurrence in dataset; map to road closure only if label means that.

## 8. Evaluation (on untouched spatial test set)

- PR-AUC (main), ROC-AUC, Brier score, log loss.
- Reliability curve (calibration plot), before vs after calibration. Expected Calibration Error.
- Recall / precision at chosen thresholds. Pick risk bands: Low < 0.3, Medium 0.3–0.6, High > 0.6 (tune from data and cost of missed flood).
- Feature importance + SHAP summary (sanity check; rainfall and elevation should dominate).
- Compare baseline logistic regression to prove XGBoost value.

## 9. Artifacts

- `model.joblib` (calibrated model, one object) via joblib.
- `metadata.json`: feature order, encoding map, versions (xgboost, sklearn), training date, metrics, thresholds, positive rate.
- Optional: export ONNX for faster inference. Only if latency target missed.

## 10. FastAPI Service

Endpoints:

- `GET /health`: status + model version.
- `GET /model-info`: metadata, metrics, feature list.
- `POST /predict/segments`: batch of segments.
  ```json
  {"segments": [{"segment_id": "s1", "latitude": 10.5, "longitude": 76.2,
    "rainfall_1h": 12, "rainfall_6h": 40, "rainfall_24h": 90,
    "elevation": 8.5, "historical_flood_frequency": 3, "flood_zone": "high"}]}
  ```
  Response: per segment `flood_probability`, `risk_level`.
- `POST /predict/route`: segments in order. Response adds route-level risk:
  - `route_risk = 1 - prod(1 - p_i)` (assumes independence; state this)
  - `max_segment_risk`, count of high-risk segments, list of worst segments.
  Flutter / routing layer compares candidate routes with this.

Implementation rules:
- Load model once in FastAPI `lifespan` from `backend/ml/artifacts/`, keep in app state. Fail startup loudly if artifacts missing.
- Pydantic validation: ranges, rainfall ordering, enum for flood_zone, max batch size (e.g. 1000).
- Vectorise: build one numpy / DataFrame for whole batch, single `predict_proba` call. No per-row loops.
- Feature engineering shared function used by both training and serving (`data_prep.build_features`). Avoids train/serve skew.
- Sync `def` endpoints fine (CPU-bound). Run uvicorn with multiple workers.
- CORS enabled for Flutter web/dev. API key header optional.
- Log latency per request. Target < 10 ms for 500 segments (model time only).

## 11. Feature Assembly at Serving Time (later phase)

Flutter app sends route; backend must fill features:
- Rainfall_1h/6h/24h: live/forecast from weather API (e.g. Open-Meteo, IMD).
- Elevation: DEM lookup (SRTM) or precomputed grid.
- Historical_flood_frequency + Flood_zone: precomputed lookup by KD-tree / grid cell from dataset.
Keep as separate `features_service` module so ML endpoint stays pure and fast.

## 12. Testing

- Unit: feature builder, schema validation, rainfall ordering.
- Model: output in [0, 1], monotonic sanity (more rain -> prob not lower).
- API: health, single, batch of 500, invalid payload -> 422.
- Latency benchmark: batch 100 / 500 / 1000.

## 13. Deployment

- `backend/Dockerfile` (python:3.11-slim), build context = `backend/`, pinned requirements, `uvicorn app.main:app --workers 2`. Copy `ml/artifacts/` into image so model ships with API.
- Expose port, health check on `/health`.
- Host: Render / Railway / local on hackathon laptop with ngrok fallback.

## 14. Milestones

1. Data audit + feature builder + spatial split
2. Baseline + XGBoost training
3. Calibration + evaluation plots
4. Artifacts + FastAPI endpoints
5. Tests + latency benchmark
6. Docker + hand API contract (OpenAPI `/docs`) to Flutter team
7. Stretch: feature assembly service, SHAP explanation per segment

## 15. Risks

- Spatial leakage -> fake high score. Mitigated by grouped split.
- Too few positives -> isotonic overfits. Fallback sigmoid.
- Train/serve skew in features. Mitigated by single shared builder.
- Label meaning (flood occurred vs road closed). Clarify, state in docs.