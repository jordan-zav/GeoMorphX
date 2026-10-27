import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from geomorphx.recommendations import execute_recipe, recommend
from geomorphx.validation import inspect_dem, sha256_file


@pytest.fixture
def recipe_dem(tmp_path):
    source = tmp_path / "dem.tif"
    with rasterio.open(source, "w", driver="GTiff", count=1, width=13, height=11,
                       dtype="float32", crs="EPSG:32718", transform=from_origin(0, 22, 2, 2)) as dst:
        dst.write(np.arange(143, dtype=np.float32).reshape(11, 13), 1)
    return source


def test_recipe_checks_physical_pixel_size_before_creating_outputs(recipe_dem, tmp_path):
    recipe = recommend("general_relief", pixel_size_m=1)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match="does not match"):
        execute_recipe(recipe, dem_path=recipe_dem, out_dir=output)
    assert not output.exists()


@pytest.mark.parametrize("bad_entry", [
    {"method": "unknown"}, {"method": "slope", "parameters": {"window": 2}},
    {"method": "slope", "parameters": {"out_path": "override.tif"}},
    {"method": "rrim_multiscale", "parameters": {"scales": []}},
    {"method": "rrim_plus", "parameters": {"anisotropy_weight": 1}},
    {"method": "geomorphons", "parameters": {"flatness_deg": 0}},
    {"method": "hillshade", "parameters": {"azimuth_deg": "bad"}},
])
def test_entire_recipe_is_validated_before_first_output(recipe_dem, tmp_path, bad_entry):
    recipe = {"schema_version": "1.0", "recommendations": [{"method": "slope"}, bad_entry]}
    output = tmp_path / "out"
    with pytest.raises(ValueError):
        execute_recipe(recipe, dem_path=recipe_dem, out_dir=output)
    assert not output.exists()


def test_recipe_manifest_binds_actual_input_and_output_hashes(recipe_dem, tmp_path):
    recipe = recommend("drainage", pixel_size_m=2)
    outputs, manifest_path = execute_recipe(recipe, dem_path=recipe_dem, out_dir=tmp_path / "out")
    manifest = json.loads(manifest_path.read_text())
    source_info = manifest["input_validation"]
    assert source_info["sha256"] == sha256_file(recipe_dem)
    assert source_info["cell_size_m"] == [2, 2]
    assert source_info["shape"] == [11, 13]
    for output, item in zip(outputs, manifest["outputs"]):
        assert item["sha256"] == sha256_file(output)


def test_inspection_rejects_geographic_grids(tmp_path):
    source = tmp_path / "geographic.tif"
    with rasterio.open(source, "w", driver="GTiff", count=1, width=3, height=3,
                       dtype="float32", crs="EPSG:4326", transform=from_origin(0, 10, .1, .1)) as dst:
        dst.write(np.zeros((3, 3), dtype=np.float32), 1)
    with pytest.raises(ValueError, match="projected"):
        inspect_dem(source)
