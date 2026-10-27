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


class GMXTPITWIAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = "INPUT_DEM"
    WINDOW_SMALL = "WINDOW_SMALL"
    WINDOW_LARGE = "WINDOW_LARGE"
    OUT_TPI_SMALL = "OUT_TPI_SMALL"
    OUT_TPI_LARGE = "OUT_TPI_LARGE"
    OUT_WETNESS = "OUT_WETNESS"

    def name(self):
        return "gmx_tpi_twi"

    def displayName(self):
        return "GeoMorphX TPI + Wetness Proxy"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return (
            "Computes TPI (small and large windows) and a topographic wetness proxy. "
            "Wetness output is a proxy (not full flow-accumulation TWI)."
        )

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, "Input DEM"))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW_SMALL, "Small window", QgsProcessingParameterNumber.Integer, defaultValue=11, minValue=3))
        self.addParameter(QgsProcessingParameterNumber(self.WINDOW_LARGE, "Large window", QgsProcessingParameterNumber.Integer, defaultValue=31, minValue=5))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_TPI_SMALL, "TPI small"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_TPI_LARGE, "TPI large"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_WETNESS, "Wetness proxy"))

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("Input DEM is required")

        ws = self.parameterAsInt(parameters, self.WINDOW_SMALL, context)
        wl = self.parameterAsInt(parameters, self.WINDOW_LARGE, context)

        out_small = self.parameterAsOutputLayer(parameters, self.OUT_TPI_SMALL, context)
        out_large = self.parameterAsOutputLayer(parameters, self.OUT_TPI_LARGE, context)
        out_wet = self.parameterAsOutputLayer(parameters, self.OUT_WETNESS, context)

        ensure_suite_importable()
        from geomorphx.blocks import compute_tpi_wetness_block
        compute_tpi_wetness_block(dem_layer.source(), out_small, out_large, out_wet,
                                  window_small=ws, window_large=wl)

        return {
            self.OUT_TPI_SMALL: out_small,
            self.OUT_TPI_LARGE: out_large,
            self.OUT_WETNESS: out_wet,
        }

    def createInstance(self):
        return GMXTPITWIAlgorithm()