"""Call from a QGIS Python script with GeoMorphX enabled.

Example: run_recipe('dem.tif', 'terrain_recipe.json', 'new_output_folder')
The same algorithm is available in batch processing and Model Designer.
"""
import processing


def run_recipe(dem, recipe, output_directory):
    return processing.run("geomorphx_rrim_suite:run_recipe", {
        "INPUT_DEM": str(dem), "RECIPE": str(recipe), "OUT_DIR": str(output_directory),
    })
