# Automating GeoMorphX

English | [Español](AUTOMATIZACION.md)

The same JSON recipe works in the QGIS workbench, Processing, the CLI and the
Python API. They use the shared validator/executor in geomorphx.recipes.

## Choose an interface

| Environment | Interface |
| --- | --- |
| QGIS, without scripting | Workbench recipes, Processing batch jobs or Model Designer |
| QGIS Python console/scripts | processing.run with geomorphx_rrim_suite:run_recipe |
| Terminal or scheduled job | geomorphx run-recipe |
| Python program/notebook | Public execute_recipe API |

These are local interfaces. Enable the plugin before importing its bundled core
in QGIS. Outside QGIS, install the Python package or use the source development
environment. The plugin ZIP is the main distribution for QGIS users.

## Portable recipe format

New documents use geomorphx-recipe with schema_version 1.0:

    {
      "format": "geomorphx-recipe",
      "schema_version": "1.0",
      "input_assumptions": {},
      "products": [
        {"method": "slope", "parameters": {"tile_size": 512}},
        {"method": "geomorphons", "parameters": {"window": 9}}
      ]
    }

Each product uses the original DEM. Unspecified parameters receive the format's
defaults. Saving through the panel or save_recipe writes explicit parameters.
The JSON Schema is recipe.schema.json beside this guide. Examples are in
examples/automation in the repository and examples inside the ZIP.

Windows and scales are in pixels. Set input_assumptions.pixel_size_m to require
a particular resolution: execution checks both axes after conversion to metres.
An empty assumptions object allows different resolutions, so review the physical
meaning of the pixel windows yourself. Use a local, single-band, north-up DEM
with a projected CRS and matching horizontal/elevation units.

## QGIS workbench and Processing

Use Save recipe in the workbench, then pass that file to the CLI, API or
Processing. Load recipe accepts current and legacy documents. Resolution
assumptions, roles and rationale survive import/export.

In the QGIS Python console with GeoMorphX enabled:

    import processing

    result = processing.run("geomorphx_rrim_suite:run_recipe", {
        "INPUT_DEM": "D:/data/dem.tif",
        "RECIPE": "D:/recipes/terrain.json",
        "OUT_DIR": "D:/results/run_001",
    })
    print(result["MANIFEST"])

Run portable recipe is in the Automation group. It supports Processing batches
and Model Designer. Use different output directories for different jobs. This
tool returns an output folder and manifest; the workbench additionally loads
product layers into the project.

## Command line

With the GeoMorphX CLI installed in the active environment:

    geomorphx validate-recipe --recipe terrain.json
    geomorphx run-recipe --recipe terrain.json --dem dem.tif --out-dir run_001

Generate an objective-based recipe or convert an old document:

    geomorphx recommend --objective landforms --pixel-size-m 2 --out forms.json
    geomorphx validate-recipe --recipe legacy.json --out portable.json

validate-recipe checks the whole document without opening a DEM or computing
products. Execution checks the real DEM resolution. A normal CLI run exits with
zero; an uncaught error exits nonzero. Retain stdout/stderr in scheduled jobs.
In a source development checkout, python -m cli.geomorphx_cli accepts the same
arguments without installing a command entry point.

## Python API

    from geomorphx import create_recipe, save_recipe, execute_recipe

    recipe = create_recipe([
        {"method": "slope", "parameters": {"tile_size": 512}},
        {"method": "tri_riley"},
    ])
    save_recipe(recipe, "terrain.json")
    outputs, manifest = execute_recipe(
        "terrain.json", dem_path="dem.tif", out_dir="run_001",
    )

| Public function | Result |
| --- | --- |
| create_recipe(products, ...) | Canonical document with defaults and optional assumptions/metadata |
| load_recipe(path) | Validated canonical document; accepts UTF-8 with or without a BOM |
| normalize_recipe(document) | Detached canonical copy, with no file I/O |
| save_recipe(document, path) | Validated canonical JSON written to the requested path |
| execute_recipe(document_or_path, ...) | Completed output paths and execution-manifest path |

execute_recipe accepts progress, a callable receiving a percentage, and
cancelled, a callable returning a boolean. Cancellation is checked between
products, not inside a running kernel. A cancelled run returns completed outputs
and a manifest marked cancelled; inspect that status before declaring success.

The API function recommend still returns its historical recommendation structure.
save_recipe converts it to portable JSON. Existing calls through
geomorphx.recommendations.execute_recipe remain available as a compatibility
adapter. Direct raster/array APIs, such as compute_rrim and compute_rrim_array,
remain available when a recipe is unnecessary.

## Defaults and explicit comparisons

| Recipe/API parameter | Format 1.0 default |
| --- | --- |
| window / scales | 9 / [5, 15, 45] pixels |
| azimuth_deg | 0 degrees |
| tile_size | 0, full-array request |
| flatness_deg / geomorphon_skip | 1 degree / 0 |
| directional_weight | 0.5 |
| anisotropy_weight / roughness_weight / structural_weight | 0.35 / 0.25 / 0.15 |

The panel starts with azimuth 45 and block size 512 and saves those explicit
values. Direct Processing compute tools retain historical defaults: azimuth 45,
directional weight 0.6, anisotropy weight 0.3 and structural weight 0.2.
Set parameters explicitly when comparing a direct Processing call with a recipe.
Every frontend uses the same numerical engine, but initial UI defaults are not
identical. The run_recipe tool reads the recipe's values.

## Files, failures and concurrent jobs

Core products create GeoTIFFs and metadata sidecars. recipe_run_manifest.json
records the normalized recipe, actual DEM profile and SHA-256, completed products,
parameters, output hashes and complete/cancelled/failed status. The workbench also
writes workflow.json as a compatibility view of that record.

All products are validated before computation. API preflight errors, including
invalid methods or incompatible resolution, create no output products. If a
later product fails, completed products and a failed manifest are retained, and
the error is re-raised. The panel also records preflight failures in its run log.

Existing products and manifests are rejected. An exclusively created
recipe_run.reservation.json prevents two recipe jobs from sharing an output
directory. It is retained after success or failure; choose a fresh directory to
retry. There is no automatic cleanup or resume mechanism. This overwrite guard
belongs to the recipe executor; do not assume that every low-level compute call
has the same policy.

## Compatibility and limits

The reader accepts portable geomorphx-recipe 1.0, geomorphx-workbench version 1
and recommendation schema_version 1.0. New files use the portable format;
unsupported versions are rejected. Processing currently exposes 43 tools.

Automation does not change method limits. RRIM variants remain experimental,
geomorphons implements the documented basic rule, and hydrology needs full-grid
memory. Review units, scale and outputs before interpreting them. Synthetic and
offscreen QGIS integration checks do not establish field accuracy.
