"""Probability calibration using Isotonic regression or Platt scaling (Sigmoid).

Repairs probability distortions introduced by class-imbalance weighting (scale_pos_weight).
Uses held-out spatial calibration split with genuine empirical class distribution.
"""

from typing import Any, Dict, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, log_loss

from ml.config import (
    MODEL_FILE,
    RAW_DATA_FILE,
    RAW_MODEL_FILE,
)
from ml.data_prep import build_features


def get_calibrated_classifier(estimator: Any, method: str = "isotonic") -> CalibratedClassifierCV:
    """Create CalibratedClassifierCV compatible across scikit-learn >= 1.6 and < 1.6."""
    try:
        from sklearn.frozen import FrozenEstimator
        frozen = FrozenEstimator(estimator)
        return CalibratedClassifierCV(estimator=frozen, method=method)
    except (ImportError, TypeError, AttributeError):
        # Fallback for scikit-learn < 1.6
        return CalibratedClassifierCV(estimator=estimator, method=method, cv="prefit")


def calibrate_model(feature_set: str = "full") -> Tuple[CalibratedClassifierCV, Dict[str, Any]]:
    """Calibrate the raw XGBoost model using the held-out spatial calibration split."""
    from ml.config import (
        LIVE_MODEL_FILE,
        LIVE_RAW_MODEL_FILE,
    )

    cal_path = RAW_DATA_FILE.parent.parent / "processed" / "cal.parquet"
    if not cal_path.exists():
        raise FileNotFoundError(f"Calibration data not found at {cal_path}. Run ml.train first.")

    raw_model_path = LIVE_RAW_MODEL_FILE if feature_set == "live" else RAW_MODEL_FILE
    model_out_path = LIVE_MODEL_FILE if feature_set == "live" else MODEL_FILE

    if not raw_model_path.exists():
        raise FileNotFoundError(f"Raw model not found at {raw_model_path}. Run ml.train first.")

    cal_df = pd.read_parquet(cal_path)
    X_cal, y_cal = build_features(cal_df, return_target=True, feature_set=feature_set)

    raw_model = joblib.load(raw_model_path)

    # Raw uncalibrated probabilities and scores
    raw_probs = raw_model.predict_proba(X_cal)[:, 1]
    raw_brier = brier_score_loss(y_cal, raw_probs)
    raw_logloss = log_loss(y_cal, raw_probs)

    num_pos = int((y_cal == 1).sum())
    total_cal = len(y_cal)

    print(f"=== Model Calibration ({feature_set}) ===")
    print(f"Calibration split size: {total_cal} samples ({num_pos} positives, {num_pos/total_cal:.1%} positive rate)")
    print(f"Raw Model -> Brier Score: {raw_brier:.4f} | Log Loss: {raw_logloss:.4f}")

    # 1. Fit Isotonic Calibration
    iso_cal = get_calibrated_classifier(raw_model, method="isotonic")
    iso_cal.fit(X_cal, y_cal)
    iso_probs = iso_cal.predict_proba(X_cal)[:, 1]
    iso_brier = brier_score_loss(y_cal, iso_probs)
    iso_logloss = log_loss(y_cal, iso_probs)

    # 2. Fit Sigmoid (Platt) Calibration
    sig_cal = get_calibrated_classifier(raw_model, method="sigmoid")
    sig_cal.fit(X_cal, y_cal)
    sig_probs = sig_cal.predict_proba(X_cal)[:, 1]
    sig_brier = brier_score_loss(y_cal, sig_probs)
    sig_logloss = log_loss(y_cal, sig_probs)

    print(f"Isotonic  -> Brier Score: {iso_brier:.4f} | Log Loss: {iso_logloss:.4f}")
    print(f"Sigmoid   -> Brier Score: {sig_brier:.4f} | Log Loss: {sig_logloss:.4f}")

    # Selection policy:
    if num_pos >= 100 and iso_brier <= (sig_brier + 0.005):
        selected_method = "isotonic"
        best_model = iso_cal
        best_brier = iso_brier
        best_logloss = iso_logloss
    else:
        selected_method = "sigmoid"
        best_model = sig_cal
        best_brier = sig_brier
        best_logloss = sig_logloss

    print(f"Selected Calibration Method: '{selected_method.upper()}' (Brier: {best_brier:.4f})")

    # Save calibrated model artifact
    joblib.dump(best_model, model_out_path)
    print(f"Saved calibrated model to {model_out_path}")

    info = {
        "feature_set": feature_set,
        "calibration_method": selected_method,
        "calibration_samples": total_cal,
        "calibration_positives": num_pos,
        "raw_brier_score": float(raw_brier),
        "raw_log_loss": float(raw_logloss),
        "calibrated_brier_score": float(best_brier),
        "calibrated_log_loss": float(best_logloss),
        "isotonic_brier": float(iso_brier),
        "sigmoid_brier": float(sig_brier),
    }

    return best_model, info


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calibrate Flood Risk Model")
    parser.add_argument(
        "--feature-set",
        type=str,
        choices=["full", "live"],
        default="full",
        help="Feature set: 'full' or 'live'",
    )
    args = parser.parse_args()

    calibrate_model(feature_set=args.feature_set)
