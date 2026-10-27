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
    mask = band.GetMaskBand().ReadAsArray() == 0
    if nodata is not None:
        mask |= arr == nodata
    arr[mask | ~np.isfinite(arr)] = np.nan
    nodata = float("nan")
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
    if nodata is None and np.issubdtype(arr.dtype, np.floating) and np.isnan(arr).any():
        nodata = float("nan")
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
    from .suite_imports import ensure_suite_importable
    ensure_suite_importable()
    from core_py.geomorphx_core.focal import local_stat
    return local_stat(arr, window, "mean")


def neighborhood_relief(arr: np.ndarray, window: int) -> np.ndarray:
    from .suite_imports import ensure_suite_importable
    ensure_suite_importable()
    from core_py.geomorphx_core.focal import local_stat
    return local_stat(arr, window, "relief")
