# Plan de Implementación

## Fase 1 – Fundacional (completada)
1. RRIM baseline reproducible.
2. RRIM multiescala.
3. CLI `geomorphx compute`.
4. Metadatos JSON por ejecución.
5. Validación con tests sintéticos.

## Fase 2 – Extensión (avance fuerte)
1. RRIM anisotrópico: implementado.
2. RRIM anisotrópico multiescala: implementado.
3. Tensor estructural (coherencia + alineación): implementado (`rrim_structural`).
4. RRIM++ v1: implementado (baseline + anisotrópico + rugosidad + estructura).
5. Tensor estructural multiescala y multiorientación: implementado (`rrim_structural_multiscale`).
6. Comparación cuantitativa con baseline: implementada mediante CLI `geomorphx compare`.
7. Recomendación reproducible por objetivo y escala física: implementada mediante CLI `geomorphx recommend`.

## Fase 3 – Escalabilidad
1. Port de kernels críticos a Rust (`core_rs`).
2. Pipeline por tiles grandes.
3. Paralelismo multicore real.
4. Benchmarks reproducibles (base automática ya implementada en CLI `benchmark`).

## Fase 4 – Difusión
1. Manuscrito metodológico.
2. Release open-source.
3. Integración GIS (plugin ligero).

## Entregables actuales
- Núcleo Python beta (`core_py`).
- API unificada (`geomorphx/api.py`).
- CLI (`cli/geomorphx_cli.py`).
- Pruebas unitarias RRIM (`tests/test_rrim.py`).
