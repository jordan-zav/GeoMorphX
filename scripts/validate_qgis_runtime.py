"""Exercise the distributable ZIP in a real QGIS Python runtime, offscreen.

Run with QGIS's python-qgis launcher through DEVRESOURCES_RUN.cmd. This uses
an isolated profile and does not install a plugin in the user's QGIS profile.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["GEOMORPHX_RASTER_BACKEND"] = "gdal"
os.environ.setdefault("MPLBACKEND", "Agg")


def exercise(app):
    from osgeo import gdal, osr
    import numpy as np
    from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsProcessingContext, QgsProcessingFeedback, Qgis
    from qgis.PyQt.QtWidgets import QMainWindow, QWidget
    from qgis.PyQt.QtCore import Qt

    repo = Path(__file__).resolve().parents[1]
    root = Path(os.environ["DEVRESOURCES_SESSION"]) / "qgis_runtime"
    root.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location("gmx_builder", repo / "scripts/build_qgis_plugin.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    bundle = builder.build_plugin(repo, root)
    with zipfile.ZipFile(bundle) as archive:
        archive.extractall(root / "plugins")
    sys.path.insert(0, str(root / "plugins"))
    # Processing ships with QGIS but is outside the default Python module path.
    sys.path.append(str(Path(QgsApplication.prefixPath()) / "python/plugins"))
    sys.path.append(str(Path(QgsApplication.prefixPath()) / "python/plugins"))
    from processing.core.Processing import Processing
    import processing
    Processing.initialize()
    from geomorphx_rrim_suite import classFactory
    plugin = classFactory(None)
    plugin.initProcessing()
    provider = plugin.provider
    provider_id = provider.id()
    algorithm_ids = [a.id() for a in provider.algorithms()]
    assert len(algorithm_ids) == 43, algorithm_ids

    from geomorphx.api import compute_rrim_array
    from geomorphx.methods import METHODS
    from core_py.geomorphx_core.io import read_dem
    from geomorphx.validation import inspect_dem
    from geomorphx_rrim_suite.workbench import validate_recipe, ProductTask
    y, x = np.mgrid[:25, :27]
    dem = (100 + .1 * x * x + 4 * np.cos(y / 4) + .3 * y).astype(np.float32)
    dem[3, 3] = np.nan
    inputs = root / "inputs"; inputs.mkdir()
    source = inputs / "synthetic_dem.tif"
    crs = osr.SpatialReference(); crs.ImportFromEPSG(32718)
    ds = gdal.GetDriverByName("GTiff").Create(str(source), 27, 25, 1, gdal.GDT_Float32)
    ds.SetProjection(crs.ExportToWkt()); ds.SetGeoTransform((400000, 3, 0, 8600000, 0, -2))
    ds.GetRasterBand(1).SetNoDataValue(-9999)
    ds.GetRasterBand(1).WriteArray(np.where(np.isnan(dem), -9999, dem))
    ds = None
    info = inspect_dem(source)
    assert info["cell_size_m"] == [2, 3]
    parameters = dict(window=5, scales=[3, 5], azimuth_deg="0,45", tile_size=7,
                      flatness_deg=1., geomorphon_skip=0, directional_weight=.5,
                      anisotropy_weight=.35, roughness_weight=.25, structural_weight=.15)
    comparisons = []
    for method in METHODS:
        output = root / (method + ".tif")
        context, feedback = QgsProcessingContext(), QgsProcessingFeedback()
        args = dict(INPUT_DEM=str(source), OUTPUT=str(output), WINDOW=5, SCALES="3,5", AZIMUTH=45.,
                    TILE_SIZE=7, FLATNESS=1., GEOMORPHON_SKIP=0,
                    DIRECTIONAL_WEIGHT=.5, ANISOTROPY_WEIGHT=.35, ROUGHNESS_WEIGHT=.25, STRUCTURAL_WEIGHT=.15)
        processing.run(provider.id() + ":terrain_" + method, args, context=context, feedback=feedback)
        actual, profile = read_dem(output)
        expected, _, _ = compute_rrim_array(dem, method=method, cell_size=(2, 3),
                                           **{k: v for k, v in parameters.items() if k != "tile_size" and k != "azimuth_deg"}, azimuth_deg=45.)
        np.testing.assert_allclose(actual, expected, atol=2e-5, rtol=2e-5, equal_nan=True)
        assert profile["crs"].to_epsg() == 32718
        assert np.isnan(actual[3, 3])
        comparisons.append(method)
        print("PASS Processing:", method, flush=True)

    # Batch formerly discarded these GUI parameters; verify the actual sidecar.
    processing.run(provider.id() + ":gmx_suite_compute_batch", dict(
        DEM_DIR=str(inputs), OUT_DIR=str(root / "batch"), METHOD=METHODS.index("geomorphons"),
        WINDOW=7, SCALES="3,5", TILE_SIZE=7, FLATNESS=2.5, GEOMORPHON_SKIP=1,
    ))
    batch_meta = json.loads((root / "batch/synthetic_dem.tif.meta.json").read_text())
    assert batch_meta["parameters"]["tile_size"] == 7, batch_meta
    assert batch_meta["parameters"]["flatness_deg"] == 2.5, batch_meta

    for name, outputs in (
        ("gmx_curvature", ["OUT_PROFILE", "OUT_PLAN", "OUT_MEAN"]),
        ("gmx_tpi_twi", ["OUT_TPI_SMALL", "OUT_TPI_LARGE", "OUT_WETNESS"]),
        ("gmx_geomorphons", ["OUTPUT_CLASS", "OUTPUT_CONF"]),
        ("gmx_geomorphons_los", ["OUTPUT_CLASS", "OUTPUT_TERNARY"]),
    ):
        algorithm = next((a for a in provider.algorithms() if a.name() == name), None)
        if algorithm is None:
            raise AssertionError(f"Missing block {name}")
        args = dict(INPUT_DEM=str(source), **{key: str(root / f"{name}_{key}.tif") for key in outputs})
        processing.run(algorithm.id(), args)

    processing.run(provider.id() + ":gmx_suite_compute", dict(
        INPUT_DEM=str(source), METHOD=METHODS.index("tri_riley"),
        OUTPUT=str(root / "suite_tri.tif"), WINDOW=3, TILE_SIZE=7,
    ))
    classic = processing.run(provider.id() + ":rrim_generator", dict(
        INPUT_RASTER=str(source), AUTO_NORMALIZE=False,
        OUT_SLOPE=str(root / "classic_slope.tif"), OUT_DIFF=str(root / "classic_openness.tif"),
    ))
    rgb = root / "classic_rgb.tif"
    processing.run(provider.id() + ":rrim_rgb_composer", dict(
        INPUT_SLOPE=classic["OUT_SLOPE"], INPUT_DO=classic["OUT_DIFF"], OUTPUT=str(rgb),
    ))
    ds = gdal.Open(str(rgb)); assert ds.RasterCount >= 3; ds = None
    processing.run(provider.id() + ":gmx_suite_benchmark", dict(
        OUT_DIR=str(root / "benchmark"), SIZE=32, REPEATS=1, WINDOW=3, SCALES="3,5",
    ))
    processing.run(provider.id() + ":gmx_suite_benchmark_batch", dict(
        DEM_DIR=str(inputs), OUT_DIR=str(root / "benchmark_batch"), REPEATS=1, WINDOW=3, SCALES="3,5",
    ))

    # Invalid recipes fail before any files are created.
    product = dict(method="slope", parameters=parameters)
    assert validate_recipe(dict(format="geomorphx-workbench", version=1, products=[product]))
    try:
        validate_recipe(dict(format="geomorphx-workbench", version=1, products=[dict(method="not-a-method")]))
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown recipe accepted")

    # Native Qt widgets + QGIS task manager in an isolated offscreen window.
    class Interface:
        def __init__(self):
            self.window = QMainWindow()
            self.window.resize(1300, 950)
            self.window.setCentralWidget(QWidget())
            self.layer = QgsRasterLayer(str(source), "Synthetic DEM")
            QgsProject.instance().addMapLayer(self.layer)
            self.menu = self.window.menuBar().addMenu("Raster")
            self.toolbar = self.window.addToolBar("GeoMorphX")

        def mainWindow(self): return self.window
        def activeLayer(self): return self.layer
        def addPluginToRasterMenu(self, _name, action): self.menu.addAction(action)
        def removePluginRasterMenu(self, _name, action): self.menu.removeAction(action)
        def addToolBarIcon(self, action): self.toolbar.addAction(action)
        def removeToolBarIcon(self, action): self.toolbar.removeAction(action)
        def addDockWidget(self, area, dock): self.window.addDockWidget(area, dock)
        def removeDockWidget(self, dock): self.window.removeDockWidget(dock)
        def addRasterLayer(self, path, name):
            layer = QgsRasterLayer(path, name)
            assert layer.isValid()
            QgsProject.instance().addMapLayer(layer)
            return layer

    plugin.unload()
    iface = Interface()
    plugin = classFactory(iface)
    plugin.initGui()
    plugin.show_workbench()
    dock = plugin.dock
    dock.layer_combo.setLayer(iface.layer)
    dock.output_dir.setText(str(root / "workbench_outputs"))
    dock.category.setCurrentIndex(2)  # Landforms: verify categorized renderer too.
    dock.window.setValue(5)
    dock.tile_size.setValue(7)
    dock.add_product()
    # The panel exports exactly the file consumed by the public API and Processing.
    from geomorphx import save_recipe, load_recipe, execute_recipe, normalize_recipe
    portable_path = save_recipe(dock.recipe(), root / "portable_recipe.json")
    assert json.loads(portable_path.read_text())["format"] == "geomorphx-recipe"
    dock.set_recipe(load_recipe(portable_path))
    api_outputs, _ = execute_recipe(portable_path, dem_path=source, out_dir=root / "recipe_api")
    recipe_result = processing.run(provider_id + ":run_recipe", dict(
        INPUT_DEM=str(source), RECIPE=str(portable_path), OUT_DIR=str(root / "recipe_processing"),
    ))
    assert Path(recipe_result["MANIFEST"]).is_file()
    for output in api_outputs:
        a, _ = read_dem(output)
        b, _ = read_dem(root / "recipe_processing" / output.name)
        np.testing.assert_equal(a, b)
    # Legacy recommendation resolution assumptions survive panel import/export.
    legacy = {"schema_version": "1.0", "input_assumptions": {"pixel_size_m": 2},
              "recommendations": [{"method": "slope"}], "objective": "general_relief"}
    previous = dock.recipe()
    dock.set_recipe(legacy)
    assert dock.recipe() == normalize_recipe(legacy)
    dock.set_recipe(previous)
    dock.category.setCurrentIndex(0)
    dock.method.setCurrentIndex(dock.method.findData("slope"))
    dock.add_product()
    iface.window.show()
    iface.window.resizeDocks([dock], [450], Qt.Horizontal)
    app.processEvents()
    dock.grab().save(str(root / "workbench.png"))
    dock.run_products()
    assert dock.task is not None
    deadline = time.monotonic() + 120
    while dock.task is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert dock.task is None, "Background task did not finish"
    manifests = list((root / "workbench_outputs").glob("*/workflow.json"))
    assert len(manifests) == 1
    workflow = json.loads(manifests[0].read_text())
    assert workflow["status"] == "complete", workflow
    assert len(workflow["outputs"]) == 2
    classes = [l for l in QgsProject.instance().mapLayers().values() if l.name() == "geomorphons"]
    assert classes and classes[0].renderer().type() == "paletted"
    cancelled = ProductTask(str(source), root / "cancelled", [product], dock)
    cancelled.cancel()
    assert not cancelled.run()
    cancelled_manifest = json.loads((cancelled.run_directory / "workflow.json").read_text())
    assert cancelled_manifest["status"] == "cancelled" and not cancelled_manifest["outputs"]
    failed = ProductTask(str(root / "missing_dem.tif"), root / "failed", [product], dock)
    assert not failed.run()
    failed_manifest = json.loads((failed.run_directory / "workflow.json").read_text())
    assert failed_manifest["status"] == "failed" and failed_manifest["error"]
    dock.grab().save(str(root / "workbench_completed.png"))
    plugin.unload()
    assert QgsApplication.processingRegistry().providerById(provider_id) is None
    result = dict(status="pass", qgis_version=Qgis.QGIS_VERSION, zip=str(bundle),
                  backend="gdal", named_algorithms_compared=comparisons,
                  registered_algorithms=len(algorithm_ids), batch_parameters="pass",
                  classic_rrim_rgb="pass", suite_and_benchmarks="pass",
                  native_dock_background_task="pass", landform_style="pass", unload="pass",
                  cancelled_and_failed_run_manifests="pass",
                  portable_recipe_api_processing_panel="pass",
                  screenshot=str(root / "workbench.png"))
    QgsProject.instance().clear()
    iface.window.close()
    return root, result


def main():
    import gc
    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QEvent
    from qgis.PyQt.QtGui import QFontDatabase, QFont
    root = Path(os.environ["DEVRESOURCES_SESSION"]) / "qgis_runtime"
    app = QgsApplication([], True, str(root / "profile"))
    app.initQgis()
    font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf"
    if font.is_file():
        QFontDatabase.addApplicationFont(str(font))
        app.setFont(QFont("Segoe UI", 9))
    root, result = exercise(app)
    app.processEvents()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    gc.collect()
    app.exitQgis()
    del app
    gc.collect()
    (root / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
