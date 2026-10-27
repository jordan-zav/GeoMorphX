# Original project brief

This is a historical design summary derived from the local conceptual PDF.
For current features and limits, see [Status](STATUS.md) and the
[project README](../README.md).

## Original purpose

Build a scientific/computational framework for advanced DEM geomorphometry,
keeping numerical computation separate from the graphical interface. Bridge
published terrain-analysis methods and practical everyday GIS workflows.

The original principles were an independent scientific core, API/CLI automation,
progressive tiling and parallelism, reproducibility, traceable parameters and
methodological extensibility. The initial MVP comprised RRIM baseline/multiscale,
batch computation, raster outputs and JSON metadata.

## Evolution of the design

Python remains the shared core; optional Rust kernels have been implemented.
QGIS, initially described as an optional frontend, is now the primary desktop
interface. Core computation and the Python API/CLI remain usable outside QGIS.
The original two-method MVP is not the current catalogue or a claim of stable
scientific validation. Plugin 0.5.1 is experimental.

The conceptual PDF is historical planning material. Proposed features in it
must be checked against the implementation plan and current status.
