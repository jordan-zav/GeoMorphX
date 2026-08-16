"""High-level API for GeoMorphX workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from core_py.geomorphx_core.io import read_dem, write_raster
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
) -> tuple[np.ndarray, list[int], dict[str, Any]]:
    from core_py.geomorphx_core.rrim import _parse_azimuths
    parsed_azimuths = _parse_azimuths(azimuth_deg)
    metadata_azimuth = parsed_azimuths if len(parsed_azimuths) > 1 else (parsed_azimuths[0] if parsed_azimuths else 0.0)

    metadata_params: dict[str, Any] = {"window": window}
    if method == "rrim_baseline":
        out = rrim_baseline(dem, window=window)
        used_scales: list[int] = [window]
    elif method == "rrim_multiscale":
        used_scales = [int(s) for s in (scales or [5, 15, 45])]
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
        used_scales = [int(s) for s in (scales or [5, 15, 45])]
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
        used_scales = [int(s) for s in (scales or [5, 15, 45])]
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
        out = slope_deg(dem)
    elif method == "aspect":
        used_scales = [window]
        out = aspect_deg(dem)
    elif method == "hillshade":
        used_scales = [window]
        first_az = float(parsed_azimuths[0]) if parsed_azimuths else 315.0
        out = hillshade(dem, azimuth_deg=first_az, altitude_deg=45.0, z_factor=1.0)
        metadata_params["azimuth_deg"] = first_az
    elif method == "multidirectional_hillshade":
        used_scales = [window]
        out = multidirectional_hillshade(dem)
        metadata_params["directions"] = 8
    elif method == "positive_openness":
        used_scales = [window]
        out = positive_openness(dem, radius=max(1, window // 2))
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "negative_openness":
        used_scales = [window]
        out = negative_openness(dem, radius=max(1, window // 2))
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "sky_view_factor":
        used_scales = [window]
        out = sky_view_factor(dem, radius=max(1, window // 2))
        metadata_params["radius_px"] = max(1, window // 2)
        metadata_params["directions"] = 16
    elif method == "curvature_profile":
        used_scales = [window]
        out = profile_curvature(dem)
    elif method == "curvature_plan":
        used_scales = [window]
        out = plan_curvature(dem)
    elif method == "curvature_mean":
        used_scales = [window]
        out = mean_curvature(dem)
    elif method == "tpi":
        used_scales = [window]
        out = tpi(dem, window=window)
    elif method == "tri":
        used_scales = [window]
        out = tri(dem, window=window)
    elif method == "wetness_proxy":
        used_scales = [window]
        out = wetness_proxy(dem, window=window)
    else:
        raise ValueError(
            "method must be rrim_baseline, rrim_multiscale, rrim_anisotropic, rrim_anisotropic_multiscale, rrim_structural, rrim_structural_multiscale, rrim_plus, slope, aspect, hillshade, curvature_profile, curvature_plan, curvature_mean, tpi, tri, or wetness_proxy"
        )

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
) -> Path:
    if tile_size > 0:
        from geomorphx.tiling import compute_tiled
        import rasterio

        compute_tiled(
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
            value_range = [vmin, vmax] if vmin != float("inf") else [0.0, 0.0]

        used_scales = [window]
        if method in ("rrim_multiscale", "rrim_anisotropic_multiscale", "rrim_structural_multiscale") and scales:
            used_scales = [int(s) for s in scales]

        metadata_params = {"window": window}
        from core_py.geomorphx_core.rrim import _parse_azimuths
        parsed_azimuths = _parse_azimuths(azimuth_deg)
        metadata_azimuth = parsed_azimuths if len(parsed_azimuths) > 1 else (parsed_azimuths[0] if parsed_azimuths else 0.0)
        metadata_params["azimuth_deg"] = metadata_azimuth

        metadata = {
            "framework": "GeoMorphX",
            "version": "0.4.0-beta",
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
            "version": "0.4.0-beta",
            "method": method,
            "scales": used_scales,
            "parameters": metadata_params,
            "shape": [int(out.shape[0]), int(out.shape[1])],
            "value_range": [float(np.nanmin(out)), float(np.nanmax(out))],
            "intermediates": intermediates,
        }

    out_path_obj = Path(out_path)
    sidecar = out_path_obj.with_suffix(out_path_obj.suffix + ".meta.json")
    sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
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
) -> tuple[list[Path], Path]:
    source_dir = Path(dem_dir)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    iterator = source_dir.rglob(pattern) if recursive else source_dir.glob(pattern)
    files = [p for p in iterator if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}]
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
        )
        written.append(produced)
        manifest.append({"input": str(dem_path), "output": str(produced)})

    manifest_path = target_dir / "compute_batch_manifest.json"
    manifest_path.write_text(json.dumps({"items": manifest}, indent=2), encoding="utf-8")
    return written, manifest_path
