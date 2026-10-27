"""Execute Processing adapters with host API doubles, not a QGIS installation.

Raster computation and I/O are real. Only parameter access and Qt/QGIS classes
are substituted, so these tests do not assert GUI/provider compatibility.
"""

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from core_py.geomorphx_core.io import read_dem


@pytest.fixture
def processing_host(monkeypatch):
    class Parameter:
        Integer = 0
        Double = 1

        def __init__(self, name, *args, **kwargs):
            self.name = name
            self.default = kwargs.get("defaultValue")

    class Algorithm:
        def addParameter(self, parameter):
            if not hasattr(self, "defaults"):
                self.defaults = {}
            self.defaults[parameter.name] = parameter.default

        def _value(self, parameters, key):
            return parameters.get(key, self.defaults.get(key))

        def parameterAsRasterLayer(self, parameters, key, context):
            value = self._value(parameters, key)
            return SimpleNamespace(source=lambda: str(value)) if value else None

        def parameterAsInt(self, parameters, key, context):
            return int(self._value(parameters, key))

        def parameterAsDouble(self, parameters, key, context):
            return float(self._value(parameters, key))

        def parameterAsBool(self, parameters, key, context):
            return bool(self._value(parameters, key))

        def parameterAsString(self, parameters, key, context):
            return str(self._value(parameters, key))

        parameterAsOutputLayer = parameterAsString
        parameterAsEnum = parameterAsInt

    for name in ("qgis", "qgis.core", "qgis.PyQt", "qgis.PyQt.QtGui"):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    core = sys.modules["qgis.core"]
    core.QgsProcessingAlgorithm = Algorithm
    core.QgsProcessingException = ValueError
    for suffix in ("Number", "RasterLayer", "RasterDestination", "Boolean", "Enum", "String"):
        setattr(core, "QgsProcessingParameter" + suffix, Parameter)
    sys.modules["qgis.PyQt.QtGui"].QIcon = object
    plugin_path = Path(__file__).resolve().parents[1] / "qgis_plugin"
    spec = importlib.util.spec_from_file_location(
        "_geomorphx_qgis_test", plugin_path / "__init__.py",
        submodule_search_locations=[str(plugin_path)],
    )
    package = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, package)
    spec.loader.exec_module(package)
    yield lambda name: importlib.import_module(f"{spec.name}.{name}")
    for name in list(sys.modules):
        if name.startswith(spec.name + "."):
            monkeypatch.delitem(sys.modules, name)


@pytest.mark.parametrize("module,class_name,extra,outputs", [
    ("gmx_curvature_algorithm", "GMXCurvatureAlgorithm", {},
     ["OUT_PROFILE", "OUT_PLAN", "OUT_MEAN"]),
    ("gmx_tpi_twi_algorithm", "GMXTPITWIAlgorithm", {},
     ["OUT_TPI_SMALL", "OUT_TPI_LARGE", "OUT_WETNESS"]),
    ("gmx_geomorphons_algorithm", "GMXGeomorphonsAlgorithm", {"RADIUS": 2},
     ["OUTPUT_CLASS", "OUTPUT_CONF"]),
    ("gmx_geomorphons_los_algorithm", "GMXGeomorphonsLOSAlgorithm", {},
     ["OUTPUT_CLASS", "OUTPUT_TERNARY"]),
    ("gmx_suite_compute_algorithm", "GMXSuiteComputeAlgorithm", {"METHOD": 25},
     ["OUTPUT"]),
])
def test_processing_adapter_writes_real_georeferenced_outputs(
    processing_host, tmp_path, module, class_name, extra, outputs,
):
    dem = np.zeros((19, 21), dtype=np.float32)
    dem[9, 10] = 10
    dem[3, 3] = -9999
    source = tmp_path / "dem.tif"
    with rasterio.open(
        source, "w", driver="GTiff", dtype="float32", count=1, height=19, width=21,
        crs="EPSG:32718", transform=from_origin(0, 60, 2, 2), nodata=-9999,
    ) as dst:
        dst.write(dem, 1)
    algorithm = getattr(processing_host(module), class_name)()
    algorithm.initAlgorithm()
    parameters = {"INPUT_DEM": source, **extra}
    parameters.update({key: str(tmp_path / f"{key}.tif") for key in outputs})
    result = algorithm.processAlgorithm(parameters, None, SimpleNamespace(pushInfo=lambda text: None))
    assert set(result) == set(outputs)
    for key, path in result.items():
        arr, profile = read_dem(path)
        assert arr.shape == dem.shape
        assert profile["crs"].to_epsg() == 32718
        assert np.isnan(arr[3, 3])
        if module == "gmx_geomorphons_algorithm" and key == "OUTPUT_CLASS":
            assert arr[9, 10] == 2  # Existing peak ID is preserved.
        if module == "gmx_geomorphons_los_algorithm" and key == "OUTPUT_CLASS":
            assert arr[9, 10] == 2
