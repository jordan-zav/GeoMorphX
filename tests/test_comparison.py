import numpy as np
import pytest

from geomorphx.comparison import calculate_entropy, compare_rasters, generate_comparison_report


def test_comparison_metrics():
    np.random.seed(42)
    r1 = np.random.rand(20, 20).astype(np.float32)
    r2 = r1 + np.random.normal(0, 0.05, (20, 20)).astype(np.float32)

    metrics = compare_rasters(r1, r2, "R1", "R2")
    assert metrics["num_pixels"] == 400
    assert 0.8 < metrics["pearson_correlation"] <= 1.0
    assert metrics["mean_absolute_difference"] > 0
    assert "R1" in metrics["entropy"]
    assert "R2" in metrics["entropy"]

    report = generate_comparison_report(metrics, "R1", "R2")
    assert "Correlación de Pearson" in report
    assert "R1" in report
    assert "R2" in report
