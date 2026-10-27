# Status and known issues

Plugin 0.5.1 is experimental. Core package version: 0.1.0.
Reviewed on 26 October 2026. [Español: auditoría detallada](AUDITORIA_Y_ESTADO.md).

## Implemented and checked

| Area | Current evidence |
| --- | --- |
| Shared catalogue | 32 methods; 43 QGIS Processing algorithms |
| QGIS interface | Dock, project-layer selection, product recipes, background task and layer loading |
| Portable recipes | Shared panel/API/CLI/Processing executor; readers for two older formats |
| Traceability | Input/output hashes, resolution preflight, complete/cancelled/failed manifests |
| Conservation | Recipe collision checks and an exclusive retained directory reservation |
| Raster I/O | Rasterio backend and native GDAL fallback; QGIS tested without Rasterio |
| Source suite | 162 passed, 9 Rust tests skipped because that checkout lacked the extension |
| Host integration | QGIS 3.44.12, Windows, Python 3.12; isolated profile and offscreen Qt |

The host integration check executed all 43 Processing tools. The 32 named
methods were compared with the shared array core on synthetic data with NoData
and rectangular pixels. Checks also covered block tools, classic RRIM/RGB,
benchmarks, portable recipes, panel background tasks, styles and provider unload.

These checks establish numerical consistency within the implementation and
integration with that host. They do not establish field accuracy or independent
agreement with another geomorphometry application. Earlier compiled-wheel/Rust
checks are recorded separately in the historical audit and are not a fresh
Rust build of this documentation revision.

## Known limitations

- Experimental RRIM variants retain a legacy unit-pixel convention. Their
  equivalence to classical RRIM or the published commercial product is unverified.
- The classic RGB renderer emits a PNG-driver update-access diagnostic even when
  GeoTIFF export completes. The integration check confirms a colour output exists;
  a dedicated review of dimensions, rendering fidelity and that diagnostic remains.
- Geomorphons implements the basic documented comparison. Extended correction,
  alternate comparisons and independent executable comparisons are pending.
- Hydrology uses full-grid memory; block size does not bound its memory use.
- No vertical-unit conversion, general rotated-grid support or automatic vertical
  datum inference is implemented.
- Cancellation is between products. Intermediate RRIM stages and recipe directory
  reservations remain on disk; there is no automatic cleanup or resume.
- QGIS 3.28–3.x is the declared range, but only the 3.44.12 Windows installation
  above has been exercised in the real-host check. QGIS 4 is not declared supported.

## Remaining work

Manual sessions with real DEMs, independent method comparisons, explicit RRIM
scale review, other QGIS versions/platforms and regional memory/I/O benchmarks
remain priorities. CI is configured for Python/Rust on Windows and Linux; the
existence of a workflow is not evidence that this local development passed remote CI.

No official QGIS plugin submission or new public release is represented by
these local package checks. QGIS is the primary desktop product; the standalone
GUI remains a compatibility interface. The manuscript directory is an outline,
not a published scientific validation.
