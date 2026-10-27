# GeoMorphX documentation

English | [Español](README.es.md)

Start with the [project README](../README.md). QGIS is the primary desktop
interface; the shared Python core and CLI support automation. Plugin 0.5.1 is
experimental, with 32 core methods and 43 Processing tools.

## User documentation

| Document | Purpose |
| --- | --- |
| [User guide](USER_GUIDE.md) | Installation, DEM preparation, workbench, outputs and troubleshooting |
| [Automation](AUTOMATION.md) | Portable recipes, Python API, CLI, Processing and manifests |
| [Recipe schema](recipe.schema.json) | JSON Schema for geomorphx-recipe 1.0 |
| [Geomorphons](GEOMORPHONS.md) | Search geometry, class codes, NoData and method limits |
| [Scalability](SCALABILITY.md) | Block processing, scratch disk, cache behavior and optional hydrology |
| [Status](STATUS.md) | Verified behavior, known issues and remaining validation |
| [QGIS plugin guide](../qgis_plugin/README.md) | Self-contained plugin instructions, also included in the ZIP |

## Development and project records

| Document | Purpose |
| --- | --- |
| [Development](DEVELOPMENT.md) | Source setup, ZIP/wheel packaging and appropriate checks |
| [Implementation plan, Spanish](IMPLEMENTATION_PLAN.md) | Implemented work and outstanding priorities |
| [Concept coverage, Spanish](PDF_COVERAGE_STATUS.md) | Coverage of the original conceptual document |
| [Local audit history, Spanish](AUDITORIA_Y_ESTADO.md) | Detailed historical runs; includes machine-specific paths |
| [Original brief](PROJECT_BRIEF.md) | Historical planning context, not the current feature list |
| [Initial requirements](REQUIREMENTS.md) | Original requirements and changes in product direction |

The conceptual PDF and extracted text are historical design material, not
evidence that every proposed method is implemented or validated. Follow Status
and the implementation plan for current behavior. Generated run artifacts and
local paths in the audit are not required to install the plugin.

## Repository layout

| Folder | Responsibility |
| --- | --- |
| qgis_plugin | Primary desktop UI, QGIS tasks and Processing adapters |
| geomorphx | API, method catalogue, recipes, streaming and validation |
| core_py/geomorphx_core | Numerical methods and raster I/O |
| core_rs | Optional Rust kernels |
| cli | Command-line interface |
| standalone_app | Secondary compatibility UI |
| examples/automation | Runnable Python/Processing examples and sample JSON |
| tests | Numerical and integration checks |
| notebooks | Reproducible synthetic validation notebook |
| benchmarks | Performance tooling and retained run artifacts |
| paper | Manuscript outline; publication remains pending |

English user guides are the default. Spanish guides are listed in the
[Spanish index](README.es.md). Method identifiers, UI labels and JSON keys remain
unchanged across languages. Documentation language does not change the QGIS UI.
