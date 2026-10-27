"""Reproducible analytical/synthetic checks and exportable RRIM comparison figure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rasterio
from rasterio.transform import from_origin

from core_py.geomorphx_core.hydrology import _priority_flood, _mfd_accumulate
from core_py.geomorphx_core.io import read_dem
from core_py.geomorphx_core.terrain import slope_deg, tri_riley
from geomorphx.api import compute_rrim, compute_rrim_array


def run_validation(out_dir):
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    plane = np.tile(np.arange(17, dtype=np.float32) * 2, (17, 1))
    slope_error = float(np.max(np.abs(slope_deg(plane, cell_size=(2, 2)) - 45)))
    peak = np.zeros((9, 9), dtype=np.float32)
    peak[4, 4] = 10
    tri_error = abs(float(tri_riley(peak)[4, 4]) - np.sqrt(800))
    divergent = np.zeros((3, 3))
    divergent[1, 1] = 1
    filled, parents = _priority_flood(divergent)
    accumulation, outlets = _mfd_accumulate(filled, parents, (1, 1))
    flow_error = abs(float(accumulation[outlets].sum()) - 9)

    y, x = np.mgrid[:65, :79]
    dem = (30 * np.sin(x / 9) + 20 * np.cos(y / 11) + .03 * (x - 39) ** 2).astype(np.float32)
    dem[26:29, 35:38] = np.nan
    source, streamed = target / "synthetic_dem.tif", target / "rrim_streamed.tif"
    with rasterio.open(source, "w", driver="GTiff", count=1, height=65, width=79,
                       dtype="float32", crs="EPSG:32718", nodata=np.nan,
                       transform=from_origin(500000, 9000000, 1, 1)) as dst:
        dst.write(dem, 1)
    kwargs = dict(method="rrim_plus", window=7, azimuth_deg=[0, 45, 90, 135])
    reference, _, _ = compute_rrim_array(dem, **kwargs)
    compute_rrim(source, streamed, tile_size=16, scratch_dir=target / "stages", **kwargs)
    tiled, _ = read_dem(streamed)
    difference = np.abs(tiled - reference)
    max_error = float(np.nanmax(difference))
    mask_equal = bool(np.array_equal(np.isnan(tiled), np.isnan(reference)))
    checks = {"plane_slope_45_degrees": slope_error < 1e-5,
              "riley_peak_sqrt_800": bool(tri_error < 1e-4),
              "mfd_runoff_conservation": flow_error < 1e-12,
              "rrim_stream_equivalence": max_error < 3e-6,
              "rrim_nodata_mask_equal": mask_equal}
    result = {"validation_scope": "analytical_and_synthetic_only", "checks": checks,
              "slope_max_error_deg": slope_error, "tri_peak_error": float(tri_error),
              "mfd_outlet_runoff_error": flow_error, "rrim_max_abs_error": max_error}
    (target / "validation.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Synthetic validation failed: {checks}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for ax, arr, title, cmap in zip(axes.flat,
        (dem, reference, tiled, difference),
        ("Synthetic DEM with NoData", "RRIM+ full array", "RRIM+ global windowed passes", "Absolute difference"),
        ("terrain", "gray", "gray", "magma")):
        limits = {"vmin": 0, "vmax": max(max_error, 3e-6)} if title == "Absolute difference" else (
            {"vmin": 0, "vmax": 1} if title.startswith("RRIM+") else {})
        artist = ax.imshow(arr, cmap=cmap, **limits)
        ax.set_title(title)
        ax.set_xlabel("Column (1 m pixels)")
        ax.set_ylabel("Row")
        fig.colorbar(artist, ax=ax, shrink=.8)
    fig.suptitle(f"Synthetic numerical validation — maximum RRIM difference {max_error:.3g}")
    fig.savefig(target / "synthetic_validation.png", dpi=180)
    fig.savefig(target / "synthetic_validation.pdf")
    plt.close(fig)
    lines = ["# Validación sintética de GeoMorphX", "", "Alcance: casos analíticos y sintéticos; no sustituye validación de campo.", ""]
    lines.extend(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
    lines.extend(["", f"Diferencia máxima RRIM completo frente a bloques: {max_error:.9g}.",
                  "", "Productos: validation.json, synthetic_validation.png y synthetic_validation.pdf."])
    (target / "validation.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_validation(args.out_dir), indent=2))


if __name__ == "__main__":
    main()
