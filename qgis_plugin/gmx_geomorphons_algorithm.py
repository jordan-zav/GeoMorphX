from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
)
from qgis.PyQt.QtGui import QIcon


from .suite_imports import ensure_suite_importable


class GMXGeomorphonsAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = "INPUT_DEM"
    RADIUS = "RADIUS"
    THRESHOLD = "THRESHOLD"
    OUTPUT_CLASS = "OUTPUT_CLASS"
    OUTPUT_CONF = "OUTPUT_CONF"

    def name(self):
        return "gmx_geomorphons"

    def displayName(self):
        return "GeoMorphX Geomorphons (Simplified)"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return (
            "Simplified geomorphons-style landform classification based on directional "
            "elevation sign patterns around each pixel.\n"
            "Class IDs: 0 flat, 1 pit, 2 peak, 3 saddle, 4 ridge, 5 valley, 6 upper_slope, 7 lower_slope, 8 slope."
        )

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, "Input DEM"))
        self.addParameter(QgsProcessingParameterNumber(self.RADIUS, "Search radius (cells)", QgsProcessingParameterNumber.Integer, defaultValue=5, minValue=1))
        self.addParameter(QgsProcessingParameterNumber(self.THRESHOLD, "Flat threshold (elevation units)", QgsProcessingParameterNumber.Double, defaultValue=0.5, minValue=0.0))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_CLASS, "Landform classes"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_CONF, "Classification confidence"))

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("Input DEM is required")

        radius = self.parameterAsInt(parameters, self.RADIUS, context)
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        out_class = self.parameterAsOutputLayer(parameters, self.OUTPUT_CLASS, context)
        out_conf = self.parameterAsOutputLayer(parameters, self.OUTPUT_CONF, context)

        ensure_suite_importable()
        from geomorphx.blocks import compute_geomorphons_legacy_block
        compute_geomorphons_legacy_block(dem_layer.source(), out_class, out_conf,
                                         radius=radius, threshold=threshold)

        return {
            self.OUTPUT_CLASS: out_class,
            self.OUTPUT_CONF: out_conf,
        }

    def createInstance(self):
        return GMXGeomorphonsAlgorithm()