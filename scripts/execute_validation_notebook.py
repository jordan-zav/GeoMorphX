"""Execute the committed synthetic notebook and retain all results in a unique run."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    import nbformat
    from nbclient import NotebookClient
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    root = Path(__file__).resolve().parents[1]
    run = args.out_dir.resolve() / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run.mkdir(parents=True)
    os.environ["GEOMORPHX_VALIDATION_DIR"] = str(run)
    notebook = nbformat.read(root / "notebooks" / "01_synthetic_validation.ipynb", as_version=4)
    NotebookClient(notebook, timeout=180, kernel_name="python3",
                   resources={"metadata": {"path": str(root)}}).execute()
    executed = run / "01_synthetic_validation.executed.ipynb"
    nbformat.write(notebook, executed)
    print(executed)
    for cell in notebook.cells:
        for item in cell.get("outputs", []):
            if item.get("output_type") == "stream":
                print(item.get("text", "").strip())
            elif item.get("output_type") == "execute_result":
                print(item.get("data", {}).get("text/plain", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
