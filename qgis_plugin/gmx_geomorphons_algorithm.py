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
from osgeo import gdal

from .gmx_raster_utils import read_dem_array, write_array_as_geotiff


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

    def _sample_offset(self, arr: np.ndarray, dr: int, dc: int, radius: int) -> np.ndarray:
        rows, cols = arr.shape
        rr = np.clip(np.arange(rows)[:, None] + dr * radius, 0, rows - 1)
        cc = np.clip(np.arange(cols)[None, :] + dc * radius, 0, cols - 1)
        return arr[rr, cc]

    def processAlgorithm(self, parameters, context, feedback):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("Input DEM is required")

        radius = self.parameterAsInt(parameters, self.RADIUS, context)
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        out_class = self.parameterAsOutputLayer(parameters, self.OUTPUT_CLASS, context)
        out_conf = self.parameterAsOutputLayer(parameters, self.OUTPUT_CONF, context)

        dem, gt, proj, nodata = read_dem_array(dem_layer.source())

        offsets = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
        pos = np.zeros_like(dem, dtype=np.int16)
        neg = np.zeros_like(dem, dtype=np.int16)

        for dr, dc in offsets:
            nbr = self._sample_offset(dem, dr, dc, radius)
            diff = nbr - dem
            pos += (diff > threshold).astype(np.int16)
            neg += (diff < -threshold).astype(np.int16)

        classes = np.full_like(dem, 8, dtype=np.int16)
        classes[(pos == 0) & (neg == 0)] = 0
        classes[(pos >= 6) & (neg == 0)] = 1
        classes[(neg >= 6) & (pos == 0)] = 2
        classes[(pos >= 4) & (neg >= 4)] = 3
        classes[(neg >= 4) & (pos <= 2)] = 4
        classes[(pos >= 4) & (neg <= 2)] = 5
        classes[(neg > pos) & ~((neg >= 4) & (pos <= 2))] = 6
        classes[(pos > neg) & ~((pos >= 4) & (neg <= 2))] = 7

        confidence = np.abs(pos - neg).astype(np.float32) / 8.0

        write_array_as_geotiff(out_class, classes, gt, proj, nodata=None, gdal_dtype=gdal.GDT_Int16)
        write_array_as_geotiff(out_conf, confidence, gt, proj, nodata=nodata, gdal_dtype=gdal.GDT_Float32)

        return {
            self.OUTPUT_CLASS: out_class,
            self.OUTPUT_CONF: out_conf,
        }

    def createInstance(self):
        return GMXGeomorphonsAlgorithm()