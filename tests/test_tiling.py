import numpy as np
import pytest
import rasterio
from pathlib import Path

from core_py.geomorphx_core.io import read_dem
from geomorphx.api import compute_rrim
from geomorphx.tiling import compute_tiled


def test_tiling_vs_untiled(tmp_path):
    dem_path = tmp_path / "dem.tif"
    out_untiled_path = tmp_path / "untiled.tif"
    out_tiled_path = tmp_path / "tiled.tif"

    # Create a synthetic DEM (size 128x128)
    np.random.seed(42)
    dem = np.random.rand(128, 128).astype(np.float32) * 100.0

    profile = {
        "driver": "GTiff",
        "height": 128,
        "width": 128,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32618",
        "transform": rasterio.transform.from_origin(500000, 4000000, 10, 10),
    }

    with rasterio.open(dem_path, "w", **profile) as dst:
        dst.write(dem, 1)

    # Run untiled
    compute_rrim(
        dem_path=dem_path,
        out_path=out_untiled_path,
        method="slope",
        window=9,
    )

    # Run tiled with a very small tile size (e.g. 32) to force multiple tiles
    compute_tiled(
        input_path=dem_path,
        output_path=out_tiled_path,
        method="slope",
        tile_size=32,
        window=9,
    )

    # Compare results (interior should be identical)
    untiled, _ = read_dem(out_untiled_path)
    tiled, _ = read_dem(out_tiled_path)

    np.testing.assert_allclose(tiled[4:-4, 4:-4], untiled[4:-4, 4:-4], rtol=1e-5, atol=1e-5)
