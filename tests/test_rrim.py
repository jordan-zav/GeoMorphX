import numpy as np
import pytest

from core_py.geomorphx_core.rrim import (
    rrim_anisotropic,
    rrim_anisotropic_multiscale,
    rrim_baseline,
    rrim_multiscale,
    rrim_plus,
    rrim_structural,
    rrim_structural_multiscale,
)


def _demo_dem(size: int = 64) -> np.ndarray:
    x = np.linspace(0.0, 4.0 * np.pi, size, dtype=np.float32)
    y = np.linspace(0.0, 4.0 * np.pi, size, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    return (np.sin(xx) + np.cos(yy) + 0.2 * np.sin(xx + yy)).astype(np.float32)


def test_rrim_baseline_shape_and_range():
    dem = np.array([[1, 2, 3], [2, 3, 4], [3, 4, 5]], dtype=np.float32)
    out = rrim_baseline(dem, window=3)
    assert out.shape == dem.shape
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_rrim_multiscale_shape():
    dem = np.arange(100, dtype=np.float32).reshape(10, 10)
    out = rrim_multiscale(dem, scales=[5, 9, 15])
    assert out.shape == dem.shape


def test_rrim_anisotropic_changes_with_azimuth():
    dem = _demo_dem()
    out_0 = rrim_anisotropic(dem, window=5, azimuth_deg=0.0)
    out_90 = rrim_anisotropic(dem, window=5, azimuth_deg=90.0)
    assert out_0.shape == dem.shape
    assert out_90.shape == dem.shape
    assert float(np.mean(np.abs(out_0 - out_90))) > 1e-4


def test_rrim_anisotropic_multiscale_shape_and_range():
    dem = _demo_dem()
    out = rrim_anisotropic_multiscale(dem, scales=[5, 9, 15], azimuth_deg=30)
    assert out.shape == dem.shape
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_rrim_structural_shape_and_range():
    dem = _demo_dem()
    out = rrim_structural(dem, window=7, azimuth_deg=45)
    assert out.shape == dem.shape
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_rrim_structural_multiscale_accepts_multiple_orientations():
    dem = _demo_dem()
    out = rrim_structural_multiscale(
        dem,
        scales=[5, 9, 15],
        azimuth_deg=[0, 45, 90, 135],
    )
    assert out.shape == dem.shape
    assert out.dtype == np.float32
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_rrim_structural_multiscale_requires_scale():
    with pytest.raises(ValueError, match="at least one scale"):
        rrim_structural_multiscale(_demo_dem(), scales=[])


def test_rrim_plus_shape_and_normalized_range():
    dem = np.arange(400, dtype=np.float32).reshape(20, 20)
    out = rrim_plus(dem, window=5, azimuth_deg=35)
    assert out.shape == dem.shape
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_rrim_plus_rejects_invalid_weight_sum():
    dem = np.arange(100, dtype=np.float32).reshape(10, 10)
    with pytest.raises(ValueError):
        rrim_plus(dem, anisotropy_weight=0.5, roughness_weight=0.4, structural_weight=0.2)
