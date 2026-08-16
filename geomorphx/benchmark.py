"""Benchmark utilities for method comparison."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
import statistics
import time
from typing import Iterable

import numpy as np

from core_py.geomorphx_core.io import read_dem
from geomorphx.api import compute_rrim_array


@dataclass(frozen=True)
class BenchmarkRow:
    method: str
    repeats: int
    runtime_ms_mean: float
    runtime_ms_std: float
    output_min: float
    output_max: float
    output_mean: float
    output_std: float


@dataclass(frozen=True)
class BatchBenchmarkRow:
    dem_path: str
    output_dir: str
    fastest_method: str
    fastest_runtime_ms: float


def generate_synthetic_dem(size: int = 512) -> np.ndarray:
    """Generate a deterministic synthetic DEM for benchmarks."""
    x = np.linspace(0.0, 8.0 * np.pi, size, dtype=np.float32)
    y = np.linspace(0.0, 8.0 * np.pi, size, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    dem = (
        1200.0
        + 120.0 * np.sin(xx)
        + 90.0 * np.cos(yy)
        + 50.0 * np.sin(0.5 * xx + 1.7 * yy)
        + 20.0 * np.sin(3.0 * xx) * np.cos(2.0 * yy)
    )
    return dem.astype(np.float32)


def _split_tiles(dem: np.ndarray, tile_size: int) -> list[np.ndarray]:
    if tile_size <= 0:
        return [dem]
    if tile_size < 16:
        raise ValueError("tile_size must be >= 16 when provided")

    tiles: list[np.ndarray] = []
    rows, cols = dem.shape
    for r0 in range(0, rows, tile_size):
        for c0 in range(0, cols, tile_size):
            tile = dem[r0 : r0 + tile_size, c0 : c0 + tile_size]
            if tile.size > 0:
                tiles.append(tile)
    return tiles


def _run_one(
    dem: np.ndarray,
    method: str,
    *,
    scales: Iterable[int],
    window: int,
    azimuth_deg: float,
    directional_weight: float,
    anisotropy_weight: float,
    roughness_weight: float,
    structural_weight: float,
) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    out, _, _ = compute_rrim_array(
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
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return out, elapsed_ms


def benchmark_methods(
    dem: np.ndarray,
    *,
    methods: Iterable[str],
    repeats: int = 3,
    scales: Iterable[int] = (5, 15, 45),
    window: int = 9,
    azimuth_deg: float = 45.0,
    directional_weight: float = 0.6,
    anisotropy_weight: float = 0.3,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.2,
    tile_size: int = 0,
) -> list[BenchmarkRow]:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    tiles = _split_tiles(dem, tile_size=tile_size)
    rows: list[BenchmarkRow] = []
    for method in methods:
        runtimes: list[float] = []
        last_outputs: list[np.ndarray] = []
        for _ in range(repeats):
            repeat_runtime = 0.0
            current_outputs: list[np.ndarray] = []
            for tile in tiles:
                out, elapsed_ms = _run_one(
                    tile,
                    method,
                    scales=scales,
                    window=window,
                    azimuth_deg=azimuth_deg,
                    directional_weight=directional_weight,
                    anisotropy_weight=anisotropy_weight,
                    roughness_weight=roughness_weight,
                    structural_weight=structural_weight,
                )
                repeat_runtime += elapsed_ms
                current_outputs.append(out)
            runtimes.append(repeat_runtime)
            last_outputs = current_outputs

        flat = np.concatenate([arr.ravel() for arr in last_outputs], axis=0)
        rows.append(
            BenchmarkRow(
                method=method,
                repeats=repeats,
                runtime_ms_mean=float(statistics.mean(runtimes)),
                runtime_ms_std=float(statistics.pstdev(runtimes)),
                output_min=float(np.nanmin(flat)),
                output_max=float(np.nanmax(flat)),
                output_mean=float(np.nanmean(flat)),
                output_std=float(np.nanstd(flat)),
            )
        )
    return rows


def save_benchmark_outputs(
    out_dir: str | Path,
    rows: list[BenchmarkRow],
    *,
    source: str,
    dem_shape: tuple[int, int],
    tile_size: int,
) -> tuple[Path, Path, Path, Path | None]:
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    csv_path = out_root / "benchmark_results.csv"
    json_path = out_root / "benchmark_results.json"
    md_path = out_root / "benchmark_report.md"
    png_path: Path | None = out_root / "benchmark_runtime.png"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    payload = {
        "source": source,
        "dem_shape": [int(dem_shape[0]), int(dem_shape[1])],
        "tile_size": int(tile_size),
        "rows": [asdict(row) for row in rows],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ranked = sorted(rows, key=lambda item: item.runtime_ms_mean)
    md_lines = [
        "# GeoMorphX Benchmark Report",
        "",
        f"- Source: `{source}`",
        f"- DEM shape: `{dem_shape[0]} x {dem_shape[1]}`",
        f"- Tile size: `{tile_size}` (0 = disabled)",
        "",
        "## Ranking (Fastest to Slowest)",
        "",
    ]
    for idx, row in enumerate(ranked, start=1):
        md_lines.append(f"{idx}. `{row.method}` - {row.runtime_ms_mean:.3f} ms")
    md_lines.extend(
        [
            "",
            "## Results Table",
            "",
            "| method | repeats | runtime_ms_mean | runtime_ms_std | output_min | output_max | output_mean | output_std |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        md_lines.append(
            f"| {row.method} | {row.repeats} | {row.runtime_ms_mean:.6f} | {row.runtime_ms_std:.6f} | "
            f"{row.output_min:.6f} | {row.output_max:.6f} | {row.output_mean:.6f} | {row.output_std:.6f} |"
        )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        png_path = None
    else:
        names = [row.method for row in rows]
        means = [row.runtime_ms_mean for row in rows]
        stds = [row.runtime_ms_std for row in rows]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(names, means, yerr=stds, capsize=5)
        ax.set_title("GeoMorphX Benchmark Runtime (ms)")
        ax.set_ylabel("Runtime (ms)")
        ax.set_xlabel("Method")
        ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()
        fig.savefig(png_path, dpi=160)
        plt.close(fig)

    return csv_path, json_path, md_path, png_path


def run_benchmark_suite(
    *,
    out_dir: str | Path,
    dem_path: str | Path | None = None,
    size: int = 512,
    repeats: int = 3,
    scales: Iterable[int] = (5, 15, 45),
    window: int = 9,
    azimuth_deg: float = 45.0,
    directional_weight: float = 0.6,
    anisotropy_weight: float = 0.3,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.2,
    tile_size: int = 0,
) -> tuple[list[BenchmarkRow], Path, Path, Path, Path | None]:
    methods = [
        "rrim_baseline",
        "rrim_multiscale",
        "rrim_anisotropic",
        "rrim_anisotropic_multiscale",
        "rrim_structural",
        "rrim_structural_multiscale",
        "rrim_plus",
    ]

    if dem_path is None:
        dem = generate_synthetic_dem(size=size)
        source = f"synthetic:{size}"
    else:
        dem, _ = read_dem(dem_path)
        source = str(Path(dem_path))

    rows = benchmark_methods(
        dem,
        methods=methods,
        repeats=repeats,
        scales=scales,
        window=window,
        azimuth_deg=azimuth_deg,
        directional_weight=directional_weight,
        anisotropy_weight=anisotropy_weight,
        roughness_weight=roughness_weight,
        structural_weight=structural_weight,
        tile_size=tile_size,
    )
    csv_path, json_path, md_path, png_path = save_benchmark_outputs(
        out_dir=out_dir,
        rows=rows,
        source=source,
        dem_shape=(int(dem.shape[0]), int(dem.shape[1])),
        tile_size=tile_size,
    )
    return rows, csv_path, json_path, md_path, png_path


def run_benchmark_batch(
    *,
    dem_dir: str | Path,
    out_dir: str | Path,
    pattern: str = "*",
    recursive: bool = True,
    repeats: int = 3,
    scales: Iterable[int] = (5, 15, 45),
    window: int = 9,
    azimuth_deg: float = 45.0,
    directional_weight: float = 0.6,
    anisotropy_weight: float = 0.3,
    roughness_weight: float = 0.25,
    structural_weight: float = 0.2,
    tile_size: int = 0,
) -> tuple[list[BatchBenchmarkRow], Path, Path, Path]:
    source_dir = Path(dem_dir)
    if not source_dir.exists():
        raise ValueError(f"dem_dir not found: {source_dir}")

    iterator = source_dir.rglob(pattern) if recursive else source_dir.glob(pattern)
    dem_files = [p for p in iterator if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}]
    if not dem_files:
        raise ValueError("No DEM files found for batch benchmark")

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    rows: list[BatchBenchmarkRow] = []
    for dem_path in sorted(dem_files):
        safe_name = dem_path.stem
        target = out_root / safe_name
        bench_rows, _, _, _, _ = run_benchmark_suite(
            out_dir=target,
            dem_path=dem_path,
            repeats=repeats,
            scales=scales,
            window=window,
            azimuth_deg=azimuth_deg,
            directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            tile_size=tile_size,
        )
        fastest = min(bench_rows, key=lambda item: item.runtime_ms_mean)
        rows.append(
            BatchBenchmarkRow(
                dem_path=str(dem_path),
                output_dir=str(target),
                fastest_method=fastest.method,
                fastest_runtime_ms=fastest.runtime_ms_mean,
            )
        )

    summary_csv = out_root / "batch_summary.csv"
    summary_json = out_root / "batch_summary.json"
    summary_md = out_root / "batch_summary.md"

    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    summary_json.write_text(
        json.dumps({"items": [asdict(row) for row in rows]}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# GeoMorphX Batch Benchmark Summary",
        "",
        f"- Inputs: `{len(rows)}` DEM files",
        "",
        "| dem_path | output_dir | fastest_method | fastest_runtime_ms |",
        "|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.dem_path} | {row.output_dir} | {row.fastest_method} | {row.fastest_runtime_ms:.6f} |"
        )
    summary_md.write_text("\n".join(lines), encoding="utf-8")

    return rows, summary_csv, summary_json, summary_md
