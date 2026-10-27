# GeoMorphX para QGIS

[English](README.md) | Español

Complemento 0.5.1 experimental. QGIS es la interfaz principal de escritorio.
El ZIP incluye el núcleo Python y utiliza NumPy/GDAL de QGIS; Rasterio y Rust
son opcionales. No instala dependencias ni modifica el intérprete anfitrión.

## Instalar y abrir

Instala el ZIP mediante Complementos → Administrar e instalar complementos →
Instalar a partir de ZIP. Activa GeoMorphX y abre Ráster → GeoMorphX → GeoMorphX
Terrain Workbench. Reinicia QGIS al sustituir una versión que ya estuviera cargada.

Desde las fuentes, genera un ZIP con:

    python scripts/build_qgis_plugin.py --out-dir dist/qgis

Instala el paquete generado, no una compresión de todo el repositorio. Se declara
QGIS 3.28–3.x; se ha comprobado QGIS 3.44.12 en Windows, Python 3.12. El complemento
todavía no está publicado en el repositorio oficial.

## Panel

Selecciona un DEM local de una banda con CRS proyectado y las mismas unidades
horizontales y de elevación. Elige un método, ajusta parámetros y pulsa Add
product. Cada producto conserva los parámetros con los que se añadió; para
sustituirlo, quítalo y añádelo de nuevo. Todos parten del DEM original.

Elige la carpeta de salida y pulsa Run and add layers. Una tarea de fondo crea
una carpeta de corrida y carga los productos completados. Las clases geomorphon
reciben una leyenda categorizada. Run log muestra resultados y errores; Guide
explica el flujo. La cancelación se aplica entre productos.

Save recipe guarda JSON geomorphx-recipe 1.0, válido para panel, API, Processing
y CLI. Load recipe también acepta los dos formatos anteriores. Se conservan
los supuestos de resolución y el contexto importados. Revisa las ventanas en
píxeles si vas a utilizar otro DEM con distinta resolución.

## Processing y automatización

El proveedor conserva el ID geomorphx_rrim_suite. Sus 43 herramientas incluyen:

- 32 métodos individuales con terrain_ seguido del identificador del método;
- cómputo de suite y carpetas;
- benchmarks individuales y de carpetas;
- bloques de curvatura, TPI/humedad y dos modelos geomorphon;
- generación y composición RGB de RRIM clásico;
- run_recipe, mostrado como Run portable recipe en el grupo Automation.

Se mantienen los diez IDs originales y los seis primeros índices históricos
para los modelos existentes. Usa lotes o Model Designer para automatizar. Cada
ejecución de receta necesita una carpeta nueva. El manifiesto registra hashes
de entrada/salida y estados de finalización, cancelación o fallo.

El ZIP incluye AUTOMATION.md en inglés, AUTOMATIZACION.md en español,
recipe.schema.json y ejemplos ejecutables. En las fuentes, las guías están en
docs. Los parámetros de receta admiten una lista explícita de métodos y opciones;
no permiten sustituir las rutas de entrada/salida ni ejecutar código Python.

## Métodos, memoria y límites conocidos

Las variantes RRIM del núcleo son experimentales y distintas del generador y
compositor clásicos. El proxy de humedad heredado es diferente del TWI basado
en acumulación. La hidrología es adicional y todavía carga todo el DEM; el
tamaño de bloque no limita su memoria.

Los productos locales usan márgenes y RRIM por ventanas utiliza normalización
global con etapas en disco conservadas. El adaptador GDAL respeta la caché del
anfitrión. No se convierten automáticamente las unidades verticales.

El ZIP se ejecutó con Processing real y Qt fuera de pantalla en un perfil
aislado. Se comprobaron las 43 herramientas, comparaciones sintéticas, recetas,
tareas, leyendas y descarga. Quedan pendientes uso manual, otras plataformas y
validación científica independiente. El exportador RGB heredado emite un
diagnóstico PNG sobre acceso de actualización aunque complete el GeoTIFF;
ese flujo de renderizado necesita una revisión específica.
