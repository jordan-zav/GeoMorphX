"""Windowed processing with method-specific halos and full-grid safeguards."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import warnings

import numpy as np
from core_py.geomorphx_core.raster_backend import get_backend

rasterio = get_backend()
Window = rasterio.windows.Window

from core_py.geomorphx_core.io import raster_cell_size, read_dem, write_raster
from geomorphx.methods import GLOBAL_METHODS, METHODS


def compute_tiled(
    input_path: str | Path,
    output_path: str | Path,
    *,
    method: str,
    tile_size: int = 1024,
    window: int = 9,
    scales: Iterable[int] | None = None,
    azimuth_deg: float | Iterable[float] | str = 0.0,
    directional_weight: float = 0.5,
    anisotropy_weight: float = 0.35,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.15,
    flatness_deg: float = 1.0,
    geomorphon_skip: int = 0,
    scratch_dir: str | Path | None = None,
) -> tuple[list[int], dict]:
    """Compute local products with halos; global methods explicitly use full memory.

    RRIM normalization and hydrological connectivity depend on the whole DEM.
    Computing them independently per tile would change the scientific result.
    """
    from geomorphx.api import compute_rrim_array

    if not isinstance(tile_size, int) or tile_size < 1:
        raise ValueError("tile_size must be a positive integer")
    if not isinstance(window, (int, np.integer)) or window < 3:
        raise ValueError("window must be an integer >= 3")
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}")
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise ValueError("Input DEM and output raster must be different files")
    window += int(window % 2 == 0)
    scales = None if scales is None else list(scales)
    from core_py.geomorphx_core.rrim import _parse_azimuths
    azimuth_deg = _parse_azimuths(azimuth_deg)
    parameters = dict(
        method=method, window=window, scales=scales, azimuth_deg=azimuth_deg,
        directional_weight=directional_weight, anisotropy_weight=anisotropy_weight,
        roughness_weight=roughness_weight, structural_weight=structural_weight,
        flatness_deg=flatness_deg, geomorphon_skip=geomorphon_skip,
    )
    if method.startswith("rrim_"):
        from geomorphx.streaming import compute_rrim_streamed
        return compute_rrim_streamed(
            input_path, output_path, method=method, tile_size=tile_size, window=window,
            scales=scales, azimuth_deg=azimuth_deg, directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight, roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            scratch_dir=scratch_dir,
        )
    if method in GLOBAL_METHODS:
        warnings.warn(
            f"{method} requires global context: using full DEM in memory; "
            "tile_size does not bound memory for this method.",
            RuntimeWarning, stacklevel=2,
        )
        dem, profile = read_dem(input_path)
        out, used_scales, metadata = compute_rrim_array(
            dem, cell_size=raster_cell_size(profile, method=method), **parameters,
        )
        write_raster(output_path, out, profile)
        metadata.update(processing_mode="full_grid_fallback", requested_tile_size=tile_size)
        return used_scales, metadata

    if method.startswith("curvature_"):
        pad = 2  # Two successive gradient operators.
    elif method in {"slope", "aspect", "hillshade", "multidirectional_hillshade", "tri_riley"}:
        pad = 1
    else:
        pad = window // 2

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(input_path) as src:
        if src.count != 1:
            raise ValueError("DEM must have exactly one raster band")
        profile = src.profile.copy()
        cell_size = raster_cell_size(profile, method=method)
        if method in {"geomorphons", "geomorphon_ternary"}:
            from core_py.geomorphx_core.geomorphons import search_geometry
            _, pad = search_geometry(window // 2, geomorphon_skip, cell_size)
        profile.update(dtype="float32", count=1, nodata=np.nan,
                       tiled=True, blockxsize=256, blockysize=256)
        with rasterio.open(output_path, "w", **profile) as dst:
            for ty in range(0, src.height, tile_size):
                for tx in range(0, src.width, tile_size):
                    tile_w = min(tile_size, src.width - tx)
                    tile_h = min(tile_size, src.height - ty)
                    rx, ry = max(0, tx - pad), max(0, ty - pad)
                    rw = min(src.width, tx + tile_w + pad) - rx
                    rh = min(src.height, ty + tile_h + pad) - ry
                    dem = src.read(1, window=Window(rx, ry, rw, rh), masked=True)
                    dem = dem.astype(np.float32).filled(np.nan)
                    out, used_scales, metadata = compute_rrim_array(
                        dem, cell_size=cell_size, **parameters,
                    )
                    # Keep the actual raster edge: pre-padding would alter derivatives.
                    y0, x0 = ty - ry, tx - rx
                    dst.write(out[y0:y0 + tile_h, x0:x0 + tile_w].astype(np.float32),
                              1, window=Window(tx, ty, tile_w, tile_h))
    metadata.update(processing_mode="windowed", tile_size=tile_size, halo_px=pad)
    return used_scales, metadata
