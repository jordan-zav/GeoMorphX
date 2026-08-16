from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

from .suite_imports import ensure_suite_importable


_METHODS = [
    "rrim_baseline",
    "rrim_multiscale",
    "rrim_anisotropic",
    "rrim_anisotropic_multiscale",
    "rrim_structural",
    "rrim_plus",
]


class GMXSuiteComputeBatchAlgorithm(QgsProcessingAlgorithm):
    DEM_DIR = "DEM_DIR"
    OUT_DIR = "OUT_DIR"
    PATTERN = "PATTERN"
    RECURSIVE = "RECURSIVE"
    METHOD = "METHOD"
    WINDOW = "WINDOW"
    SCALES = "SCALES"
    AZIMUTH = "AZIMUTH"
    DIRECTIONAL_WEIGHT = "DIRECTIONAL_WEIGHT"
    ANISOTROPY_WEIGHT = "ANISOTROPY_WEIGHT"
    ROUGHNESS_WEIGHT = "ROUGHNESS_WEIGHT"
    STRUCTURAL_WEIGHT = "STRUCTURAL_WEIGHT"
    SAVE_DEBUG = "SAVE_DEBUG"

    def name(self):
        return "gmx_suite_compute_batch"

    def displayName(self):
        return "GeoMorphX Suite Compute Batch"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return "Run GeoMorphX suite methods for all DEM files in a folder."

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.DEM_DIR, "Input DEM folder", behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUT_DIR, "Output folder"))
        self.addParameter(QgsProcessingParameterString(self.PATTERN, "Pattern", defaultValue="*"))
        self.addParameter(QgsProcessingParameterBoolean(self.RECURSIVE, "Recursive", defaultValue=True))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD, "Method", options=_METHODS, defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW, "Window", QgsProcessingParameterNumber.Integer, defaultValue=9, minValue=3))
        self.addParameter(QgsProcessingParameterString(self.SCALES, "Scales (comma-separated)", defaultValue="5,15,45"))
        self.addParameter(QgsProcessingParameterNumber(self.AZIMUTH, "Azimuth", QgsProcessingParameterNumber.Double, defaultValue=45.0))
        self.addParameter(QgsProcessingParameterNumber(self.DIRECTIONAL_WEIGHT, "Directional Weight", QgsProcessingParameterNumber.Double, defaultValue=0.6))
        self.addParameter(QgsProcessingParameterNumber(self.ANISOTROPY_WEIGHT, "Anisotropy Weight", QgsProcessingParameterNumber.Double, defaultValue=0.3))
        self.addParameter(QgsProcessingParameterNumber(self.ROUGHNESS_WEIGHT, "Roughness Weight", QgsProcessingParameterNumber.Double, defaultValue=0.25))
        self.addParameter(QgsProcessingParameterNumber(self.STRUCTURAL_WEIGHT, "Structural Weight", QgsProcessingParameterNumber.Double, defaultValue=0.2))
        self.addParameter(QgsProcessingParameterBoolean(self.SAVE_DEBUG, "Save RRIM++ debug intermediates", defaultValue=False))

    def processAlgorithm(self, parameters, context, feedback):
        dem_dir = self.parameterAsFile(parameters, self.DEM_DIR, context)
        out_dir = self.parameterAsString(parameters, self.OUT_DIR, context)

        if not dem_dir:
            raise QgsProcessingException("Input DEM folder is required")

        method = _METHODS[self.parameterAsEnum(parameters, self.METHOD, context)]
        scales_raw = self.parameterAsString(parameters, self.SCALES, context)
        scales = [int(x.strip()) for x in scales_raw.split(",") if x.strip()]

        ensure_suite_importable()
        from geomorphx.api import compute_rrim_batch

        outputs, manifest = compute_rrim_batch(
            dem_dir=dem_dir,
            out_dir=out_dir,
            method=method,
            pattern=self.parameterAsString(parameters, self.PATTERN, context),
            recursive=self.parameterAsBool(parameters, self.RECURSIVE, context),
            scales=scales,
            window=self.parameterAsInt(parameters, self.WINDOW, context),
            azimuth_deg=self.parameterAsDouble(parameters, self.AZIMUTH, context),
            directional_weight=self.parameterAsDouble(parameters, self.DIRECTIONAL_WEIGHT, context),
            anisotropy_weight=self.parameterAsDouble(parameters, self.ANISOTROPY_WEIGHT, context),
            roughness_weight=self.parameterAsDouble(parameters, self.ROUGHNESS_WEIGHT, context),
            structural_weight=self.parameterAsDouble(parameters, self.STRUCTURAL_WEIGHT, context),
            save_debug=self.parameterAsBool(parameters, self.SAVE_DEBUG, context),
        )

        feedback.pushInfo(f"Computed files: {len(outputs)}")
        feedback.pushInfo(f"Manifest: {manifest}")
        return {self.OUT_DIR: out_dir}

    def createInstance(self):
        return GMXSuiteComputeBatchAlgorithm()