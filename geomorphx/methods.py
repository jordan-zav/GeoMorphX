"""Shared method catalogue for the API and every frontend.

Keep the original six QGIS entries in order: saved Processing models use indices.
"""

METHODS = (
    "rrim_baseline", "rrim_multiscale", "rrim_anisotropic",
    "rrim_anisotropic_multiscale", "rrim_structural", "rrim_plus",
    "rrim_structural_multiscale", "slope", "aspect", "hillshade",
    "multidirectional_hillshade", "positive_openness", "negative_openness",
    "sky_view_factor", "curvature_profile", "curvature_plan", "curvature_mean",
    "tpi", "tri", "wetness_proxy", "local_relief", "tri_riley",
    "fill_depressions", "flow_accumulation_d8", "twi_d8",
    "geomorphons", "geomorphon_ternary",
    "flow_direction_d8", "drainage_basins_d8", "flow_length_d8",
    "flow_accumulation_mfd", "twi_mfd",
)

GLOBAL_METHODS = frozenset(
    method for method in METHODS
    if method.startswith("rrim_") or method in {
        "fill_depressions", "flow_accumulation_d8", "twi_d8",
        "flow_direction_d8", "drainage_basins_d8", "flow_length_d8",
        "flow_accumulation_mfd", "twi_mfd",
    }
)
