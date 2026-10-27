from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

from .suite_imports import ensure_suite_importable


def _suite_methods():
    ensure_suite_importable()
    from geomorphx.methods import METHODS
    return list(METHODS)


class GMXSuiteComputeAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = "INPUT_DEM"
    METHOD = "METHOD"
    WINDOW = "WINDOW"
    SCALES = "SCALES"
    AZIMUTH = "AZIMUTH"
    DIRECTIONAL_WEIGHT = "DIRECTIONAL_WEIGHT"
    ANISOTROPY_WEIGHT = "ANISOTROPY_WEIGHT"
    ROUGHNESS_WEIGHT = "ROUGHNESS_WEIGHT"
    STRUCTURAL_WEIGHT = "STRUCTURAL_WEIGHT"
    TILE_SIZE = "TILE_SIZE"
    SCRATCH_DIR = "SCRATCH_DIR"
    FLATNESS = "FLATNESS"
    GEOMORPHON_SKIP = "GEOMORPHON_SKIP"
    SAVE_DEBUG = "SAVE_DEBUG"
    OUTPUT = "OUTPUT"

    def name(self):
        return "gmx_suite_compute"

    def displayName(self):
        return "GeoMorphX Suite Compute"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return "Run GeoMorphX suite methods on a single DEM and write output GeoTIFF + metadata sidecar."

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, "Input DEM"))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD, "Method", options=_suite_methods(), defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW, "Window", QgsProcessingParameterNumber.Integer, defaultValue=9, minValue=3))
        self.addParameter(QgsProcessingParameterString(self.SCALES, "Scales (comma-separated)", defaultValue="5,15,45"))
        self.addParameter(QgsProcessingParameterNumber(self.AZIMUTH, "Azimuth", QgsProcessingParameterNumber.Double, defaultValue=45.0))
        self.addParameter(QgsProcessingParameterNumber(self.DIRECTIONAL_WEIGHT, "Directional Weight", QgsProcessingParameterNumber.Double, defaultValue=0.6))
        self.addParameter(QgsProcessingParameterNumber(self.ANISOTROPY_WEIGHT, "Anisotropy Weight", QgsProcessingParameterNumber.Double, defaultValue=0.3))
        self.addParameter(QgsProcessingParameterNumber(self.ROUGHNESS_WEIGHT, "Roughness Weight", QgsProcessingParameterNumber.Double, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterNumber(self.STRUCTURAL_WEIGHT, "Structural Weight", QgsProcessingParameterNumber.Double, defaultValue=0.2))
        self.addParameter(QgsProcessingParameterNumber(self.TILE_SIZE, "Tile size (0 = full array)", QgsProcessingParameterNumber.Integer, defaultValue=0, minValue=0))
        self.addParameter(QgsProcessingParameterString(self.SCRATCH_DIR, "Temporary raster directory (optional)", defaultValue="", optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.FLATNESS, "Geomorphon flatness (degrees)", QgsProcessingParameterNumber.Double, defaultValue=1.0, minValue=0.000001, maxValue=89.999999))
        self.addParameter(QgsProcessingParameterNumber(self.GEOMORPHON_SKIP, "Geomorphon inner steps to skip", QgsProcessingParameterNumber.Integer, defaultValue=0, minValue=0))
        self.addParameter(QgsProcessingParameterBoolean(self.SAVE_DEBUG, "Save RRIM++ debug intermediates", defaultValue=False))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, "Output GeoTIFF"))

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("Input DEM is required")

        method = self.selected_method(parameters, context)
        scales_raw = self.parameterAsString(parameters, self.SCALES, context)
        scales = [int(x.strip()) for x in scales_raw.split(",") if x.strip()]

        window = self.parameterAsInt(parameters, self.WINDOW, context)
        azimuth = self.parameterAsDouble(parameters, self.AZIMUTH, context)
        directional_weight = self.parameterAsDouble(parameters, self.DIRECTIONAL_WEIGHT, context)
        anisotropy_weight = self.parameterAsDouble(parameters, self.ANISOTROPY_WEIGHT, context)
        roughness_weight = self.parameterAsDouble(parameters, self.ROUGHNESS_WEIGHT, context)
        structural_weight = self.parameterAsDouble(parameters, self.STRUCTURAL_WEIGHT, context)
        save_debug = self.parameterAsBool(parameters, self.SAVE_DEBUG, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        ensure_suite_importable()
        from geomorphx.api import compute_rrim

        debug_dir = None
        if save_debug:
            debug_dir = output + "_debug"

        result = compute_rrim(
            dem_path=dem_layer.source(),
            out_path=output,
            method=method,
            scales=scales,
            window=window,
            azimuth_deg=azimuth,
            directional_weight=directional_weight,
            anisotropy_weight=anisotropy_weight,
            roughness_weight=roughness_weight,
            structural_weight=structural_weight,
            tile_size=self.parameterAsInt(parameters, self.TILE_SIZE, context),
            scratch_dir=(self.parameterAsString(parameters, self.SCRATCH_DIR, context) or None),
            flatness_deg=self.parameterAsDouble(parameters, self.FLATNESS, context),
            geomorphon_skip=self.parameterAsInt(parameters, self.GEOMORPHON_SKIP, context),
            debug_dir=debug_dir,
        )

        feedback.pushInfo(f"Generated: {result}")
        feedback.pushInfo(f"Metadata: {result}.meta.json")

        return {self.OUTPUT: str(result)}

    def createInstance(self):
        return GMXSuiteComputeAlgorithm()

    def selected_method(self, parameters, context):
        return _suite_methods()[self.parameterAsEnum(parameters, self.METHOD, context)]
