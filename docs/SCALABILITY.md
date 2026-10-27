# Memory, tiling and additional hydrology

English | [Español](ESCALABILIDAD_Y_HIDROLOGIA.md)

GeoMorphX focuses on geomorphometry and relief visualization. The hydrological
methods already present remain an additional toolset with different memory
requirements. A block-size setting is not a universal RAM limit.

## Local terrain products

Local processing reads windows with method-specific halos. Derivatives, focal
statistics and geomorphon searches use enough surrounding cells to match the
full-grid computation. Raster edges remain real raster edges; internal block
boundaries are not treated as separate DEM boundaries.

Window dimensions, halo size and simultaneous arrays control working memory.
Large windows can still require substantial memory. Python, GDAL, optional Rust,
open datasets and host caches contribute to total process use.

## Globally normalized RRIM

The seven experimental variants use multiple windowed passes. Components are
written to disk, their ranges are collected globally, and the same normalization
range is used over the whole DEM. This avoids independent per-block stretching.

    geomorphx compute --dem dem.tif --out outputs/rrim.tif --method rrim_plus --window 15 --tile-size 512 --scratch-dir D:/GeoMorphX_Scratch

A zero tile size requests full-array processing. In direct QGIS Compute/Compute
Batch tools the scratch directory can be selected. The dock uses the normal
session/system temporary location for RRIM stages.

Scratch storage can grow to several times the input size. Each run has a unique
stage directory under the selected scratch root, DevResources session or system
temporary directory. Stages and pipeline.json are retained for review. The
pipeline manifest records operation inputs/outputs, halos, global ranges,
largest read window and complete/failed status.

The Rasterio path requests a 32 MiB GDAL cache during streamed evaluation. The
native GDAL fallback deliberately preserves QGIS's existing global cache settings.
Neither path promises an exact process-wide memory ceiling.

Streaming does not change RRIM's scientific convention. The core compositions
retain legacy unit-pixel components; equivalent block processing does not prove
equivalence to classical RRIM.

## Additional hydrology

| Method | Convention |
| --- | --- |
| fill_depressions | Priority-Flood filling |
| flow_accumulation_d8 | Contributing-cell count, including the cell itself |
| twi_d8 | TWI from D8 contributing area and filled-DEM slope |
| flow_direction_d8 | 0 outlet; 1 N, 2 NE, 3 E, 4 SE, 5 S, 6 SW, 7 W, 8 NW |
| drainage_basins_d8 | Final D8 outlet labels, starting at 1 in row-major outlet order |
| flow_length_d8 | Downstream distance to the outlet, in CRS horizontal units |
| flow_accumulation_mfd | Fractional contributing-cell count, including the cell itself |
| twi_mfd | TWI using the multiple-flow contributing area |

Routing uses Priority-Flood depression filling. D8 chooses the steepest
descending neighbor; MFD weights descending neighbors by slope to power 1.1 and
normalizes their contributions. Filled flats with no descent use the flood
parent tree. Raster boundaries and NoData holes are open outlet boundaries.
This deterministic treatment is not an observation of actual channel positions.

Both TWI variants use an approximate contour width of sqrt(pixel area) and a
slope-tangent floor of 1e-6. No additional contour-length weighting is applied.
The implementations are not claimed numerically identical to every SAGA or
RichDEM option. See the [RichDEM flow metrics](https://richdem.readthedocs.io/en/latest/flow_metrics.html)
and [SAGA flow accumulation](https://saga-gis.sourceforge.io/saga_tool_doc/9.9.1/ta_hydrology_1.html)
references for method context.

These methods currently hold the whole routing grid in memory. Requesting
blocks triggers an explicit full-grid fallback. Float32 products lose exact
integer counts above 2^24; excessive basin-label counts are rejected to avoid
label collisions. Vector networks, Strahler order and external pour-point basin
delineation are not implemented.

## Recipes and evidence

Recipes validate methods, parameters and actual raster resolution before
computing. Manifests record input/output hashes and recheck the source at the
end. See [Automation](AUTOMATION.md) for cancellation, failures and reservations.

The source tests check local and streamed/full-grid consistency, including
NoData and boundaries. The synthetic notebook checks analytical slope and TRI,
MFD conservation and one RRIM+ full/block comparison. These are numerical checks,
not regional performance measurements or field validation. Benchmark tile
microtests do not establish spatial continuity of production rasters.

Real QGIS 3.44.12 integration has been checked on Windows without Rasterio.
Other platforms, larger regional DEMs and optimized I/O/scratch usage remain
work items. See [Status](STATUS.md) and [Development](DEVELOPMENT.md).
