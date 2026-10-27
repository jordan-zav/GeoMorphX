"""General geomorphometric terrain methods (non-RRIM specific)."""

from __future__ import annotations

import math

import numpy as np

Array = np.ndarray


def _validate_dem(dem: Array) -> None:
    if dem.ndim != 2:
        raise ValueError("DEM must be a 2D array")
    if dem.size == 0:
        raise ValueError("DEM cannot be empty")


def _safe_gradient(dem: Array, *, cell_size=(1.0, 1.0)) -> tuple[Array, Array]:
    dy, dx = cell_size
    if not all(math.isfinite(v) and v > 0 for v in (dy, dx)):
        raise ValueError("cell_size must contain positive finite (dy, dx)")
    values = dem.astype(np.float64)
    gy = np.gradient(values, dy, axis=0) if dem.shape[0] > 1 else np.zeros_like(values)
    gx = np.gradient(values, dx, axis=1) if dem.shape[1] > 1 else np.zeros_like(values)
    gy[~np.isfinite(values)] = np.nan
    gx[~np.isfinite(values)] = np.nan
    return gy.astype(np.float32), gx.astype(np.float32)


def slope_deg(dem: Array, *, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    gy, gx = _safe_gradient(dem, cell_size=cell_size)
    slope = np.arctan(np.sqrt(gx * gx + gy * gy))
    return np.degrees(slope).astype(np.float32)


def aspect_deg(dem: Array, *, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    gy, gx = _safe_gradient(dem, cell_size=cell_size)
    # Clockwise degrees from North in [0, 360).
    aspect = np.degrees(np.arctan2(-gx, gy)) % 360.0
    aspect[(gx == 0) & (gy == 0)] = np.nan
    return aspect.astype(np.float32)


def hillshade(
    dem: Array,
    *,
    azimuth_deg: float = 315.0,
    altitude_deg: float = 45.0,
    z_factor: float = 1.0,
    cell_size=(1.0, 1.0),
) -> Array:
    _validate_dem(dem)
    if not (0.0 <= azimuth_deg < 360.0):
        raise ValueError("azimuth_deg must be in [0, 360)")
    if not (0.0 < altitude_deg <= 90.0):
        raise ValueError("altitude_deg must be in (0, 90]")
    if z_factor <= 0.0:
        raise ValueError("z_factor must be > 0")

    gy, gx = _safe_gradient(dem, cell_size=cell_size)
    slope = np.arctan(z_factor * np.sqrt(gx * gx + gy * gy))
    aspect = np.arctan2(-gx, gy)

    az = math.radians(azimuth_deg)
    alt = math.radians(altitude_deg)
    illum = (np.sin(alt) * np.cos(slope)) + (np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    hs = np.clip(255.0 * illum, 0.0, 255.0)
    return hs.astype(np.float32)


def multidirectional_hillshade(
    dem: Array,
    *,
    directions: int = 8,
    altitude_deg: float = 45.0,
    z_factor: float = 1.0,
    cell_size=(1.0, 1.0),
) -> Array:
    """Average analytical hillshades from evenly spaced light directions."""
    _validate_dem(dem)
    if directions < 2:
        raise ValueError("directions must be >= 2")
    layers = [
        hillshade(
            dem,
            azimuth_deg=(360.0 * index / directions) % 360.0,
            altitude_deg=altitude_deg,
            z_factor=z_factor,
            cell_size=cell_size,
        )
        for index in range(directions)
    ]
    return np.mean(np.stack(layers, axis=0), axis=0).astype(np.float32)


def _horizon_angles(dem: Array, *, radius: int, directions: int, cell_size=(1.0, 1.0)) -> Array:
    """Maximum horizon elevation angle for each compass direction in radians."""
    _validate_dem(dem)
    if radius < 1:
        raise ValueError("radius must be >= 1")
    if directions < 4:
        raise ValueError("directions must be >= 4")
    dy_size, dx_size = cell_size
    if not all(math.isfinite(v) and v > 0 for v in cell_size):
        raise ValueError("cell_size must contain positive finite (dy, dx)")

    values = dem.astype(np.float32)
    padded = np.pad(values, radius, mode="edge")
    rows, cols = values.shape
    horizons: list[Array] = []
    for index in range(directions):
        azimuth = 2.0 * math.pi * index / directions
        best_slope = np.full(values.shape, -np.inf, dtype=np.float32)
        shifts: set[tuple[int, int]] = set()
        for distance in range(1, radius + 1):
            dy = int(round(-math.cos(azimuth) * distance))
            dx = int(round(math.sin(azimuth) * distance))
            if (dy, dx) == (0, 0) or (dy, dx) in shifts:
                continue
            shifts.add((dy, dx))
            neighbour = padded[
                radius + dy : radius + dy + rows,
                radius + dx : radius + dx + cols,
            ]
            horizontal_distance = math.hypot(dy * dy_size, dx * dx_size)
            best_slope = np.fmax(best_slope, (neighbour - values) / horizontal_distance)
        best_slope[~np.isfinite(best_slope)] = np.nan
        horizons.append(np.arctan(best_slope).astype(np.float32))
    return np.stack(horizons, axis=0)


def positive_openness(dem: Array, *, radius: int = 10, directions: int = 16, cell_size=(1.0, 1.0)) -> Array:
    """Return positive openness (degrees): openness of the sky hemisphere."""
    horizons = _horizon_angles(dem, radius=radius, directions=directions, cell_size=cell_size)
    return np.degrees((math.pi / 2.0) - np.mean(horizons, axis=0)).astype(np.float32)


def negative_openness(dem: Array, *, radius: int = 10, directions: int = 16, cell_size=(1.0, 1.0)) -> Array:
    """Return negative openness (degrees): openness of the lower hemisphere."""
    return positive_openness(-dem.astype(np.float32), radius=radius, directions=directions, cell_size=cell_size)


def sky_view_factor(dem: Array, *, radius: int = 10, directions: int = 16, cell_size=(1.0, 1.0)) -> Array:
    """Approximate the visible fraction of sky from directional horizon angles."""
    horizons = _horizon_angles(dem, radius=radius, directions=directions, cell_size=cell_size)
    visible = 1.0 - np.sin(np.maximum(horizons, 0.0))
    return np.mean(visible, axis=0).astype(np.float32)


def _curvature_terms(dem: Array, *, cell_size=(1.0, 1.0)) -> tuple[Array, Array, Array, Array]:
    gy, gx = _safe_gradient(dem, cell_size=cell_size)
    q, p = gy, gx
    qy, qx = _safe_gradient(q, cell_size=cell_size)
    py, px = _safe_gradient(p, cell_size=cell_size)
    r = px.astype(np.float32)
    s = (0.5 * (py + qx)).astype(np.float32)
    t = qy.astype(np.float32)
    g = (p * p + q * q).astype(np.float32)
    return p, q, g, (r, s, t)


def profile_curvature(dem: Array, *, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    p, q, g, (r, s, t) = _curvature_terms(dem, cell_size=cell_size)
    eps = 1e-9
    g_safe = np.maximum(g, eps)
    val = -(r * p * p + 2.0 * s * p * q + t * q * q) / (g_safe * np.power(1.0 + g_safe, 1.5))
    return val.astype(np.float32)


def plan_curvature(dem: Array, *, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    p, q, g, (r, s, t) = _curvature_terms(dem, cell_size=cell_size)
    eps = 1e-9
    g_safe = np.maximum(g, eps)
    val = (r * q * q - 2.0 * s * p * q + t * p * p) / np.power(g_safe, 1.5)
    return val.astype(np.float32)


def mean_curvature(dem: Array, *, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    p, q, g, (r, s, t) = _curvature_terms(dem, cell_size=cell_size)
    eps = 1e-9
    g_safe = np.maximum(g, eps)
    val = -((1.0 + q * q) * r - 2.0 * p * q * s + (1.0 + p * p) * t) / (2.0 * np.power(1.0 + g_safe, 1.5))
    return val.astype(np.float32)


def _local_mean(arr: Array, window: int) -> Array:
    from .focal import local_stat
    return local_stat(arr, window, "mean")


def _local_relief(arr: Array, window: int) -> Array:
    from .focal import local_stat
    return local_stat(arr, window, "relief")


def tpi(dem: Array, *, window: int = 11) -> Array:
    _validate_dem(dem)
    return (dem.astype(np.float32) - _local_mean(dem, window)).astype(np.float32)


def tri(dem: Array, *, window: int = 11) -> Array:
    """Legacy local range; use tri_riley for the Riley ruggedness index."""
    _validate_dem(dem)
    return _local_relief(dem, window).astype(np.float32)


def tri_riley(dem: Array) -> Array:
    """Square root of summed squared differences to eight neighbours.

    Replicate edge pixels. Any missing neighbour makes the result unknown.
    """
    _validate_dem(dem)
    values = dem.astype(np.float64)
    padded = np.pad(values, 1, mode="edge")
    total = np.zeros_like(values)
    for dr in range(3):
        for dc in range(3):
            if dr == dc == 1:
                continue
            neighbour = padded[dr:dr + dem.shape[0], dc:dc + dem.shape[1]]
            total += (neighbour - values) ** 2
    return np.sqrt(total).astype(np.float32)


def local_relief(dem: Array, *, window: int = 11) -> Array:
    """Elevation range (maximum minus minimum) in the local window."""
    return tri(dem, window=window)


def wetness_proxy(dem: Array, *, window: int = 11, cell_size=(1.0, 1.0)) -> Array:
    _validate_dem(dem)
    gy, gx = _safe_gradient(dem, cell_size=cell_size)
    slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))
    relief = _local_relief(dem, window)
    a_proxy = relief + 1.0
    wet = np.log(a_proxy / (np.tan(slope_rad) + 1e-6))
    return wet.astype(np.float32)
