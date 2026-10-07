"""Model evaluation on held-out spatial test set: metrics, calibration curves, SHAP, and metadata export."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Tuple
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
import xgboost as xgb
import sklearn

from ml.config import (
    BASELINE_MODEL_FILE,
    FLOOD_ZONE_MAP,
    METADATA_FILE,
    METRICS_FILE,
    MODEL_FEATURE_COLUMNS,
    MODEL_FILE,
    PLOTS_DIR,
    RAW_DATA_FILE,
    RAW_MODEL_FILE,
    RISK_HIGH_THRESHOLD,
    RISK_LOW_THRESHOLD,
    TARGET_COLUMN,
)
from ml.data_prep import build_features


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across equal-width confidence bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total = len(y_true)

    for i in range(n_bins):
        in_bin = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if i == n_bins - 1:
            in_bin = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        count = np.sum(in_bin)
        if count > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (count / total) * np.abs(bin_acc - bin_conf)

    return float(ece)


def calculate_threshold_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> Dict[str, float]:
    """Compute precision, recall, specificity, and F1 at a specified threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    return {
        "threshold": threshold,
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "specificity": round(float(spec), 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
    }


def plot_reliability_curve(
    y_true: np.ndarray,
    raw_probs: np.ndarray,
    cal_probs: np.ndarray,
    output_path: str,
):
    """Plot reliability / calibration curves for both raw and calibrated models."""
    plt.figure(figsize=(7, 6))
    plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")

    prob_true_raw, prob_pred_raw = calibration_curve(y_true, raw_probs, n_bins=10, strategy="uniform")
    plt.plot(prob_pred_raw, prob_true_raw, "s-", color="#e74c3c", label="XGBoost (Raw, uncalibrated)")

    prob_true_cal, prob_pred_cal = calibration_curve(y_true, cal_probs, n_bins=10, strategy="uniform")
    plt.plot(prob_pred_cal, prob_true_cal, "o-", color="#2ecc71", label="XGBoost (Calibrated)")

    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives (Empirical)")
    plt.title("Reliability Curve: Pre- vs Post-Calibration (Untouched Spatial Test Set)")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_pr_and_roc_curves(
    y_true: np.ndarray,
    cal_probs: np.ndarray,
    base_probs: np.ndarray,
    output_pr: str,
    output_roc: str,
):
    """Plot Precision-Recall and ROC curves comparing Calibrated XGBoost vs Baseline."""
    # PR Curve
    plt.figure(figsize=(7, 6))
    prec_xgb, rec_xgb, _ = precision_recall_curve(y_true, cal_probs)
    pr_auc_xgb = average_precision_score(y_true, cal_probs)

    prec_base, rec_base, _ = precision_recall_curve(y_true, base_probs)
    pr_auc_base = average_precision_score(y_true, base_probs)

    baseline_random = np.mean(y_true)
    plt.axhline(y=baseline_random, color="gray", linestyle="--", label=f"Random Chance ({baseline_random:.2f})")
    plt.plot(rec_base, prec_base, color="#3498db", label=f"Baseline Logistic (PR-AUC = {pr_auc_base:.3f})")
    plt.plot(rec_xgb, prec_xgb, color="#2ecc71", linewidth=2, label=f"Calibrated XGBoost (PR-AUC = {pr_auc_xgb:.3f})")

    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve (Spatial Test Set)")
    plt.legend(loc="upper right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_pr, dpi=200)
    plt.close()

    # ROC Curve
    plt.figure(figsize=(7, 6))
    fpr_xgb, tpr_xgb, _ = roc_curve(y_true, cal_probs)
    roc_auc_xgb = roc_auc_score(y_true, cal_probs)

    fpr_base, tpr_base, _ = roc_curve(y_true, base_probs)
    roc_auc_base = roc_auc_score(y_true, base_probs)

    plt.plot([0, 1], [0, 1], "k--", label="Random Classifier (0.50)")
    plt.plot(fpr_base, tpr_base, color="#3498db", label=f"Baseline Logistic (ROC-AUC = {roc_auc_base:.3f})")
    plt.plot(fpr_xgb, tpr_xgb, color="#2ecc71", linewidth=2, label=f"Calibrated XGBoost (ROC-AUC = {roc_auc_xgb:.3f})")

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve (Spatial Test Set)")
    plt.legend(loc="lower right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_roc, dpi=200)
    plt.close()


def plot_feature_importance(raw_model: xgb.XGBClassifier, feature_names: List[str], output_path: str):
    """Plot feature importance by gain."""
    booster = raw_model.get_booster()
    score_dict = booster.get_score(importance_type="gain")
    
    # Map f0, f1... to feature names if necessary
    mapped_scores = {}
    for i, name in enumerate(feature_names):
        f_key = f"f{i}"
        val = score_dict.get(name, score_dict.get(f_key, 0.0))
        mapped_scores[name] = val

    sorted_features = sorted(mapped_scores.items(), key=lambda x: x[1], reverse=True)
    names, gains = zip(*sorted_features) if sorted_features else ([], [])

    plt.figure(figsize=(8, 6))
    y_pos = np.arange(len(names))
    plt.barh(y_pos, gains, align="center", color="#3498db")
    plt.yticks(y_pos, names)
    plt.gca().invert_yaxis()
    plt.xlabel("Average Gain")
    plt.title("XGBoost Feature Importance (Gain)")
    plt.grid(True, axis="x", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def evaluate_pipeline() -> Dict[str, Any]:
    """Execute end-to-end evaluation on the held-out spatial test set."""
    test_path = RAW_DATA_FILE.parent.parent / "processed" / "test.parquet"
    if not test_path.exists():
        raise FileNotFoundError(f"Test split not found at {test_path}. Run ml.train first.")

    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Calibrated model not found at {MODEL_FILE}. Run ml.calibrate first.")

    test_df = pd.read_parquet(test_path)
    X_test, y_test = build_features(test_df, return_target=True)
    y_true = y_test.values

    # Load models
    cal_model = joblib.load(MODEL_FILE)
    raw_model = joblib.load(RAW_MODEL_FILE)
    base_model = joblib.load(BASELINE_MODEL_FILE)

    # Predictions
    cal_probs = cal_model.predict_proba(X_test)[:, 1]
    raw_probs = raw_model.predict_proba(X_test)[:, 1]
    base_probs = base_model.predict_proba(X_test)[:, 1]

    # Metrics computation
    cal_pr_auc = float(average_precision_score(y_true, cal_probs))
    cal_roc_auc = float(roc_auc_score(y_true, cal_probs))
    cal_brier = float(brier_score_loss(y_true, cal_probs))
    cal_logloss = float(log_loss(y_true, cal_probs))
    cal_ece = compute_ece(y_true, cal_probs)

    raw_pr_auc = float(average_precision_score(y_true, raw_probs))
    raw_roc_auc = float(roc_auc_score(y_true, raw_probs))
    raw_brier = float(brier_score_loss(y_true, raw_probs))
    raw_logloss = float(log_loss(y_true, raw_probs))
    raw_ece = compute_ece(y_true, raw_probs)

    base_pr_auc = float(average_precision_score(y_true, base_probs))
    base_roc_auc = float(roc_auc_score(y_true, base_probs))
    base_brier = float(brier_score_loss(y_true, base_probs))
    base_logloss = float(log_loss(y_true, base_probs))
    base_ece = compute_ece(y_true, base_probs)

    # Risk band threshold evaluations
    low_band_metrics = calculate_threshold_metrics(y_true, cal_probs, RISK_LOW_THRESHOLD)
    high_band_metrics = calculate_threshold_metrics(y_true, cal_probs, RISK_HIGH_THRESHOLD)

    # Generate plots
    plot_reliability_curve(y_true, raw_probs, cal_probs, str(PLOTS_DIR / "reliability_curve.png"))
    plot_pr_and_roc_curves(
        y_true,
        cal_probs,
        base_probs,
        str(PLOTS_DIR / "pr_curve.png"),
        str(PLOTS_DIR / "roc_curve.png"),
    )
    plot_feature_importance(raw_model, MODEL_FEATURE_COLUMNS, str(PLOTS_DIR / "feature_importance.png"))

    metrics_payload = {
        "spatial_test_samples": len(y_true),
        "test_positives": int(np.sum(y_true)),
        "test_positive_rate": round(float(np.mean(y_true)), 4),
        "calibrated_model": {
            "pr_auc": round(cal_pr_auc, 4),
            "roc_auc": round(cal_roc_auc, 4),
            "brier_score": round(cal_brier, 4),
            "log_loss": round(cal_logloss, 4),
            "expected_calibration_error": round(cal_ece, 4),
        },
        "raw_model": {
            "pr_auc": round(raw_pr_auc, 4),
            "roc_auc": round(raw_roc_auc, 4),
            "brier_score": round(raw_brier, 4),
            "log_loss": round(raw_logloss, 4),
            "expected_calibration_error": round(raw_ece, 4),
        },
        "baseline_logistic_regression": {
            "pr_auc": round(base_pr_auc, 4),
            "roc_auc": round(base_roc_auc, 4),
            "brier_score": round(base_brier, 4),
            "log_loss": round(base_logloss, 4),
            "expected_calibration_error": round(base_ece, 4),
        },
        "risk_thresholds": {
            "low_risk_cutoff": RISK_LOW_THRESHOLD,
            "high_risk_cutoff": RISK_HIGH_THRESHOLD,
            "metrics_at_low_cutoff": low_band_metrics,
            "metrics_at_high_cutoff": high_band_metrics,
        },
    }

    # Save metrics.json
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved evaluation metrics to {METRICS_FILE}")

    # Save metadata.json
    metadata_payload = {
        "model_name": "FLOODRIX Calibrated Flood Hazard Predictor",
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "frameworks": {
            "xgboost_version": xgb.__version__,
            "scikit_learn_version": sklearn.__version__,
            "python_version": "3.11+",
        },
        "features": {
            "feature_order": MODEL_FEATURE_COLUMNS,
            "num_features": len(MODEL_FEATURE_COLUMNS),
            "flood_zone_mapping": FLOOD_ZONE_MAP,
        },
        "risk_bands": {
            "low": f"< {RISK_LOW_THRESHOLD}",
            "medium": f"{RISK_LOW_THRESHOLD} - {RISK_HIGH_THRESHOLD}",
            "high": f"> {RISK_HIGH_THRESHOLD}",
        },
        "calibration_note": (
            "Calibrated probabilities represent empirical flood occurrence frequency "
            "conditional on environmental indicators. Road closure and logistics rerouting decisions "
            "are governed by downstream risk engine constraints."
        ),
        "test_metrics": metrics_payload["calibrated_model"],
    }

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata_payload, f, indent=2)
    print(f"Saved model metadata to {METADATA_FILE}")

    print("\n=== Untouched Spatial Test Set Results ===")
    print(f"Calibrated XGBoost -> PR-AUC: {cal_pr_auc:.4f} | ROC-AUC: {cal_roc_auc:.4f} | Brier: {cal_brier:.4f} | ECE: {cal_ece:.4f}")
    print(f"Baseline Logistic  -> PR-AUC: {base_pr_auc:.4f} | ROC-AUC: {base_roc_auc:.4f} | Brier: {base_brier:.4f} | ECE: {base_ece:.4f}")
    print(f"Lift over baseline: +{(cal_pr_auc - base_pr_auc):.4f} PR-AUC")

    return metrics_payload


if __name__ == "__main__":
    evaluate_pipeline()
