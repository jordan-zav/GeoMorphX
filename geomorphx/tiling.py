"""Tiled processing engine for large rasters."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio
from rasterio.windows import Window


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
) -> None:
    """Compute geomorphometric products by processing the raster in tiles."""
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        width = src.width
        height = src.height
        nodata = src.nodata

    # Determine maximum window size across all methods/scales
    max_w = window
    if method in ("rrim_multiscale", "rrim_anisotropic_multiscale", "rrim_structural_multiscale") and scales:
        max_w = max(scales)

    pad = max_w // 2

    # Update output profile
    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )

    from geomorphx.api import compute_rrim_array

    with rasterio.open(input_path) as src, rasterio.open(output_path, "w", **profile) as dst:
        for ty in range(0, height, tile_size):
            for tx in range(0, width, tile_size):
                # Target window to write to (without pad)
                tile_w = min(tile_size, width - tx)
                tile_h = min(tile_size, height - ty)
                write_window = Window(tx, ty, tile_w, tile_h)

                # Read window with pad (expanding bounds)
                read_x = max(0, tx - pad)
                read_y = max(0, ty - pad)
                read_w = min(width, tx + tile_w + pad) - read_x
                read_h = min(height, ty + tile_h + pad) - read_y
                read_window = Window(read_x, read_y, read_w, read_h)

                # Read data
                dem_tile = src.read(1, window=read_window).astype(np.float32)

                # Handle NoData
                if nodata is not None:
                    dem_tile[dem_tile == nodata] = np.nan

                # Determine padding needed if we hit DEM boundaries
                pad_top = read_y - (ty - pad)
                pad_bottom = (ty + tile_h + pad) - (read_y + read_h)
                pad_left = read_x - (tx - pad)
                pad_right = (tx + tile_w + pad) - (read_x + read_w)

                if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
                    dem_tile = np.pad(
                        dem_tile,
                        ((pad_top, pad_bottom), (pad_left, pad_right)),
                        mode="edge",
                    )

                # Run compute
                out_tile, _, _ = compute_rrim_array(
                    dem_tile,
                    method=method,
                    scales=scales,
                    window=window,
                    azimuth_deg=azimuth_deg,
                    directional_weight=directional_weight,
                    anisotropy_weight=anisotropy_weight,
                    roughness_weight=roughness_weight,
                    structural_weight=structural_weight,
                )

                # Crop out the pad
                crop_y_start = pad
                crop_y_end = pad + tile_h
                crop_x_start = pad
                crop_x_end = pad + tile_w
                cropped = out_tile[crop_y_start:crop_y_end, crop_x_start:crop_x_end]

                # Write to destination
                dst.write(cropped, 1, window=write_window)
