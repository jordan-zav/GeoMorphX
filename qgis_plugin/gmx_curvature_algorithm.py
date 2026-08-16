from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
)
from qgis.PyQt.QtGui import QIcon

import numpy as np

from .gmx_raster_utils import read_dem_array, write_array_as_geotiff


class GMXCurvatureAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = "INPUT_DEM"
    OUT_PROFILE = "OUT_PROFILE"
    OUT_PLAN = "OUT_PLAN"
    OUT_MEAN = "OUT_MEAN"

    def name(self):
        return "gmx_curvature"

    def displayName(self):
        return "GeoMorphX Curvature Block"

    def group(self):
        return "GeoMorphX Suite"

    def groupId(self):
        return "geomorphx_suite"

    def shortHelpString(self):
        return "Computes profile, plan, and mean curvature (Zevenbergen & Thorne style derivatives)."

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, "Input DEM"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_PROFILE, "Profile curvature"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_PLAN, "Plan curvature"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUT_MEAN, "Mean curvature"))

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("Input DEM is required")

        out_profile = self.parameterAsOutputLayer(parameters, self.OUT_PROFILE, context)
        out_plan = self.parameterAsOutputLayer(parameters, self.OUT_PLAN, context)
        out_mean = self.parameterAsOutputLayer(parameters, self.OUT_MEAN, context)

        dem, gt, proj, nodata = read_dem_array(dem_layer.source())
        dx = abs(float(gt[1])) if gt[1] != 0 else 1.0
        dy = abs(float(gt[5])) if gt[5] != 0 else 1.0

        q, p = np.gradient(dem, dy, dx)
        qy, qx = np.gradient(q, dy, dx)
        py, px = np.gradient(p, dy, dx)

        r = px
        s = 0.5 * (py + qx)
        t = qy

        eps = 1e-9
        g = p * p + q * q
        g_safe = np.maximum(g, eps)

        profile = -(r * p * p + 2.0 * s * p * q + t * q * q) / (g_safe * np.power(1.0 + g_safe, 1.5))
        plan = (r * q * q - 2.0 * s * p * q + t * p * p) / np.power(g_safe, 1.5)
        mean = -((1.0 + q * q) * r - 2.0 * p * q * s + (1.0 + p * p) * t) / (2.0 * np.power(1.0 + g_safe, 1.5))

        write_array_as_geotiff(out_profile, profile.astype(np.float32), gt, proj, nodata=nodata)
        write_array_as_geotiff(out_plan, plan.astype(np.float32), gt, proj, nodata=nodata)
        write_array_as_geotiff(out_mean, mean.astype(np.float32), gt, proj, nodata=nodata)

        return {
            self.OUT_PROFILE: out_profile,
            self.OUT_PLAN: out_plan,
            self.OUT_MEAN: out_mean,
        }

    def createInstance(self):
        return GMXCurvatureAlgorithm()