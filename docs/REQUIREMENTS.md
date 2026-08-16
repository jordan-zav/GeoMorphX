# Requisitos Iniciales

## Funcionales
- Ingesta de DEM raster single-band.
- Cálculo de `rrim_baseline`.
- Cálculo de `rrim_multiscale` con escalas configurables.
- Exportación GeoTIFF.
- Metadatos de ejecución en JSON.
- CLI para ejecución reproducible.

## No funcionales
- Reproducibilidad: parámetros explícitos por ejecución.
- Trazabilidad: outputs con sidecar metadata.
- Escalabilidad progresiva: diseño preparado para Rust.
- Modularidad: separación core/API/CLI/frontend.

## Restricciones
- No depende de QGIS para calcular.
- QGIS solo frontend opcional.
- Implementación actual es beta científica interna.