"""
Internal openness calculation utilities for QGIS-RRIM.
"""

import math

import numpy as np
from osgeo import gdal


def _direction_offsets(radius, num_directions, pixel_width, pixel_height):
    for index in range(num_directions):
        angle = (2.0 * math.pi * index) / num_directions
        offsets = []
        seen = set()

        for step in range(1, radius + 1):
            dx = int(round(math.cos(angle) * step))
            dy = int(round(math.sin(angle) * step))
            if dx == 0 and dy == 0:
                continue
            if (dy, dx) in seen:
                continue

            seen.add((dy, dx))
            distance = math.hypot(dx * pixel_width, dy * pixel_height)
            if distance == 0:
                continue

            offsets.append((dy, dx, distance))

        if offsets:
            yield offsets


def _shift_array(array, dy, dx):
    shifted = np.full(array.shape, np.nan, dtype=np.float64)

    src_row_start = max(0, -dy)
    src_row_end = array.shape[0] - max(0, dy)
    src_col_start = max(0, -dx)
    src_col_end = array.shape[1] - max(0, dx)

    if src_row_start >= src_row_end or src_col_start >= src_col_end:
        return shifted

    dst_row_start = max(0, dy)
    dst_row_end = dst_row_start + (src_row_end - src_row_start)
    dst_col_start = max(0, dx)
    dst_col_end = dst_col_start + (src_col_end - src_col_start)

    shifted[dst_row_start:dst_row_end, dst_col_start:dst_col_end] = array[src_row_start:src_row_end, src_col_start:src_col_end]
    return shifted


def _calculate_openness(dem_array, radius, num_directions, pixel_width, pixel_height, feedback=None):
    directions = list(_direction_offsets(radius, num_directions, pixel_width, pixel_height))
    openness_sum = np.zeros(dem_array.shape, dtype=np.float64)
    direction_count = np.zeros(dem_array.shape, dtype=np.uint16)

    total_directions = max(len(directions), 1)

    for direction_index, offsets in enumerate(directions, start=1):
        max_horizon = np.full(dem_array.shape, -np.inf, dtype=np.float64)
        valid_samples = np.zeros(dem_array.shape, dtype=bool)

        for dy, dx, distance in offsets:
            shifted = _shift_array(dem_array, dy, dx)
            sample_mask = ~np.isnan(shifted)
            if not sample_mask.any():
                continue

            horizon_angle = np.degrees(np.arctan((shifted - dem_array) / distance))
            max_horizon = np.where(sample_mask, np.maximum(max_horizon, horizon_angle), max_horizon)
            valid_samples |= sample_mask

        if valid_samples.any():
            openness_sum = np.where(valid_samples, openness_sum + (90.0 - max_horizon), openness_sum)
            direction_count += valid_samples.astype(np.uint16)

        if feedback is not None:
            feedback.setProgress(int(direction_index * 100 / total_directions))

    openness = np.full(dem_array.shape, np.nan, dtype=np.float32)
    valid_cells = direction_count > 0
    openness[valid_cells] = (openness_sum[valid_cells] / direction_count[valid_cells]).astype(np.float32)
    return openness


def compute_openness_raster(input_path, output_path, radius=10, num_directions=16, invert=False, feedback=None):
    dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise RuntimeError(f"Could not open DEM: {input_path}")

    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray().astype(np.float64)
    nodata_value = band.GetNoDataValue()
    if nodata_value is not None:
        array[array == nodata_value] = np.nan

    if invert:
        array *= -1.0

    geotransform = dataset.GetGeoTransform()
    pixel_width = abs(geotransform[1]) if geotransform else 1.0
    pixel_height = abs(geotransform[5]) if geotransform and geotransform[5] != 0 else pixel_width

    openness = _calculate_openness(
        array,
        radius=radius,
        num_directions=num_directions,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
        feedback=feedback,
    )

    driver = gdal.GetDriverByName("GTiff")
    output = driver.Create(
        output_path,
        dataset.RasterXSize,
        dataset.RasterYSize,
        1,
        gdal.GDT_Float32,
        options=["COMPRESS=LZW", "TILED=YES"],
    )
    if output is None:
        raise RuntimeError(f"Could not create openness raster: {output_path}")

    output.SetGeoTransform(dataset.GetGeoTransform())
    output.SetProjection(dataset.GetProjection())

    out_band = output.GetRasterBand(1)
    out_band.WriteArray(openness)
    out_band.SetNoDataValue(np.nan)
    out_band.FlushCache()

    output.FlushCache()
    output = None
    dataset = None

    return output_path
