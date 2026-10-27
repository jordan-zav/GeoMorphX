"""Ten-class line-of-sight geomorphons; separate ID from the legacy model."""

from qgis.core import QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination

from .gmx_geomorphons_algorithm import GMXGeomorphonsAlgorithm
from .suite_imports import ensure_suite_importable


class GMXGeomorphonsLOSAlgorithm(GMXGeomorphonsAlgorithm):
    OUTPUT_TERNARY = "OUTPUT_TERNARY"
    SKIP = "SKIP"

    def name(self):
        return "gmx_geomorphons_los"

    def displayName(self):
        return "GeoMorphX Geomorphons (Line of Sight, 10 Forms)"

    def shortHelpString(self):
        return (
            "Eight-direction zenith/nadir horizons, basic anglev1 comparison. "
            "Classes: 1 flat, 2 peak, 3 ridge, 4 shoulder, 5 spur, 6 slope, "
            "7 hollow, 8 footslope, 9 valley, 10 pit. Flatness is in degrees. "
            "NoData stops rays; all eight rays must have samples. Equal absolute "
            "zenith/nadir angles produce a neutral sign, including exact planar profiles. "
            "No extended form correction. Outputs include a canonical ternary pattern."
        )

    def initAlgorithm(self, config=None):
        # Import here as the base module already provides QGIS' raster parameter.
        from qgis.core import QgsProcessingParameterRasterLayer
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DEM, "Input DEM (projected CRS)"))
        self.addParameter(QgsProcessingParameterNumber(
            self.RADIUS, "Search radius (cells)", QgsProcessingParameterNumber.Integer,
            defaultValue=4, minValue=2,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.THRESHOLD, "Flatness threshold (degrees)", QgsProcessingParameterNumber.Double,
            defaultValue=1.0, minValue=0.000001, maxValue=89.999999,
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.SKIP, "Inner steps to skip", QgsProcessingParameterNumber.Integer,
            defaultValue=0, minValue=0,
        ))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_CLASS, "Landform classes (1-10)"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_TERNARY, "Canonical ternary pattern"))

    def processAlgorithm(self, parameters, context, feedback):
        from qgis.core import QgsProcessingException
        layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if layer is None:
            raise QgsProcessingException("Input DEM is required")
        out_class = self.parameterAsOutputLayer(parameters, self.OUTPUT_CLASS, context)
        out_ternary = self.parameterAsOutputLayer(parameters, self.OUTPUT_TERNARY, context)
        ensure_suite_importable()
        from geomorphx.blocks import compute_geomorphons_block
        compute_geomorphons_block(
            layer.source(), out_class, out_ternary,
            radius=self.parameterAsInt(parameters, self.RADIUS, context),
            flatness_deg=self.parameterAsDouble(parameters, self.THRESHOLD, context),
            skip=self.parameterAsInt(parameters, self.SKIP, context),
        )
        return {self.OUTPUT_CLASS: out_class, self.OUTPUT_TERNARY: out_ternary}

    def createInstance(self):
        return GMXGeomorphonsLOSAlgorithm()
