from pathlib import Path

import numpy as np

import geomorphx.api as api
from core_py.geomorphx_core.rrim import rrim_plus_components


def test_rrim_plus_components_contract():
    dem = np.arange(400, dtype=np.float32).reshape(20, 20)
    comps = rrim_plus_components(dem, window=5)
    expected = {"baseline", "anisotropic", "roughness", "structural", "coherence", "orientation", "composite"}
    assert expected.issubset(set(comps.keys()))
    assert comps["composite"].shape == dem.shape


def test_generator_azimuths_are_not_consumed_before_processing():
    dem = np.random.default_rng(9).normal(size=(9, 11)).astype(np.float32)
    expected, _, _ = api.compute_rrim_array(dem, method="rrim_anisotropic", azimuth_deg=[0, 90])
    actual, _, _ = api.compute_rrim_array(dem, method="rrim_anisotropic", azimuth_deg=iter([0, 90]))
    np.testing.assert_allclose(actual, expected)


def test_compute_rrim_array_structural_multiscale_metadata():
    dem = np.arange(400, dtype=np.float32).reshape(20, 20)
    output, scales, metadata = api.compute_rrim_array(
        dem,
        method="rrim_structural_multiscale",
        scales=[5, 9],
        azimuth_deg=[0, 90],
    )
    assert output.shape == dem.shape
    assert scales == [5, 9]
    assert metadata["scales"] == [5, 9]
    assert metadata["azimuth_deg"] == [0.0, 90.0]


def test_compute_rrim_batch_with_mocks(tmp_path: Path, monkeypatch):
    dem_dir = tmp_path / "dems"
    out_dir = tmp_path / "out"
    dem_dir.mkdir(parents=True, exist_ok=True)
    (dem_dir / "a.tif").write_bytes(b"x")
    (dem_dir / "b.tiff").write_bytes(b"x")

    fake_dem = np.arange(100, dtype=np.float32).reshape(10, 10)

    def fake_read_dem(path):
        return fake_dem, {"driver": "GTiff", "count": 1}

    def fake_write_raster(path, data, profile):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fake-raster")

    monkeypatch.setattr(api, "read_dem", fake_read_dem)
    monkeypatch.setattr(api, "write_raster", fake_write_raster)

    outputs, manifest = api.compute_rrim_batch(
        dem_dir=dem_dir,
        out_dir=out_dir,
        method="rrim_plus",
        recursive=False,
        save_debug=True,
        window=5,
    )

    assert len(outputs) == 2
    assert manifest.exists()
