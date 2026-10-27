import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile


def test_plugin_zip_contains_a_standalone_python_core_and_verified_manifest(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("gmx_bundle_builder", repo / "scripts" / "build_qgis_plugin.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    bundle = builder.build_plugin(repo, tmp_path)
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        prefix = "geomorphx_rrim_suite/"
        assert prefix + "metadata.txt" in names
        assert prefix + "vendor/geomorphx/streaming.py" in names
        assert prefix + "workbench.py" in names
        assert prefix + "recipe_algorithm.py" in names
        assert prefix + "vendor/geomorphx/recipes.py" in names
        assert prefix + "AUTOMATION.md" in names
        assert prefix + "recipe.schema.json" in names
        assert prefix + "examples/terrain_recipe.json" in names
        assert prefix + "method_algorithm.py" in names
        assert prefix + "vendor/core_py/geomorphx_core/raster_backend.py" in names
        assert prefix + "vendor/core_py/geomorphx_core/hydrology.py" in names
        assert not any(".devresources" in name or "__pycache__" in name for name in names)
        assert not any(name.endswith((".pyd", "auth.json")) for name in names)
        manifest = json.loads(archive.read(prefix + "bundle_manifest.json"))
        assert "GDAL (provided by QGIS)" in manifest["runtime_dependencies"]
        assert not any("rasterio" in dependency.lower() for dependency in manifest["runtime_dependencies"])
        for item in manifest["files"]:
            assert hashlib.sha256(archive.read(item["path"])).hexdigest() == item["sha256"]
        archive.extractall(tmp_path / "installed")
    # Run outside the checkout: imports must resolve to the bundled Python core.
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from geomorphx_rrim_suite.suite_imports import ensure_suite_importable; "
        "ensure_suite_importable(); import geomorphx; print(geomorphx.__file__)"
    )
    result = subprocess.run([sys.executable, "-c", code, str(tmp_path / "installed")],
                            cwd=tmp_path, check=True, capture_output=True, text=True)
    assert str(tmp_path / "installed" / "geomorphx_rrim_suite" / "vendor") in result.stdout
