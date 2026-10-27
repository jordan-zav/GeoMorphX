# GeoMorphX user guide

See [Español: guía del complemento](../qgis_plugin/README.es.md) for the Spanish
installation and workbench guide.

## Installation

Use the plugin ZIP for version 0.5.1. If working from source, run the packaging
command in the project README; generated archives live in dist/qgis and are
excluded from Git. In QGIS, select Plugins → Manage and Install Plugins → Install
from ZIP, choose the archive and enable GeoMorphX. This follows QGIS's
[documented plugin installation workflow](https://docs.qgis.org/3.44/en/docs/user_manual/plugins/plugins.html).

The package includes its Python core. It uses NumPy and either Rasterio or the
native GDAL bindings supplied by QGIS. It does not install Python packages or
require a Rust toolchain. Restart QGIS if an older GeoMorphX core was loaded.
The declared range is QGIS 3.28–3.x; the tested installation is QGIS 3.44.12 on
Windows, Python 3.12. QGIS 4 is outside the declared range.

## Prepare the DEM

Use a local single-band elevation raster, preferably GeoTIFF. Check:

- valid projected CRS and a north-up, unrotated grid;
- horizontal/elevation units that match, such as metres/metres;
- a resolution appropriate to the landform you want to examine;
- an explicit NoData value or mask and sensible raster bounds.

Assigning a CRS label does not reproject coordinates. Reproject a geographic
longitude/latitude DEM to an appropriate projected CRS before calculation.
GeoMorphX does not infer a vertical datum or convert vertical units, and it does
not distinguish intended units from plausible-looking numeric values.

## Prepare products

Open Raster → GeoMorphX → GeoMorphX Terrain Workbench. Select the project layer
under Input DEM. Choose a category and method. Geomorphometry, RRIM and Terrain
forms are the main categories; Hydrology is an additional toolset.

Only parameters relevant to the selected method are shown. Window and scale
sizes are pixels, not metres. The geomorphon window is a diameter; its search
radius is approximately half that window, with the documented physical-distance
rule. Use block size to control local processing windows, not as a guarantee of
total process memory. Hydrology still requires a complete grid.

Click Add product to snapshot the current parameters. Change the method or
parameters and add another product if needed. To replace a queued product,
remove it and add a new one. Each product uses the source DEM; products are not
a sequential filter stack. If the list is empty, Run uses the current selection.

Save recipe exports a reusable JSON document. Load recipe accepts current and
legacy formats. Imported resolution assumptions are retained; an incompatible
DEM causes execution to fail rather than silently changing the recipe.

## Run and inspect

Choose an output directory and click Run and add layers. The panel creates a
uniquely named run folder and processes the products in a background QGIS task.
Completed products are loaded into the project. Ten-class geomorphon layers
receive a categorized renderer; other products use their default raster display.

| File | Purpose |
| --- | --- |
| Numbered method GeoTIFFs | Core numerical products |
| Matching .tif.meta.json files | Method, effective parameters, grid shape and processing mode |
| recipe_run_manifest.json | Recipe, input validation, hashes, completed products and status |
| workflow.json | Panel compatibility view of the run manifest |
| recipe_run.reservation.json | Exclusive reservation of that recipe output folder |

The classic RRIM tools are separate legacy workflows and may produce different
intermediate/display artifacts. Experimental RRIM stages may occupy several
times the DEM's storage; inspect the recorded scratch directory and pipeline.json.
They are retained for review.

Run log shows paths and errors. Cancellation waits for the current product and
stops before the next. Completed products are retained. A cancelled or failed
manifest does not mean the full requested workflow completed.

## Troubleshooting

| Symptom | Check or action |
| --- | --- |
| No layer in the selector | Add a raster to the project and select a valid one-band DEM |
| Geographic/rotated grid rejected | Reproject to a suitable north-up projected grid |
| Recipe pixel-size mismatch | Review both raster axes and the recipe's pixel_size_m assumption |
| NoData fringe or empty geomorphon edges | Each of the eight search rays needs valid samples; inspect holes and radius |
| Memory remains high with hydrology | Those methods still use full-grid memory; block size does not change routing requirements |
| High disk use with RRIM | The globally normalized pipeline retains intermediate rasters |
| Existing recipe output rejected | Use a new folder; do not share one recipe output folder between jobs |
| Cancellation appears delayed | The current product completes before cancellation is checked |
| Old behavior after replacing the plugin | Restart QGIS to unload the previous bundled modules |
| PNG update-access diagnostic in classic RGB export | Known legacy rendering issue; verify the output and consult Status |

See [automation](AUTOMATION.md), [method details](GEOMORPHONS.md),
[memory and tiling](SCALABILITY.md) and [known issues](STATUS.md).
