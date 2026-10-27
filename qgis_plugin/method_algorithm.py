"""Named Processing algorithms for every shared method; no numerical duplication."""
from .gmx_suite_compute_algorithm import GMXSuiteComputeAlgorithm


class GMXMethodAlgorithm(GMXSuiteComputeAlgorithm):
    def __init__(self, method):
        super().__init__()
        self.method_id = method

    def name(self):
        return "terrain_" + self.method_id

    def displayName(self):
        return self.method_id.replace("rrim", "RRIM").replace("tpi", "TPI").replace("tri", "TRI").replace("_", " ")

    def groupId(self):
        if self.method_id.startswith("rrim_"):
            return "rrim_experimental"
        if self.method_id.startswith("geomorphon"):
            return "terrain_forms"
        if self.method_id in {"fill_depressions", "flow_accumulation_d8", "flow_accumulation_mfd",
                              "twi_d8", "twi_mfd", "flow_direction_d8", "flow_length_d8", "drainage_basins_d8"}:
            return "hydrology_additional"
        return "geomorphometry"

    def group(self):
        return {"rrim_experimental": "RRIM (experimental)", "terrain_forms": "Terrain forms",
                "hydrology_additional": "Hydrology (additional)", "geomorphometry": "Geomorphometry"}[self.groupId()]

    def initAlgorithm(self, config=None):
        super().initAlgorithm(config)
        self.removeParameter(self.METHOD)
        from qgis.core import QgsProcessingParameterDefinition
        relevant = {self.INPUT_DEM, self.OUTPUT, self.TILE_SIZE}
        if self.method_id.startswith("rrim_") or self.method_id.startswith("geomorphon") or self.method_id in {
            "tpi", "tri", "local_relief", "wetness_proxy", "positive_openness", "negative_openness", "sky_view_factor"
        }:
            relevant.add(self.WINDOW)
        if self.method_id.endswith("multiscale"):
            relevant.add(self.SCALES)
        if "anisotropic" in self.method_id or "structural" in self.method_id or self.method_id == "rrim_plus":
            relevant.add(self.AZIMUTH)
        if self.method_id.startswith("geomorphon"):
            relevant.update({self.FLATNESS, self.GEOMORPHON_SKIP})
        for parameter in self.parameterDefinitions():
            if parameter.name() not in relevant:
                parameter.setFlags(parameter.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

    def shortHelpString(self):
        text = "Compute " + self.displayName() + " from a single-band DEM. NoData is preserved; windows are in pixels. "
        if self.groupId() == "rrim_experimental":
            text += "Experimental composition using the documented legacy pixel convention; not an independently validated classical RRIM reproduction."
        elif self.groupId() == "hydrology_additional":
            text += "Global hydrology loads the full DEM even when a block size is supplied."
        else:
            text += "Use a projected CRS and matching horizontal/elevation units."
        return text

    def selected_method(self, parameters, context):
        return self.method_id

    def createInstance(self):
        return GMXMethodAlgorithm(self.method_id)
