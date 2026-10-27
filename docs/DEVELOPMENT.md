# Development and packaging

See [Status](STATUS.md) before treating experimental methods as validated.
The QGIS plugin and Python package have separate version numbers and build paths.

## Build the QGIS ZIP

From a complete source checkout with Python 3.10 or newer:

    python scripts/build_qgis_plugin.py --out-dir dist/qgis

The packager uses the standard library, includes the Python core, English/Spanish
instructions, automation guides, schema and examples, and records SHA-256 for its
source members. It excludes local environment settings, caches and Rust binaries.
Archives have versioned unique names and are ignored by Git. Do not distribute an
archive of the repository as if it were the installable plugin.

Installing the ZIP does not require Rust or a pip installation into QGIS. Follow
the user guide and test it with an isolated profile before wider distribution.

## Python development without Rust

Create and activate a virtual environment using the normal commands for your
platform. For a source checkout using the Rasterio backend:

    python -m pip install numpy rasterio pytest matplotlib
    python -m pytest -q
    python -m cli.geomorphx_cli --help

Run from the repository root. The CLI module supports the same arguments as the
installed geomorphx command. Tests that require the compiled extension are
skipped when it is absent. A passing Python fallback suite is not a Rust build.

## Build/install the optional Python package

To install the package and its command entry points, use Python 3.10+ and a Rust
toolchain compatible with the project's Maturin/PyO3 setup:

    python -m pip install ".[raster,dev]"

The maturin build backend compiles the Rust extension. Install a wheel built for
your own Python ABI and platform; a CPython 3.11 Windows wheel is not a QGIS
Python 3.12 dependency. The QGIS ZIP deliberately avoids this binary requirement.

To build a release wheel explicitly:

    python -m pip install maturin
    python -m maturin build --release --out dist/wheels

Validate an installed wheel outside the checkout so imports cannot accidentally
resolve to source. The Windows helper scripts/validate_package.ps1 performs
that workflow on the managed DevResources workstation. It requires the local
launcher and is not a portable prerequisite for plugin users.

## Checks

| Check | Command or entry point |
| --- | --- |
| Source suite | python -m pytest -q |
| Plugin archive/import | python -m pytest tests/test_plugin_bundle.py -q |
| Recipe parameters | python -m cli.geomorphx_cli validate-recipe --recipe examples/automation/terrain_recipe.json |
| Real QGIS runtime | scripts/validate_qgis_runtime.py with QGIS's own Python launcher |
| Synthetic science notebook | scripts/execute_validation_notebook.py --out-dir benchmarks/out/scientific_validation |

The real-host script requires a fresh DEVRESOURCES_SESSION directory. It builds
and extracts a ZIP into that session, uses an isolated QGIS profile and offscreen
Qt, and leaves artifacts and a report. It does not activate a plugin in the
normal user profile. On the configured Windows workstation, run it through:

    .\DEVRESOURCES_RUN.cmd "C:\Program Files\QGIS 3.44.12\bin\python-qgis-ltr.bat" scripts\validate_qgis_runtime.py

Use the installed QGIS launcher's actual path on other machines. On managed
workstations, use DEVRESOURCES_RUN.cmd for development commands to preserve
workspace locks, unique temporary directories and build-slot coordination.

## Maintenance rules

Keep numerical methods in the shared core. Preserve Processing IDs and the first
six historical suite indices for saved models. New recipe formats require an
explicit schema version and reader compatibility decisions. Verify links in
both language READMEs and keep method counts and tested-host claims consistent
with metadata, the provider and recorded evidence.

The sample notebook needs the notebooks optional dependencies and a Python
kernel. Its outputs and benchmark artifacts belong to unique run directories;
they are not field-validation data. Documentation changes do not require a new
scientific validation run, but updated plugin documentation must be included in
a freshly checked ZIP.
