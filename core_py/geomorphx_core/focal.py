"""Shared local statistics with identical NoData policy across backends."""

from __future__ import annotations

import numpy as np


def local_stat(values: np.ndarray, window: int, statistic: str) -> np.ndarray:
    if values.ndim != 2 or not values.size:
        raise ValueError("Input must be a non-empty 2D array")
    if not isinstance(window, (int, np.integer)) or window < 3:
        raise ValueError("window must be an integer >= 3")
    window += int(window % 2 == 0)
    arr = np.asarray(values, dtype=np.float32)
    if statistic not in {"mean", "std", "relief"}:
        raise ValueError("Unknown local statistic")
    if np.isfinite(arr).all():
        try:
            from geomorphx import geomorphx_core_rs
        except ImportError:
            pass
        else:
            return getattr(geomorphx_core_rs, f"local_{statistic}_rs")(arr, window)
    radius = window // 2
    padded = np.pad(arr, radius, mode="edge")
    out = np.empty_like(arr)
    # A strided view per row bounds temporary storage and avoids Python pixel loops.
    for row in range(arr.shape[0]):
        blocks = np.lib.stride_tricks.sliding_window_view(
            padded[row:row + window], (window, window),
        )[0]
        if statistic == "mean":
            out[row] = np.mean(blocks, axis=(-2, -1), dtype=np.float64)
        elif statistic == "std":
            out[row] = np.std(blocks, axis=(-2, -1), dtype=np.float64)
        else:
            out[row] = np.max(blocks, axis=(-2, -1)) - np.min(blocks, axis=(-2, -1))
    return out
