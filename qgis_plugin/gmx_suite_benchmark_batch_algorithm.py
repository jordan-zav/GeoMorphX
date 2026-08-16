from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

from .suite_imports import ensure_suite_importable


class GMXSuiteBenchmarkBatchAlgorithm(QgsProcessingAlgorithm):
    DEM_DIR = "DEM_DIR"
    OUT_DIR = "OUT_DIR"
    PATTERN = "PATTERN"
    RECURSIVE = "RECURSIVE"
    REPEATS = "REPEATS"
    WINDOW = "WINDOW"
    SCALES = "SCALES"
    AZIMUTH = "AZIMUTH"
    TILE_SIZE = "TILE_SIZE"

    def name(self):
        return "gmx_suite_benchmark_batch"

    def displayName(self):
        return "GeoMorphX Suite Benchmark Batch"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return "Benchmark GeoMorphX suite methods for multiple DEM files."

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.DEM_DIR, "Input DEM folder", behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUT_DIR, "Output folder"))
        self.addParameter(QgsProcessingParameterString(self.PATTERN, "Pattern", defaultValue="*"))
        self.addParameter(QgsProcessingParameterBoolean(self.RECURSIVE, "Recursive", defaultValue=True))
        self.addParameter(QgsProcessingParameterNumber(self.REPEATS, "Repeats", QgsProcessingParameterNumber.Integer, defaultValue=3, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW, "Window", QgsProcessingParameterNumber.Integer, defaultValue=9, minValue=3))
        self.addParameter(QgsProcessingParameterString(self.SCALES, "Scales (comma-separated)", defaultValue="5,15,45"))
        self.addParameter(QgsProcessingParameterNumber(self.AZIMUTH, "Azimuth", QgsProcessingParameterNumber.Double, defaultValue=45.0))
        self.addParameter(QgsProcessingParameterNumber(self.TILE_SIZE, "Tile size (0 disables)", QgsProcessingParameterNumber.Integer, defaultValue=0, minValue=0))

    def processAlgorithm(self, parameters, context, feedback):
        scales_raw = self.parameterAsString(parameters, self.SCALES, context)
        scales = [int(x.strip()) for x in scales_raw.split(",") if x.strip()]

        ensure_suite_importable()
        from geomorphx.benchmark import run_benchmark_batch

        rows, summary_csv, summary_json, summary_md = run_benchmark_batch(
            dem_dir=self.parameterAsFile(parameters, self.DEM_DIR, context),
            out_dir=self.parameterAsString(parameters, self.OUT_DIR, context),
            pattern=self.parameterAsString(parameters, self.PATTERN, context),
            recursive=self.parameterAsBool(parameters, self.RECURSIVE, context),
            repeats=self.parameterAsInt(parameters, self.REPEATS, context),
            scales=scales,
            window=self.parameterAsInt(parameters, self.WINDOW, context),
            azimuth_deg=self.parameterAsDouble(parameters, self.AZIMUTH, context),
            tile_size=self.parameterAsInt(parameters, self.TILE_SIZE, context),
        )

        feedback.pushInfo(f"Benchmark batch inputs: {len(rows)}")
        feedback.pushInfo(f"Summary CSV: {summary_csv}")
        feedback.pushInfo(f"Summary JSON: {summary_json}")
        feedback.pushInfo(f"Summary MD: {summary_md}")

        return {self.OUT_DIR: self.parameterAsString(parameters, self.OUT_DIR, context)}

    def createInstance(self):
        return GMXSuiteBenchmarkBatchAlgorithm()