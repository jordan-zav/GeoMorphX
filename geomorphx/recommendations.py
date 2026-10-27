"""Objective-driven, reproducible terrain-visualization recommendations.

This module deliberately does not decide scientific interpretation.  It turns a
declared mapping objective and the physical size of a target feature into a
transparent processing recipe that a user can inspect, save, modify and rerun.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from geomorphx.api import compute_rrim


@dataclass(frozen=True)
class Recommendation:
    """A method recipe and the reason it was selected."""

    method: str
    role: str
    parameters: dict[str, Any]
    rationale: str


_OBJECTIVES: dict[str, tuple[str, tuple[tuple[str, str, str], ...]]] = {
    "hydrology_mfd": (
        "Exploración de drenaje mediante flujo múltiple de Freeman, exponente 1.1.",
        (("fill_depressions", "diagnostic", "Permite inspeccionar el relleno de depresiones."),
         ("flow_accumulation_mfd", "primary", "Distribuye el aporte entre vecinos de menor elevación."),
         ("twi_mfd", "support", "Índice topográfico con área de flujo múltiple; no equivale a humedad observada.")),
    ),
    "drainage": (
        "Dirección, cuencas y longitud aguas abajo de la red D8.",
        (("flow_direction_d8", "primary", "Conserva el sentido de salida de cada celda."),
         ("drainage_basins_d8", "primary", "Agrupa las celdas que comparten salida del DEM."),
         ("flow_length_d8", "diagnostic", "Mide la distancia acumulada hasta la salida.")),
    ),
    "landforms": (
        "Clasificación exploratoria de diez formas mediante horizontes en ocho direcciones.",
        (
            ("geomorphons", "primary", "Clasifica formas por patrones de líneas de visión; comparación anglev1."),
            ("geomorphon_ternary", "diagnostic", "Conserva el patrón invariante para revisar la clasificación."),
            ("slope", "context", "Permite contrastar las clases con la pendiente física del terreno."),
        ),
    ),
    "general_relief": (
        "Lectura general del relieve sin depender de una sola dirección de luz.",
        (
            ("multidirectional_hillshade", "context", "Evita ocultar laderas por depender de una sola dirección de luz."),
            ("rrim_multiscale", "detail", "Integra contraste local en varias escalas."),
            ("slope", "diagnostic", "Permite comprobar qué pendientes explican el contraste."),
        ),
    ),
    "microtopography": (
        "Búsqueda de rasgos sutiles de escala pequeña, como zanjas, montículos o terrazas.",
        (
            ("positive_openness", "primary", "Mide cuán abierto está el hemisferio superior y destaca formas sutiles."),
            ("rrim_multiscale", "secondary", "Resalta variación de relieve local a escalas pequeñas y medias."),
            ("tpi", "diagnostic", "Separa elevaciones y depresiones respecto de su vecindario."),
            ("multidirectional_hillshade", "context", "Ayuda a verificar visualmente la morfología sin sesgo de una única luz."),
        ),
    ),
    "lineaments": (
        "Reconocimiento exploratorio de alineamientos, escarpes y discontinuidades.",
        (
            ("rrim_structural_multiscale", "primary", "Mide coherencia y orientación local en varias escalas."),
            ("rrim_anisotropic_multiscale", "secondary", "Ofrece contraste direccional complementario."),
            ("slope", "diagnostic", "Permite descartar respuestas causadas solo por pendiente alta."),
        ),
    ),
    "paleochannels": (
        "Identificación exploratoria de depresiones y formas de drenaje abandonado.",
        (
            ("negative_openness", "primary", "Destaca la apertura del hemisferio inferior, útil para depresiones y formas incisas."),
            ("rrim_multiscale", "secondary", "Conserva variación local a más de una escala."),
            ("tpi", "diagnostic", "Hace visibles zonas relativamente deprimidas."),
            ("wetness_proxy", "support", "Aporta una señal topográfica auxiliar, no un modelo hidrológico."),
        ),
    ),
    "landslides": (
        "Inspección de escarpes, rugosidad y cambios locales de pendiente asociados a remoción en masa.",
        (
            ("rrim_plus", "primary", "Combina relieve local, pendiente, rugosidad y estructura."),
            ("curvature_profile", "diagnostic", "Ayuda a localizar cambios de convexidad en la dirección de máxima pendiente."),
            ("tri_riley", "diagnostic", "Rugosidad de Riley respecto de ocho vecinos."),
        ),
    ),
    "hydrology": (
        "Exploración de drenaje superficial mediante relleno de depresiones y flujo D8.",
        (
            ("fill_depressions", "diagnostic", "Permite inspeccionar la modificación de depresiones."),
            ("flow_accumulation_d8", "primary", "Cuenta las celdas contribuyentes tras rellenar depresiones."),
            ("twi_d8", "support", "Combina área contribuyente D8 y pendiente; no modela humedad observada."),
        ),
    ),
}


def available_objectives() -> tuple[str, ...]:
    """Return stable objective identifiers accepted by :func:`recommend`.
    """
    return tuple(_OBJECTIVES)


def _odd_window(value: int) -> int:
    value = max(3, int(value))
    return value if value % 2 else value + 1


def recommend(
    objective: str,
    *,
    pixel_size_m: float,
    feature_min_m: float | None = None,
    feature_max_m: float | None = None,
) -> dict[str, Any]:
    """Build a transparent processing recipe for a terrain-mapping objective.

    Feature dimensions are optional. When supplied, they are converted to odd
    pixel windows. This keeps the recommendation tied to DEM resolution instead
    of to arbitrary hard-coded raster windows.
    """
    if objective not in _OBJECTIVES:
        raise ValueError(f"objective must be one of: {', '.join(available_objectives())}")
    if not math.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be > 0")
    if (feature_min_m is None) != (feature_max_m is None):
        raise ValueError("feature_min_m and feature_max_m must be provided together")
    if feature_min_m is not None and (not math.isfinite(feature_min_m) or feature_max_m is None
                                    or not math.isfinite(feature_max_m)
                                    or feature_min_m <= 0 or feature_max_m < feature_min_m):
        raise ValueError("feature sizes must be positive and feature_max_m must be >= feature_min_m")

    if feature_min_m is None:
        scales = [5, 15, 45]
        scale_basis = "default pixel windows; provide feature_min_m and feature_max_m for physical calibration"
    else:
        mid_m = (feature_min_m + feature_max_m) / 2.0
        scales = sorted({_odd_window(feature_min_m / pixel_size_m), _odd_window(mid_m / pixel_size_m), _odd_window(feature_max_m / pixel_size_m)})
        scale_basis = "windows derived from requested feature sizes and DEM pixel size"

    description, entries = _OBJECTIVES[objective]
    recommendations: list[Recommendation] = []
    for method, role, rationale in entries:
        parameters: dict[str, Any] = {}
        if method in {"geomorphons", "geomorphon_ternary"}:
            # Radius >= 3 permits multiple samples along diagonal rays.
            parameters.update(window=max(7, scales[len(scales) // 2]), flatness_deg=1.0, geomorphon_skip=0)
        elif "multiscale" in method:
            parameters["scales"] = scales
        elif method in {
            "rrim_plus",
            "tpi",
            "tri",
            "wetness_proxy",
            "positive_openness",
            "negative_openness",
            "sky_view_factor",
        }:
            parameters["window"] = scales[len(scales) // 2]
        recommendations.append(Recommendation(method, role, parameters, rationale))

    return {
        "schema_version": "1.0",
        "objective": objective,
        "objective_description": description,
        "input_assumptions": {
            "pixel_size_m": float(pixel_size_m),
            "feature_min_m": feature_min_m,
            "feature_max_m": feature_max_m,
        },
        "scale_windows_px": scales,
        "scale_basis": scale_basis,
        "recommendations": [asdict(item) for item in recommendations],
        "validation_note": "Recommendations guide visual exploration; confirm interpreted features against independent data or field evidence.",
    }


def execute_recipe(recipe, *, dem_path, out_dir):
    """Compatibility entry point; accepts all supported recipe formats."""
    from geomorphx.recipes import _execute_recipe
    return _execute_recipe(recipe, dem_path=dem_path, out_dir=out_dir, compute=compute_rrim)
