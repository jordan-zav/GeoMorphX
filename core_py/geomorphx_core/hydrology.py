"""Deterministic in-memory D8 hydrology on a north-up metric grid.

Priority-Flood fills depressions. Steepest descent routes each cell to one
neighbour; flood parents resolve equal-height flats without elevation epsilon.
Raster edges and cells touching NoData are open drainage boundaries.
"""

from __future__ import annotations

from collections import deque
import heapq
import math

import numpy as np

OFFSETS = ((-1, 0), (-1, 1), (0, 1), (1, 1),
           (1, 0), (1, -1), (0, -1), (-1, -1))


def _priority_flood(dem: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(dem, dtype=np.float64)
    if values.ndim != 2 or not values.size:
        raise ValueError("DEM must be a non-empty 2D array")
    filled = values.copy()
    valid = np.isfinite(values)
    filled[~valid] = np.nan
    rows, cols = values.shape
    seen = ~valid.copy()
    parents = np.full(values.size, -1, dtype=np.int64)
    queue: list[tuple[float, int]] = []
    for r, c in zip(*np.nonzero(valid)):
        boundary = r == 0 or c == 0 or r == rows - 1 or c == cols - 1
        if not boundary:
            boundary = any(not valid[r + dr, c + dc] for dr, dc in OFFSETS)
        if boundary:
            seen[r, c] = True
            heapq.heappush(queue, (float(values[r, c]), int(r * cols + c)))
    while queue:
        elevation, index = heapq.heappop(queue)
        r, c = divmod(index, cols)
        for dr, dc in OFFSETS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols) or seen[nr, nc]:
                continue
            seen[nr, nc] = True
            neighbour = nr * cols + nc
            filled[nr, nc] = max(elevation, values[nr, nc])
            parents[neighbour] = index
            heapq.heappush(queue, (float(filled[nr, nc]), neighbour))
    return filled, parents


def fill_depressions(dem: np.ndarray) -> np.ndarray:
    """Return a filled DEM, without modifying the input or raising outlets."""
    return _priority_flood(dem)[0]


def _d8_network(dem: np.ndarray, cell_size: tuple[float, float]):
    dy, dx = cell_size
    if not all(math.isfinite(v) and v > 0 for v in (dy, dx)):
        raise ValueError("cell_size must contain positive finite (dy, dx)")
    filled, parents = _priority_flood(dem)
    rows, cols = filled.shape
    receiver = np.full(filled.size, -1, dtype=np.int64)
    valid = np.isfinite(filled).ravel()
    for index in np.flatnonzero(valid):
        r, c = divmod(int(index), cols)
        best_slope = 0.0
        for dr, dc in OFFSETS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            drop = filled[r, c] - filled[nr, nc]
            slope = drop / math.hypot(dr * dy, dc * dx)
            if slope > best_slope:
                best_slope = slope
                receiver[index] = nr * cols + nc
        if receiver[index] < 0:
            receiver[index] = parents[index]
    return filled, receiver, valid


def flow_accumulation_d8(
    dem: np.ndarray, *, cell_size: tuple[float, float] = (1.0, 1.0),
) -> np.ndarray:
    """Upslope contributing cell count, including the cell itself.

    Depression filling and flat routing are always applied. Ties in positive
    slope follow OFFSETS order. NoData is excluded, never assigned unit runoff.
    """
    filled, receiver, valid = _d8_network(dem, cell_size)
    return _accumulate(filled, receiver, valid)


def _accumulate(filled, receiver, valid):
    order = _topological_order(receiver, valid)
    accumulation = valid.astype(np.float64)
    for index in order:
        target = receiver[index]
        if target >= 0:
            accumulation[target] += accumulation[index]
    accumulation[~valid] = np.nan
    return accumulation.reshape(filled.shape)


def _topological_order(receiver, valid):
    indegree = np.zeros(receiver.size, dtype=np.int64)
    routed = receiver[receiver >= 0]
    np.add.at(indegree, routed, 1)
    queue = deque(int(i) for i in np.flatnonzero(valid & (indegree == 0)))
    order = []
    while queue:
        index = queue.popleft()
        order.append(index)
        target = receiver[index]
        if target >= 0:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(int(target))
    if len(order) != np.count_nonzero(valid):
        raise RuntimeError("D8 routing contains a cycle")
    return order


def twi_d8(
    dem: np.ndarray, *, cell_size: tuple[float, float] = (1.0, 1.0),
) -> np.ndarray:
    """ln(specific catchment area / tan(slope)) using D8 contributing area.

    Area = count * dx * dy; contour width approximation = sqrt(dx * dy).
    Slope is measured on the filled surface, with a tangent floor of 1e-6.
    Horizontal and vertical units must match. This is a D8 variant, not SAGA MFD.
    """
    from .terrain import _safe_gradient

    filled, receiver, valid = _d8_network(dem, cell_size)
    accumulation = _accumulate(filled, receiver, valid)
    gy, gx = _safe_gradient(filled, cell_size=cell_size)
    tangent = np.maximum(np.hypot(gy, gx), 1e-6)
    dy, dx = cell_size
    return np.log(accumulation * math.sqrt(dx * dy) / tangent).astype(np.float32)


def d8_drainage_products(dem: np.ndarray, *, cell_size=(1.0, 1.0)):
    """Direction codes, outlet basins and distance downstream to the outlet.

    Codes are 0 outlet, 1 N, 2 NE, 3 E, 4 SE, 5 S, 6 SW, 7 W, 8 NW.
    Basin labels start at 1 in row-major outlet order. Distances use CRS units.
    """
    filled, receiver, valid = _d8_network(dem, cell_size)
    order = _topological_order(receiver, valid)
    cols = filled.shape[1]
    direction = np.full(receiver.size, np.nan)
    basins = np.full(receiver.size, np.nan)
    length = np.full(receiver.size, np.nan)
    outlets = np.flatnonzero(valid & (receiver < 0))
    basins[outlets] = np.arange(1, len(outlets) + 1)
    direction[outlets] = 0
    length[outlets] = 0
    offset_codes = {offset: code for code, offset in enumerate(OFFSETS, 1)}
    dy, dx = cell_size
    for index in reversed(order):
        target = receiver[index]
        if target < 0:
            continue
        r, c = divmod(index, cols)
        tr, tc = divmod(int(target), cols)
        direction[index] = offset_codes[(tr - r, tc - c)]
        basins[index] = basins[target]
        length[index] = length[target] + math.hypot((tr - r) * dy, (tc - c) * dx)
    return {"flow_direction_d8": direction.reshape(filled.shape),
            "drainage_basins_d8": basins.reshape(filled.shape),
            "flow_length_d8": length.reshape(filled.shape)}


def _mfd_accumulate(filled, parents, cell_size, *, exponent=1.1):
    """Freeman slope-power fractions; flood-tree routing on filled flats.

    Fractions are proportional to downhill slope**exponent. This uses no
    optional contour-length correction. Every valid cell contributes one unit.
    """
    if not math.isfinite(exponent) or exponent <= 0:
        raise ValueError("MFD exponent must be positive and finite")
    dy, dx = cell_size
    if not all(math.isfinite(v) and v > 0 for v in cell_size):
        raise ValueError("cell_size must contain positive finite (dy, dx)")
    rows, cols = filled.shape
    valid = np.isfinite(filled).ravel()
    fractions = np.zeros((filled.size, 8), dtype=np.float64)
    indegree = np.zeros(filled.size, dtype=np.int64)
    distances = [math.hypot(dr * dy, dc * dx) for dr, dc in OFFSETS]
    for index in np.flatnonzero(valid):
        r, c = divmod(int(index), cols)
        slopes = np.zeros(8)
        for k, (dr, dc) in enumerate(OFFSETS):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and np.isfinite(filled[nr, nc]):
                slopes[k] = max(0., (filled[r, c] - filled[nr, nc]) / distances[k])
        maximum = slopes.max()
        if maximum > 0:
            weights = (slopes / maximum) ** exponent
            fractions[index] = weights / weights.sum()
        elif parents[index] >= 0:
            pr, pc = divmod(int(parents[index]), cols)
            fractions[index, OFFSETS.index((pr - r, pc - c))] = 1.
        for k in np.flatnonzero(fractions[index]):
            dr, dc = OFFSETS[k]
            indegree[(r + dr) * cols + c + dc] += 1
    accumulation = valid.astype(np.float64)
    queue = deque(int(i) for i in np.flatnonzero(valid & (indegree == 0)))
    processed = 0
    while queue:
        index = queue.popleft()
        processed += 1
        r, c = divmod(index, cols)
        for k in np.flatnonzero(fractions[index]):
            dr, dc = OFFSETS[k]
            target = (r + dr) * cols + c + dc
            accumulation[target] += accumulation[index] * fractions[index, k]
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if processed != np.count_nonzero(valid):
        raise RuntimeError("MFD routing contains a cycle")
    accumulation[~valid] = np.nan
    outlets = valid & (fractions.sum(axis=1) == 0)
    return accumulation.reshape(filled.shape), outlets.reshape(filled.shape)


def flow_accumulation_mfd(dem: np.ndarray, *, cell_size=(1.0, 1.0), exponent=1.1):
    """Fractional contributing cell count, with Priority-Flood depression filling."""
    filled, parents = _priority_flood(dem)
    return _mfd_accumulate(filled, parents, cell_size, exponent=exponent)[0]


def twi_mfd(dem: np.ndarray, *, cell_size=(1.0, 1.0), exponent=1.1):
    """TWI using Freeman MFD area, sqrt(cell area) width and filled-surface slope."""
    from .terrain import _safe_gradient
    filled, parents = _priority_flood(dem)
    accumulation, _ = _mfd_accumulate(filled, parents, cell_size, exponent=exponent)
    gy, gx = _safe_gradient(filled, cell_size=cell_size)
    tangent = np.maximum(np.hypot(gy, gx), 1e-6)
    return np.log(accumulation * math.sqrt(cell_size[0] * cell_size[1]) / tangent).astype(np.float32)
