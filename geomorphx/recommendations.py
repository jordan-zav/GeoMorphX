"""Objective-driven, reproducible terrain-visualization recommendations.

This module deliberately does not decide scientific interpretation.  It turns a
declared mapping objective and the physical size of a target feature into a
transparent processing recipe that a user can inspect, save, modify and rerun.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
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
            ("tri", "diagnostic", "Resume rugosidad local para contrastar superficies alteradas."),
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
    if pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be > 0")
    if (feature_min_m is None) != (feature_max_m is None):
        raise ValueError("feature_min_m and feature_max_m must be provided together")
    if feature_min_m is not None and (feature_min_m <= 0 or feature_max_m is None or feature_max_m < feature_min_m):
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
        if "multiscale" in method:
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
            parameters["window"] = scales[1]
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


def execute_recipe(
    recipe: dict[str, Any],
    *,
    dem_path: str | Path,
    out_dir: str | Path,
) -> tuple[list[Path], Path]:
    """Run every method in a recommendation recipe and write a manifest.

    The recipe is intentionally explicit: only the listed method identifiers and
    parameters are executed.  This makes it possible to retain, review and rerun
    a visualization decision without hidden defaults in a GUI session.
    """
    if recipe.get("schema_version") != "1.0":
        raise ValueError("unsupported or missing recipe schema_version")
    entries = recipe.get("recommendations")
    if not isinstance(entries, list) or not entries:
        raise ValueError("recipe must contain at least one recommendation")

    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    manifest_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        method = entry.get("method")
        parameters = entry.get("parameters", {})
        if not isinstance(method, str) or not method:
            raise ValueError("each recommendation must define a method")
        if not isinstance(parameters, dict):
            raise ValueError("recommendation parameters must be an object")

        output = target / f"{index:02d}_{method}.tif"
        produced = compute_rrim(
            dem_path=dem_path,
            out_path=output,
            method=method,
            **parameters,
        )
        outputs.append(produced)
        manifest_entries.append(
            {
                "role": entry.get("role", "unspecified"),
                "method": method,
                "parameters": parameters,
                "rationale": entry.get("rationale", ""),
                "output": str(produced),
                "metadata": str(produced) + ".meta.json",
            }
        )

    manifest = target / "recipe_run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "recipe": recipe,
                "input_dem": str(dem_path),
                "outputs": manifest_entries,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    return outputs, manifest
