import itertools

import numpy as np
import pytest

from core_py.geomorphx_core.geomorphons import (
    DIRECTIONS, _canonical_codes, geomorphon_components, geomorphons,
    geomorphons_simplified,
)
from geomorphx.api import compute_rrim_array


@pytest.mark.parametrize("neg,pos,expected", [
    (0, 0, 1), (8, 0, 2), (6, 0, 3), (3, 0, 4), (5, 2, 5),
    (3, 3, 6), (2, 4, 7), (0, 3, 8), (0, 6, 9), (0, 8, 10),
])
def test_all_ten_forms_from_constructed_visibility_profiles(neg, pos, expected):
    dem = np.zeros((13, 13), dtype=np.float32)
    signs = [-1] * neg + [1] * pos + [0] * (8 - neg - pos)
    for sign, (dr, dc) in zip(signs, DIRECTIONS):
        dem[6 + dr, 6 + dc] = sign * 2
        dem[6 + 2 * dr, 6 + 2 * dc] = sign * 3
    components = geomorphon_components(dem, radius=4)
    assert components["positive_count"][6, 6] == pos
    assert components["negative_count"][6, 6] == neg
    assert components["forms"][6, 6] == expected


def test_canonical_patterns_have_498_rotation_and_reflection_classes():
    table = _canonical_codes()
    assert len(np.unique(table)) == 498
    for digits in itertools.product(range(3), repeat=8):
        code = sum(value * 3 ** i for i, value in enumerate(digits))
        rotated = digits[1:] + digits[:1]
        reflected = digits[::-1]
        assert table[code] == table[sum(v * 3 ** i for i, v in enumerate(rotated))]
        assert table[code] == table[sum(v * 3 ** i for i, v in enumerate(reflected))]


def test_forms_and_patterns_are_rotation_invariant_on_square_grid():
    dem = np.random.default_rng(34).normal(size=(21, 21))
    before = geomorphon_components(dem)
    after = geomorphon_components(np.rot90(dem))
    for key in before:
        np.testing.assert_array_equal(np.rot90(before[key]), after[key])


def test_missing_data_stops_rays_and_does_not_look_through_holes():
    dem = np.zeros((15, 15))
    dem[5, 7] = np.nan  # Second step north of the center.
    before = geomorphon_components(dem, radius=5)
    dem[4, 7] = 1000  # Not visible through the hole.
    after = geomorphon_components(dem, radius=5)
    for key in before:
        assert before[key][7, 7] == after[key][7, 7]
    dem[6, 7] = np.nan  # No valid northern samples now.
    incomplete = geomorphon_components(dem, radius=5)
    assert np.isnan(incomplete["forms"][7, 7])
    assert incomplete["coverage"][7, 7] == 7 / 8
    assert np.isnan(incomplete["forms"][0, 0])


def test_anglev1_equal_absolute_angles_have_neutral_sign():
    # Exact uniform profiles are ties in the reference anglev1 rule.
    dem = np.tile(np.arange(15, dtype=np.float32), (15, 1))
    assert geomorphons(dem)[7, 7] == 1


def test_threshold_and_skip_change_the_visibility_response():
    dem = np.zeros((15, 15))
    dem[7, 7] = 0.1
    assert geomorphons(dem, flatness_deg=0.1)[7, 7] == 2
    assert geomorphons(dem, flatness_deg=80)[7, 7] == 1
    dem = np.zeros((15, 15))
    for dr, dc in DIRECTIONS:
        dem[7 + dr, 7 + dc] = 10
    assert geomorphons(dem, skip=0)[7, 7] == 10
    assert geomorphons(dem, skip=1)[7, 7] == 1


def test_api_records_geomorphon_conventions():
    out, _, metadata = compute_rrim_array(
        np.zeros((15, 15)), method="geomorphons", window=9,
        flatness_deg=2, geomorphon_skip=1,
    )
    assert out[7, 7] == 1
    assert metadata["flatness_deg"] == 2
    assert metadata["geomorphon_skip"] == 1
    assert metadata["classes"][10] == "pit"
    assert metadata["comparison"] == "anglev1"


@pytest.mark.parametrize("kwargs", [
    {"radius": 1}, {"skip": 3}, {"flatness_deg": 0}, {"flatness_deg": np.nan},
    {"cell_size": (0, 2)},
])
def test_invalid_geomorphon_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        geomorphons(np.zeros((13, 13)), **kwargs)


@pytest.mark.parametrize("height,expected", [(10, 2), (-10, 1)])
def test_legacy_extreme_classes_are_not_overwritten(height, expected):
    dem = np.zeros((9, 9))
    dem[4, 4] = height
    classes, confidence = geomorphons_simplified(dem, radius=2)
    assert classes[4, 4] == expected
    assert confidence[4, 4] == 1
