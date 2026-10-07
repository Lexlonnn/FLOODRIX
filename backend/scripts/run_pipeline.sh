#!/usr/bin/env bash
set -e

# Change directory to backend root
cd "$(dirname "$0")/.."

echo "=========================================================="
echo "FLOODRIX ML Pipeline: Ingestion -> Train -> Calibrate -> Evaluate"
echo "=========================================================="

if [ -d ".venv" ]; then
    PYTHON_EXEC="./.venv/bin/python"
else
    PYTHON_EXEC="python"
fi

export PYTHONPATH="."

echo "[1/3] Running Model Training & Hyperparameter Tuning..."
$PYTHON_EXEC -m ml.train

echo "[2/3] Running Probability Calibration on Unseen Spatial Set..."
$PYTHON_EXEC -m ml.calibrate

echo "[3/3] Running Evaluation on Untouched Spatial Test Set & Generating Plots..."
$PYTHON_EXEC -m ml.evaluate

echo "=========================================================="
echo "ML Pipeline Complete!"
echo "Model artifact:    ml/artifacts/model.joblib"
echo "Metadata:          ml/artifacts/metadata.json"
echo "Evaluation:        ml/artifacts/metrics.json"
echo "Plots:             ml/artifacts/plots/"
echo "=========================================================="
