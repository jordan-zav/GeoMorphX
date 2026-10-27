import numpy as np
import pytest

from core_py.geomorphx_core.hydrology import (
    _d8_network, fill_depressions, flow_accumulation_d8, twi_d8,
)
from core_py.geomorphx_core.terrain import tri_riley


def test_priority_flood_fills_pit_and_preserves_input_and_outlets():
    dem = np.full((5, 5), 10.0)
    dem[1:-1, 1:-1] = 1
    original = dem.copy()
    filled = fill_depressions(dem)
    np.testing.assert_array_equal(filled, 10)
    np.testing.assert_array_equal(dem, original)
    np.testing.assert_array_equal(fill_depressions(filled), filled)


def test_d8_accumulation_on_east_draining_plane():
    dem = np.tile([4., 3., 2., 1.], (3, 1))
    actual = flow_accumulation_d8(dem, cell_size=(2, 3))
    np.testing.assert_array_equal(actual, np.tile([1., 2., 3., 4.], (3, 1)))


@pytest.mark.parametrize("kind", ["random", "flat", "pit", "nodata"])
def test_d8_conserves_runoff_and_has_no_cycles(kind):
    dem = np.random.default_rng(18).normal(size=(11, 13))
    if kind == "flat":
        dem[:] = 7
    elif kind == "pit":
        dem[1:-1, 1:-1] -= 100
    elif kind == "nodata":
        dem[4:6, 5:7] = np.nan
    _, receivers, valid = _d8_network(dem, (1, 1))
    accum = flow_accumulation_d8(dem).ravel()
    assert np.sum(accum[valid & (receivers < 0)]) == np.count_nonzero(valid)
    assert np.isnan(accum[~valid]).all()


def test_twi_uses_physical_specific_area():
    dem = np.tile([8., 6., 4., 2.], (3, 1))
    # Pixel size 2: tan(slope)=1; area/width = count * 2.
    expected = np.log(np.tile([2., 4., 6., 8.], (3, 1)))
    np.testing.assert_allclose(twi_d8(dem, cell_size=(2, 2)), expected, rtol=1e-6)


def test_riley_is_not_elevation_range():
    dem = np.ones((3, 3))
    dem[1, 1] = 0
    assert tri_riley(dem)[1, 1] == pytest.approx(np.sqrt(8))


def test_hydrology_handles_empty_mask_and_single_cell():
    empty_mask = np.full((3, 4), np.nan)
    assert np.isnan(fill_depressions(empty_mask)).all()
    assert np.isnan(flow_accumulation_d8(empty_mask)).all()
    np.testing.assert_array_equal(flow_accumulation_d8(np.array([[2.]])), [[1.]])
    with pytest.raises(ValueError):
        flow_accumulation_d8(np.zeros((3, 3)), cell_size=(0, 1))
