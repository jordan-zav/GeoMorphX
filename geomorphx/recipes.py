"""Portable, versioned recipes shared by Python, CLI and QGIS.

Legacy recommendation and workbench documents are accepted at the boundary.
Only an explicit method/parameter allowlist reaches the numerical engine.
"""
from __future__ import annotations

import json
import math
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

from geomorphx.api import compute_rrim
from geomorphx.methods import METHODS
from geomorphx.validation import inspect_dem, sha256_file

FORMAT = "geomorphx-recipe"
SCHEMA_VERSION = "1.0"
DEFAULT_PARAMETERS = dict(window=9, scales=[5, 15, 45], azimuth_deg=0., tile_size=0,
                          flatness_deg=1., geomorphon_skip=0, directional_weight=.5,
                          anisotropy_weight=.35, roughness_weight=.25, structural_weight=.15)


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"Recipe {name} must be an integer >= {minimum}")


def _number(value, name, lower, upper, *, exclusive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Recipe {name} must be finite and numeric")
    valid = lower < value < upper if exclusive else lower <= value <= upper
    if not valid:
        raise ValueError(f"Recipe {name} must be between {lower} and {upper}")


def normalize_recipe(recipe: dict) -> dict:
    """Validate all products and return a detached canonical recipe with defaults.

    Accepts geomorphx-recipe/1.0, legacy recommendations schema 1.0, and
    geomorphx-workbench/version 1. Does not read DEMs or create output files.
    """
    if not isinstance(recipe, dict):
        raise ValueError("Recipe must be an object")
    kind = recipe.get("format")
    if kind == FORMAT and recipe.get("schema_version") == SCHEMA_VERSION:
        entries = recipe.get("products")
    elif kind == "geomorphx-workbench" and type(recipe.get("version")) is int and recipe["version"] == 1:
        entries = recipe.get("products")
    elif kind is None and recipe.get("schema_version") == "1.0":
        entries = recipe.get("recommendations")
    else:
        raise ValueError("Unsupported recipe format or schema_version")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Recipe must contain at least one product")
    if "products" in recipe and "recommendations" in recipe:
        raise ValueError("Recipe cannot contain both products and recommendations")
    assumptions = deepcopy(recipe.get("input_assumptions", {}))
    if not isinstance(assumptions, dict):
        raise ValueError("input_assumptions must be an object")
    if "pixel_size_m" in assumptions and assumptions["pixel_size_m"] is not None:
        _number(assumptions["pixel_size_m"], "pixel_size_m", 0, math.inf, exclusive=True)
    products = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("method") not in METHODS:
            raise ValueError("Each product must define a known method")
        supplied = entry.get("parameters", {})
        if not isinstance(supplied, dict):
            raise ValueError("Product parameters must be an object")
        unknown = set(supplied) - DEFAULT_PARAMETERS.keys()
        if unknown:
            raise ValueError(f"Unsupported recipe parameters: {sorted(unknown)}")
        params = deepcopy(DEFAULT_PARAMETERS)
        params.update(deepcopy(supplied))
        if params["scales"] is None:  # Legacy recommendation recipes allowed null.
            params["scales"] = deepcopy(DEFAULT_PARAMETERS["scales"])
        _integer(params["window"], "window", 3)
        _integer(params["tile_size"], "tile_size", 0)
        _integer(params["geomorphon_skip"], "geomorphon_skip", 0)
        if not isinstance(params["scales"], list) or not params["scales"]:
            raise ValueError("Recipe scales must be a non-empty list of integers >= 3")
        for scale in params["scales"]:
            _integer(scale, "scale", 3)
        for name in ("directional_weight", "anisotropy_weight", "roughness_weight", "structural_weight"):
            _number(params[name], name, 0, 1)
        _number(params["flatness_deg"], "flatness_deg", 0, 90, exclusive=True)
        method = entry["method"]
        if method == "rrim_plus" and sum(params[name] for name in (
            "anisotropy_weight", "roughness_weight", "structural_weight"
        )) > 1:
            raise ValueError("Recipe RRIM+ weights must sum to <= 1")
        if method.startswith("geomorphon"):
            radius = (params["window"] + int(params["window"] % 2 == 0)) // 2
            if radius < 2 or params["geomorphon_skip"] > radius - 2:
                raise ValueError("Geomorphon skip must be in [0, radius - 2]; window must be >= 5")
        from core_py.geomorphx_core.rrim import _parse_azimuths
        try:
            angles = _parse_azimuths(params["azimuth_deg"])
            if not all(math.isfinite(angle) for angle in angles):
                raise ValueError("Nonfinite angle")
        except (TypeError, ValueError) as error:
            raise ValueError("Recipe azimuth_deg must contain finite angles") from error
        if method == "hillshade" and angles and not 0 <= angles[0] < 360:
            raise ValueError("Recipe hillshade azimuth must be in [0, 360)")
        params["azimuth_deg"] = angles[0] if len(angles) == 1 else angles
        role, rationale = entry.get("role", "unspecified"), entry.get("rationale", "")
        if not isinstance(role, str) or not isinstance(rationale, str):
            raise ValueError("Product role and rationale must be strings")
        products.append(dict(method=method, parameters=params, role=role, rationale=rationale))
    metadata = deepcopy(recipe.get("metadata", {}))
    if not isinstance(metadata, dict):
        raise ValueError("Recipe metadata must be an object")
    # Retain the interpretation context of recommendation documents as metadata.
    for name in ("objective", "description", "scale_windows_px", "scale_basis", "validation_note"):
        if name in recipe:
            metadata[name] = deepcopy(recipe[name])
    normalized = dict(format=FORMAT, schema_version=SCHEMA_VERSION,
                      input_assumptions=assumptions, metadata=metadata, products=products)
    try:
        json.dumps(normalized, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("Recipe must contain finite JSON-serializable values") from error
    return normalized


def create_recipe(products: list[dict], *, input_assumptions=None, metadata=None) -> dict:
    """Create a canonical recipe from explicit product methods and parameters."""
    return normalize_recipe(dict(format=FORMAT, schema_version=SCHEMA_VERSION, products=products,
                                 input_assumptions={} if input_assumptions is None else input_assumptions,
                                 metadata={} if metadata is None else metadata))


def load_recipe(path: str | Path) -> dict:
    """Load canonical or legacy JSON, accepting a Windows UTF-8 BOM."""
    return normalize_recipe(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def save_recipe(recipe: dict, path: str | Path) -> Path:
    """Write a validated canonical document usable by every frontend."""
    normalized = normalize_recipe(recipe)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(normalized, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return target


def execute_recipe(recipe: dict | str | Path, *, dem_path: str | Path, out_dir: str | Path,
                   cancelled: Callable[[], bool] | None = None,
                   progress: Callable[[float], None] | None = None) -> tuple[list[Path], Path]:
    """Execute a portable or legacy recipe, preserving outputs on failure/cancel.

    Validates every product and the DEM before creating outputs. Existing product
    files/manifests are rejected. Cancellation is checked between products. A
    cancelled run returns its completed outputs and a manifest with that status;
    computation failures write a failed manifest and re-raise the original error.
    """
    return _execute_recipe(recipe, dem_path=dem_path, out_dir=out_dir,
                           cancelled=cancelled, progress=progress, compute=compute_rrim)


def _execute_recipe(recipe, *, dem_path, out_dir, compute, cancelled=None, progress=None):
    normalized = normalize_recipe(recipe) if isinstance(recipe, dict) else load_recipe(recipe)
    source_info = inspect_dem(dem_path, expected_pixel_size_m=normalized["input_assumptions"].get("pixel_size_m"))
    source_info["sha256"] = sha256_file(dem_path)
    target = Path(out_dir)
    manifest = target / "recipe_run_manifest.json"
    reservation = target / "recipe_run.reservation.json"
    paths = [target / f"{index:02d}_{entry['method']}.tif" for index, entry in enumerate(normalized["products"], 1)]
    for path in [manifest, reservation, *paths, *(Path(str(p) + ".meta.json") for p in paths)]:
        if path.resolve() == Path(dem_path).resolve():
            raise ValueError("Recipe output must differ from the input DEM")
        if path.exists():
            raise FileExistsError(f"Recipe output already exists; choose a new directory: {path}")
    target.mkdir(parents=True, exist_ok=True)
    # An exclusive, retained reservation prevents concurrent jobs from passing
    # the same preflight and overwriting each other's products. No lock cleanup.
    with reservation.open("x", encoding="utf-8") as handle:
        json.dump(dict(format="geomorphx-run-reservation", input_sha256=source_info["sha256"]), handle)
    outputs, records = [], []
    report = dict(format="geomorphx-run", schema_version=SCHEMA_VERSION, recipe=normalized,
                  input_dem=str(dem_path), input_validation=source_info, outputs=records,
                  status="running", error="")
    try:
        for entry, path in zip(normalized["products"], paths):
            if cancelled is not None and cancelled():
                report["status"] = "cancelled"
                break
            produced = compute(dem_path=dem_path, out_path=path, method=entry["method"], **entry["parameters"])
            outputs.append(Path(produced))
            records.append(dict(method=entry["method"], role=entry["role"], rationale=entry["rationale"],
                                parameters=entry["parameters"], output=str(produced),
                                metadata=str(produced) + ".meta.json", sha256=sha256_file(produced)))
            if progress is not None:
                progress(100 * len(outputs) / len(paths))
        else:
            report["status"] = "complete"
        if sha256_file(dem_path) != source_info["sha256"]:
            raise RuntimeError("Input DEM changed while the recipe was running; outputs require review")
    except Exception as error:
        report.update(status="failed", error=str(error))
        raise
    finally:
        manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return outputs, manifest
