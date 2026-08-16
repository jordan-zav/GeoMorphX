"""Raster I/O utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _require_rasterio():
    try:
        import rasterio  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Raster I/O requires rasterio. Install with: pip install -e .[raster]"
        ) from exc
    return rasterio


def read_dem(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    rasterio = _require_rasterio()
    src = Path(path)
    with rasterio.open(src) as ds:  # type: ignore
        arr = ds.read(1).astype(np.float32)
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
        }
    )
    with rasterio.open(dst, "w", **out_profile) as ds:  # type: ignore
        ds.write(data.astype(np.float32), 1)