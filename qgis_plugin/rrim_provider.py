from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
import os

from .gmx_curvature_algorithm import GMXCurvatureAlgorithm
from .gmx_geomorphons_algorithm import GMXGeomorphonsAlgorithm
from .gmx_geomorphons_los_algorithm import GMXGeomorphonsLOSAlgorithm
from .gmx_suite_benchmark_algorithm import GMXSuiteBenchmarkAlgorithm
from .gmx_suite_benchmark_batch_algorithm import GMXSuiteBenchmarkBatchAlgorithm
from .gmx_suite_compute_algorithm import GMXSuiteComputeAlgorithm
from .gmx_suite_compute_batch_algorithm import GMXSuiteComputeBatchAlgorithm
from .gmx_tpi_twi_algorithm import GMXTPITWIAlgorithm
from .rrim_algorithm import RRIMGenerator
from .rrim_rgb_composer import RRIMRGBComposer
from .method_algorithm import GMXMethodAlgorithm
from .recipe_algorithm import GMXRecipeAlgorithm


class RRIMProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        # Classic template algorithms from released plugin.
        self.addAlgorithm(RRIMGenerator())
        self.addAlgorithm(RRIMRGBComposer())

        # GeoMorphX suite algorithms.
        self.addAlgorithm(GMXSuiteComputeAlgorithm())
        self.addAlgorithm(GMXSuiteComputeBatchAlgorithm())
        self.addAlgorithm(GMXSuiteBenchmarkAlgorithm())
        self.addAlgorithm(GMXSuiteBenchmarkBatchAlgorithm())

        # Paper-backed geomorphometry blocks requested.
        self.addAlgorithm(GMXGeomorphonsAlgorithm())
        self.addAlgorithm(GMXGeomorphonsLOSAlgorithm())
        self.addAlgorithm(GMXCurvatureAlgorithm())
        self.addAlgorithm(GMXTPITWIAlgorithm())
        self.addAlgorithm(GMXRecipeAlgorithm())
        from .suite_imports import ensure_suite_importable
        ensure_suite_importable()
        from geomorphx.methods import METHODS
        for method in METHODS:
            self.addAlgorithm(GMXMethodAlgorithm(method))

    def id(self):
        return "geomorphx_rrim_suite"

    def name(self):
        return "GeoMorphX"

    def longName(self):
        return "GeoMorphX — Terrain Analysis"

    def icon(self):
        return QIcon(
            os.path.join(
                os.path.dirname(__file__),
                "icon.png"
            )
        )
