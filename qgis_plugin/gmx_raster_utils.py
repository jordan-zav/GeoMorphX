"""Raster IO helpers for QGIS plugin algorithms."""

from __future__ import annotations

from osgeo import gdal
import numpy as np


def read_dem_array(path: str) -> tuple[np.ndarray, tuple[float, ...], str, float | None]:
    ds = gdal.Open(path)
    if ds is None:
        raise ValueError(f"Unable to open DEM: {path}")

    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    ds = None

    return arr, gt, proj, nodata


def write_array_as_geotiff(
    path: str,
    arr: np.ndarray,
    geotransform: tuple[float, ...],
    projection: str,
    nodata: float | None = None,
    gdal_dtype: int = gdal.GDT_Float32,
) -> str:
    rows, cols = arr.shape
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(path, cols, rows, 1, gdal_dtype, options=["COMPRESS=LZW"])
    if ds is None:
        raise ValueError(f"Unable to create output: {path}")

    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection)

    band = ds.GetRasterBand(1)
    band.WriteArray(arr)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.FlushCache()

    ds = None
    return path


def _integral_image(arr: np.ndarray) -> np.ndarray:
    return arr.cumsum(axis=0).cumsum(axis=1)


def _window_sum(integral: np.ndarray, r0: int, c0: int, r1: int, c1: int) -> float:
    total = integral[r1, c1]
    if r0 > 0:
        total -= integral[r0 - 1, c1]
    if c0 > 0:
        total -= integral[r1, c0 - 1]
    if r0 > 0 and c0 > 0:
        total += integral[r0 - 1, c0 - 1]
    return float(total)


def local_mean(arr: np.ndarray, window: int) -> np.ndarray:
    if window < 3:
        raise ValueError("window must be >= 3")
    if window % 2 == 0:
        window += 1

    radius = window // 2
    padded = np.pad(arr, pad_width=radius, mode="edge")
    integral = _integral_image(padded)

    rows, cols = arr.shape
    out = np.zeros_like(arr, dtype=np.float32)
    area = float(window * window)

    for r in range(rows):
        for c in range(cols):
            r0 = r
            c0 = c
            r1 = r + window - 1
            c1 = c + window - 1
            out[r, c] = _window_sum(integral, r0, c0, r1, c1) / area

    return out


def neighborhood_relief(arr: np.ndarray, window: int) -> np.ndarray:
    if window < 3:
        raise ValueError("window must be >= 3")
    if window % 2 == 0:
        window += 1

    radius = window // 2
    padded = np.pad(arr, pad_width=radius, mode="edge")
    rows, cols = arr.shape
    out = np.zeros_like(arr, dtype=np.float32)

    for r in range(rows):
        for c in range(cols):
            block = padded[r : r + window, c : c + window]
            out[r, c] = float(block.max() - block.min())

    return out