from copy import deepcopy
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from cli.geomorphx_cli import main as cli_main
from geomorphx import execute_recipe, load_recipe, normalize_recipe, save_recipe
from geomorphx.recommendations import recommend
from geomorphx.validation import sha256_file
from geomorphx.methods import METHODS
from pathlib import Path


@pytest.fixture
def dem(tmp_path):
    path = tmp_path / "source.tif"
    with rasterio.open(path, "w", driver="GTiff", width=15, height=13, count=1,
                       dtype="float32", crs="EPSG:32718", transform=from_origin(0, 26, 2, 2), nodata=-9999) as dst:
        data = np.arange(195, dtype=np.float32).reshape(13, 15)
        data[3, 3] = -9999
        dst.write(data, 1)
    return path


def forms():
    entries = [{"method": "slope", "parameters": {"tile_size": 4}}, {"method": "tri_riley"}]
    return [
        {"format": "geomorphx-recipe", "schema_version": "1.0", "products": entries},
        {"schema_version": "1.0", "recommendations": entries},
        {"format": "geomorphx-workbench", "version": 1, "products": entries},
    ]


@pytest.mark.parametrize("recipe", forms())
def test_supported_formats_have_the_same_execution_and_manifest(recipe, dem, tmp_path):
    original = deepcopy(recipe)
    before = sha256_file(dem)
    outputs, manifest_path = execute_recipe(recipe, dem_path=dem, out_dir=tmp_path / "out")
    assert recipe == original
    assert sha256_file(dem) == before
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "complete"
    assert manifest["recipe"] == normalize_recipe(forms()[0])
    assert len(outputs) == 2
    for output, record in zip(outputs, manifest["outputs"]):
        assert record["sha256"] == sha256_file(output)
        with rasterio.open(output) as src:
            assert src.crs.to_epsg() == 32718
            assert np.isnan(src.read(1)[3, 3])


def test_normalization_is_idempotent_and_preserves_resolution_and_context():
    legacy = recommend("landforms", pixel_size_m=2, feature_min_m=4, feature_max_m=12)
    canonical = normalize_recipe(legacy)
    assert normalize_recipe(canonical) == canonical
    assert canonical["input_assumptions"] == legacy["input_assumptions"]
    assert canonical["metadata"]["objective"] == "landforms"
    assert canonical["products"][0]["role"] == legacy["recommendations"][0]["role"]
    canonical["products"][0]["parameters"]["window"] = 999
    assert legacy["recommendations"][0]["parameters"]["window"] != 999


def test_utf8_bom_load_and_canonical_save(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps(forms()[2]), encoding="utf-8-sig")
    output = save_recipe(load_recipe(path), tmp_path / "new.json")
    assert load_recipe(output) == normalize_recipe(forms()[0])
    assert json.loads(output.read_text())["format"] == "geomorphx-recipe"


def test_cli_runs_the_same_file_as_the_api_and_can_convert_legacy(dem, tmp_path):
    path = tmp_path / "panel.json"
    path.write_text(json.dumps(forms()[2]), encoding="utf-8")
    canonical = tmp_path / "portable.json"
    assert cli_main(["validate-recipe", "--recipe", str(path), "--out", str(canonical)]) == 0
    assert cli_main(["run-recipe", "--recipe", str(canonical), "--dem", str(dem), "--out-dir", str(tmp_path / "cli")]) == 0
    outputs, _ = execute_recipe(canonical, dem_path=dem, out_dir=tmp_path / "api")
    for output in outputs:
        with rasterio.open(output) as a, rasterio.open(tmp_path / "cli" / output.name) as b:
            np.testing.assert_equal(a.read(1), b.read(1))


def test_cli_recommend_exports_a_portable_recipe(tmp_path):
    path = tmp_path / "recommended.json"
    assert cli_main(["recommend", "--objective", "landforms", "--pixel-size-m", "2", "--out", str(path)]) == 0
    data = json.loads(path.read_text())
    assert data["format"] == "geomorphx-recipe"
    assert data["input_assumptions"]["pixel_size_m"] == 2


@pytest.mark.parametrize("recipe", [
    {"format": "geomorphx-recipe", "schema_version": "2.0", "products": [{"method": "slope"}]},
    {"format": "geomorphx-workbench", "version": True, "products": [{"method": "slope"}]},
    {"format": "geomorphx-recipe", "schema_version": "1.0", "products": [], "recommendations": [{"method": "slope"}]},
    {"schema_version": "1.0", "recommendations": [{"method": "slope", "parameters": {"window": True}}]},
    {"schema_version": "1.0", "recommendations": [{"method": "slope", "parameters": {"output": "outside.tif"}}]},
])
def test_bad_documents_fail_before_io(recipe, tmp_path):
    output = tmp_path / "out"
    with pytest.raises(ValueError):
        execute_recipe(recipe, dem_path=tmp_path / "does_not_exist.tif", out_dir=output)
    assert not output.exists()


def test_existing_outputs_are_rejected_without_modifying_any_file(dem, tmp_path):
    target = tmp_path / "out"
    target.mkdir()
    old = target / "02_tri_riley.tif"
    old.write_bytes(b"preserve old result")
    with pytest.raises(FileExistsError):
        execute_recipe(forms()[0], dem_path=dem, out_dir=target)
    assert old.read_bytes() == b"preserve old result"
    assert not (target / "01_slope.tif").exists()


def test_cancel_retains_completed_products_and_hashes(dem, tmp_path):
    progress = []
    outputs, manifest = execute_recipe(forms()[0], dem_path=dem, out_dir=tmp_path / "out",
                                       cancelled=lambda: bool(progress), progress=progress.append)
    report = json.loads(manifest.read_text())
    assert report["status"] == "cancelled"
    assert len(outputs) == 1 and report["outputs"][0]["sha256"] == sha256_file(outputs[0])
    assert progress == [50.]


def test_failure_manifest_retains_previously_completed_products(dem, tmp_path, monkeypatch):
    import geomorphx.recipes as recipes
    original = recipes.compute_rrim
    calls = []

    def compute(**kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            raise RuntimeError("synthetic failure")
        return original(**kwargs)

    monkeypatch.setattr(recipes, "compute_rrim", compute)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        execute_recipe(forms()[0], dem_path=dem, out_dir=tmp_path / "out")
    report = json.loads((tmp_path / "out/recipe_run_manifest.json").read_text())
    assert report["status"] == "failed" and report["error"] == "synthetic failure"
    assert len(report["outputs"]) == 1
    assert (tmp_path / "out/01_slope.tif").exists()


def test_shipped_example_and_schema_cover_the_public_catalogue(dem, tmp_path):
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "docs/recipe.schema.json").read_text())
    assert set(schema["properties"]["products"]["items"]["properties"]["method"]["enum"]) == set(METHODS)
    path = root / "examples/automation/terrain_recipe.json"
    outputs, manifest = execute_recipe(path, dem_path=dem, out_dir=tmp_path / "example")
    assert len(outputs) == 2 and json.loads(manifest.read_text())["status"] == "complete"


def test_parallel_runs_cannot_share_an_output_directory(dem, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    target = tmp_path / "out"

    def run():
        try:
            execute_recipe(forms()[0], dem_path=dem, out_dir=target)
            return "complete"
        except FileExistsError:
            return "already reserved"

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: run(), range(2)))
    assert sorted(results) == ["already reserved", "complete"]
    assert json.loads((target / "recipe_run_manifest.json").read_text())["status"] == "complete"
