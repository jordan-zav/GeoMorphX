"""Quantitative comparison metrics for raster datasets."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def calculate_entropy(arr: np.ndarray) -> float:
    """Calculate Shannon entropy of a 2D float array (normalized to [0, 1])."""
    valid = arr[~np.isnan(arr)]
    if valid.size == 0:
        return 0.0
    vmin, vmax = float(np.min(valid)), float(np.max(valid))
    if vmax == vmin:
        return 0.0

    # Normalize to [0, 255] and cast to uint8
    discretized = ((valid - vmin) / (vmax - vmin) * 255.0).astype(np.uint8)
    counts = np.bincount(discretized)
    probs = counts / float(valid.size)
    probs = probs[probs > 0]
    return -float(np.sum(probs * np.log2(probs)))


def local_contrast(arr: np.ndarray) -> float:
    """Calculate mean local gradient magnitude as a proxy for contrast/detail."""
    valid = arr[~np.isnan(arr)]
    if valid.size == 0:
        return 0.0

    # Calculate standard deviation of gradient magnitude
    gy, gx = np.gradient(arr.astype(np.float32))
    grad_mag = np.sqrt(gx * gx + gy * gy)
    return float(np.nanmean(grad_mag))


def compare_rasters(
    raster1: np.ndarray,
    raster2: np.ndarray,
    name1: str = "Raster 1",
    name2: str = "Raster 2",
) -> dict[str, Any]:
    """Compare two raster arrays and return comparison metrics."""
    if raster1.shape != raster2.shape:
        raise ValueError(f"Shape mismatch: {raster1.shape} vs {raster2.shape}")

    mask = np.isnan(raster1) | np.isnan(raster2)
    r1_valid = raster1[~mask]
    r2_valid = raster2[~mask]

    if r1_valid.size == 0:
        raise ValueError("No valid overlapping pixels to compare")

    if r1_valid.std() == 0 or r2_valid.std() == 0:
        pearson = 0.0
    else:
        pearson = float(np.corrcoef(r1_valid, r2_valid)[0, 1])

    mad = float(np.mean(np.abs(r1_valid - r2_valid)))
    rmsd = float(np.sqrt(np.mean((r1_valid - r2_valid) ** 2)))

    entropy1 = calculate_entropy(raster1)
    entropy2 = calculate_entropy(raster2)
    entropy_gain = entropy2 - entropy1

    contrast1 = local_contrast(raster1)
    contrast2 = local_contrast(raster2)
    contrast_ratio = contrast2 / (contrast1 + 1e-9)

    return {
        "num_pixels": int(r1_valid.size),
        "pearson_correlation": pearson,
        "mean_absolute_difference": mad,
        "root_mean_square_difference": rmsd,
        "entropy": {
            name1: entropy1,
            name2: entropy2,
            "gain": entropy_gain,
        },
        "contrast": {
            name1: contrast1,
            name2: contrast2,
            "ratio": contrast_ratio,
        },
    }


def generate_comparison_report(
    metrics: dict[str, Any],
    name1: str = "Raster 1",
    name2: str = "Raster 2",
    path1: str | None = None,
    path2: str | None = None,
) -> str:
    """Generate a Markdown report from comparison metrics."""
    report = []
    report.append("# Reporte de Comparación Geomorfométrica Cuantitativa")
    report.append("")
    report.append("Comparación entre el raster base e incremental para evaluar diferencias y ganancias de detalle.")
    report.append("")
    report.append("## Datos de Entrada")
    report.append(f"- **{name1}**: {path1 or 'N/A'}")
    report.append(f"- **{name2}**: {path2 or 'N/A'}")
    report.append(f"- **Píxeles superpuestos válidos**: {metrics['num_pixels']:,}")
    report.append("")
    report.append("## Métricas de Comparación")
    report.append("| Métrica | Valor | Interpretación |")
    report.append("| --- | --- | --- |")
    report.append(f"| **Correlación de Pearson** | {metrics['pearson_correlation']:.4f} | 1.0 = idénticos, 0.0 = linealmente independientes |")
    report.append(f"| **Diferencia Absoluta Media (MAD)** | {metrics['mean_absolute_difference']:.4f} | Magnitud promedio de diferencia por píxel |")
    report.append(f"| **Diferencia Cuadrática Media (RMSD)** | {metrics['root_mean_square_difference']:.4f} | Raíz del error cuadrático medio global |")
    report.append("")
    report.append("## Análisis de Detalle e Información")
    report.append("| Raster | Entropía de Shannon (bits) | Contraste Local (Gradiente medio) |")
    report.append("| --- | --- | --- |")
    report.append(f"| **{name1}** | {metrics['entropy'][name1]:.4f} | {metrics['contrast'][name1]:.4f} |")
    report.append(f"| **{name2}** | {metrics['entropy'][name2]:.4f} | {metrics['contrast'][name2]:.4f} |")
    report.append(f"| **Diferencia / Ratio** | Ganancia: {metrics['entropy']['gain']:.4f} bits | Ratio de contraste: {metrics['contrast']['ratio']:.4f}x |")
    report.append("")
    report.append("### Notas de Interpretación:")
    report.append(f"- **Entropía de Shannon**: Mide el grado de detalle e información visual de la imagen. Valores más altos indican una mayor cantidad de rasgos/micro-relieves capturados.")
    report.append(f"- **Contraste Local (Gradiente)**: Indica qué tan pronunciadas son las transiciones locales (bordes y pendientes). Un ratio > 1.0 significa que `{name2}` resalta los detalles del terreno con mayor fuerza que `{name1}`.")

    return "\n".join(report)
