import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from core_py.geomorphx_core.io import read_dem
from geomorphx.api import compute_rrim_array
from geomorphx.blocks import (
    compute_curvature_block, compute_tpi_wetness_block,
    compute_geomorphons_legacy_block, compute_geomorphons_block,
)


@pytest.fixture
def block_dem(tmp_path):
    source = tmp_path / "source.tif"
    dem = np.random.default_rng(71).normal(size=(19, 21)).astype(np.float32)
    dem[8, 8] = -9999
    with rasterio.open(
        source, "w", driver="GTiff", count=1, height=19, width=21,
        dtype="float32", nodata=-9999, crs="EPSG:32718",
        transform=from_origin(500000, 9000000, 2, 3),
    ) as dst:
        dst.write(dem, 1)
    return source


@pytest.mark.parametrize("block,methods", [
    ("curvature", ["curvature_profile", "curvature_plan", "curvature_mean"]),
    ("tpi", ["tpi", "tpi", "wetness_proxy"]),
    ("geomorphons", ["geomorphons", "geomorphon_ternary"]),
])
def test_shared_blocks_equal_core_results_with_georeference_and_metadata(block_dem, tmp_path, block, methods):
    targets = [tmp_path / f"{i}.tif" for i in range(len(methods))]
    windows = [9] * len(methods)
    if block == "curvature":
        compute_curvature_block(block_dem, *targets)
    elif block == "tpi":
        windows = [3, 5, 3]
        compute_tpi_wetness_block(block_dem, *targets, window_small=3, window_large=5)
    else:
        compute_geomorphons_block(block_dem, *targets)
    dem, profile = read_dem(block_dem)
    for target, method, window in zip(targets, methods, windows):
        actual, output_profile = read_dem(target)
        expected, _, _ = compute_rrim_array(dem, method=method, window=window, cell_size=(3, 2))
        np.testing.assert_allclose(actual, expected, equal_nan=True)
        assert output_profile["transform"] == profile["transform"]
        assert output_profile["crs"] == profile["crs"]
        assert json.loads(target.with_suffix(".tif.meta.json").read_text())["method"] == method


def test_legacy_block_preserves_integer_categories_and_nodata(block_dem, tmp_path):
    classes, confidence = tmp_path / "class.tif", tmp_path / "conf.tif"
    compute_geomorphons_legacy_block(block_dem, classes, confidence, radius=2)
    with rasterio.open(classes) as src:
        assert src.dtypes == ("int16",)
        assert src.nodata == -32768
        assert src.read(1, masked=True).mask[8, 8]
    assert np.isnan(read_dem(confidence)[0][8, 8])


def test_block_rejects_colliding_paths_before_writing(block_dem, tmp_path):
    original = block_dem.read_bytes()
    with pytest.raises(ValueError, match="distinct"):
        compute_curvature_block(block_dem, tmp_path / "a.tif", block_dem, tmp_path / "b.tif")
    assert block_dem.read_bytes() == original
    assert not (tmp_path / "a.tif").exists()
