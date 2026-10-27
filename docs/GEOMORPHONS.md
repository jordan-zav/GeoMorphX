# Line-of-sight geomorphons

English | [Español](GEOMORPHONS.es.md)

GeoMorphX implements a basic eight-direction line-of-sight classification.
It exposes ten terrain forms and a canonical ternary pattern. The older
simplified QGIS algorithm retains its separate identifier and nine-class legend.

## Methods and parameters

| Method | Output |
| --- | --- |
| geomorphons | Terrain-form codes 1–10 |
| geomorphon_ternary | Minimum ternary code across eight rotations and their reflections; 498 possible patterns |

The window parameter is a pixel diameter. Even windows become the next odd
value, and radius is window // 2. The minimum accepted window is 5; at least 7
gives more than the minimum search support and reduces the special short-profile
tie cases. Choose a scale appropriate to the DEM and landforms.

| Parameter | Convention |
| --- | --- |
| window | Default 9; odd pixel diameter after normalization |
| flatness_deg | Default 1 degree; strictly between 0 and 90 |
| geomorphon_skip | Default 0; integer inner steps omitted from each ray, at most radius - 2 |
| cell_size | Physical (dy, dx), inferred for files or supplied to the array API |

CLI example:

    geomorphx compute --dem dem.tif --out forms.tif --method geomorphons --window 15 --flatness-deg 1 --geomorphon-skip 0

Use geomorphon_ternary for the pattern output. The landforms recommendation
includes forms, the ternary pattern and physical slope for comparison.

QGIS provides terrain_geomorphons and terrain_geomorphon_ternary under provider
geomorphx_rrim_suite. The gmx_geomorphons_los block writes both products. All
these adapters call the shared core.

## Numerical convention

Eight profiles are ordered clockwise from north. Each keeps its maximum and
minimum elevation angle. Samples must be strictly within radius × max(dy, dx)
in physical distance. Rectangular pixels and diagonals use their physical
distances; the processing halo expands to include that footprint.

The implemented basic anglev1 rule compares the absolute angular extrema to
assign a positive, negative or neutral sign. Profiles below the flatness
threshold, and exact equal-absolute-angle ties, are neutral. Sign counts map to
the ten forms. A mathematical constant-gradient surface can therefore be
classified as flat under this comparison; it is not a separate slope estimate.
The implementation explicitly tests that behavior.

The [GRASS manual](https://grass.osgeo.org/grass-stable/manuals/r.geomorphon.html)
describes the reference method and its broader option set. GeoMorphX implements
the basic rule only; its ray boundary and NoData policies are specified here.

## Legend

| Code | Form |
| --- | --- |
| 1 | Flat |
| 2 | Peak |
| 3 | Ridge |
| 4 | Shoulder |
| 5 | Spur |
| 6 | Slope |
| 7 | Hollow |
| 8 | Footslope |
| 9 | Valley |
| 10 | Pit |

## Raster edges and NoData

A ray stops at the raster boundary or the first NoData sample. It does not look
through a gap. Every one of the eight directions needs at least one valid
sample; otherwise the output is NaN. Expect excluded edges and fringes near
holes rather than a classification everywhere.

The geomorphon_components API also returns sign counts and ray coverage.
Coverage is the fraction of directions with samples, not confidence in the
geological correctness of the class. The simplified model's confidence output
is a separate legacy sign-contrast measure.

## Validation scope

Tests cover constructed ten-form examples, all 6,561 ternary patterns and their
498 canonical groups, rotation invariance, thresholds, skip, NoData and
full-grid/block consistency. Real QGIS 3.44.12 integration used an isolated
profile and offscreen Qt; it tested the algorithms and a categorized layer.
The source suite also contains adapter tests using substituted host APIs.

Extended correction, threshold-relaxation distance, anglev2/anglev2_distance
and additional geometry metrics are not implemented. Independent comparisons
with GRASS/Whitebox executables and field reference data remain pending. Do not
interpret implementation consistency as complete GRASS output equivalence.

## Implementation references

- [GRASS horizon comparison](https://github.com/OSGeo/grass/blob/main/raster/r.geomorphon/pattern.c)
- [GRASS form matrix and canonical patterns](https://github.com/OSGeo/grass/blob/main/raster/r.geomorphon/geom.c)
- [WhiteboxTools geomorphons implementation](https://github.com/jblindsay/whitebox-tools/blob/master/whitebox-tools-app/src/tools/terrain_analysis/geomorphons.rs)
