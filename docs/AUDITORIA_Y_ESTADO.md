# Auditoría y estado de GeoMorphX

## Estado vigente: recetas comunes y automatización, 0.5.1, 26/10/2026

geomorphx/recipes.py centraliza creación, carga, normalización, guardado y
ejecución de recetas. El formato nuevo es geomorphx-recipe 1.0. Se leen también
las recomendaciones schema_version 1.0 y el panel geomorphx-workbench versión 1.
Los supuestos de resolución, roles y justificaciones se conservan. La API previa
de recomendaciones continúa como adaptador; la CLI exporta el formato común.

El panel delega sus tareas al mismo ejecutor y ofrece acceso programático mediante
recipe y set_recipe. Processing incorpora run_recipe, por lo que el proveedor
registra ahora 43 herramientas. La API pública expone create_recipe, load_recipe,
normalize_recipe, save_recipe y execute_recipe. La CLI añade validate-recipe.

Antes del cálculo se valida la receta completa y la resolución real del DEM.
Los manifiestos conservan hashes y estados complete, cancelled o failed. Se
rechazan resultados existentes y una reserva exclusiva impide que dos trabajos
compartan una carpeta de salida. No se limpian corridas ni se reanudan trabajos.

Verificación final:

- 162 pruebas Python correctas; nueve omitidas por Rust ausente en el checkout.
- Comparación API/CLI sobre el mismo JSON y lectura de los tres formatos.
- Fallos de prevalidación sin resultados; conservación ante cancelación y error;
  protección de salidas existentes y prueba de trabajos concurrentes.
- Esquema JSON y ejemplo canónico validados; comprobaciones Python E/F correctas.
- ZIP con guía, esquema y ejemplos comprobado en QGIS 3.44.12 real, perfil
  aislado y Qt fuera de pantalla. API, Processing y panel consumieron la misma
  receta exportada. Proceso completo con salida 0, incluidas las 43 herramientas.

Paquete vigente:
[ZIP QGIS 0.5.1](../dist/qgis/geomorphx_rrim_suite_0.5.1_20261027T002621368586Z.zip).
SHA-256: 28F4C727079CBB857BDD695F13B710770DB0486AC575AE065523DEA10BE753DD.
Guía de usuarios: [automatización](AUTOMATIZACION.md).
Evidencias:
D:/DevResources/Sessions/GeoMorphX-48c27cf33a/20261026_192619_aaf1e29c23de432584f4ed998c203377/qgis_runtime.

No hubo commit, push ni publicación oficial en esta ampliación. Los límites
científicos, la prueba manual pendiente y el diagnóstico PNG del compositor
RRIM histórico descritos abajo continúan vigentes.

## Conversión de QGIS a interfaz principal, 0.5.0, 26/10/2026

Esta actualización sustituye los pendientes de integración QGIS de las
revisiones históricas conservadas más abajo. El complemento 0.5.0 experimental
ya tiene panel acoplable, selección de capas del proyecto, parámetros por método,
productos independientes, recetas JSON, tarea de fondo, registro y carga de
resultados. Su organización visual toma como referencia TerraWorkbench sin
copiar su núcleo de procesamiento.

Processing registra y ejecuta 42 herramientas: los 32 métodos individuales y
diez herramientas históricas de suite, bloques, RRIM clásico y benchmarks.
Se preservan el identificador del proveedor, los algoritmos antiguos y los
primeros seis índices del selector. La suite por carpetas ya transmite tamaño
de bloque, directorio temporal, umbral angular y salto interior al núcleo.

El I/O compartido usa GDAL nativo cuando Rasterio está ausente. No se instalaron
paquetes en QGIS. Rust es opcional y no se incluye como binario en el ZIP.
La hidrología existente queda como conjunto adicional; no es la orientación
principal del producto y conserva sus límites de memoria global.

Verificación sobre el ZIP extraído, fuera del checkout, con QGIS 3.44.12,
Windows y Python 3.12:

- Los 32 métodos ejecutados mediante Processing coinciden con el cálculo de
  arrays del núcleo en un DEM sintético de píxeles rectangulares, con CRS y NoData.
- Ejecutados cómputo de suite, lote con parámetros no predeterminados, los cuatro
  bloques, generador y compositor RRIM clásico, y ambos benchmarks.
- Panel construido con Qt real fuera de pantalla; tarea de fondo completada,
  dos productos cargados y leyenda geomorphon categorizada.
- Verificados manifiestos de cancelación previa y fallo, además de descarga del
  proveedor. La cancelación es entre productos: no interrumpe un kernel en curso.
- Suite Python del checkout: 145 pruebas correctas y nueve omitidas por ausencia
  de la extensión Rust en ese árbol. No se recompiló Rust en esta conversión.
- Prueba QGIS completa con salida de proceso 0; perfil temporal aislado,
  sin instalar ni activar el complemento en el perfil habitual del usuario.

El exportador histórico de RRIM RGB emite un diagnóstico del driver PNG sobre
acceso de actualización durante el renderizado de QGIS; la exportación GeoTIFF
completó y el archivo tiene bandas de color. Las dimensiones y la fidelidad
visual de ese flujo heredado necesitan una revisión específica; este ensayo
no constituye validación independiente de su composición.

Paquete comprobado:
[ZIP QGIS 0.5.0](../dist/qgis/geomorphx_rrim_suite_0.5.0_20261027T001047708157Z.zip).
SHA-256: A764D2BF18B0642F384A3698C6F68EA01C51B2E8B28FD81B38CAB08B502AEAE2.
Prueba reproducible: scripts/validate_qgis_runtime.py. Evidencias en la sesión
D:/DevResources/Sessions/GeoMorphX-48c27cf33a/20261026_191046_527b4238c2a34c8ba63fc800b203ede4/qgis_runtime.

Siguen pendientes sesiones manuales completas, otras plataformas/versiones de
QGIS y validación científica con DEM reales y referencias independientes.
La GUI independiente queda como compatibilidad secundaria. No se hizo commit,
push ni envío al repositorio oficial de plugins en esta conversión.

## Revisiones históricas

Fecha: 25 de octubre de 2026. Revisión del código, interfaces, pruebas,
instalación y correspondencia con el documento conceptual local.

## Resultado

La base era funcional, pero no estaba terminada. Había diferencias entre las
listas de métodos de cada interfaz, documentos desactualizados y fallos de
NoData, unidades físicas, bordes y trazabilidad del cálculo por bloques.

La organización conserva todas las rutas, datos, lanzadores e históricos. Se
centralizó el catálogo en geomorphx/methods.py, las estadísticas locales en
core_py/geomorphx_core/focal.py y la hidrología en un módulo independiente.
El índice docs/README.md describe las responsabilidades de cada carpeta.

## Algoritmos añadidos y métodos conectados

| Método | Implementación y estado |
| --- | --- |
| tri_riley | Raíz de la suma de diferencias cuadráticas con los ocho vecinos, ventana fija 3 × 3 |
| local_relief | Nombre explícito del rango máximo menos mínimo; conserva tri como alias heredado |
| fill_depressions | Relleno Priority-Flood con vecindad de ocho celdas |
| flow_accumulation_d8 | Ruta de máxima pendiente, resolución determinista de planos por padres del relleno, acumulación incluida la celda propia |
| twi_d8 | Logaritmo de área contribuyente específica dividida por tangente de pendiente |
| Hidrología en recetas | Nuevo objetivo hydrology, que ejecuta relleno, acumulación y TWI |
| Métodos previamente ocultos | Aperturas, SVF, sombreado multidireccional y RRIM estructural multiescala disponibles también en escritorio y suite QGIS |

Las interfaces principales usan los mismos 32 identificadores (estado actualizado al 26/10). Los primeros
seis índices de QGIS conservan su orden para no alterar modelos guardados.
El bloque QGIS antiguo de humedad conserva su nombre y su comportamiento de
proxy; el TWI nuevo se selecciona como twi_d8 en Suite Compute.

## Correcciones

- Lectura de máscaras y NoData como NaN; las salidas float32 declaran NaN.
- Estadísticas locales compartidas entre terreno y RRIM. Si una ventana contiene
  NoData, la estadística resulta desconocida. Las aperturas omiten muestras
  desconocidas del horizonte y devuelven NaN si una dirección no tiene muestras.
- Normalización RRIM segura para capas completamente vacías o constantes con huecos.
- Pendiente, orientación, curvaturas, sombreado, aperturas y proxy de humedad usan
  el tamaño físico del píxel leído del GeoTIFF.
- Orientación de ladera consistente con norte y filas hacia el sur; plano sin
  orientación devuelve NaN. Sombreado corregido respecto de azimut y altura solar.
- Rechazo de grillas rotadas/invertidas y CRS geográficos para derivadas físicas.
- Bloques locales con márgenes de uno, dos o radio de ventana según el método;
  los bordes exteriores coinciden con la ejecución sobre el DEM completo.
- RRIM usa ahora varias pasadas con normalización global y lectura por ventanas.
  La hidrología mantiene full_grid_fallback: ese modo todavía carga el DEM completo.
- Metadatos conservan escalas y parámetros efectivos. Rangos vacíos se escriben
  como null, con JSON estricto; versión de núcleo coherente con pyproject.toml.
- Lotes excluyen sus propias salidas anidadas y rechazan destinos que contienen
  las entradas. No se permite usar el mismo archivo como DEM y resultado.
- Recetas válidas cuando las escalas físicas se reducen a una única ventana.
- Generadores de escalas y azimuts no se consumen antes del cálculo.
- Kernels Rust validan entrada y ventanas, propagan huecos en el rango local y
  utilizan la interfaz Bound de PyO3 disponible en la versión instalada.
- El wheel incluye API, núcleo Python, CLI y escritorio. Extra dev para pruebas.
- Validación reproducible del paquete en scripts/validate_package.ps1 y workflow
  de CI para Python 3.10–3.12 en Windows y Linux. CI todavía no ejecutado en GitHub.

## Convenciones y límites científicos

La API de arrays usa cell_size=(dy, dx), por defecto (1, 1). Los archivos usan
las unidades de su CRS proyectado. Las elevaciones deben emplear las mismas
unidades; no se deducen ni convierten automáticamente las unidades verticales.
Las ventanas y escalas siguen expresándose en píxeles, no en metros.

RRIM sigue siendo la composición experimental interna basada en rango local y
pendiente normalizada. Conserva la convención histórica de píxel unitario en sus
componentes, registrada como legacy_unit_pixel. No se presenta como reproducción
validada del RRIM clásico ni del producto de Asia Air Survey.

D8 rellena depresiones antes de enrutar. Los bordes del ráster y de los huecos
NoData son límites de drenaje abiertos. Los empates entre pendientes positivas
usan el orden norte, noreste, este, sureste, sur, suroeste, oeste y noroeste.
Los planos sin descenso usan el árbol de Priority-Flood; la elección es
determinista, pero no representa canales observados sobre una llanura.

La acumulación se expresa en número de celdas, incluida la propia. TWI usa área
igual a acumulación por área de píxel y ancho de contorno aproximado igual a la
raíz del área de píxel. La tangente de pendiente tiene un mínimo de 1e-6.
No es equivalente al TWI de flujo múltiple de SAGA. Las salidas GeoTIFF son
float32; cuentas muy grandes pueden perder precisión entera por encima de 2^24.

Los benchmarks con tile_size miden arrays independientes sin margen ni
normalización compartida. Se identifican como microbenchmarks; no validan la
continuidad espacial del motor de GeoTIFF por bloques.

## Verificación

La suite inicial tenía 28 pruebas correctas y cuatro omitidas por Rust ausente.
Se ejecutó además la compilación release, instalación del wheel en un entorno
separado y pruebas fuera del checkout para evitar importar las fuentes por error.
Resultado de la primera revisión (antes de añadir geomorphons LOS):

- Fuentes con backend Python: 63 pruebas correctas y siete omitidas por extensión
  Rust ausente en el árbol de fuentes.
- Wheel release instalado fuera del checkout: 70 pruebas correctas, cero omitidas.
- CLI instalada: ayuda ejecutada correctamente.
- Sintaxis de QGIS, escritorio, CLI, núcleo y API: comprobada con compileall.
- Revisión de diferencias: sin errores de espacios mediante git diff --check.

Entorno comprobado: Windows, CPython 3.11. Wheel final conservado en
D:/DevResources/Sessions/GeoMorphX-48c27cf33a/20261025_214013_2c45dc23988d4f5797193010686be60e/wheels/geomorphx-0.1.0-cp311-cp311-win_amd64.whl.

Las pruebas cubren planos con solución conocida, orientación cardinal, altura
solar, TRI analítico, depresión cerrada, conservación del flujo, planos D8,
NoData, límites de lote y equivalencia de bloques, incluidos los bordes.
No se ejecutó QGIS ni se validaron interactivamente sus diálogos. Las pruebas posteriores de adaptadores sustituyen la API anfitriona y no son una ejecución de QGIS. Tampoco se
realizó una validación científica sobre DEM reales con referencia independiente.

## Pendientes reales

| Prioridad | Trabajo pendiente |
| --- | --- |
| Alta | Validación independiente de RRIM y sus extensiones; resolver su convención de escala y azimut antes de una versión científica estable |
| Alta | RRIM por varias pasadas implementado; pendientes optimización de I/O y conectividad hidrológica con memoria limitada |
| Alta | Ensayos dentro de QGIS; curvatura, TPI y humedad ya delegan en el núcleo compartido |
| Media | Geomorphons LOS básico implementado; pendientes corrección extendida, comparación externa y métricas geométricas adicionales |
| Media | MFD y cuencas D8 implementados; pendientes D-infinity, extracción vectorial de redes y cuencas por puntos externos |
| Media | Entradas opcionales del documento: geología, fallas, lineamientos y orientaciones estructurales externas |
| Media | Resolución real y hashes de recetas implementados; pendiente conversión vertical explícita y lectura de escalas/offsets ráster |
| Media | Notebook sintético ejecutable implementado; pendientes datos de referencia reales y comparación con ejecutables externos |
| Media | ZIP QGIS generado y GUI construida sin interacción; faltan instalador autónomo y validación de uso dentro de QGIS/GUI |
| Posterior | Manuscrito completo, versión publicada y validación del rendimiento regional/continental |

## Referencias metodológicas

- [GDAL: TRI de Riley](https://gdal.org/en/stable/programs/gdal_raster_tri.html).
- [Priority-Flood, Barnes y colaboradores](https://arxiv.org/abs/1511.04463).
- [RichDEM: métricas de flujo y D8](https://richdem.readthedocs.io/en/latest/flow_metrics.html).
- [SAGA: definición del TWI](https://saga-gis.sourceforge.io/saga_tool_doc/9.12.0/ta_hydrology_20.html).


## Ampliación: geomorphons y bloques compartidos

Segunda revisión del 25 de octubre de 2026:

- Nuevos métodos geomorphons y geomorphon_ternary; catálogo común de 27 métodos.
- Ocho horizontes de línea de visión, diez formas y 498 patrones canónicos.
- Umbral angular y salto interior expuestos en API, CLI, escritorio y QGIS.
- Nuevo objetivo de recetas landforms y algoritmo QGIS gmx_geomorphons_los.
- Curvatura, TPI y humedad de los bloques QGIS delegan en el núcleo compartido
  y producen los mismos metadatos que la API.
- El simplificado conserva sus nueve clases e Int16; picos y depresiones ya no
  se sobrescriben por reglas posteriores. NoData se registra como -32768.
- Funciones focales antiguas de compatibilidad delegan en las estadísticas comunes.
- Corregida la captura del mensaje de excepción en callbacks diferidos de la GUI.

La verificación final del wheel release instalado fuera del checkout pasa
107 pruebas, cero omitidas. Incluye los kernels Rust, las diez formas
sintéticas, los 6.561 patrones, invariancia, huecos, equivalencia de bloques y
cinco adaptadores Processing con I/O real y API QGIS sustituida.
La sintaxis de todos los paquetes y del plugin también pasa compileall.

Wheel de esta ampliación:
D:/DevResources/Sessions/GeoMorphX-48c27cf33a/20261025_222553_744a2cc8befe459a82b5ca81443e1e27/wheels/geomorphx-0.1.0-cp311-cp311-win_amd64.whl.

Consulte GEOMORPHONS.md para la regla anglev1, sus empates en perfiles planos,
la política de NoData y las opciones que aún no se implementan. La comparación
con un ejecutable externo y las pruebas interactivas de QGIS siguen pendientes.
Los cambios se conservan locales; no se ha creado commit ni publicado una versión.


## Ampliación del 26 de octubre de 2026

- Las siete variantes RRIM procesan por ventanas, con intermedios en disco y
  normalización global. Se prueban 21 combinaciones de variante y contenido,
  además de límites de lectura y rechazo de configuraciones inválidas.
- Cinco métodos adicionales: dirección, cuencas y longitud D8, acumulación MFD
  Freeman con exponente 1,1 y TWI MFD. Catálogo de 32 métodos.
- Recetas verificadas completas antes de producir resultados, con validación
  de resolución real en metros y hashes SHA-256 de entrada y salidas.
- Elección de tamaño de bloque y directorio de intermedios en CLI, GUI y QGIS.
- Acumuladores focales Rust en float64 para conservar relieve pequeño sobre
  elevación grande, manteniendo salidas float32.
- ZIP QGIS con núcleo Python incluido, manifiesto de archivos y prueba de
  importación fuera del checkout. Las dependencias de su intérprete no se instalan.
- Notebook sintético ejecutado: pendiente 45 grados y TRI analíticos correctos,
  conservación MFD y diferencia máxima RRIM+ completo frente a bloques igual
  a cero en ese ejemplo. Figuras exportadas a PNG/PDF; no es validación de campo.
- GUI con los 32 métodos construida y cerrada en Windows sin errores. No se
  ha simulado un flujo interactivo completo ni ejecutado QGIS real.

Paquete wheel compilado e instalado fuera del checkout: 154 pruebas correctas,
cero omitidas. Los resultados corresponden a Windows y CPython 3.11.
Wheel:
D:/DevResources/Sessions/GeoMorphX-48c27cf33a/20261026_100045_0d88b7074cbd466994d4c506e5e829dd/wheels/geomorphx-0.1.0-cp311-cp311-win_amd64.whl.

Consulte ESCALABILIDAD_Y_HIDROLOGIA.md para uso, memoria, espacio de disco y
límites de los nuevos algoritmos. No se ejecutó commit/push ni otro apagado.


### Entregables conservados de la ampliación del 26/10

- [ZIP QGIS con núcleo Python](../dist/qgis/geomorphx_rrim_suite_20261026T145924620390Z.zip).
- [Notebook fuente](../notebooks/01_synthetic_validation.ipynb).
- [Notebook ejecutado](../benchmarks/out/scientific_validation/20261026T150038647358Z/01_synthetic_validation.executed.ipynb).
- [Informe sintético](../benchmarks/out/scientific_validation/20261026T150038647358Z/science_20261026T150046387310Z/validation.md).
- [Figura PDF](../benchmarks/out/scientific_validation/20261026T150038647358Z/science_20261026T150046387310Z/synthetic_validation.pdf).

La última compilación del wheel y su instalación aislada repitieron las 154
pruebas sin omisiones. El ejecutor del notebook y sus dependencias opcionales
quedan declarados en el repositorio; sus cinco controles analíticos/sintéticos
pasaron. No se han eliminado corridas, intermedios ni entregas anteriores.
