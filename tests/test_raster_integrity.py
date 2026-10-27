import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from core_py.geomorphx_core.io import read_dem
from geomorphx.api import compute_rrim, compute_rrim_array, compute_rrim_batch
from geomorphx.methods import GLOBAL_METHODS, METHODS
from geomorphx.tiling import compute_tiled


def make_dem(path, data, *, nodata=None, crs="EPSG:32718"):
    with rasterio.open(
        path, "w", driver="GTiff", width=data.shape[1], height=data.shape[0],
        count=1, dtype="float32", transform=from_origin(500000, 9000000, 2, 3),
        crs=crs, nodata=nodata,
    ) as dst:
        dst.write(data.astype(np.float32), 1)


@pytest.mark.parametrize("method", [m for m in METHODS if m not in GLOBAL_METHODS])
def test_local_tiles_equal_whole_raster_including_edges_and_nodata(tmp_path, method):
    data = np.random.default_rng(2).normal(size=(17, 19)).astype(np.float32)
    data[8, 9] = -9999
    source, full, tiled = (tmp_path / n for n in ("dem.tif", "full.tif", "tile.tif"))
    make_dem(source, data, nodata=-9999)
    window = 9 if method.startswith("geomorphon") else 3
    compute_rrim(source, full, method=method, window=window)
    compute_rrim(source, tiled, method=method, window=window, tile_size=4)
    expected, _ = read_dem(full)
    actual, _ = read_dem(tiled)
    np.testing.assert_allclose(actual, expected, equal_nan=True, rtol=1e-6, atol=1e-6)
    assert np.isnan(actual[8, 9])


@pytest.mark.parametrize("method", ["flow_accumulation_d8"])
def test_global_tiles_use_explicit_equivalent_fallback(tmp_path, method):
    source, full, tiled = (tmp_path / n for n in ("dem.tif", "full.tif", "tile.tif"))
    make_dem(source, np.random.default_rng(3).normal(size=(13, 15)))
    compute_rrim(source, full, method=method, scales=[3, 5])
    with pytest.warns(RuntimeWarning, match="global context"):
        compute_rrim(source, tiled, method=method, scales=iter([3, 5]), tile_size=4)
    np.testing.assert_allclose(read_dem(tiled)[0], read_dem(full)[0], equal_nan=True)
    meta = json.loads(tiled.with_suffix(".tif.meta.json").read_text())
    assert meta["parameters"]["processing_mode"] == "full_grid_fallback"


def test_metric_slope_aspect_and_illumination():
    dem = np.tile(np.arange(5, dtype=np.float32) * 2, (5, 1))
    slope, _, _ = compute_rrim_array(dem, method="slope", cell_size=(3, 2))
    aspect, _, _ = compute_rrim_array(dem, method="aspect", cell_size=(3, 2))
    np.testing.assert_allclose(slope, 45)
    np.testing.assert_allclose(aspect, 270)
    from core_py.geomorphx_core.terrain import hillshade
    flat = np.zeros((5, 5))
    np.testing.assert_allclose(hillshade(flat, altitude_deg=30), 127.5, rtol=1e-6)
    assert hillshade(dem, azimuth_deg=270).mean() > hillshade(dem, azimuth_deg=90).mean()


def test_missing_data_and_empty_range_have_valid_json(tmp_path):
    source, target = tmp_path / "dem.tif", tmp_path / "out.tif"
    make_dem(source, np.full((5, 5), -9999), nodata=-9999)
    compute_rrim(source, target, method="rrim_baseline")
    data, profile = read_dem(target)
    assert np.isnan(data).all()
    assert np.isnan(profile["nodata"])
    meta = json.loads(target.with_suffix(".tif.meta.json").read_text())
    assert meta["value_range"] == [None, None]


def test_geographic_derivatives_and_destructive_outputs_are_rejected(tmp_path):
    source = tmp_path / "dem.tif"
    make_dem(source, np.zeros((5, 5)), crs="EPSG:4326")
    with pytest.raises(ValueError, match="projected CRS"):
        compute_rrim(source, tmp_path / "slope.tif", method="slope")
    with pytest.raises(ValueError, match="different files"):
        compute_rrim(source, source)
    with pytest.raises(ValueError, match="different files"):
        compute_tiled(source, source, method="slope")
    with pytest.raises(ValueError, match="must not contain"):
        compute_rrim_batch(tmp_path, tmp_path)


def test_nested_batch_output_is_not_reprocessed(tmp_path):
    source = tmp_path / "dem.tif"
    make_dem(source, np.ones((5, 5)))
    output = tmp_path / "derived"
    compute_rrim_batch(tmp_path, output, method="tri_riley")
    outputs, _ = compute_rrim_batch(tmp_path, output, method="tri_riley")
    assert len(outputs) == 1
