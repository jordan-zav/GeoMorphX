"""Global RRIM normalization using bounded raster windows and disk-backed stages.

Intermediate rasters and the execution manifest are retained, never cleaned up
automatically. RAM depends on tile size, focal radius and inputs per operation,
not on the DEM dimensions. Scratch disk usage grows with the number of stages.
"""

from __future__ import annotations

from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile

import numpy as np
from core_py.geomorphx_core.raster_backend import get_backend

rasterio = get_backend()
Window = rasterio.windows.Window

from core_py.geomorphx_core import rrim
from core_py.geomorphx_core.io import raster_cell_size
from core_py.geomorphx_core.terrain import _safe_gradient


class RasterStages:
    def __init__(self, source, *, tile_size, scratch_dir=None):
        self.source = Path(source)
        self.tile_size = tile_size
        with rasterio.open(source) as src:
            if src.count != 1:
                raise ValueError("DEM must have exactly one raster band")
            self.profile = src.profile.copy()
            self.height, self.width = src.height, src.width
        parent = scratch_dir or os.environ.get("DEVRESOURCES_SESSION") or tempfile.gettempdir()
        Path(parent).mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="geomorphx_rrim_", dir=parent))
        self.profile.update(driver="GTiff", count=1, dtype="float32", nodata=np.nan,
                            tiled=True, blockxsize=256, blockysize=256, BIGTIFF="IF_SAFER")
        self.nodes = []
        self.cache = {}
        self.max_read_shape = [0, 0]

    def windows(self):
        for y in range(0, self.height, self.tile_size):
            for x in range(0, self.width, self.tile_size):
                yield x, y, min(self.tile_size, self.width - x), min(self.tile_size, self.height - y)

    def evaluate(self, key, inputs, operation, *, halo=0, target=None):
        if key in self.cache and target is None:
            return self.cache[key]
        path = Path(target) if target else self.root / f"stage_{len(self.nodes):03d}.tif"
        path.parent.mkdir(parents=True, exist_ok=True)
        with ExitStack() as stack:
            sources = [stack.enter_context(rasterio.open(item)) for item in inputs]
            dst = stack.enter_context(rasterio.open(path, "w", **self.profile))
            for x, y, width, height in self.windows():
                rx, ry = max(0, x - halo), max(0, y - halo)
                rw = min(self.width, x + width + halo) - rx
                rh = min(self.height, y + height + halo) - ry
                self.max_read_shape[0] = max(self.max_read_shape[0], rh)
                self.max_read_shape[1] = max(self.max_read_shape[1], rw)
                arrays = []
                for src in sources:
                    arr = src.read(1, window=Window(rx, ry, rw, rh), masked=True)
                    arr = arr.astype(np.float32).filled(np.nan)
                    arr[~np.isfinite(arr)] = np.nan
                    arrays.append(arr)
                result = np.asarray(operation(*arrays), dtype=np.float32)
                if result.shape != (rh, rw):
                    raise RuntimeError(f"Stage {key} returned an incorrect shape")
                y0, x0 = y - ry, x - rx
                dst.write(result[y0:y0 + height, x0:x0 + width], 1,
                          window=Window(x, y, width, height))
        self.cache[key] = path
        self.nodes.append({"operation": str(key), "inputs": [str(p) for p in inputs],
                           "output": str(path), "halo_px": halo})
        return path

    def normalize(self, source):
        key = ("normalize", str(source))
        if key in self.cache:
            return self.cache[key]
        lower, upper = np.inf, -np.inf
        with rasterio.open(source) as src:
            for x, y, width, height in self.windows():
                arr = src.read(1, window=Window(x, y, width, height))
                finite = arr[np.isfinite(arr)]
                if finite.size:
                    lower = min(lower, float(finite.min()))
                    upper = max(upper, float(finite.max()))
        def operation(arr):
            if not np.isfinite(lower):
                return np.full_like(arr, np.nan)
            if upper == lower:
                return np.where(np.isfinite(arr), 0, np.nan)
            return (arr - lower) / (upper - lower)
        target = self.evaluate(key, [source], operation)
        self.nodes[-1]["global_range"] = [lower, upper] if np.isfinite(lower) else [None, None]
        return target

    def manifest(self, *, method, status, error=None):
        path = self.root / "pipeline.json"
        path.write_text(json.dumps({
            "method": method, "status": status, "input": str(self.source.resolve()),
            "tile_size": self.tile_size, "shape": [self.height, self.width],
            "max_read_shape": self.max_read_shape, "stages": self.nodes, "error": error,
            "scratch_retained": True,
        }, indent=2, allow_nan=False), encoding="utf-8")
        return path


def compute_rrim_streamed(input_path, output_path, *, method, tile_size=1024,
                          window=9, scales=None, azimuth_deg=0., directional_weight=0.5,
                          anisotropy_weight=0.35, roughness_weight=0.25,
                          structural_weight=0.15, scratch_dir=None):
    """Compute the existing seven RRIM variants with global, not per-tile, ranges."""
    from geomorphx.methods import METHODS
    if method not in METHODS or not method.startswith("rrim_"):
        raise ValueError("Streamed RRIM requires an RRIM method")
    if not isinstance(tile_size, int) or tile_size < 1:
        raise ValueError("tile_size must be a positive integer")
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise ValueError("Input DEM and output raster must be different files")
    if not isinstance(window, (int, np.integer)) or window < 3:
        raise ValueError("window must be an integer >= 3")
    window = int(rrim._ensure_odd_window(window))
    scales = list(scales) if scales is not None else [5, 15, 45]
    if any(not isinstance(s, (int, np.integer)) or s < 3 for s in scales):
        raise ValueError("scales must contain integers >= 3")
    scales = [int(rrim._ensure_odd_window(s)) for s in scales]
    multiscale = method.endswith("multiscale")
    if multiscale and not scales:
        raise ValueError("at least one scale is required")
    azimuths = rrim._parse_azimuths(azimuth_deg)
    if not all(np.isfinite(a) for a in azimuths):
        raise ValueError("azimuths must be finite")
    weights = (directional_weight, anisotropy_weight, roughness_weight, structural_weight)
    if not all(np.isfinite(w) for w in weights):
        raise ValueError("weights must be finite")
    if "anisotropic" in method and not 0 <= directional_weight <= 1:
        raise ValueError("directional_weight must be between 0 and 1")
    if method == "rrim_plus" and (min(weights[1:]) < 0 or sum(weights[1:]) > 1):
        raise ValueError("RRIM+ weights must be >= 0 with sum <= 1")
    with rasterio.open(input_path) as src:
        cell_size = raster_cell_size(src.profile, method=method)
    graph = RasterStages(input_path, tile_size=tile_size, scratch_dir=scratch_dir)
    source = graph.source
    norm = graph.normalize
    point = graph.evaluate

    def slope():
        return norm(point("slope", [source], rrim._slope_deg, halo=1))

    def baseline(size):
        relief = norm(point(("relief", size), [source], lambda a: rrim._local_relief(a, size), halo=size // 2))
        return point(("baseline", size), [relief, slope()], lambda a, b: 0.6 * a + 0.4 * b)

    def directional():
        def operation(arr):
            if not azimuths:
                return np.zeros_like(arr)
            return np.max(np.stack([rrim._directional_gradient_response(arr, a) for a in azimuths]), axis=0)
        return norm(point("directional", [source], operation, halo=1))

    def anisotropic(size, weight):
        return point(("anisotropic", size, weight), [baseline(size), directional()],
                     lambda a, b: (1 - weight) * a + weight * b)

    def structure(size):
        gx = point("gx", [source], lambda a: _safe_gradient(a)[1], halo=1)
        gy = point("gy", [source], lambda a: _safe_gradient(a)[0], halo=1)
        moments = []
        for name, inputs, operation in (
            ("xx", [gx], lambda a: a * a), ("xy", [gx, gy], lambda a, b: a * b),
            ("yy", [gy], lambda a: a * a),
        ):
            product = point(name, inputs, operation)
            moments.append(point(("mean", name, size), [product],
                                 lambda a: rrim._local_mean(a, size), halo=size // 2))
        raw = point(("structure", size), moments,
                    lambda a, b, c: rrim._tensor_from_moments(a, b, c, azimuths)[0])
        return norm(raw)

    try:
        with rasterio.Env(GDAL_CACHEMAX=32 * 1024 * 1024):
            if method == "rrim_plus":
                roughness = norm(point(("std", window), [source],
                                       lambda a: rrim._local_std(a, window), halo=window // 2))
                inputs = [baseline(window), anisotropic(window, 0.7), roughness, structure(window)]
                base_weight = 1 - anisotropy_weight - roughness_weight - structural_weight
                raw = point("plus", inputs, lambda a, b, c, d:
                            base_weight * a + anisotropy_weight * b + roughness_weight * c + structural_weight * d)
                result = norm(raw)
            else:
                sizes = scales if multiscale else [window]
                layers = []
                for size in sizes:
                    if "structural" in method:
                        layers.append(structure(size))
                    elif "anisotropic" in method:
                        layers.append(anisotropic(size, directional_weight))
                    else:
                        layers.append(baseline(size))
                result = point("multiscale", layers, lambda *items: np.mean(np.stack(items), axis=0)) if multiscale else layers[0]
            point("output", [result, source], lambda a, dem: np.where(np.isfinite(dem), a, np.nan), target=output_path)
        manifest = graph.manifest(method=method, status="complete")
    except Exception as exc:
        graph.manifest(method=method, status="failed", error=str(exc))
        raise
    params = {"window": window, "cell_size": list(cell_size), "spacing_policy": "legacy_unit_pixel",
              "processing_mode": "windowed_global_normalization", "tile_size": tile_size,
              "scratch_dir": str(graph.root), "pipeline_manifest": str(manifest),
              "stages": len(graph.nodes), "max_read_shape": graph.max_read_shape}
    if multiscale:
        params["scales"] = scales
    if "anisotropic" in method or "structural" in method or method == "rrim_plus":
        params["azimuth_deg"] = azimuths if len(azimuths) > 1 else (azimuths[0] if azimuths else 0.)
    if "anisotropic" in method:
        params["directional_weight"] = directional_weight
    if method == "rrim_plus":
        params.update(anisotropy_weight=anisotropy_weight, roughness_weight=roughness_weight,
                      structural_weight=structural_weight)
    return scales if multiscale else [window], params
