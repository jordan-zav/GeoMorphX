"""Run a panel/CLI/API recipe with the public Python API.

Example: python run_recipe.py --recipe terrain_recipe.json --dem dem.tif --out-dir new_run
Requires the geomorphx package or an activated GeoMorphX plugin in QGIS Python.
"""
import argparse
import json

from geomorphx import execute_recipe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--dem", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    outputs, manifest = execute_recipe(args.recipe, dem_path=args.dem, out_dir=args.out_dir)
    report = json.loads(manifest.read_text(encoding="utf-8"))
    print(f"{report['status']}: {len(outputs)} products; manifest: {manifest}")
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
