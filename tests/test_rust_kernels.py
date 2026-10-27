import numpy as np
import pytest

try:
    from geomorphx import geomorphx_core_rs
    HAS_RUST = True
except ImportError:
    HAS_RUST = False

# Copy Python implementations for baseline comparison
def python_local_relief(dem: np.ndarray, window: int) -> np.ndarray:
    radius = max(1, window // 2)
    padded = np.pad(dem, pad_width=radius, mode="edge")
    out = np.zeros_like(dem, dtype=np.float32)
    for r in range(dem.shape[0]):
        for c in range(dem.shape[1]):
            block = padded[r : r + 2 * radius + 1, c : c + 2 * radius + 1]
            out[r, c] = float(np.max(block) - np.min(block))
    return out


def python_local_std(dem: np.ndarray, window: int) -> np.ndarray:
    radius = max(1, window // 2)
    padded = np.pad(dem, pad_width=radius, mode="edge")
    out = np.zeros_like(dem, dtype=np.float32)
    for r in range(dem.shape[0]):
        for c in range(dem.shape[1]):
            block = padded[r : r + 2 * radius + 1, c : c + 2 * radius + 1]
            out[r, c] = float(np.std(block))
    return out


def python_local_mean(values: np.ndarray, window: int) -> np.ndarray:
    radius = max(1, window // 2)
    padded = np.pad(values, pad_width=radius, mode="edge")
    out = np.zeros_like(values, dtype=np.float32)
    for r in range(values.shape[0]):
        for c in range(values.shape[1]):
            block = padded[r : r + 2 * radius + 1, c : c + 2 * radius + 1]
            out[r, c] = float(np.mean(block))
    return out


def python_directional_gradient_response(dem: np.ndarray, azimuth_deg: float) -> np.ndarray:
    import math
    gy, gx = np.gradient(dem.astype(np.float32))
    theta = math.radians(float(azimuth_deg) % 360.0)
    ux = math.cos(theta)
    uy = math.sin(theta)
    return np.abs(gx * ux + gy * uy).astype(np.float32)


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
def test_rust_local_relief_matches_python():
    np.random.seed(42)
    dem = np.random.rand(50, 50).astype(np.float32) * 100.0
    for w in [3, 5, 9]:
        py_res = python_local_relief(dem, w)
        rs_res = geomorphx_core_rs.local_relief_rs(dem, w)
        np.testing.assert_allclose(rs_res, py_res, rtol=1e-5, atol=1e-5)


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
def test_rust_local_std_matches_python():
    np.random.seed(42)
    dem = np.random.rand(50, 50).astype(np.float32) * 100.0
    for w in [3, 5, 9]:
        py_res = python_local_std(dem, w)
        rs_res = geomorphx_core_rs.local_std_rs(dem, w)
        np.testing.assert_allclose(rs_res, py_res, rtol=1e-4, atol=1e-4)


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
def test_rust_local_mean_matches_python():
    np.random.seed(42)
    dem = np.random.rand(50, 50).astype(np.float32) * 100.0
    for w in [3, 5, 9]:
        py_res = python_local_mean(dem, w)
        rs_res = geomorphx_core_rs.local_mean_rs(dem, w)
        np.testing.assert_allclose(rs_res, py_res, rtol=1e-5, atol=1e-5)


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
def test_rust_directional_gradient_matches_python():
    np.random.seed(42)
    dem = np.random.rand(50, 50).astype(np.float32) * 100.0
    for az in [0.0, 45.0, 90.0, 135.0, 270.0]:
        py_res = python_directional_gradient_response(dem, az)
        rs_res = geomorphx_core_rs.directional_gradient_response_rs(dem, az)
        np.testing.assert_allclose(rs_res, py_res, rtol=1e-5, atol=1e-5)


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
@pytest.mark.parametrize("name", ["local_mean_rs", "local_std_rs", "local_relief_rs"])
def test_native_kernels_validate_windows_and_propagate_nodata(name):
    kernel = getattr(geomorphx_core_rs, name)
    with pytest.raises(ValueError):
        kernel(np.zeros((3, 3), dtype=np.float32), 4)
    with pytest.raises(ValueError):
        kernel(np.zeros((0, 3), dtype=np.float32), 3)
    dem = np.zeros((5, 5), dtype=np.float32)
    dem[2, 2] = np.nan
    out = kernel(dem, 3)
    assert np.isnan(out[1:4, 1:4]).all()
    assert out[0, 0] == 0


@pytest.mark.skipif(not HAS_RUST, reason="Rust extension not built")
@pytest.mark.parametrize("statistic", ["mean", "std"])
def test_native_focal_statistics_preserve_small_relief_at_large_elevation(statistic):
    dem = (1_000_000 + np.random.default_rng(4).integers(-8, 9, size=(17, 19)) / 4).astype(np.float32)
    blocks = np.lib.stride_tricks.sliding_window_view(np.pad(dem, 4, mode="edge"), (9, 9))
    operation = np.mean if statistic == "mean" else np.std
    expected = operation(blocks, axis=(-2, -1), dtype=np.float64).astype(np.float32)
    actual = getattr(geomorphx_core_rs, f"local_{statistic}_rs")(dem, 9)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-6)
