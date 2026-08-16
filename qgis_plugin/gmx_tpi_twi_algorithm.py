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

import numpy as np

from .gmx_raster_utils import local_mean, neighborhood_relief, read_dem_array, write_array_as_geotiff


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

        dem, gt, proj, nodata = read_dem_array(dem_layer.source())

        mean_small = local_mean(dem, ws)
        mean_large = local_mean(dem, wl)

        tpi_small = (dem - mean_small).astype(np.float32)
        tpi_large = (dem - mean_large).astype(np.float32)

        dy, dx = abs(float(gt[5])) if gt[5] != 0 else 1.0, abs(float(gt[1])) if gt[1] != 0 else 1.0
        gy, gx = np.gradient(dem, dy, dx)
        slope_rad = np.arctan(np.sqrt(gx * gx + gy * gy))

        relief = neighborhood_relief(dem, ws)
        a_proxy = relief + 1.0
        wetness_proxy = np.log(a_proxy / (np.tan(slope_rad) + 1e-6)).astype(np.float32)

        write_array_as_geotiff(out_small, tpi_small, gt, proj, nodata=nodata)
        write_array_as_geotiff(out_large, tpi_large, gt, proj, nodata=nodata)
        write_array_as_geotiff(out_wet, wetness_proxy, gt, proj, nodata=nodata)

        return {
            self.OUT_TPI_SMALL: out_small,
            self.OUT_TPI_LARGE: out_large,
            self.OUT_WETNESS: out_wet,
        }

    def createInstance(self):
        return GMXTPITWIAlgorithm()