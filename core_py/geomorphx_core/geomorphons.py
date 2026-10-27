"""Line-of-sight geomorphons: eight directions and ten landform classes.

The zenith/nadir comparison follows the basic anglev1 rule and the published
ten-form count matrix. This is not a wrapper or a complete clone of GRASS:
extended correction and the alternate comparison modes are not implemented.
Reference: https://grass.osgeo.org/grass-stable/manuals/r.geomorphon.html
"""

from __future__ import annotations

from functools import lru_cache
import math

import numpy as np

DIRECTIONS = ((-1, 0), (-1, 1), (0, 1), (1, 1),
              (1, 0), (1, -1), (0, -1), (-1, -1))
FORM_NAMES = {1: "flat", 2: "peak", 3: "ridge", 4: "shoulder", 5: "spur",
              6: "slope", 7: "hollow", 8: "footslope", 9: "valley", 10: "pit"}
# Row = negative directions; column = positive directions. Zero is impossible.
FORM_TABLE = np.array([
    [1, 1, 1, 8, 8, 9, 9, 9, 10],
    [1, 1, 8, 8, 8, 9, 9, 9, 0],
    [1, 4, 6, 6, 7, 7, 9, 0, 0],
    [4, 4, 6, 6, 6, 7, 0, 0, 0],
    [4, 4, 5, 6, 6, 0, 0, 0, 0],
    [3, 3, 5, 5, 0, 0, 0, 0, 0],
    [3, 3, 3, 0, 0, 0, 0, 0, 0],
    [3, 3, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 0, 0, 0],
], dtype=np.uint8)


@lru_cache(maxsize=1)
def _canonical_codes() -> np.ndarray:
    """Map all 3**8 ternary patterns to 498 rotation/reflection classes."""
    codes = np.arange(3 ** 8, dtype=np.int32)
    powers = 3 ** np.arange(8, dtype=np.int32)
    digits = (codes[:, None] // powers) % 3
    canonical = codes.copy()
    for reflected in (digits, digits[:, ::-1]):
        for shift in range(8):
            candidate = np.sum(np.roll(reflected, shift, axis=1) * powers, axis=1)
            canonical = np.minimum(canonical, candidate)
    canonical.setflags(write=False)
    return canonical


def search_geometry(radius: int, skip: int, cell_size) -> tuple[float, int]:
    if not isinstance(radius, (int, np.integer)) or radius < 2:
        raise ValueError("geomorphons radius must be an integer >= 2 (window >= 5)")
    if not isinstance(skip, (int, np.integer)) or not 0 <= skip < radius - 1:
        raise ValueError("geomorphon skip must be an integer in [0, radius - 2]")
    if len(cell_size) != 2 or not all(math.isfinite(v) and v > 0 for v in cell_size):
        raise ValueError("cell_size must contain positive finite (dy, dx)")
    search_distance = radius * max(cell_size)
    if (skip + 1) * math.hypot(*cell_size) >= search_distance:
        raise ValueError("skip leaves no diagonal line-of-sight samples inside the search radius")
    halo = math.ceil(search_distance / min(cell_size))
    return search_distance, halo


def geomorphon_components(
    dem: np.ndarray, *, radius: int = 4, flatness_deg: float = 1.0,
    skip: int = 0, cell_size: tuple[float, float] = (1.0, 1.0),
) -> dict[str, np.ndarray]:
    """Return forms, canonical ternary pattern, sign counts and LOS coverage.

    Search uses a circular physical distance radius * max(dy, dx), with a strict
    outer bound. Skip excludes the first N steps in each ray. NoData terminates
    a ray; it is never seen through. Classification requires at least one valid
    sample in each of the eight directions. Incomplete cells return NaN for
    forms/pattern/counts; coverage is the fraction of sampled directions.
    """
    values = np.asarray(dem, dtype=np.float64)
    if values.ndim != 2 or not values.size:
        raise ValueError("DEM must be a non-empty 2D array")
    if not math.isfinite(flatness_deg) or not 0 < flatness_deg < 90:
        raise ValueError("flatness_deg must be in (0, 90)")
    search_distance, halo = search_geometry(radius, skip, cell_size)
    dy, dx = cell_size
    rows, cols = values.shape
    padded = np.pad(values, halo, mode="constant", constant_values=np.nan)
    positive = np.zeros(values.shape, dtype=np.uint8)
    negative = np.zeros_like(positive)
    coverage = np.zeros_like(positive)
    raw_code = np.zeros(values.shape, dtype=np.int32)
    threshold = math.radians(flatness_deg)
    center_valid = np.isfinite(values)
    for direction, (dr, dc) in enumerate(DIRECTIONS):
        alive = center_valid.copy()
        highest = np.full(values.shape, -np.inf)
        lowest = np.full(values.shape, np.inf)
        seen = np.zeros(values.shape, dtype=bool)
        step_distance = math.hypot(dr * dy, dc * dx)
        for step in range(1, halo + 1):
            distance = step * step_distance
            if distance >= search_distance:
                break
            r0, c0 = halo + step * dr, halo + step * dc
            neighbour = padded[r0:r0 + rows, c0:c0 + cols]
            alive &= np.isfinite(neighbour)
            if step <= skip:
                continue
            angle = np.arctan2(neighbour - values, distance)
            np.maximum(highest, angle, out=highest, where=alive)
            np.minimum(lowest, angle, out=lowest, where=alive)
            seen |= alive
        coverage += seen
        nonflat = seen & ((np.abs(highest) > threshold) | (np.abs(lowest) > threshold))
        sign = np.zeros(values.shape, dtype=np.int8)
        sign[nonflat & (np.abs(highest) > np.abs(lowest))] = 1
        sign[nonflat & (np.abs(lowest) > np.abs(highest))] = -1
        positive += sign == 1
        negative += sign == -1
        raw_code += (sign.astype(np.int32) + 1) * (3 ** direction)
    valid = center_valid & (coverage == 8)
    products = {
        "forms": FORM_TABLE[negative, positive].astype(np.float32),
        "ternary": _canonical_codes()[raw_code].astype(np.float32),
        "positive_count": positive.astype(np.float32),
        "negative_count": negative.astype(np.float32),
    }
    for array in products.values():
        array[~valid] = np.nan
    products["coverage"] = coverage.astype(np.float32) / 8
    products["coverage"][~center_valid] = np.nan
    return products


def geomorphons(dem: np.ndarray, **kwargs) -> np.ndarray:
    """Ten forms: 1 flat through 10 pit; NoData is NaN."""
    return geomorphon_components(dem, **kwargs)["forms"]


def geomorphons_simplified(dem: np.ndarray, *, radius=5, threshold=0.5):
    """Legacy nine-class point-sampling model, with exclusive class rules.

    Class IDs remain 0 flat, 1 pit, 2 peak, 3 saddle, 4 ridge, 5 valley,
    6 upper slope, 7 lower slope, 8 slope. NoData is NaN. Confidence is only
    abs(positive_count - negative_count)/8, not a calibrated probability.
    """
    values = np.asarray(dem, dtype=np.float32)
    if values.ndim != 2 or not values.size:
        raise ValueError("DEM must be a non-empty 2D array")
    if not isinstance(radius, (int, np.integer)) or radius < 1:
        raise ValueError("radius must be a positive integer")
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and >= 0")
    padded = np.pad(values, radius, mode="edge")
    pos = np.zeros(values.shape, dtype=np.uint8)
    neg = np.zeros_like(pos)
    valid = np.isfinite(values)
    for dr, dc in DIRECTIONS:
        r, c = radius + dr * radius, radius + dc * radius
        neighbour = padded[r:r + values.shape[0], c:c + values.shape[1]]
        valid &= np.isfinite(neighbour)
        difference = neighbour - values
        pos += difference > threshold
        neg += difference < -threshold
    classes = np.select(
        [(pos == 0) & (neg == 0), (pos >= 6) & (neg == 0),
         (neg >= 6) & (pos == 0), (pos >= 4) & (neg >= 4),
         (neg >= 4) & (pos <= 2), (pos >= 4) & (neg <= 2), neg > pos, pos > neg],
        [0, 1, 2, 3, 4, 5, 6, 7], default=8,
    ).astype(np.float32)
    confidence = np.abs(pos.astype(np.int16) - neg).astype(np.float32) / 8
    classes[~valid] = np.nan
    confidence[~valid] = np.nan
    return classes, confidence
