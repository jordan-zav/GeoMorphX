"""CLI entrypoint for GeoMorphX."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geomorphx.methods import METHODS
from geomorphx.api import compute_rrim, compute_rrim_batch
from geomorphx.benchmark import run_benchmark_batch, run_benchmark_suite
from geomorphx.recommendations import available_objectives, recommend
from geomorphx.recipes import execute_recipe, load_recipe, normalize_recipe, save_recipe


def _parse_scales(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _parse_azimuth(raw: str) -> float | list[float]:
    parts = [float(x.strip()) for x in raw.split(",") if x.strip()]
    if len(parts) == 1:
        return parts[0]
    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="geomorphx", description="GeoMorphX CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    compute = sub.add_parser("compute", help="Compute RRIM products from one DEM")
    compute.add_argument("--dem", required=True, type=Path, help="Input DEM GeoTIFF")
    compute.add_argument("--out", required=True, type=Path, help="Output raster GeoTIFF")
    compute.add_argument(
        "--method",
        default="rrim_baseline",
        choices=METHODS,
        help="Processing method",
    )
    compute.add_argument("--window", type=int, default=9, help="Window size (odd, >=3)")
    compute.add_argument("--flatness-deg", type=float, default=1.0, help="Geomorphon flatness angle in degrees")
    compute.add_argument("--geomorphon-skip", type=int, default=0, help="Geomorphon inner ray steps to skip")
    compute.add_argument("--scales", type=str, default="5,15,45", help="Comma-separated multiscale windows")
    compute.add_argument("--azimuth", type=str, default="0.0", help="Directional azimuth(s) in degrees (single value or comma-separated values)")
    compute.add_argument("--directional-weight", type=float, default=0.5, help="Anisotropic directional weight")
    compute.add_argument("--anisotropy-weight", type=float, default=0.35, help="RRIM++ anisotropy weight")
    compute.add_argument("--roughness-weight", type=float, default=0.25, help="RRIM++ roughness weight")
    compute.add_argument("--structural-weight", type=float, default=0.15, help="RRIM++ structural weight")
    compute.add_argument("--debug-dir", type=Path, default=None, help="Optional folder for intermediate rasters")
    compute.add_argument("--tile-size", type=int, default=0, help="Tile size for tiled computing (0 disables)")
    compute.add_argument("--scratch-dir", type=Path, default=None, help="Directory for retained RRIM raster stages")

    compute_batch = sub.add_parser("compute-batch", help="Compute RRIM products for multiple DEM files")
    compute_batch.add_argument("--dem-dir", required=True, type=Path, help="Directory with .tif/.tiff DEM files")
    compute_batch.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    compute_batch.add_argument("--pattern", type=str, default="*", help="Glob pattern for input files")
    compute_batch.add_argument("--recursive", action="store_true", help="Search recursively")
    compute_batch.add_argument(
        "--method",
        default="rrim_baseline",
        choices=METHODS,
        help="Processing method",
    )
    compute_batch.add_argument("--window", type=int, default=9, help="Window size (odd, >=3)")
    compute_batch.add_argument("--flatness-deg", type=float, default=1.0, help="Geomorphon flatness angle in degrees")
    compute_batch.add_argument("--geomorphon-skip", type=int, default=0, help="Geomorphon inner ray steps to skip")
    compute_batch.add_argument("--scales", type=str, default="5,15,45", help="Comma-separated multiscale windows")
    compute_batch.add_argument("--azimuth", type=str, default="0.0", help="Directional azimuth(s) in degrees (single value or comma-separated values)")
    compute_batch.add_argument("--directional-weight", type=float, default=0.5, help="Anisotropic directional weight")
    compute_batch.add_argument("--anisotropy-weight", type=float, default=0.35, help="RRIM++ anisotropy weight")
    compute_batch.add_argument("--roughness-weight", type=float, default=0.25, help="RRIM++ roughness weight")
    compute_batch.add_argument("--structural-weight", type=float, default=0.15, help="RRIM++ structural weight")
    compute_batch.add_argument("--save-debug", action="store_true", help="Save intermediate rasters where applicable")
    compute_batch.add_argument("--tile-size", type=int, default=0, help="Tile size for tiled computing (0 disables)")
    compute_batch.add_argument("--scratch-dir", type=Path, default=None, help="Directory for retained RRIM raster stages")

    benchmark = sub.add_parser("benchmark", help="Run method comparison benchmarks")
    benchmark.add_argument("--out-dir", required=True, type=Path, help="Output directory for benchmark artifacts")
    benchmark.add_argument("--dem", type=Path, default=None, help="Optional DEM path; if omitted uses synthetic DEM")
    benchmark.add_argument("--size", type=int, default=512, help="Synthetic DEM size when --dem is omitted")
    benchmark.add_argument("--repeats", type=int, default=3, help="Number of repeats per method")
    benchmark.add_argument("--window", type=int, default=9, help="Window size (odd, >=3)")
    benchmark.add_argument("--scales", type=str, default="5,15,45", help="Comma-separated multiscale windows")
    benchmark.add_argument("--azimuth", type=str, default="45.0", help="Directional azimuth(s) in degrees (single value or comma-separated values)")
    benchmark.add_argument("--directional-weight", type=float, default=0.6, help="Anisotropic directional weight")
    benchmark.add_argument("--anisotropy-weight", type=float, default=0.3, help="RRIM++ anisotropy weight")
    benchmark.add_argument("--roughness-weight", type=float, default=0.25, help="RRIM++ roughness weight")
    benchmark.add_argument("--structural-weight", type=float, default=0.2, help="RRIM++ structural weight")
    benchmark.add_argument("--tile-size", type=int, default=0, help="Optional tile size for tiled benchmarking")

    batch = sub.add_parser("benchmark-batch", help="Run benchmarks for multiple DEM files")
    batch.add_argument("--dem-dir", required=True, type=Path, help="Directory containing DEM files (.tif/.tiff)")
    batch.add_argument("--out-dir", required=True, type=Path, help="Output directory for batch benchmark artifacts")
    batch.add_argument("--pattern", type=str, default="*", help="Glob pattern for selecting files")
    batch.add_argument("--recursive", action="store_true", help="Search recursively")
    batch.add_argument("--repeats", type=int, default=3, help="Number of repeats per method")
    batch.add_argument("--window", type=int, default=9, help="Window size (odd, >=3)")
    batch.add_argument("--scales", type=str, default="5,15,45", help="Comma-separated multiscale windows")
    batch.add_argument("--azimuth", type=str, default="45.0", help="Directional azimuth(s) in degrees (single value or comma-separated values)")
    batch.add_argument("--directional-weight", type=float, default=0.6, help="Anisotropic directional weight")
    batch.add_argument("--anisotropy-weight", type=float, default=0.3, help="RRIM++ anisotropy weight")
    batch.add_argument("--roughness-weight", type=float, default=0.25, help="RRIM++ roughness weight")
    batch.add_argument("--structural-weight", type=float, default=0.2, help="RRIM++ structural weight")
    batch.add_argument("--tile-size", type=int, default=0, help="Optional tile size for tiled benchmarking")

    compare = sub.add_parser("compare", help="Compare two geomorphometric rasters quantitatively")
    compare.add_argument("--raster1", required=True, type=Path, help="Path to first raster (baseline)")
    compare.add_argument("--raster2", required=True, type=Path, help="Path to second raster (comparison)")
    compare.add_argument("--name1", type=str, default="Baseline", help="Label for raster1")
    compare.add_argument("--name2", type=str, default="Comparison", help="Label for raster2")
    compare.add_argument("--out-report", type=Path, default=None, help="Markdown report output path")
    compare.add_argument("--out-json", type=Path, default=None, help="JSON metrics output path")

    recommend_parser = sub.add_parser("recommend", help="Recommend reproducible terrain-visualization recipes")
    recommend_parser.add_argument("--objective", required=True, choices=available_objectives(), help="Mapping objective")
    recommend_parser.add_argument("--pixel-size-m", required=True, type=float, help="DEM ground sampling distance in metres")
    recommend_parser.add_argument("--feature-min-m", type=float, default=None, help="Minimum target feature size in metres")
    recommend_parser.add_argument("--feature-max-m", type=float, default=None, help="Maximum target feature size in metres")
    recommend_parser.add_argument("--out", type=Path, default=None, help="Optional JSON recipe output path")

    run_recipe = sub.add_parser("run-recipe", help="Run a portable or legacy GeoMorphX recipe")
    run_recipe.add_argument("--recipe", required=True, type=Path, help="Recipe JSON from the panel, CLI or Python API")
    run_recipe.add_argument("--dem", required=True, type=Path, help="Input DEM GeoTIFF")
    run_recipe.add_argument("--out-dir", required=True, type=Path, help="Directory for generated layers and manifest")

    validate_recipe = sub.add_parser("validate-recipe", help="Validate all recipe parameters without reading a DEM")
    validate_recipe.add_argument("--recipe", required=True, type=Path)
    validate_recipe.add_argument("--out", type=Path, help="Optional canonical JSON output")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compute":
        scales = _parse_scales(args.scales)
        azimuth_val = _parse_azimuth(args.azimuth)
        out = compute_rrim(
            dem_path=args.dem,
            out_path=args.out,
            method=args.method,
            scales=scales,
            window=args.window,
            azimuth_deg=azimuth_val,
            directional_weight=args.directional_weight,
            anisotropy_weight=args.anisotropy_weight,
            roughness_weight=args.roughness_weight,
            structural_weight=args.structural_weight,
            debug_dir=args.debug_dir,
            scratch_dir=args.scratch_dir,
            flatness_deg=args.flatness_deg,
            geomorphon_skip=args.geomorphon_skip,
            tile_size=args.tile_size,
        )
        print(f"Generated: {out}")
        print(f"Metadata: {out}.meta.json")
        return 0

    if args.command == "compute-batch":
        scales = _parse_scales(args.scales)
        azimuth_val = _parse_azimuth(args.azimuth)
        outputs, manifest = compute_rrim_batch(
            dem_dir=args.dem_dir,
            out_dir=args.out_dir,
            method=args.method,
            pattern=args.pattern,
            recursive=args.recursive,
            scales=scales,
            window=args.window,
            azimuth_deg=azimuth_val,
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

    if args.command == "benchmark":
        scales = _parse_scales(args.scales)
        azimuth_val = _parse_azimuth(args.azimuth)
        rows, csv_path, json_path, md_path, png_path = run_benchmark_suite(
            out_dir=args.out_dir,
            dem_path=args.dem,
            size=args.size,
            repeats=args.repeats,
            scales=scales,
            window=args.window,
            azimuth_deg=azimuth_val,
            directional_weight=args.directional_weight,
            anisotropy_weight=args.anisotropy_weight,
            roughness_weight=args.roughness_weight,
            structural_weight=args.structural_weight,
            tile_size=args.tile_size,
        )
        print(f"Benchmark methods: {len(rows)}")
        print(f"CSV: {csv_path}")
        print(f"JSON: {json_path}")
        print(f"Report: {md_path}")
        if png_path is None:
            print("PNG: not generated (matplotlib not available)")
        else:
            print(f"PNG: {png_path}")
        return 0

    if args.command == "benchmark-batch":
        scales = _parse_scales(args.scales)
        azimuth_val = _parse_azimuth(args.azimuth)
        rows, summary_csv, summary_json, summary_md = run_benchmark_batch(
            dem_dir=args.dem_dir,
            out_dir=args.out_dir,
            pattern=args.pattern,
            recursive=args.recursive,
            repeats=args.repeats,
            scales=scales,
            window=args.window,
            azimuth_deg=azimuth_val,
            directional_weight=args.directional_weight,
            anisotropy_weight=args.anisotropy_weight,
            roughness_weight=args.roughness_weight,
            structural_weight=args.structural_weight,
            tile_size=args.tile_size,
        )
        print(f"Benchmark batch inputs: {len(rows)}")
        print(f"Summary CSV: {summary_csv}")
        print(f"Summary JSON: {summary_json}")
        print(f"Summary MD: {summary_md}")
        return 0

    if args.command == "compare":
        from core_py.geomorphx_core.io import read_dem
        from geomorphx.comparison import compare_rasters, generate_comparison_report

        raster1, _ = read_dem(args.raster1)
        raster2, _ = read_dem(args.raster2)

        metrics = compare_rasters(raster1, raster2, name1=args.name1, name2=args.name2)

        if args.out_json:
            with open(args.out_json, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            print(f"Metrics saved to: {args.out_json}")

        report = generate_comparison_report(
            metrics,
            name1=args.name1,
            name2=args.name2,
            path1=str(args.raster1),
            path2=str(args.raster2),
        )

        if args.out_report:
            with open(args.out_report, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to: {args.out_report}")
        else:
            print(report)

        return 0

    if args.command == "recommend":
        recipe = recommend(
            args.objective,
            pixel_size_m=args.pixel_size_m,
            feature_min_m=args.feature_min_m,
            feature_max_m=args.feature_max_m,
        )
        recipe = normalize_recipe(recipe)
        rendered = json.dumps(recipe, indent=2, ensure_ascii=False)
        if args.out is not None:
            save_recipe(recipe, args.out)
            print(f"Recipe: {args.out}")
        else:
            print(rendered)
        return 0

    if args.command == "run-recipe":
        recipe = load_recipe(args.recipe)
        outputs, manifest = execute_recipe(recipe, dem_path=args.dem, out_dir=args.out_dir)
        print(f"Generated layers: {len(outputs)}")
        print(f"Manifest: {manifest}")
        return 0

    if args.command == "validate-recipe":
        recipe = load_recipe(args.recipe)
        if args.out is not None:
            save_recipe(recipe, args.out)
        print(f"Valid recipe: {len(recipe['products'])} products ({recipe['schema_version']})")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
