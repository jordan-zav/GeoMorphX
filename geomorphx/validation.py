"""Raster inspection and file fingerprints without loading the DEM into RAM."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from core_py.geomorphx_core.io import _require_rasterio, raster_cell_size


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_dem(path, *, expected_pixel_size_m=None):
    rasterio = _require_rasterio()
    source = Path(path).resolve()
    with rasterio.open(source) as src:
        if src.count != 1:
            raise ValueError("DEM must have exactly one raster band")
        dy, dx = raster_cell_size(src.profile, method="slope")
        unit_name, unit_factor = src.crs.linear_units_factor
        pixel_size_m = [dy * unit_factor, dx * unit_factor]
        if expected_pixel_size_m is not None:
            expected = expected_pixel_size_m
            if not isinstance(expected, (int, float)) or not math.isfinite(expected) or expected <= 0:
                raise ValueError("Recipe pixel_size_m must be positive and finite")
            if not all(math.isclose(size, expected, rel_tol=1e-6, abs_tol=1e-9) for size in pixel_size_m):
                raise ValueError(f"Recipe pixel_size_m={expected} does not match DEM (dy, dx)={pixel_size_m}")
        nodata = src.nodata
        return {
            "path": str(source), "shape": [src.height, src.width], "bands": src.count,
            "dtype": src.dtypes[0], "crs": src.crs.to_string(),
            "horizontal_units": unit_name, "horizontal_unit_to_m": unit_factor,
            "cell_size_crs_units": [dy, dx], "cell_size_m": pixel_size_m,
            "transform": list(src.transform)[:6],
            "nodata": nodata if nodata is not None and math.isfinite(nodata) else None,
            "vertical_units_policy": "must_match_horizontal_units",
            "size_bytes": source.stat().st_size,
        }
