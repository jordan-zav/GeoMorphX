from pathlib import Path

import pytest

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
    outputs, manifest = execute_recipe(recipe, dem_path="input.tif", out_dir=tmp_path)

    assert len(outputs) == 4
    assert manifest.exists()
    assert calls[0]["method"] == "positive_openness"
    assert calls[0]["window"] == 7
    assert calls[1]["method"] == "rrim_multiscale"
    assert calls[1]["scales"] == [3, 7, 9]
