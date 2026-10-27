"""Frontend-neutral raster blocks used by QGIS and Python workflows."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from core_py.geomorphx_core.geomorphons import geomorphons_simplified
from core_py.geomorphx_core.io import read_dem, write_raster
from geomorphx.api import compute_rrim


def _validate_outputs(source, *outputs):
    resolved = [Path(p).resolve() for p in outputs]
    if len(set(resolved)) != len(resolved) or Path(source).resolve() in resolved:
        raise ValueError("Block outputs must be distinct from each other and the input DEM")


def compute_curvature_block(dem_path, out_profile, out_plan, out_mean):
    _validate_outputs(dem_path, out_profile, out_plan, out_mean)
    return tuple(compute_rrim(dem_path, target, method=method) for method, target in (
        ("curvature_profile", out_profile), ("curvature_plan", out_plan),
        ("curvature_mean", out_mean),
    ))


def compute_tpi_wetness_block(dem_path, out_small, out_large, out_wetness, *,
                              window_small=11, window_large=31):
    _validate_outputs(dem_path, out_small, out_large, out_wetness)
    return tuple(compute_rrim(dem_path, target, method=method, window=window)
                 for method, target, window in (
                     ("tpi", out_small, window_small), ("tpi", out_large, window_large),
                     ("wetness_proxy", out_wetness, window_small),
                 ))


def compute_geomorphons_legacy_block(dem_path, out_classes, out_confidence, *,
                                    radius=5, threshold=0.5):
    _validate_outputs(dem_path, out_classes, out_confidence)
    dem, profile = read_dem(dem_path)
    classes, confidence = geomorphons_simplified(dem, radius=radius, threshold=threshold)
    # Preserve the integer class raster and IDs of the existing QGIS algorithm.
    from core_py.geomorphx_core.io import _require_rasterio
    rasterio = _require_rasterio()
    class_profile = profile.copy()
    class_profile.update(driver="GTiff", dtype="int16", count=1, nodata=-32768)
    class_path = Path(out_classes)
    class_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(class_path, "w", **class_profile) as dst:
        dst.write(np.where(np.isfinite(classes), classes, -32768).astype(np.int16), 1)
    write_raster(out_confidence, confidence, profile)
    return class_path, Path(out_confidence)


def compute_geomorphons_block(dem_path, out_classes, out_ternary, *, radius=4,
                               flatness_deg=1.0, skip=0):
    _validate_outputs(dem_path, out_classes, out_ternary)
    return tuple(compute_rrim(
        dem_path, target, method=method, window=radius * 2 + 1,
        flatness_deg=flatness_deg, geomorphon_skip=skip,
    ) for method, target in (("geomorphons", out_classes), ("geomorphon_ternary", out_ternary)))
