"""Small shared raster interface: Rasterio outside QGIS, native GDAL in QGIS.

No interpreter dependencies are installed or GDAL global settings changed.
The GDAL adapter implements only the single-band window operations used here.
"""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple
import os
import sys

import numpy as np


class GridTransform(NamedTuple):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


class RasterWindow(NamedTuple):
    col_off: int
    row_off: int
    width: int
    height: int


windows = SimpleNamespace(Window=RasterWindow)


class RasterCRS:
    def __init__(self, text):
        from osgeo import osr
        self.srs = osr.SpatialReference()
        if self.srs.SetFromUserInput(str(text)) != 0:
            raise ValueError("Invalid raster CRS")

    @property
    def is_projected(self):
        return bool(self.srs.IsProjected())

    @property
    def linear_units_factor(self):
        return self.srs.GetLinearUnitsName(), self.srs.GetLinearUnits()

    def to_wkt(self):
        return self.srs.ExportToWkt()

    def to_epsg(self):
        code = self.srs.GetAuthorityCode(None)
        return int(code) if code else None

    def to_string(self):
        code = self.to_epsg()
        return f"EPSG:{code}" if code else self.to_wkt()


class GDALRaster:
    def __init__(self, path, mode="r", **profile):
        from osgeo import gdal, gdal_array
        self.mode = mode
        if mode == "r":
            self.ds = gdal.Open(str(path), gdal.GA_ReadOnly)
        elif mode == "w":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            dtype = np.dtype(profile.get("dtype", "float32"))
            options = ["COMPRESS=LZW", "BIGTIFF=IF_SAFER"]
            if profile.get("tiled"):
                options += ["TILED=YES", f"BLOCKXSIZE={profile.get('blockxsize', 256)}",
                            f"BLOCKYSIZE={profile.get('blockysize', 256)}"]
            self.ds = gdal.GetDriverByName("GTiff").Create(
                str(path), profile["width"], profile["height"], profile.get("count", 1),
                gdal_array.NumericTypeCodeToGDALTypeCode(dtype), options=options,
            )
            if self.ds is not None:
                transform = profile.get("transform")
                if transform is not None:
                    self.ds.SetGeoTransform((transform.c, transform.a, transform.b,
                                             transform.f, transform.d, transform.e))
                crs = profile.get("crs")
                if crs is not None:
                    self.ds.SetProjection(crs.to_wkt() if hasattr(crs, "to_wkt") else RasterCRS(crs).to_wkt())
                if profile.get("nodata") is not None:
                    for band in range(1, self.ds.RasterCount + 1):
                        self.ds.GetRasterBand(band).SetNoDataValue(float(profile["nodata"]))
        else:
            raise ValueError(f"Unsupported raster mode: {mode}")
        if self.ds is None:
            raise ValueError(f"Unable to {mode} raster: {path}")
        self.width, self.height, self.count = self.ds.RasterXSize, self.ds.RasterYSize, self.ds.RasterCount
        gt = self.ds.GetGeoTransform()
        self.transform = GridTransform(gt[1], gt[2], gt[0], gt[4], gt[5], gt[3])
        projection = self.ds.GetProjection()
        self.crs = RasterCRS(projection) if projection else None
        self.nodata = self.ds.GetRasterBand(1).GetNoDataValue()
        self.dtypes = tuple(np.dtype(gdal_array.GDALTypeCodeToNumericTypeCode(
            self.ds.GetRasterBand(b).DataType)).name for b in range(1, self.count + 1))
        self.profile = dict(driver="GTiff", width=self.width, height=self.height,
                            count=self.count, dtype=self.dtypes[0], crs=self.crs,
                            transform=self.transform, nodata=self.nodata)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def close(self):
        if self.ds is not None:
            if self.mode == "w":
                self.ds.FlushCache()
            self.ds = None

    def read(self, band=1, *, window=None, masked=False):
        area = window or RasterWindow(0, 0, self.width, self.height)
        args = tuple(int(v) for v in area)
        raster_band = self.ds.GetRasterBand(band)
        array = raster_band.ReadAsArray(*args)
        if array is None:
            raise RuntimeError("GDAL failed to read the requested raster window")
        if masked:
            mask = raster_band.GetMaskBand().ReadAsArray(*args) == 0
            nodata = raster_band.GetNoDataValue()
            if nodata is not None:
                mask |= np.isnan(array) if np.isnan(nodata) else array == nodata
            mask |= ~np.isfinite(array)
            return np.ma.array(array, mask=mask)
        return array

    def write(self, array, band=1, *, window=None):
        x, y = (int(window.col_off), int(window.row_off)) if window else (0, 0)
        code = self.ds.GetRasterBand(band).WriteArray(array, x, y)
        if code not in (0, None):
            raise RuntimeError("GDAL failed to write the raster window")

    def block_windows(self, band=1):
        width, height = self.ds.GetRasterBand(band).GetBlockSize()
        for row, y in enumerate(range(0, self.height, height)):
            for col, x in enumerate(range(0, self.width, width)):
                yield (row, col), RasterWindow(x, y, min(width, self.width - x), min(height, self.height - y))


def open(path, mode="r", **profile):
    return GDALRaster(path, mode, **profile)


def Env(**_options):
    # Preserve the QGIS host's global GDAL configuration and cache.
    return nullcontext()


def get_backend():
    if os.environ.get("GEOMORPHX_RASTER_BACKEND", "auto") != "gdal":
        try:
            import rasterio
            return rasterio
        except ImportError:
            pass
    try:
        from osgeo import gdal  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Raster processing needs Rasterio or QGIS's GDAL Python bindings") from exc
    return sys.modules[__name__]
