# GeoMorphX

Framework híbrido para geomorfometría avanzada y visualización inteligente del relieve.

Este repositorio está alineado al documento maestro:
- `docs/GeoMorphX.pdf`

## Estructura

- `core_py/`: núcleo científico en Python (fase activa).
- `core_rs/`: kernels optimizados en Rust (fase futura).
- `geomorphx/`: API unificada.
- `cli/`: interfaz de línea de comandos.
- `qgis_plugin/`: plugin QGIS (frontend GIS).
- `standalone_app/`: programa standalone (fuera de QGIS).
- `notebooks/`: validación y exploración.
- `benchmarks/`: pruebas de rendimiento.
- `paper/`: manuscritos y figuras.

## Productos

- `qgis_plugin`: integración en QGIS Processing.
- `standalone_app`: ejecutable `geomorphx-standalone` para uso directo desde terminal/script.

## Estado actual

- Fase 1 completa y Fase 2 expandida:
  - `rrim_baseline`
  - `rrim_multiscale`
  - `rrim_anisotropic`
  - `rrim_anisotropic_multiscale`
  - `rrim_structural` (tensor estructural)
  - `rrim_structural_multiscale` (tensor estructural multiescala y multiorientación)
  - `rrim_plus` (baseline + anisotropía + rugosidad + estructura)
  - `multidirectional_hillshade`, `positive_openness`, `negative_openness` y `sky_view_factor`
  - CLI `geomorphx compute` y `geomorphx compute-batch`
  - salida GeoTIFF + metadatos JSON trazables
  - intermedios de validación para RRIM++ (`--debug-dir` / `--save-debug`)

## Uso rápido

```bash
python -m pip install -e .[raster]
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_baseline.tif --method rrim_baseline --window 9
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_ms.tif --method rrim_multiscale --scales 5,15,45
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_aniso.tif --method rrim_anisotropic --window 9 --azimuth 45 --directional-weight 0.6
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_aniso_ms.tif --method rrim_anisotropic_multiscale --scales 5,15,45 --azimuth 45 --directional-weight 0.6
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_structural.tif --method rrim_structural --window 9 --azimuth 45
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_structural_ms.tif --method rrim_structural_multiscale --scales 5,15,45 --azimuth 0,45,90,135
geomorphx compute --dem path/to/dem.tif --out outputs/rrim_plus.tif --method rrim_plus --window 9 --azimuth 35 --anisotropy-weight 0.30 --roughness-weight 0.25 --structural-weight 0.20
geomorphx compute --dem path/to/dem.tif --out outputs/openness.tif --method positive_openness --window 31
geomorphx compute-batch --dem-dir data/dems --out-dir outputs/batch --method rrim_plus --recursive --save-debug
geomorphx benchmark --out-dir benchmarks/out --size 512 --repeats 3 --scales 5,15,45 --window 9 --azimuth 45 --tile-size 256
geomorphx benchmark-batch --dem-dir data/dems --out-dir benchmarks/batch_out --pattern *.tif --recursive --repeats 3 --scales 5,15,45 --window 9 --azimuth 45 --tile-size 256
```

El comando `benchmark` produce:
- `benchmark_results.csv`
- `benchmark_results.json`
- `benchmark_report.md`
- `benchmark_runtime.png` (si `matplotlib` está disponible)

El comando `benchmark-batch` produce:
- benchmark individual por DEM en subcarpetas de salida
- `batch_summary.csv`
- `batch_summary.json`
- `batch_summary.md`

## Recetas guiadas por objetivo

`geomorphx recommend` convierte un objetivo de interpretación y el tamaño físico
del rasgo buscado en una receta JSON trazable. No sustituye la validación
geomorfológica: propone capas complementarias y ventanas calibradas a la
resolución del DEM.

```bash
geomorphx recommend --objective microtopography --pixel-size-m 0.5 --feature-min-m 2 --feature-max-m 10 --out recipe.json
geomorphx run-recipe --recipe recipe.json --dem path/to/dem.tif --out-dir outputs/microtopography
```

## Cobertura del PDF

Revisa el estado exacto sección por sección en:
- `docs/PDF_COVERAGE_STATUS.md`
