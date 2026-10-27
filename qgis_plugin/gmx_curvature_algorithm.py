from __future__ import annotations

import os

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
)
from qgis.PyQt.QtGui import QIcon


from .suite_imports import ensure_suite_importable


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

        ensure_suite_importable()
        from geomorphx.blocks import compute_curvature_block
        compute_curvature_block(dem_layer.source(), out_profile, out_plan, out_mean)

        return {
            self.OUT_PROFILE: out_profile,
            self.OUT_PLAN: out_plan,
            self.OUT_MEAN: out_mean,
        }

    def createInstance(self):
        return GMXCurvatureAlgorithm()