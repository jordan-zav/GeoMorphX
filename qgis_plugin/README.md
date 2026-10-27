# GeoMorphX for QGIS

English | [Español](README.es.md)

Experimental plugin 0.5.1. QGIS is the primary desktop interface. The ZIP
includes the Python core and uses QGIS's NumPy/GDAL stack; Rasterio and Rust
are optional. No dependency installer modifies the host interpreter.

## Install and open

Install the plugin ZIP through Plugins → Manage and Install Plugins → Install
from ZIP. Enable GeoMorphX, then open Raster → GeoMorphX → GeoMorphX Terrain
Workbench. Restart QGIS when replacing an already loaded GeoMorphX version.

From a source checkout, build a ZIP with:

    python scripts/build_qgis_plugin.py --out-dir dist/qgis

Install the generated archive, not an archive of the whole repository.
The declared version range is QGIS 3.28–3.x; testing used QGIS 3.44.12 on
Windows with Python 3.12. The plugin is not yet in the official repository.

## Workbench

Select a local single-band DEM with a projected CRS and matching horizontal
and elevation units. Choose a method, edit its parameters and click Add product.
Products preserve their parameter values when added; remove and add one again
to replace it. Each product uses the original DEM, not the preceding result.

Choose an output directory and click Run and add layers. A background task
creates a new run folder and loads completed products into the project.
Geomorphon classes receive a categorized legend. Run log lists results and
errors; Guide explains the workflow. Cancellation takes effect between products.

Save recipe writes portable geomorphx-recipe 1.0 JSON for the panel, API,
Processing or CLI. Load recipe also reads the two legacy formats. Imported
resolution assumptions and interpretation context are retained. Review pixel
scales before using the recipe with a different DEM resolution.

## Processing and automation

The provider ID remains geomorphx_rrim_suite. Its 43 tools comprise:

- 32 named methods with terrain_ followed by the method identifier;
- suite compute and folder compute;
- single/folder benchmarks;
- curvature, TPI/wetness and two geomorphon blocks;
- classic RRIM generation and RGB composition;
- run_recipe, shown as Run portable recipe in the Automation group.

The original ten tool IDs and first six historical method indices are retained
for existing models. Use Processing batches or Model Designer for repeatable
jobs. For recipes, choose a new output folder for each run. The manifest records
input/output hashes and completion, cancellation or failure.

The ZIP contains AUTOMATION.md in English, AUTOMATIZACION.md in Spanish,
recipe.schema.json and runnable examples. In a source checkout the guides are
in docs. Input/output paths and arbitrary Python code cannot be injected through
recipe parameters; the executor accepts explicit method and parameter names.

## Methods, memory and known limits

Core RRIM variants are experimental compositions and are separate from the
classic generator/composer. The legacy wetness proxy is distinct from TWI
computed using flow accumulation. Hydrology is an additional toolset and still
loads the entire DEM; block size does not limit its memory use.

Local products use block halos. Streamed RRIM uses global normalization and
retains disk stages. The GDAL fallback preserves the host's cache configuration.
No automatic vertical-unit conversion is performed.

The ZIP has been executed with real QGIS Processing and offscreen Qt widgets
using an isolated profile. Checks cover all 43 tools, synthetic numerical
comparisons, shared recipes, background tasks, categorized styles and unload.
Manual user sessions, other platforms and independent scientific validation
remain pending. The legacy RGB export emits a PNG update-access diagnostic even
when the GeoTIFF completes; that rendering path needs further review.
