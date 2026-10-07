"""Latency benchmark tests for high-throughput road segment batch predictions."""

import time
import pytest

from app.predictor import FloodPredictor
from app.schemas import SegmentInput


@pytest.fixture(scope="module")
def predictor():
    pred = FloodPredictor()
    pred.load()
    return pred


def generate_benchmark_batch(n_segments: int):
    return [
        SegmentInput(
            segment_id=f"bench_{i:04d}",
            latitude=9.2 + (i % 50) * 0.06,
            longitude=75.5 + (i % 30) * 0.05,
            rainfall_1h=float(10 + (i % 10)),
            rainfall_6h=float(30 + (i % 25)),
            rainfall_24h=float(80 + (i % 40)),
            elevation=float(5 + (i % 30)),
            historical_flood_frequency=i % 4,
            flood_zone="medium",
        )
        for i in range(n_segments)
    ]


@pytest.mark.parametrize("batch_size", [100, 500, 1000])
def test_batch_inference_latency(predictor, batch_size):
    segments = generate_benchmark_batch(batch_size)

    # Warmup
    for _ in range(3):
        predictor.predict_segments(segments)

    # Benchmark over multiple runs
    durations = []
    runs = 10
    for _ in range(runs):
        t0 = time.perf_counter()
        preds, reported_ms = predictor.predict_segments(segments)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations.append(elapsed_ms)
        assert len(preds) == batch_size

    mean_ms = sum(durations) / len(durations)
    min_ms = min(durations)
    print(f"\n[LATENCY BENCHMARK] Batch Size: {batch_size:4d} | Mean: {mean_ms:6.2f} ms | Min: {min_ms:6.2f} ms")

    # Target: 500 segments scored in single-digit ms or fast enough (< 25 ms in test suites on varied CPUs)
    if batch_size <= 500:
        assert min_ms < 25.0, f"Inference took {min_ms:.2f} ms for {batch_size} segments (expected < 25 ms)"
