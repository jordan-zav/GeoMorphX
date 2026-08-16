from pathlib import Path

import numpy as np

import geomorphx.benchmark as bench
from geomorphx.benchmark import generate_synthetic_dem, run_benchmark_batch, run_benchmark_suite


def test_generate_synthetic_dem_shape():
    dem = generate_synthetic_dem(size=64)
    assert dem.shape == (64, 64)


def test_run_benchmark_suite_writes_outputs(tmp_path: Path):
    rows, csv_path, json_path, md_path, png_path = run_benchmark_suite(
        out_dir=tmp_path,
        size=64,
        repeats=1,
        scales=[5, 9],
        window=5,
    )
    assert len(rows) == 7
    assert any(row.method == "rrim_structural_multiscale" for row in rows)
    assert csv_path.exists()
    assert json_path.exists()
    assert md_path.exists()
    if png_path is not None:
        assert png_path.exists()


def test_run_benchmark_suite_tile_mode(tmp_path: Path):
    rows, csv_path, json_path, md_path, _ = run_benchmark_suite(
        out_dir=tmp_path,
        size=96,
        repeats=1,
        scales=[5, 9],
        window=5,
        tile_size=32,
    )
    assert len(rows) == 7
    assert any(row.method == "rrim_structural_multiscale" for row in rows)
    assert csv_path.exists()
    assert json_path.exists()
    assert md_path.exists()


def test_run_benchmark_batch_writes_summary(tmp_path: Path, monkeypatch):
    dem_dir = tmp_path / "dems"
    dem_dir.mkdir(parents=True, exist_ok=True)
    (dem_dir / "a.tif").write_bytes(b"fake")
    (dem_dir / "b.tiff").write_bytes(b"fake")

    fake_dem = np.ones((32, 32), dtype=np.float32)

    def fake_read_dem(path):
        return fake_dem, {}

    monkeypatch.setattr(bench, "read_dem", fake_read_dem)

    rows, summary_csv, summary_json, summary_md = run_benchmark_batch(
        dem_dir=dem_dir,
        out_dir=tmp_path / "out",
        pattern="*",
        recursive=False,
        repeats=1,
        scales=[5, 9],
        window=5,
        tile_size=16,
    )

    assert len(rows) == 2
    assert summary_csv.exists()
    assert summary_json.exists()
    assert summary_md.exists()
