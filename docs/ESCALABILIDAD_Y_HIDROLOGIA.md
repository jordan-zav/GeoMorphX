# Escalabilidad RRIM, hidrología y recetas

[English](SCALABILITY.md) | Español

Estado: 26 de octubre de 2026. Catálogo compartido de 32 métodos.

## RRIM con normalización global por ventanas

Las siete variantes RRIM ya disponen de procesamiento por varias pasadas.
Cada componente se escribe como ráster intermedio, su rango global se obtiene
recorriendo ventanas y la normalización se aplica con ese mismo rango a todo
el DEM. Los gradientes, estadísticas focales y tensores tienen márgenes propios.
Los bordes de bloques no se interpretan como bordes del DEM.

La memoria de arrays depende del tamaño de bloque, de los márgenes y de la
cantidad de entradas de cada operación; no depende del número total de celdas.
La ruta Rasterio solicita 32 MiB de caché durante las pasadas. El adaptador GDAL
nativo conserva la configuración global de caché de QGIS. Esto no constituye una
garantía de un máximo exacto de memoria del proceso: Python, Rust, archivos
abiertos, buffers y el tamaño elegido de ventana también consumen memoria.

Ejemplo de CLI:

geomorphx compute --dem dem.tif --out outputs/rrim.tif --method rrim_plus --window 15 --tile-size 512 --scratch-dir D:/GeoMorphX_Scratch

Los controles equivalentes están en la GUI y QGIS Suite Compute/Compute Batch.
Un tile_size de cero sigue ejecutando el cálculo completo en memoria.

Los intermedios ocupan espacio en disco por cada etapa, que puede ser varias
veces el tamaño del DEM. Se crean en un directorio único dentro de scratch-dir,
de la sesión DevResources o del directorio temporal del sistema. Se conservan
para revisión, sin limpieza automática. pipeline.json registra las etapas,
rangos de normalización, entradas, salidas, tamaño máximo de lectura y estado.
Los metadatos finales identifican windowed_global_normalization y enlazan ese
manifiesto. Un fallo conserva el manifiesto como failed y no se presenta como
ejecución completa.

La convención científica de RRIM no ha cambiado: píxel unitario en sus
componentes y composición experimental interna. Procesamiento equivalente por
ventanas no demuestra equivalencia con el producto RRIM clásico.

## Cinco métodos hidrológicos adicionales

| Método | Producto y convención |
| --- | --- |
| flow_direction_d8 | 0 salida; 1 N, 2 NE, 3 E, 4 SE, 5 S, 6 SW, 7 W, 8 NW |
| drainage_basins_d8 | Etiqueta de la salida D8 final; IDs desde 1 en orden de filas de las salidas |
| flow_length_d8 | Distancia acumulada aguas abajo hasta la salida, en unidades horizontales del CRS |
| flow_accumulation_mfd | Número fraccionario de celdas contribuyentes, incluida la propia |
| twi_mfd | Índice de humedad topográfica con área de flujo múltiple |

Todas las rutas usan Priority-Flood para rellenar depresiones. En D8 se conserva
la regla de pendiente máxima. En flujo múltiple se distribuye el aporte entre
los vecinos de menor elevación con pesos proporcionales a pendiente elevada
a 1,1, normalizados a suma uno. En planos rellenados sin descenso se utiliza
el árbol de Priority-Flood. Los bordes y huecos son salidas potenciales abiertas.
No se aplica corrección adicional por longitud de contorno.

TWI MFD usa el mismo ancho de contorno aproximado, raíz del área de píxel, y
el mínimo de tangente 1e-6 que la variante D8. No se afirma identidad numérica
con todas las opciones de SAGA o RichDEM. El objetivo de receta hydrology_mfd
genera relleno, acumulación MFD y TWI; drainage genera dirección, cuencas y longitud D8.

La hidrología todavía usa una red global en memoria. Solicitar bloques en
estos métodos mantiene un fallback explícito que carga el DEM completo.
Los rásteres finales son float32: las cuentas grandes pierden precisión entera
por encima de 2^24. Las cuencas rechazan más de 2^24 IDs para evitar colisiones
por redondeo. No se extraen todavía redes vectoriales, orden de Strahler ni
cuencas definidas por puntos de aforo externos.

## Recetas verificadas antes de generar salidas

Se comprueban todas las entradas de la receta, métodos, parámetros permitidos,
ventanas, escalas, pesos, ángulos y opciones geomorphon antes de iniciar.
No se permite reemplazar las rutas de entrada/salida mediante parámetros.

El DEM debe ser single-band, norte arriba y con CRS proyectado. Si la receta
declara pixel_size_m, los dos tamaños reales de píxel se convierten a metros
según el CRS y se comparan con la declaración. Una discrepancia detiene la
receta antes de crear sus productos. Las unidades verticales deben coincidir
con las horizontales; todavía no se deducen ni convierten automáticamente.

El manifiesto registra perfil, resolución, CRS y SHA-256 de entrada y de cada
salida. Se vuelve a comprobar el archivo de entrada al terminar. Si cambió
durante el cálculo, no se publica un manifiesto como corrida íntegra; las
salidas parciales quedan conservadas para revisión.

## Distribución y validación reproducible

scripts/build_qgis_plugin.py construye un ZIP instalable desde QGIS que incluye
el núcleo Python, licencia y manifiesto de hashes. No incluye autenticación,
configuraciones locales ni binarios Rust. El intérprete de QGIS debe disponer
de NumPy y GDAL, incluidos normalmente con QGIS; Rasterio es opcional. El ZIP
no modifica sus dependencias automáticamente.
Las pruebas de empaquetado importan el núcleo incluido fuera del checkout.
El ZIP 0.5.1 se ejecutó con QGIS 3.44.12 real en Windows, Python 3.12 y Qt fuera
de pantalla, sin Rasterio. Se verificaron las 43 herramientas y el panel con
tarea de fondo. Siguen pendientes el uso manual con DEM reales y otras
plataformas. Consulte AUDITORIA_Y_ESTADO.md para el alcance exacto.

notebooks/01_synthetic_validation.ipynb ejecuta casos de pendiente analítica,
TRI de Riley, conservación de flujo múltiple y equivalencia RRIM+ entre cálculo
completo y bloques. scripts/validate_science.py exporta informe JSON/Markdown y
figuras PNG/PDF. Es una validación analítica y sintética, no una validación de campo.

Las medias y desviaciones focales Rust acumulan en float64 y entregan float32,
para conservar relieve pequeño sobre elevaciones grandes y reducir diferencias
entre el backend Python y el nativo en presencia de ventanas con NoData.

## Referencias

- [RichDEM: métricas de flujo, Freeman y exponente](https://richdem.readthedocs.io/en/latest/flow_metrics.html).
- [SAGA: acumulación y convergencia de Freeman](https://saga-gis.sourceforge.io/saga_tool_doc/9.9.1/ta_hydrology_1.html).


Comandos reproducibles en este entorno:

- DEVRESOURCES_RUN.cmd python scripts/execute_validation_notebook.py --out-dir benchmarks/out/scientific_validation
- DEVRESOURCES_RUN.cmd python scripts/build_qgis_plugin.py --out-dir dist/qgis
- DEVRESOURCES_RUN.cmd powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_package.ps1

El extra notebooks de pyproject.toml declara las dependencias del ejecutor del
notebook. Cada ejecución conserva un directorio nuevo con la copia ejecutada,
resultados, figuras e intermedios. El ZIP se genera con un nombre único y tampoco
sobrescribe las entregas anteriores.
