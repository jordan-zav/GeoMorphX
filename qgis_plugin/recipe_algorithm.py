"""Execute the same portable recipes used by the dock, CLI and Python API."""
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingOutputFile,
    QgsProcessingParameterFile, QgsProcessingParameterFolderDestination,
    QgsProcessingParameterRasterLayer,
)

from .suite_imports import ensure_suite_importable


class GMXRecipeAlgorithm(QgsProcessingAlgorithm):
    def name(self):
        return "run_recipe"

    def displayName(self):
        return "Run portable recipe"

    def group(self):
        return "Automation"

    def groupId(self):
        return "automation"

    def shortHelpString(self):
        return ("Run a JSON recipe exported by the panel, CLI or Python API. Legacy formats "
                "are accepted. Every product uses the original DEM. Existing outputs are "
                "rejected; choose a fresh folder. Cancellation stops between products. "
                "The JSON manifest records hashes, completed products and status.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer("INPUT_DEM", "Input DEM"))
        self.addParameter(QgsProcessingParameterFile("RECIPE", "GeoMorphX JSON recipe", extension="json"))
        self.addParameter(QgsProcessingParameterFolderDestination("OUT_DIR", "New output folder"))
        self.addOutput(QgsProcessingOutputFile("MANIFEST", "Recipe execution manifest"))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsRasterLayer(parameters, "INPUT_DEM", context)
        if layer is None:
            raise QgsProcessingException("Input DEM is required")
        ensure_suite_importable()
        from geomorphx.recipes import execute_recipe
        try:
            outputs, manifest = execute_recipe(
                self.parameterAsFile(parameters, "RECIPE", context), dem_path=layer.source(),
                out_dir=self.parameterAsString(parameters, "OUT_DIR", context),
                cancelled=feedback.isCanceled, progress=feedback.setProgress,
            )
        except Exception as error:
            raise QgsProcessingException(str(error)) from error
        feedback.pushInfo(f"Completed products: {len(outputs)}; manifest: {manifest}")
        return {"OUT_DIR": self.parameterAsString(parameters, "OUT_DIR", context), "MANIFEST": str(manifest)}

    def createInstance(self):
        return GMXRecipeAlgorithm()
