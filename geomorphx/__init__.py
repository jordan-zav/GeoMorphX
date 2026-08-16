"""Unified GeoMorphX API."""

from geomorphx.api import compute_rrim, compute_rrim_array, compute_rrim_batch
from geomorphx.benchmark import run_benchmark_batch, run_benchmark_suite
from geomorphx.recommendations import available_objectives, execute_recipe, recommend

__all__ = [
    "compute_rrim",
    "compute_rrim_array",
    "compute_rrim_batch",
    "run_benchmark_suite",
    "run_benchmark_batch",
    "available_objectives",
    "execute_recipe",
    "recommend",
]
