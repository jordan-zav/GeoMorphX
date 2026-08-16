# GeoMorphX Standalone Program

Programa standalone (fuera de QGIS) para correr la suite de GeoMorphX.

## GUI directa

- Doble click en `run_standalone_gui.bat`
- o terminal: `geomorphx-gui`

## Métodos (GUI Compute)

- RRIM: `rrim_baseline`, `rrim_multiscale`, `rrim_anisotropic`, `rrim_anisotropic_multiscale`, `rrim_structural`, `rrim_plus`
- Geomorfometría general: `slope`, `aspect`, `hillshade`, `curvature_profile`, `curvature_plan`, `curvature_mean`, `tpi`, `tri`, `wetness_proxy`

## Comandos

- `compute-batch`
- `benchmark-batch`

## Ejemplos

```bash
geomorphx-standalone compute-batch --dem-dir data/dems --out-dir outputs --recursive --method rrim_plus --save-debug
geomorphx-standalone benchmark-batch --dem-dir data/dems --out-dir benchmarks/batch --recursive
```
