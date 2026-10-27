"""Build a QGIS ZIP with the Python core, without local configuration or binaries."""

from __future__ import annotations

import argparse
import configparser
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


def build_plugin(repo_root: Path, out_dir: Path) -> Path:
    repo = repo_root.resolve()
    required = [repo / "qgis_plugin" / "metadata.txt", repo / "geomorphx" / "api.py",
                repo / "core_py" / "geomorphx_core" / "rrim.py"]
    if not all(path.is_file() for path in required):
        raise ValueError("Incomplete GeoMorphX repository")
    package = "geomorphx_rrim_suite"
    files = []
    for folder, archive_root, extensions in (
        (repo / "qgis_plugin", package, {".py", ".png", ".svg", ".txt", ".md", ".ui", ".qrc"}),
        (repo / "geomorphx", f"{package}/vendor/geomorphx", {".py"}),
        (repo / "core_py", f"{package}/vendor/core_py", {".py"}),
        (repo / "examples/automation", f"{package}/examples", {".py", ".json", ".md"}),
    ):
        for source in sorted(folder.rglob("*")):
            if not source.is_file() or source.suffix.lower() not in extensions:
                continue
            if "__pycache__" in source.parts:
                continue
            if not source.resolve().is_relative_to(repo):
                raise ValueError(f"Refusing to package a file outside the repository: {source}")
            files.append((source, f"{archive_root}/{source.relative_to(folder).as_posix()}"))
    files.append((repo / "LICENSE", f"{package}/LICENSE"))
    files.append((repo / "docs/AUTOMATION.md", f"{package}/AUTOMATION.md"))
    files.append((repo / "docs/AUTOMATIZACION.md", f"{package}/AUTOMATIZACION.md"))
    files.append((repo / "docs/recipe.schema.json", f"{package}/recipe.schema.json"))
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    metadata = configparser.ConfigParser()
    metadata.read(repo / "qgis_plugin/metadata.txt", encoding="utf-8")
    version = metadata["general"]["version"]
    target = out_dir / f"geomorphx_rrim_suite_{version}_{timestamp}.zip"
    manifest = {"built_at_utc": timestamp, "backend": "python",
                "runtime_dependencies": ["numpy>=1.24", "GDAL (provided by QGIS)"], "files": []}
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, name in files:
            data = source.read_bytes()
            archive.writestr(name, data)
            manifest["files"].append({"path": name, "sha256": hashlib.sha256(data).hexdigest()})
        archive.writestr(f"{package}/bundle_manifest.json", json.dumps(manifest, indent=2))
        archive.writestr(f"{package}/INSTALL.txt", (
            "Install this ZIP using QGIS: Plugins > Manage and Install Plugins > Install from ZIP.\n"
            "The Python core is included; Rust is not required.\n"
            "Uses NumPy and GDAL supplied by QGIS; Rasterio is optional.\n"
            "This archive does not install or change interpreter dependencies.\n"
            "Restart QGIS after installation if an older GeoMorphX version was loaded.\n"
            "Open Raster > GeoMorphX > GeoMorphX Terrain Workbench, or the Processing toolbox.\n"
            "See README.md for validation scope and scientific limitations.\n"
        ))
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(build_plugin(Path(__file__).resolve().parents[1], args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
