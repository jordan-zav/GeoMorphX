from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtGui import QIcon

from .suite_imports import ensure_suite_importable


class GMXSuiteBenchmarkAlgorithm(QgsProcessingAlgorithm):
    DEM = "DEM"
    OUT_DIR = "OUT_DIR"
    SIZE = "SIZE"
    REPEATS = "REPEATS"
    WINDOW = "WINDOW"
    SCALES = "SCALES"
    AZIMUTH = "AZIMUTH"
    TILE_SIZE = "TILE_SIZE"

    def name(self):
        return "gmx_suite_benchmark"

    def displayName(self):
        return "GeoMorphX Suite Benchmark"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return "Benchmark GeoMorphX suite methods on one DEM (or synthetic if DEM is empty)."

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.DEM, "Input DEM (optional)", optional=True))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUT_DIR, "Output folder"))
        self.addParameter(QgsProcessingParameterNumber(self.SIZE, "Synthetic DEM size", QgsProcessingParameterNumber.Integer, defaultValue=512, minValue=32))
        self.addParameter(QgsProcessingParameterNumber(self.REPEATS, "Repeats", QgsProcessingParameterNumber.Integer, defaultValue=3, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW, "Window", QgsProcessingParameterNumber.Integer, defaultValue=9, minValue=3))
        self.addParameter(QgsProcessingParameterString(self.SCALES, "Scales (comma-separated)", defaultValue="5,15,45"))
        self.addParameter(QgsProcessingParameterNumber(self.AZIMUTH, "Azimuth", QgsProcessingParameterNumber.Double, defaultValue=45.0))
        self.addParameter(QgsProcessingParameterNumber(self.TILE_SIZE, "Tile size (0 disables)", QgsProcessingParameterNumber.Integer, defaultValue=0, minValue=0))

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.DEM, context)
        dem_path = dem_layer.source() if dem_layer is not None else None

        scales_raw = self.parameterAsString(parameters, self.SCALES, context)
        scales = [int(x.strip()) for x in scales_raw.split(",") if x.strip()]

        ensure_suite_importable()
        from geomorphx.benchmark import run_benchmark_suite

        rows, csv_path, json_path, md_path, png_path = run_benchmark_suite(
            out_dir=self.parameterAsString(parameters, self.OUT_DIR, context),
            dem_path=dem_path,
            size=self.parameterAsInt(parameters, self.SIZE, context),
            repeats=self.parameterAsInt(parameters, self.REPEATS, context),
            scales=scales,
            window=self.parameterAsInt(parameters, self.WINDOW, context),
            azimuth_deg=self.parameterAsDouble(parameters, self.AZIMUTH, context),
            tile_size=self.parameterAsInt(parameters, self.TILE_SIZE, context),
        )

        feedback.pushInfo(f"Benchmark methods: {len(rows)}")
        feedback.pushInfo(f"CSV: {csv_path}")
        feedback.pushInfo(f"JSON: {json_path}")
        feedback.pushInfo(f"Report: {md_path}")
        if png_path is None:
            feedback.pushInfo("PNG: not generated (matplotlib not available)")
        else:
            feedback.pushInfo(f"PNG: {png_path}")

        return {self.OUT_DIR: self.parameterAsString(parameters, self.OUT_DIR, context)}

    def createInstance(self):
        return GMXSuiteBenchmarkAlgorithm()