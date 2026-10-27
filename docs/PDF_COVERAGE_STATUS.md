# Cobertura del documento conceptual

Fuente local: GeoMorphX.pdf y GeoMorphX.extracted.txt.
Estado revisado el 26 de octubre de 2026.

| Sección | Estado comprobado |
| --- | --- |
| Visión, motivación y principios | Arquitectura de núcleo científico y frontends separados; beta funcional |
| RRIM metodológico | Composición experimental interna y extensiones; equivalencia con RRIM clásico todavía sin validar |
| Núcleo Python | Implementado, con nuevas estadísticas compartidas e hidrología D8 |
| Motor Rust | Cuatro kernels implementados con Rayon; compilación release y wheel comprobados |
| Entrada DEM single-band | Implementada, incluidas máscaras, NoData y controles de grilla |
| Entradas geológicas y estructurales opcionales | Pendientes; el azimut configurable no sustituye estas entradas |
| Ráster y trazabilidad JSON | Implementados; intermedios para RRIM+ en ejecución completa |
| API y CLI | Implementadas con catálogo común y recetas |
| Aplicación independiente | CLI y GUI conservadas como compatibilidad secundaria; QGIS es la interfaz principal |
| Geomorphons | Diez formas LOS y patrones canónicos implementados; opciones extendidas y comparación externa pendientes |
| Plugin QGIS | Interfaz principal, panel y 43 herramientas; ZIP ejecutado en QGIS 3.44.12 real y Qt fuera de pantalla; uso manual y otras plataformas pendientes |
| Escalabilidad | Métodos locales y RRIM con ventanas y normalización global; hidrología aún en memoria global |
| Benchmarking | Implementado; microbenchmark por bloques distinguido del procesamiento espacial continuo |
| Manuscrito y publicación | Esquema inicial; cierre académico y publicación pendientes |

El documento original es conceptual. D8, TWI y TRI de Riley amplían el núcleo,
pero no sustituyen la validación metodológica ni completan todos los objetivos
futuros. Consulte AUDITORIA_Y_ESTADO.md y IMPLEMENTATION_PLAN.md.
