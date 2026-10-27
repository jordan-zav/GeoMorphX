from pathlib import Path

import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

import geomorphx.recommendations as recommendations
from geomorphx.recommendations import available_objectives, execute_recipe, recommend


def test_recommendation_calibrates_scales_in_physical_units():
    recipe = recommend(
        "microtopography",
        pixel_size_m=0.5,
        feature_min_m=2.0,
        feature_max_m=10.0,
    )
    assert recipe["scale_windows_px"] == [5, 13, 21]
    assert recipe["recommendations"][0]["method"] == "positive_openness"
    assert recipe["recommendations"][0]["parameters"]["window"] == 13
    assert recipe["recommendations"][1]["parameters"]["scales"] == [5, 13, 21]


def test_recommendation_defaults_and_objective_contract():
    recipe = recommend("lineaments", pixel_size_m=1.0)
    assert "lineaments" in available_objectives()
    assert recipe["scale_windows_px"] == [5, 15, 45]
    assert recipe["recommendations"][0]["method"] == "rrim_structural_multiscale"


def test_equal_feature_sizes_generate_a_single_valid_window():
    recipe = recommend("microtopography", pixel_size_m=1, feature_min_m=5, feature_max_m=5)
    assert recipe["scale_windows_px"] == [5]
    assert recipe["recommendations"][0]["parameters"]["window"] == 5


def test_hydrology_recipe_contains_real_accumulation_and_twi():
    recipe = recommend("hydrology", pixel_size_m=2)
    assert [r["method"] for r in recipe["recommendations"]] == [
        "fill_depressions", "flow_accumulation_d8", "twi_d8",
    ]


def test_landform_recipe_respects_minimum_diagonal_search_size():
    recipe = recommend("landforms", pixel_size_m=2, feature_min_m=1, feature_max_m=1)
    assert recipe["recommendations"][0]["method"] == "geomorphons"
    assert recipe["recommendations"][0]["parameters"]["window"] == 7


@pytest.mark.parametrize("kwargs", [
    {"pixel_size_m": 0.0},
    {"pixel_size_m": 1.0, "feature_min_m": 2.0},
    {"pixel_size_m": 1.0, "feature_min_m": 4.0, "feature_max_m": 2.0},
])
def test_recommendation_rejects_invalid_scale_inputs(kwargs):
    with pytest.raises(ValueError):
        recommend("general_relief", **kwargs)


def test_execute_recipe_writes_manifest_and_uses_explicit_parameters(tmp_path: Path, monkeypatch):
    calls = []

    def fake_compute_rrim(**kwargs):
        calls.append(kwargs)
        output = Path(kwargs["out_path"])
        output.write_bytes(b"raster")
        return output

    monkeypatch.setattr(recommendations, "compute_rrim", fake_compute_rrim)
    recipe = recommend("microtopography", pixel_size_m=1.0, feature_min_m=3.0, feature_max_m=9.0)
    source = tmp_path / "input.tif"
    with rasterio.open(source, "w", driver="GTiff", count=1, height=11, width=11,
                       dtype="float32", crs="EPSG:32718", transform=from_origin(0, 11, 1, 1)) as dst:
        dst.write(np.zeros((11, 11), dtype=np.float32), 1)
    outputs, manifest = execute_recipe(recipe, dem_path=source, out_dir=tmp_path)

    assert len(outputs) == 4
    assert manifest.exists()
    assert calls[0]["method"] == "positive_openness"
    assert calls[0]["window"] == 7
    assert calls[1]["method"] == "rrim_multiscale"
    assert calls[1]["scales"] == [3, 7, 9]
