"""Raster I/O utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def raster_cell_size(profile: dict[str, Any], *, method: str) -> tuple[float, float]:
    """Return north-up (dy, dx) in CRS units; reject unsupported physical grids."""
    transform = profile.get("transform")
    if transform is None:
        return (1.0, 1.0)
    if transform.b != 0 or transform.d != 0 or transform.a <= 0 or transform.e >= 0:
        raise ValueError("DEM must use a north-up, unrotated grid; reproject it first")
    crs = profile.get("crs")
    physical = method in {
        "slope", "aspect", "hillshade", "multidirectional_hillshade",
        "positive_openness", "negative_openness", "sky_view_factor",
        "curvature_profile", "curvature_plan", "curvature_mean", "wetness_proxy",
        "flow_accumulation_d8", "twi_d8",
        "geomorphons", "geomorphon_ternary",
        "flow_direction_d8", "drainage_basins_d8", "flow_length_d8", "flow_accumulation_mfd", "twi_mfd",
    }
    if physical and (crs is None or not crs.is_projected):
        raise ValueError("This method requires a projected CRS with matching horizontal/vertical units")
    return (abs(float(transform.e)), abs(float(transform.a)))


def _require_rasterio():
    """Compatibility helper: select Rasterio or native GDAL without installing either."""
    from .raster_backend import get_backend
    return get_backend()


def read_dem(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    rasterio = _require_rasterio()
    src = Path(path)
    with rasterio.open(src) as ds:  # type: ignore
        if ds.count != 1:
            raise ValueError("DEM must have exactly one raster band")
        arr = ds.read(1, masked=True).astype(np.float32).filled(np.nan)
        arr[~np.isfinite(arr)] = np.nan
        profile = ds.profile.copy()
    return arr, profile


def write_raster(path: str | Path, data: np.ndarray, profile: dict[str, Any]) -> None:
    rasterio = _require_rasterio()
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out_profile = profile.copy()
    out_profile.update(
        {
            "driver": "GTiff",
            "count": 1,
            "dtype": "float32",
            "height": int(data.shape[0]),
            "width": int(data.shape[1]),
            "nodata": np.nan,
        }
    )
    with rasterio.open(dst, "w", **out_profile) as ds:  # type: ignore
        ds.write(data.astype(np.float32), 1)
