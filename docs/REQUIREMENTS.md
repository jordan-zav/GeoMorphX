# Initial requirements and current direction

Historical baseline. See [Status](STATUS.md) for implemented behavior and
[the implementation plan](IMPLEMENTATION_PLAN.md) for remaining work.

## Original functional requirements

- Read a single-band DEM.
- Compute RRIM baseline and multiscale products with configurable scales.
- Export GeoTIFF and JSON parameter metadata.
- Provide a command-line interface for repeatable processing.

## Original design requirements

Keep the scientific core separate from interfaces, make parameters and outputs
traceable, and allow gradual scaling through tiles and optional Rust kernels.
Computation should not require a running QGIS application.

## Current product direction

QGIS is the primary desktop interface. The core still does not require QGIS
for ordinary array/file calculations; API and CLI remain automation interfaces.
The standalone GUI is secondary compatibility tooling. The older statement that
QGIS was only an optional product frontend describes the original plan.

The current catalogue contains 32 core methods and 43 Processing tools, plus a
shared recipe format. Experimental status, physical units, NoData, memory and
independent-validation limits remain explicit requirements for documentation.
An implemented algorithm is not automatically a scientifically validated one.
