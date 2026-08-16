import numpy as np

from geomorphx.api import compute_rrim_array


def test_non_rrim_methods_return_expected_shape():
    dem = np.arange(400, dtype=np.float32).reshape(20, 20)
    methods = [
        "slope",
        "aspect",
        "hillshade",
        "multidirectional_hillshade",
        "positive_openness",
        "negative_openness",
        "sky_view_factor",
        "curvature_profile",
        "curvature_plan",
        "curvature_mean",
        "tpi",
        "tri",
        "wetness_proxy",
    ]
    for method in methods:
        out, _, _ = compute_rrim_array(dem, method=method, window=9, azimuth_deg=45)
        assert out.shape == dem.shape


def test_horizon_visualizations_on_flat_dem():
    dem = np.ones((15, 15), dtype=np.float32)
    positive, _, _ = compute_rrim_array(dem, method="positive_openness", window=9)
    negative, _, _ = compute_rrim_array(dem, method="negative_openness", window=9)
    svf, _, _ = compute_rrim_array(dem, method="sky_view_factor", window=9)
    assert np.allclose(positive, 90.0)
    assert np.allclose(negative, 90.0)
    assert np.allclose(svf, 1.0)


def test_positive_and_negative_openness_distinguish_peak():
    dem = np.zeros((15, 15), dtype=np.float32)
    dem[7, 7] = 10.0
    positive, _, _ = compute_rrim_array(dem, method="positive_openness", window=9)
    negative, _, _ = compute_rrim_array(dem, method="negative_openness", window=9)
    assert positive[7, 7] > negative[7, 7]
