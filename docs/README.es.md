# Documentación de GeoMorphX

[English](README.md) | Español

Empieza por el [README en español](../README.es.md). QGIS es la interfaz principal
de escritorio; la CLI y el núcleo compartido permiten automatización. La versión
0.5.1 es experimental, con 32 métodos y 43 herramientas de Processing.

## Guías para usuarios

| Documento | Propósito |
| --- | --- |
| [Guía del complemento](../qgis_plugin/README.es.md) | Instalación, panel, Processing y límites; también incluida en el ZIP |
| [Automatización](AUTOMATIZACION.md) | Recetas, API, CLI, Processing y estados de ejecución |
| [Esquema de recetas](recipe.schema.json) | JSON Schema de geomorphx-recipe 1.0 |
| [Geomorphons](GEOMORPHONS.es.md) | Parámetros, clases, bordes, NoData y límites |
| [Escalabilidad](ESCALABILIDAD_Y_HIDROLOGIA.md) | Bloques, disco temporal, caché e hidrología adicional |
| [Guía de uso, en inglés](USER_GUIDE.md) | Preparación del DEM, resultados y solución de problemas |
| [Estado, en inglés](STATUS.md) | Qué se ha comprobado, problemas conocidos y pendientes |

## Desarrollo e históricos

| Documento | Propósito |
| --- | --- |
| [Desarrollo, en inglés](DEVELOPMENT.md) | Entorno, empaquetado y verificaciones |
| [Plan de implementación](IMPLEMENTATION_PLAN.md) | Trabajo completado y prioridades pendientes |
| [Cobertura conceptual](PDF_COVERAGE_STATUS.md) | Correspondencia con el diseño original |
| [Auditoría local](AUDITORIA_Y_ESTADO.md) | Histórico detallado; incluye rutas de esta estación |
| [Brief original](PROJECT_BRIEF.md) | Contexto histórico de planificación |
| [Requisitos iniciales](REQUIREMENTS.md) | Alcance original y evolución del producto |

El PDF conceptual y su texto extraído son material histórico, no evidencia de
que todas las propuestas estén implementadas o validadas. El estado y el plan
describen el comportamiento actual. No necesitas las rutas de auditoría ni las
corridas locales para instalar el complemento.

## Organización

| Carpeta | Responsabilidad |
| --- | --- |
| qgis_plugin | Interfaz principal, tareas y adaptadores Processing |
| geomorphx | API, catálogo, recetas, streaming y validación |
| core_py/geomorphx_core | Métodos numéricos e I/O ráster |
| core_rs | Kernels Rust opcionales |
| cli | Interfaz de comandos |
| standalone_app | Interfaz secundaria de compatibilidad |
| examples/automation | Ejemplos Python/Processing y JSON |
| tests | Verificaciones numéricas y de integración |
| notebooks | Notebook sintético reproducible |
| benchmarks | Herramientas e históricos de rendimiento |
| paper | Esquema de manuscrito; publicación pendiente |

Las guías de usuario principales están en inglés. Los identificadores, etiquetas
de interfaz y claves JSON se conservan en ambos idiomas. Esta documentación en
español no implica una traducción adicional de la interfaz de QGIS.
