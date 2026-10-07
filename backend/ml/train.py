"""Model training module: Logistic Regression baseline and tuned XGBoost with monotone constraints."""

import json
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from ml.config import (
    BASELINE_MODEL_FILE,
    MODEL_FEATURE_COLUMNS,
    MONOTONE_CONSTRAINTS,
    RANDOM_SEED,
    RAW_DATA_FILE,
    RAW_MODEL_FILE,
    TARGET_COLUMN,
)
from ml.data_prep import build_features, calculate_class_balance, load_raw_data, validate_data
from ml.generate_synthetic import generate_synthetic_flood_data
from ml.split import create_spatial_groups, spatial_train_cal_test_split


def build_monotone_constraints_tuple(feature_names: list[str]) -> tuple[int, ...]:
    """Build monotone constraints tuple aligned with feature column order."""
    return tuple(MONOTONE_CONSTRAINTS.get(col, 0) for col in feature_names)


def train_baseline_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> Pipeline:
    """Train standard Logistic Regression baseline with StandardScaler."""
    baseline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", random_state=RANDOM_SEED, max_iter=1000)),
    ])
    baseline.fit(X_train, y_train)

    val_probs = baseline.predict_proba(X_val)[:, 1]
    val_pr_auc = average_precision_score(y_val, val_probs)
    val_roc_auc = roc_auc_score(y_val, val_probs)

    print(f"--- Baseline Logistic Regression ---")
    print(f"Validation PR-AUC: {val_pr_auc:.4f} | ROC-AUC: {val_roc_auc:.4f}")
    return baseline


def tune_xgboost_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    groups_train: pd.Series,
    scale_pos_weight: float,
    monotone_constraints: tuple[int, ...],
    n_trials: int = 15,
) -> Dict[str, Any]:
    """Tune XGBoost hyperparameters with Optuna using grouped cross-validation."""
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    gkf = GroupKFold(n_splits=4)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "tree_method": "hist",
            "scale_pos_weight": scale_pos_weight,
            "monotone_constraints": monotone_constraints,
            "random_state": RANDOM_SEED,
            "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 7),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.65, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.65, 0.95),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 8),
            "gamma": trial.suggest_float("gamma", 0.0, 3.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 10.0, log=True),
        }

        scores = []
        for train_fold_idx, val_fold_idx in gkf.split(X_train, y_train, groups=groups_train):
            X_tr, y_tr = X_train.iloc[train_fold_idx], y_train.iloc[train_fold_idx]
            X_v, y_v = X_train.iloc[val_fold_idx], y_train.iloc[val_fold_idx]

            clf = xgb.XGBClassifier(**params)
            clf.fit(X_tr, y_tr, verbose=False)

            preds = clf.predict_proba(X_v)[:, 1]
            score = average_precision_score(y_v, preds)
            scores.append(score)

        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objective, n_trials=n_trials)

    print(f"Best Optuna Trial CV PR-AUC: {study.best_value:.4f}")
    print(f"Best hyperparameters: {study.best_params}")
    return study.best_params


def train_pipeline(
    n_optuna_trials: int = 15,
) -> Tuple[xgb.XGBClassifier, Pipeline, Dict[str, Any]]:
    """Execute complete model training workflow: ingestion, split, baseline, tuning, XGBoost fit."""
    # 1. Ingestion / fallback creation
    if not RAW_DATA_FILE.exists():
        print(f"No raw data found at {RAW_DATA_FILE}. Generating synthetic dataset...")
        generate_synthetic_flood_data()

    raw_df = load_raw_data()
    validated_df = validate_data(raw_df, is_training=True)

    # 2. Spatial group splitting
    train_df, cal_df, test_df = spatial_train_cal_test_split(validated_df)

    # Save split dataframes for calibration and evaluation stages
    train_df.to_parquet(validated_df.attrs.get("train_path", RAW_DATA_FILE.parent.parent / "processed" / "train.parquet"))
    cal_df.to_parquet(RAW_DATA_FILE.parent.parent / "processed" / "cal.parquet")
    test_df.to_parquet(RAW_DATA_FILE.parent.parent / "processed" / "test.parquet")

    # 3. Feature building
    X_train, y_train = build_features(train_df, return_target=True)
    X_cal, y_cal = build_features(cal_df, return_target=True)
    X_test, y_test = build_features(test_df, return_target=True)

    class_stats = calculate_class_balance(y_train)
    scale_pos_weight = class_stats["scale_pos_weight"]
    print(f"Train Class stats: {class_stats}")

    # 4. Train Baseline Logistic Regression
    baseline_model = train_baseline_model(X_train, y_train, X_cal, y_cal)
    joblib.dump(baseline_model, BASELINE_MODEL_FILE)
    print(f"Saved baseline model to {BASELINE_MODEL_FILE}")

    # 5. Monotone constraints
    monotone_constraints = build_monotone_constraints_tuple(MODEL_FEATURE_COLUMNS)

    # 6. Optuna hyperparameter tuning
    groups_train = train_df["group_id"]
    best_params = tune_xgboost_optuna(
        X_train,
        y_train,
        groups_train,
        scale_pos_weight=scale_pos_weight,
        monotone_constraints=monotone_constraints,
        n_trials=n_optuna_trials,
    )

    # 7. Final XGBoost model training on full train split
    final_params = {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "scale_pos_weight": scale_pos_weight,
        "monotone_constraints": monotone_constraints,
        "random_state": RANDOM_SEED,
        **best_params,
    }

    raw_model = xgb.XGBClassifier(**final_params)
    raw_model.fit(
        X_train,
        y_train,
        eval_set=[(X_cal, y_cal)],
        verbose=False,
    )

    # Evaluate raw XGBoost on calibration set
    cal_raw_probs = raw_model.predict_proba(X_cal)[:, 1]
    raw_cal_pr_auc = average_precision_score(y_cal, cal_raw_probs)
    raw_cal_roc_auc = roc_auc_score(y_cal, cal_raw_probs)
    print(f"--- Raw XGBoost Model (Pre-Calibration) ---")
    print(f"Calibration set PR-AUC: {raw_cal_pr_auc:.4f} | ROC-AUC: {raw_cal_roc_auc:.4f}")

    joblib.dump(raw_model, RAW_MODEL_FILE)
    print(f"Saved raw XGBoost model to {RAW_MODEL_FILE}")

    return raw_model, baseline_model, {
        "class_stats": class_stats,
        "best_params": best_params,
        "raw_cal_pr_auc": float(raw_cal_pr_auc),
        "raw_cal_roc_auc": float(raw_cal_roc_auc),
    }


if __name__ == "__main__":
    train_pipeline()
