# Synthetic validation notebook

01_synthetic_validation.ipynb checks analytical slope and Riley TRI, MFD
conservation and an RRIM+ full-grid/block comparison. It exports traceable
reports and PNG/PDF figures. It has been executed on Windows, CPython 3.11.

From a source checkout with the notebook dependencies and a Python kernel:

    python scripts/execute_validation_notebook.py --out-dir benchmarks/out/scientific_validation

The notebooks optional dependency group includes nbclient, nbformat, ipykernel
and plotting/raster dependencies. Installing the full Python package through
Maturin also builds Rust; see the development guide for the source-only route.
On configured workstations, run through DEVRESOURCES_RUN.cmd.

Every execution retains a unique output directory. Generated artifacts are
excluded from normal source distribution. These are analytical/synthetic checks,
not field validation or an independent external-program comparison.

Future analyses include comparison to a classical RRIM reference, directional
sensitivity and RRIM+ ablation. They are work items, not existing notebooks.
See [development](../docs/DEVELOPMENT.md) and [status](../docs/STATUS.md).
