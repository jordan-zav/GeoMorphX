import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from core_py.geomorphx_core.io import read_dem
from geomorphx.api import compute_rrim, compute_rrim_array
from geomorphx.methods import METHODS
from geomorphx.streaming import compute_rrim_streamed


@pytest.mark.parametrize("method", [m for m in METHODS if m.startswith("rrim_")])
@pytest.mark.parametrize("kind", ["relief_with_hole", "constant_with_hole", "all_nodata"])
def test_streamed_rrim_matches_full_grid_across_tiles_and_edges(tmp_path, method, kind):
    source, target = tmp_path / "dem.tif", tmp_path / "out.tif"
    dem = np.random.default_rng(236).normal(size=(19, 23)).astype(np.float32)
    if kind == "constant_with_hole":
        dem[:] = 500
    elif kind == "all_nodata":
        dem[:] = np.nan
    dem[7, 10] = np.nan
    with rasterio.open(
        source, "w", driver="GTiff", count=1, dtype="float32", width=23, height=19,
        crs="EPSG:32718", transform=from_origin(0, 100, 2, 3), nodata=np.nan,
    ) as dst:
        dst.write(dem, 1)
    kwargs = dict(method=method, window=5, scales=[3, 7], azimuth_deg=[0, 37, 90])
    expected, expected_scales, _ = compute_rrim_array(dem, **kwargs)
    compute_rrim(source, target, tile_size=6, **kwargs)
    actual, profile = read_dem(target)
    np.testing.assert_allclose(actual, expected, equal_nan=True, atol=3e-6, rtol=3e-6)
    assert profile["transform"] == from_origin(0, 100, 2, 3)
    metadata = json.loads(target.with_suffix(".tif.meta.json").read_text())
    assert metadata["scales"] == expected_scales
    params = metadata["parameters"]
    assert params["processing_mode"] == "windowed_global_normalization"
    assert max(params["max_read_shape"]) <= 6 + 7 // 2 * 2
    manifest = json.loads(Path(params["pipeline_manifest"]).read_text())
    assert manifest["status"] == "complete"
    assert manifest["scratch_retained"]


def test_streamed_rrim_never_reads_the_full_input_or_uses_full_grid_fallback(tmp_path, monkeypatch):
    source, target = tmp_path / "dem.tif", tmp_path / "out.tif"
    with rasterio.open(
        source, "w", driver="GTiff", count=1, dtype="float32", width=41, height=37,
        crs="EPSG:32718", transform=from_origin(0, 100, 1, 1),
    ) as dst:
        dst.write(np.random.default_rng(94).normal(size=(37, 41)).astype(np.float32), 1)
    original_open = rasterio.open
    reads = []

    class WindowedSource:
        def __init__(self, ds):
            self.ds = ds

        def __getattr__(self, key):
            return getattr(self.ds, key)

        def __enter__(self):
            self.ds.__enter__()
            return self

        def __exit__(self, *args):
            return self.ds.__exit__(*args)

        def read(self, *args, **kwargs):
            window = kwargs.get("window")
            assert window is not None
            assert window.width <= 8 + 6 and window.height <= 8 + 6
            reads.append(window)
            return self.ds.read(*args, **kwargs)

    def tracked_open(path, *args, **kwargs):
        ds = original_open(path, *args, **kwargs)
        return WindowedSource(ds) if Path(path).resolve() == source.resolve() else ds

    monkeypatch.setattr(rasterio, "open", tracked_open)
    import geomorphx.tiling as tiling
    monkeypatch.setattr(tiling, "read_dem", lambda *a: pytest.fail("Full-grid fallback was used"))
    compute_rrim(source, target, method="rrim_plus", window=7, tile_size=8)
    assert len(reads) > 1


def test_streaming_rejects_invalid_scales_before_creating_scratch(tmp_path):
    with pytest.raises(ValueError, match="at least one scale"):
        compute_rrim_streamed(tmp_path / "missing.tif", tmp_path / "out.tif",
                              method="rrim_multiscale", scales=[], scratch_dir=tmp_path)
    assert not list(tmp_path.iterdir())
