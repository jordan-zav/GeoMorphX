<div align="center">

# GeoMorphX

**Geomorfometría multiescala y visualización inteligente del relieve**

Un mismo núcleo científico para procesar modelos digitales de elevación desde
Python, la línea de comandos, una aplicación independiente o QGIS Processing.

[![Status: beta](https://img.shields.io/badge/status-beta-f59e0b)](#estado-del-proyecto)
[![Version 0.1.0](https://img.shields.io/badge/core-0.1.0-2563eb)](pyproject.toml)
[![QGIS suite 0.4.0](https://img.shields.io/badge/QGIS%20suite-0.4.0-589632?logo=qgis&logoColor=white)](qgis_plugin/metadata.txt)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-0f766e)](LICENSE)

</div>

> [!IMPORTANT]
> GeoMorphX está en fase beta. Las capas derivadas dependen de la resolución,
> unidades, proyección, calidad y escala del DEM. Una receta recomendada ayuda a
> elegir parámetros, pero no sustituye la validación geomorfológica.

## Flujo general

```text
DEM proyectado y documentado
            │
            ▼
 Validación de resolución, NoData y unidades
            │
            ▼
 RRIM / apertura / sombreado / curvatura / TPI / TRI
            │
            ▼
 Composición multiescala, anisotrópica o estructural
            │
            ▼
 GeoTIFF + JSON trazable + capas intermedias opcionales
            │
            ├──► CLI / lotes / benchmarks
            ├──► aplicación independiente
            └──► QGIS Processing
```

## Capacidades

| Familia | Métodos incluidos |
| --- | --- |
| RRIM | Baseline, multiescala, anisotrópico, anisotrópico multiescala, estructural y RRIM+ |
| Iluminación | Hillshade clásico y multidireccional |
| Apertura | Apertura positiva, negativa y sky-view factor |
| Derivadas | Pendiente, aspecto, curvatura de perfil, plana y media |
| Contexto local | TPI, TRI y proxy de humedad topográfica |
| Automatización | Cómputo individual/por lotes, recetas JSON y benchmarks reproducibles |
| Integración | API de Python, CLI, GUI independiente y proveedor de QGIS Processing |

## Variantes RRIM

| Método | Objetivo |
| --- | --- |
| `rrim_baseline` | Composición RRIM convencional para una ventana |
| `rrim_multiscale` | Integrar respuesta de varias ventanas físicas |
| `rrim_anisotropic` | Resaltar respuesta respecto a un azimut controlado |
| `rrim_anisotropic_multiscale` | Combinar orientación y escalas múltiples |
| `rrim_structural` | Incorporar coherencia del tensor estructural |
| `rrim_structural_multiscale` | Evaluar estructura en varias escalas y orientaciones |
| `rrim_plus` | Combinar relieve, anisotropía, rugosidad y estructura |

## Entradas y productos

### Entrada principal

- DEM ráster, preferentemente GeoTIFF;
- CRS proyectado y unidades horizontales/verticales conocidas;
- píxel y extensión apropiados para el rasgo buscado; y
- NoData correctamente declarado.

### Productos

- GeoTIFF georreferenciados;
- metadatos JSON con método y parámetros;
- componentes intermedios opcionales para auditoría;
- CSV, JSON, Markdown y figura de rendimiento para benchmarks; y
- resúmenes por lote cuando se procesan varios DEM.

## Instalación

La instalación editable usa Maturin y necesita una cadena de Rust disponible.
Para lectura/escritura de ráster instala también el extra `raster`:

```powershell
git clone https://github.com/jordan-zav/GeoMorphX.git
cd GeoMorphX
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[raster,scientific]"
```

## Uso rápido

```powershell
geomorphx compute --dem dem.tif --out outputs/rrim.tif --method rrim_baseline --window 9
geomorphx compute --dem dem.tif --out outputs/multiscale.tif --method rrim_multiscale --scales 5,15,45
geomorphx compute --dem dem.tif --out outputs/structural.tif --method rrim_structural_multiscale --scales 5,15,45 --azimuth 0,45,90,135
geomorphx compute-batch --dem-dir data/dems --out-dir outputs/batch --method rrim_plus --recursive --save-debug
```

### Recetas por objetivo

```powershell
geomorphx recommend --objective microtopography --pixel-size-m 0.5 --feature-min-m 2 --feature-max-m 10 --out recipe.json
geomorphx run-recipe --recipe recipe.json --dem dem.tif --out-dir outputs/microtopography
```

La receta registra el objetivo, la escala espacial y los parámetros propuestos
para que la decisión pueda revisarse y repetirse.

### Benchmarks

```powershell
geomorphx benchmark --out-dir benchmarks/out --size 512 --repeats 3 --scales 5,15,45 --window 9 --tile-size 256
geomorphx benchmark-batch --dem-dir data/dems --out-dir benchmarks/batch --recursive --repeats 3
```

Los benchmarks generan resultados CSV/JSON, informe Markdown y gráfico de
tiempos cuando Matplotlib está disponible.

## Interfaces

| Interfaz | Uso |
| --- | --- |
| `geomorphx` | CLI principal para cómputo, recetas y benchmarks |
| `geomorphx-gui` | Aplicación de escritorio independiente |
| `run_standalone_gui.bat` | Inicio rápido de la GUI en Windows |
| `qgis_plugin` | Algoritmos individuales y por lotes dentro de QGIS |

El complemento QGIS conserva el generador/compositor RRIM clásico y añade
bloques GeoMorphX de suite, geomorphons simplificados, curvatura, TPI y humedad.

## Desarrollo y verificación

```powershell
python -m pytest -q
```

La suite cubre API, métodos de terreno, RRIM, teselado, recomendaciones,
benchmarks, aplicación independiente y kernels Rust. Los resultados científicos
deben compararse además con DEM sintéticos y casos de referencia conocidos.

## Documentación y trazabilidad

- [Documento maestro](docs/GeoMorphX.pdf)
- [Cobertura del documento](docs/PDF_COVERAGE_STATUS.md)
- [Requisitos](docs/REQUIREMENTS.md)
- [Plan de implementación](docs/IMPLEMENTATION_PLAN.md)
- [Benchmarks](benchmarks/README.md)
- [Aplicación independiente](standalone_app/README.md)
- [Complemento QGIS](qgis_plugin/README.md)

## Mapa del repositorio

| Ruta | Contenido |
| --- | --- |
| `core_py` | Núcleo científico de referencia en Python |
| `core_rs` | Kernels optimizados en Rust |
| `geomorphx` | API unificada, benchmarks, comparación y recomendaciones |
| `cli` | Interfaz de línea de comandos |
| `standalone_app` | Aplicación fuera de QGIS |
| `qgis_plugin` | Proveedor y algoritmos QGIS Processing |
| `tests` | Pruebas numéricas, funcionales y de integración |
| `docs`, `paper` | Especificación, cobertura y material científico |

## Estado del proyecto

El núcleo está en versión 0.1.0 beta y la suite QGIS en 0.4.0. La arquitectura
multisuperficie funciona, pero API, parámetros y formatos de receta todavía
pueden cambiar. No se debe presentar una salida como interpretación geológica
validada únicamente porque el procesamiento terminó correctamente.

## Licencia y contacto

GeoMorphX se distribuye bajo la [GNU General Public License v3.0](LICENSE).

Jordan Zavaleta — GisGeo Dev<br>
[jordanzav@gisgeo.dev](mailto:jordanzav@gisgeo.dev) · [gisgeo.dev](https://gisgeo.dev)
