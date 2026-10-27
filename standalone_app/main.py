"""Standalone GeoMorphX program (outside QGIS)."""

from __future__ import annotations

import argparse
from pathlib import Path

from geomorphx.methods import METHODS
from geomorphx.api import compute_rrim_batch
from geomorphx.benchmark import run_benchmark_batch

_METHODS = METHODS


def _parse_scales(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geomorphx-standalone",
        description="GeoMorphX standalone batch program",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compute_batch = sub.add_parser("compute-batch", help="Run many DEM files")
    compute_batch.add_argument("--dem-dir", required=True, type=Path)
    compute_batch.add_argument("--out-dir", required=True, type=Path)
    compute_batch.add_argument("--pattern", default="*")
    compute_batch.add_argument("--recursive", action="store_true")
    compute_batch.add_argument("--method", choices=_METHODS, default="rrim_baseline")
    compute_batch.add_argument("--window", type=int, default=9)
    compute_batch.add_argument("--flatness-deg", type=float, default=1.0, help="Geomorphon flatness angle in degrees")
    compute_batch.add_argument("--geomorphon-skip", type=int, default=0, help="Geomorphon inner ray steps to skip")
    compute_batch.add_argument("--scales", default="5,15,45")
    compute_batch.add_argument("--azimuth", type=float, default=45.0)
    compute_batch.add_argument("--directional-weight", type=float, default=0.6)
    compute_batch.add_argument("--anisotropy-weight", type=float, default=0.3)
    compute_batch.add_argument("--roughness-weight", type=float, default=0.25)
    compute_batch.add_argument("--structural-weight", type=float, default=0.2)
    compute_batch.add_argument("--save-debug", action="store_true")
    compute_batch.add_argument("--tile-size", type=int, default=0)
    compute_batch.add_argument("--scratch-dir", type=Path, default=None, help="Directory for retained RRIM raster stages")

    bench_batch = sub.add_parser("benchmark-batch", help="Benchmark many DEM files")
    bench_batch.add_argument("--dem-dir", required=True, type=Path)
    bench_batch.add_argument("--out-dir", required=True, type=Path)
    bench_batch.add_argument("--pattern", default="*")
    bench_batch.add_argument("--recursive", action="store_true")
    bench_batch.add_argument("--repeats", type=int, default=3)
    bench_batch.add_argument("--window", type=int, default=9)
    bench_batch.add_argument("--scales", default="5,15,45")
    bench_batch.add_argument("--azimuth", type=float, default=45.0)
    bench_batch.add_argument("--tile-size", type=int, default=0)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compute-batch":
        outputs, manifest = compute_rrim_batch(
            dem_dir=args.dem_dir,
            out_dir=args.out_dir,
            method=args.method,
            pattern=args.pattern,
            recursive=args.recursive,
            scales=_parse_scales(args.scales),
            window=args.window,
            azimuth_deg=args.azimuth,
            directional_weight=args.directional_weight,
            anisotropy_weight=args.anisotropy_weight,
            roughness_weight=args.roughness_weight,
            structural_weight=args.structural_weight,
            save_debug=args.save_debug,
            scratch_dir=args.scratch_dir,
            flatness_deg=args.flatness_deg,
            geomorphon_skip=args.geomorphon_skip,
            tile_size=args.tile_size,
        )
        print(f"Computed files: {len(outputs)}")
        print(f"Manifest: {manifest}")
        return 0

    if args.command == "benchmark-batch":
        rows, summary_csv, summary_json, summary_md = run_benchmark_batch(
            dem_dir=args.dem_dir,
            out_dir=args.out_dir,
            pattern=args.pattern,
            recursive=args.recursive,
            repeats=args.repeats,
            scales=_parse_scales(args.scales),
            window=args.window,
            azimuth_deg=args.azimuth,
            tile_size=args.tile_size,
        )
        print(f"Benchmark batch inputs: {len(rows)}")
        print(f"Summary CSV: {summary_csv}")
        print(f"Summary JSON: {summary_json}")
        print(f"Summary MD: {summary_md}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
