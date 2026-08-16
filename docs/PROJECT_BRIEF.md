# GeoMorphX – Brief Ejecutivo

## Fuente
Este brief se deriva de `docs/GeoMorphX.pdf` (documento interno).

## Propósito
Construir un framework científico-computacional para análisis geomorfométrico avanzado de DEM, con separación estricta entre cálculo científico y GUI.

## Problema que resuelve
Cerrar la brecha entre métodos geomorfométricos avanzados publicados en literatura y herramientas GIS operativas de uso cotidiano.

## Principios clave
- Ciencia desacoplada del SIG.
- CLI-first y API-first.
- Escalabilidad (tiles, paralelismo, datasets grandes).
- Reproducibilidad y trazabilidad completa.
- Extensibilidad metodológica.

## MVP (beta funcional)
- RRIM baseline.
- RRIM multiescala.
- CLI estable para cómputo batch.
- Outputs raster + metadatos de parámetros.

## Arquitectura objetivo
- Python como núcleo científico inicial.
- Rust como motor de kernels optimizados en fases posteriores.
- QGIS como frontend opcional para visualización.