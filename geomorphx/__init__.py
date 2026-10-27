"""Unified GeoMorphX API."""

from geomorphx.api import compute_rrim, compute_rrim_array, compute_rrim_batch
from geomorphx.methods import METHODS
from geomorphx.benchmark import run_benchmark_batch, run_benchmark_suite
from geomorphx.recommendations import available_objectives, recommend
from geomorphx.recipes import create_recipe, execute_recipe, load_recipe, normalize_recipe, save_recipe

__all__ = [
    "compute_rrim",
    "METHODS",
    "compute_rrim_array",
    "compute_rrim_batch",
    "run_benchmark_suite",
    "run_benchmark_batch",
    "available_objectives",
    "execute_recipe",
    "create_recipe",
    "load_recipe",
    "normalize_recipe",
    "save_recipe",
    "recommend",
]
