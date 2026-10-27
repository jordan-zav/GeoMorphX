import numpy as np
import pytest

from core_py.geomorphx_core.hydrology import (
    _priority_flood, _mfd_accumulate, flow_accumulation_d8, flow_accumulation_mfd,
    d8_drainage_products, twi_mfd,
)
from geomorphx.api import compute_rrim_array


def test_d8_direction_basins_and_length_on_an_east_draining_plane():
    dem = np.tile([4., 3., 2., 1.], (3, 1))
    products = d8_drainage_products(dem, cell_size=(2, 3))
    np.testing.assert_array_equal(products["flow_direction_d8"], np.tile([3, 3, 3, 0], (3, 1)))
    np.testing.assert_array_equal(products["drainage_basins_d8"], np.repeat([[1], [2], [3]], 4, axis=1))
    np.testing.assert_array_equal(products["flow_length_d8"], np.tile([9., 6., 3., 0.], (3, 1)))


def test_mfd_freeman_shares_runoff_by_slope_power():
    dem = np.zeros((3, 3))
    dem[1, 1] = 1
    actual = flow_accumulation_mfd(dem)
    diagonal = (1 / np.sqrt(2)) ** 1.1
    total = 4 + 4 * diagonal
    assert actual[1, 1] == 1
    assert actual[0, 1] == pytest.approx(1 + 1 / total)
    assert actual[0, 0] == pytest.approx(1 + diagonal / total)
    assert actual.sum() - actual[1, 1] == pytest.approx(9)


@pytest.mark.parametrize("kind", ["random", "flat", "hole", "depression", "all_nodata"])
def test_mfd_conserves_total_runoff_at_outlets(kind):
    dem = np.random.default_rng(73).normal(size=(13, 15))
    if kind == "flat":
        dem[:] = 3
    elif kind == "hole":
        dem[5:7, 6:8] = np.nan
    elif kind == "depression":
        dem[1:-1, 1:-1] -= 100
    elif kind == "all_nodata":
        dem[:] = np.nan
    filled, parents = _priority_flood(dem)
    accumulation, outlets = _mfd_accumulate(filled, parents, (2, 3))
    assert np.nansum(accumulation[outlets]) == pytest.approx(np.isfinite(dem).sum(), rel=1e-12)
    assert np.isnan(accumulation[~np.isfinite(dem)]).all()
    if kind == "flat":
        np.testing.assert_array_equal(accumulation, flow_accumulation_d8(dem, cell_size=(2, 3)))


def test_mfd_twi_uses_the_same_area_and_filled_surface_slope():
    dem = np.zeros((5, 5))
    actual = twi_mfd(dem, cell_size=(2, 2))
    accumulation = flow_accumulation_mfd(dem, cell_size=(2, 2))
    np.testing.assert_allclose(actual, np.log(accumulation * 2 / 1e-6), rtol=1e-6)


@pytest.mark.parametrize("method", ["flow_direction_d8", "drainage_basins_d8", "flow_length_d8", "flow_accumulation_mfd", "twi_mfd"])
def test_extended_hydrology_api_preserves_nodata_and_metadata(method):
    dem = np.arange(81, dtype=np.float32).reshape(9, 9)
    dem[3, 3] = np.nan
    out, scales, metadata = compute_rrim_array(dem, method=method, cell_size=(2, 3))
    assert np.isnan(out[3, 3])
    assert scales == []
    assert metadata["nodata_boundary"] == "open"
