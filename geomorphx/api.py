"""High-level API for GeoMorphX workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from geomorphx.methods import METHODS
from core_py.geomorphx_core.hydrology import (
    fill_depressions, flow_accumulation_d8, twi_d8, d8_drainage_products,
    flow_accumulation_mfd, twi_mfd,
)
from core_py.geomorphx_core.geomorphons import FORM_NAMES, geomorphon_components

from core_py.geomorphx_core.io import raster_cell_size, read_dem, write_raster
from core_py.geomorphx_core.rrim import (
    rrim_anisotropic,
    rrim_anisotropic_multiscale,
    rrim_baseline,
    rrim_multiscale,
    rrim_plus,
    rrim_plus_components,
    rrim_structural,
    rrim_structural_multiscale,
)
from core_py.geomorphx_core.terrain import (
    aspect_deg,
    hillshade,
    mean_curvature,
    multidirectional_hillshade,
    negative_openness,
    plan_curvature,
    positive_openness,
    profile_curvature,
    sky_view_factor,
    slope_deg,
    tpi,
    tri,
    wetness_proxy,
    local_relief,
    tri_riley,
)


def compute_rrim_array(
    dem: np.ndarray,
    *,
    method: str = "rrim_baseline",
    scales: Iterable[int] | None = None,
    window: int = 9,
    azimuth_deg: float | Iterable[float] | str = 0.0,
    directional_weight: float = 0.5,
    anisotropy_weight: float = 0.35,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.15,
    cell_size: tuple[float, float] = (1.0, 1.0),
    flatness_deg: float = 1.0,
    geomorphon_skip: int = 0,
) -> tuple[np.ndarray, list[int], dict[str, Any]]:
    dem = np.asarray(dem, dtype=np.float32).copy()
    if dem.ndim != 2 or not dem.size:
        raise ValueError("DEM must be a non-empty 2D array")
    dem[~np.isfinite(dem)] = np.nan
    if method not in METHODS:
        raise ValueError(f"Unknown method {method!r}; choose from {', '.join(METHODS)}")
    if len(cell_size) != 2 or not all(np.isfinite(v) and v > 0 for v in cell_size):
        raise ValueError("cell_size must contain positive finite (dy, dx)")
    if not isinstance(window, (int, np.integer)) or window < 3:
        raise ValueError("window must be an integer >= 3")
    window += int(window % 2 == 0)
    scales = None if scales is None else list(scales)
    if scales is not None:
        if any(not isinstance(s, (int, np.integer)) or s < 3 for s in scales):
            raise ValueError("scales must contain integers >= 3")
        scales = [int(s) + int(s % 2 == 0) for s in scales]
    from core_py.geomorphx_core.rrim import _parse_azimuths
    parsed_azimuths = _parse_azimuths(azimuth_deg)
    if not all(np.isfinite(a) for a in parsed_azimuths):
        raise ValueError("azimuths must be finite")
    azimuth_deg = parsed_azimuths
    if not all(np.isfinite(w) for w in (
        directional_weight, anisotropy_weight, roughness_weight, structural_weight,
    )):
        raise ValueError("weights must be finite")
    metadata_azimuth = parsed_azimuths if len(parsed_azimuths) > 1 else (parsed_azimuths[0] if parsed_azimuths else 0.0)

    metadata_params: dict[str, Any] = {"window": window, "cell_size": list(cell_size)}
    if method.startswith("rrim_"):
        metadata_params["spacing_policy"] = "legacy_unit_pixel"
    if method == "rrim_baseline":
        out = rrim_baseline(dem, window=window)
        used_scales: list[int] = [window]
    elif method == "rrim_multiscale":
        used_scales = [int(s) for s in (scales if scales is not None else [5, 15, 45])]
        out = rrim_multiscale(dem, used_scales)
        metadata_params["scales"] = used_scales
    elif method == "rrim_anisotropic":
        used_scales = [window]
        out = rrim_anisotropic(
            dem,
            window=window,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
        )
        metadata_params["azimuth_deg"] = metadata_azimuth
        metadata_params["directional_weight"] = float(directional_weight)
    elif method == "rrim_anisotropic_multiscale":
        used_scales = [int(s) for s in (scales if scales is not None else [5, 15, 45])]
        out = rrim_anisotropic_multiscale(
            dem,
            scales=used_scales,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
        )
        metadata_params["scales"] = used_scales
        metadata_params["azimuth_deg"] = metadata_azimuth
        metadata_params["directional_weight"] = float(directional_weight)
    elif method == "rrim_structural":
        used_scales = [window]
        out = rrim_structural(dem, window=window, azimuth_deg=azimuth_deg)
        metadata_params["azimuth_deg"] = metadata_azimuth
    elif method == "rrim_structural_multiscale":
        used_scales = [int(s) for s in (scales if scales is not None else [5, 15, 45])]
        out = rrim_structural_multiscale(
            dem,
            scales=used_scales,
            azimuth_deg=azimuth_deg,
        )
        metadata_params["scales"] = used_scales
        metadata_params["azimuth_deg"] = metadata_azimuth
    elif method == "rrim_plus":
        used_scales = [window]
        out = rrim_plus(
            dem,
            window=window,
            azimuth_deg=azimuth_deg,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
        )
        metadata_params["azimuth_deg"] = metadata_azimuth
        metadata_params["anisotropy_weight"] = float(anisotropy_weight)
        metadata_params["roughness_weight"] = float(roughness_weight)
        metadata_params["structural_weight"] = float(structural_weight)
    elif method == "slope":
        used_scales = [window]
        out = slope_deg(dem, cell_size=cell_size)
    elif method == "aspect":
        used_scales = [window]
        out = aspect_deg(dem, cell_size=cell_size)
    elif method == "hillshade":
        used_scales = [window]
        first_az = float(parsed_azimuths[0]) if parsed_azimuths else 315.0
        out = hillshade(dem, azimuth_deg=first_az, altitude_deg=45.0, z_factor=1.0, cell_size=cell_size)
        metadata_params["azimuth_deg"] = first_az
    elif method == "multidirectional_hillshade":
        used_scales = [window]
        out = multidirectional_hillshade(dem, cell_size=cell_size)
        metadata_params["directions"] = 8
    elif method == "positive_openness":
        used_scales = [window]
        out = positive_openness(dem, radius=max(1, window // 2), cell_size=cell_size)
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "negative_openness":
        used_scales = [window]
        out = negative_openness(dem, radius=max(1, window // 2), cell_size=cell_size)
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "sky_view_factor":
        used_scales = [window]
        out = sky_view_factor(dem, radius=max(1, window // 2), cell_size=cell_size)
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "curvature_profile":
        used_scales = [window]
        out = profile_curvature(dem, cell_size=cell_size)
    elif method == "curvature_plan":
        used_scales = [window]
        out = plan_curvature(dem, cell_size=cell_size)
    elif method == "curvature_mean":
        used_scales = [window]
        out = mean_curvature(dem, cell_size=cell_size)
    elif method == "tpi":
        used_scales = [window]
        out = tpi(dem, window=window)
    elif method == "tri":
        used_scales = [window]
        out = tri(dem, window=window)
    elif method == "wetness_proxy":
        used_scales = [window]
        out = wetness_proxy(dem, window=window, cell_size=cell_size)
    elif method == "local_relief":
        used_scales = [window]
        out = local_relief(dem, window=window)
    elif method == "tri_riley":
        used_scales = [3]
        out = tri_riley(dem)
        metadata_params["window"] = 3
    elif method in {"geomorphons", "geomorphon_ternary"}:
        components = geomorphon_components(
            dem, radius=window // 2, flatness_deg=flatness_deg,
            skip=geomorphon_skip, cell_size=cell_size,
        )
        used_scales = [window]
        out = components["forms" if method == "geomorphons" else "ternary"]
        metadata_params.update({
            "radius_px": window // 2, "flatness_deg": float(flatness_deg),
            "geomorphon_skip": int(geomorphon_skip), "comparison": "anglev1",
            "search_distance": (window // 2) * max(cell_size),
            "search_boundary": "strict", "missing_ray_policy": "require_all_eight",
            "nodata_ray_policy": "stop", "extended_correction": False,
        })
        if method == "geomorphons":
            metadata_params["classes"] = FORM_NAMES
    elif method in {"flow_direction_d8", "drainage_basins_d8", "flow_length_d8"}:
        used_scales = []
        out = d8_drainage_products(dem, cell_size=cell_size)[method]
        metadata_params.update({"depression_filling": "priority_flood", "nodata_boundary": "open"})
        if method == "flow_direction_d8":
            metadata_params["classes"] = {0: "outlet", 1: "N", 2: "NE", 3: "E", 4: "SE",
                                          5: "S", 6: "SW", 7: "W", 8: "NW"}
        elif method == "drainage_basins_d8":
            metadata_params["labels"] = "row_major_outlets_starting_at_1"
            if np.isfinite(out).any() and np.nanmax(out) > 2 ** 24:
                raise ValueError("Too many basin IDs for exact float32 raster output")
        else:
            metadata_params["units"] = "CRS_horizontal_units"
    elif method in {"flow_accumulation_mfd", "twi_mfd"}:
        used_scales = []
        out = (flow_accumulation_mfd if method == "flow_accumulation_mfd" else twi_mfd)(dem, cell_size=cell_size)
        metadata_params.update({"depression_filling": "priority_flood", "nodata_boundary": "open",
                                "routing": "freeman_mfd", "exponent": 1.1,
                                "flat_routing": "priority_flood_tree", "contour_weighting": False})
        if method == "flow_accumulation_mfd":
            metadata_params["units"] = "fractional_contributing_cells_including_self"
        else:
            metadata_params.update(contour_width="sqrt_cell_area", slope_tangent_floor=1e-6)
    elif method in {"fill_depressions", "flow_accumulation_d8", "twi_d8"}:
        used_scales = []
        metadata_params.update({"depression_filling": "priority_flood", "nodata_boundary": "open"})
        if method == "fill_depressions":
            out = fill_depressions(dem)
        elif method == "flow_accumulation_d8":
            out = flow_accumulation_d8(dem, cell_size=cell_size)
            metadata_params["units"] = "contributing_cells_including_self"
        else:
            out = twi_d8(dem, cell_size=cell_size)
            metadata_params.update({"contour_width": "sqrt_cell_area", "slope_tangent_floor": 1e-6})
    else:
        raise ValueError(f"Method has no implementation: {method}")

    out[~np.isfinite(dem)] = np.nan
    return out, used_scales, metadata_params


def _write_debug_intermediates(
    *,
    dem: np.ndarray,
    profile: dict[str, Any],
    debug_dir: Path,
    method: str,
    window: int,
    azimuth_deg: float,
    anisotropy_weight: float,
    roughness_weight: float,
    structural_weight: float,
) -> list[str]:
    debug_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    if method != "rrim_plus":
        return written

    comps = rrim_plus_components(
        dem,
        window=window,
        azimuth_deg=azimuth_deg,
        anisotropy_weight=anisotropy_weight,
        roughness_weight=roughness_weight,
        structural_weight=structural_weight,
    )
    for name, arr in comps.items():
        target = debug_dir / f"{name}.tif"
        write_raster(target, arr, profile)
        written.append(str(target))
    return written


def compute_rrim(
    dem_path: str | Path,
    out_path: str | Path,
    *,
    method: str = "rrim_baseline",
    scales: Iterable[int] | None = None,
    window: int = 9,
    azimuth_deg: float | Iterable[float] | str = 0.0,
    directional_weight: float = 0.5,
    anisotropy_weight: float = 0.35,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.15,
    debug_dir: str | Path | None = None,
    tile_size: int = 0,
    flatness_deg: float = 1.0,
    geomorphon_skip: int = 0,
    scratch_dir: str | Path | None = None,
) -> Path:
    if tile_size < 0:
        raise ValueError("tile_size must be >= 0")
    if Path(dem_path).resolve() == Path(out_path).resolve():
        raise ValueError("Input DEM and output raster must be different files")
    from core_py.geomorphx_core.rrim import _parse_azimuths
    azimuth_deg = _parse_azimuths(azimuth_deg)
    scales = None if scales is None else list(scales)
    if debug_dir is not None and tile_size > 0:
        raise ValueError("Debug intermediates require tile_size=0")
    if tile_size > 0:
        from geomorphx.tiling import compute_tiled
        from core_py.geomorphx_core.raster_backend import get_backend
        rasterio = get_backend()

        used_scales, metadata_params = compute_tiled(
            input_path=dem_path,
            output_path=out_path,
            method=method,
            tile_size=tile_size,
            window=window,
            scales=scales,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            flatness_deg=flatness_deg,
            geomorphon_skip=geomorphon_skip,
            scratch_dir=scratch_dir,
        )

        with rasterio.open(out_path) as dst:
            height, width = dst.height, dst.width
            vmin, vmax = float("inf"), float("-inf")
            for _, window_obj in dst.block_windows(1):
                block = dst.read(1, window=window_obj)
                valid = block[~np.isnan(block)]
                if valid.size > 0:
                    vmin = min(vmin, float(np.min(valid)))
                    vmax = max(vmax, float(np.max(valid)))
            value_range = [vmin, vmax] if vmin != float("inf") else [None, None]

        metadata = {
            "framework": "GeoMorphX",
            "version": "0.1.0",
            "method": method,
            "scales": used_scales,
            "parameters": metadata_params,
            "shape": [height, width],
            "value_range": value_range,
            "intermediates": [],
        }

    else:
        dem, profile = read_dem(dem_path)
        out, used_scales, metadata_params = compute_rrim_array(
            dem,
            method=method,
            scales=scales,
            window=window,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            cell_size=raster_cell_size(profile, method=method),
            flatness_deg=flatness_deg,
            geomorphon_skip=geomorphon_skip,
        )

        write_raster(out_path, out, profile)

        intermediates: list[str] = []
        if debug_dir is not None:
            intermediates = _write_debug_intermediates(
                dem=dem,
                profile=profile,
                debug_dir=Path(debug_dir),
                method=method,
                window=window,
                azimuth_deg=azimuth_deg,
                anisotropy_weight=anisotropy_weight,
                roughness_weight=roughness_weight,
                structural_weight=structural_weight,
            )

        metadata = {
            "framework": "GeoMorphX",
            "version": "0.1.0",
            "method": method,
            "scales": used_scales,
            "parameters": metadata_params,
            "shape": [int(out.shape[0]), int(out.shape[1])],
            "value_range": ([float(np.nanmin(out)), float(np.nanmax(out))]
                            if np.isfinite(out).any() else [None, None]),
            "intermediates": intermediates,
        }

    metadata["input_dem"] = str(Path(dem_path).resolve())
    metadata["nodata_policy"] = "propagate_unknown"
    out_path_obj = Path(out_path)
    sidecar = out_path_obj.with_suffix(out_path_obj.suffix + ".meta.json")
    sidecar.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return out_path_obj


def compute_rrim_batch(
    dem_dir: str | Path,
    out_dir: str | Path,
    *,
    method: str = "rrim_baseline",
    pattern: str = "*",
    recursive: bool = True,
    scales: Iterable[int] | None = None,
    window: int = 9,
    azimuth_deg: float | Iterable[float] | str = 0.0,
    directional_weight: float = 0.5,
    anisotropy_weight: float = 0.35,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.15,
    save_debug: bool = False,
    tile_size: int = 0,
    flatness_deg: float = 1.0,
    geomorphon_skip: int = 0,
    scratch_dir: str | Path | None = None,
) -> tuple[list[Path], Path]:
    source_dir = Path(dem_dir)
    target_dir = Path(out_dir)
    source_resolved, target_resolved = source_dir.resolve(), target_dir.resolve()
    if target_resolved == source_resolved or source_resolved.is_relative_to(target_resolved):
        raise ValueError("Output directory must not contain the input directory")
    scales = None if scales is None else list(scales)
    target_dir.mkdir(parents=True, exist_ok=True)

    iterator = source_dir.rglob(pattern) if recursive else source_dir.glob(pattern)
    files = [p for p in iterator if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}
             and not p.resolve().is_relative_to(target_resolved)]
    if not files:
        raise ValueError("No DEM files found for compute batch")

    written: list[Path] = []
    manifest: list[dict[str, Any]] = []
    for dem_path in sorted(files):
        rel = dem_path.relative_to(source_dir)
        out_path = target_dir / rel.with_suffix(".tif")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        debug_dir = None
        if save_debug:
            debug_dir = out_path.parent / (out_path.stem + "_debug")

        produced = compute_rrim(
            dem_path=dem_path,
            out_path=out_path,
            method=method,
            scales=scales,
            window=window,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            debug_dir=debug_dir,
            tile_size=tile_size,
            flatness_deg=flatness_deg,
            geomorphon_skip=geomorphon_skip,
            scratch_dir=scratch_dir,
        )
        written.append(produced)
        manifest.append({"input": str(dem_path), "output": str(produced)})

    manifest_path = target_dir / "compute_batch_manifest.json"
    manifest_path.write_text(json.dumps({"items": manifest}, indent=2), encoding="utf-8")
    return written, manifest_path
