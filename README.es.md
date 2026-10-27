# GeoMorphX

**Análisis del terreno y visualización multiescala del relieve en QGIS.**

[English](README.md) | Español

GeoMorphX es un complemento experimental de QGIS para explorar modelos digitales
de elevación (DEM). Selecciona una capa del proyecto, prepara productos del
terreno, guarda una receta y añade los resultados al mapa. Un mismo núcleo Python
alimenta el panel, Processing, la API y la automatización por terminal.

**Complemento 0.5.1 · Núcleo 0.1.0 · GPL-3.0-or-later**

![Panel de GeoMorphX con un DEM sintético](docs/images/qgis_workbench_0.5.0.png)

## Instalación

Instala el ZIP de GeoMorphX mediante **Complementos → Administrar e instalar
complementos → Instalar a partir de ZIP** en QGIS. Actívalo y abre **Ráster →
GeoMorphX → GeoMorphX Terrain Workbench** o su botón de barra de herramientas.

Si tienes las fuentes en lugar de un ZIP, genera uno desde la raíz del
repositorio con Python 3.10 o posterior:

    python scripts/build_qgis_plugin.py --out-dir dist/qgis

Instala el ZIP generado, no una compresión de todo el repositorio. El paquete
incluye el núcleo Python, guías en ambos idiomas, esquema y ejemplos de recetas.
El empaquetador usa la biblioteca estándar de Python y no compila Rust.
Los ZIP generados son archivos locales excluidos de Git.

El complemento utiliza NumPy y GDAL de QGIS. Rasterio es opcional: el adaptador
GDAL nativo realiza el I/O cuando falta Rasterio. No instala dependencias ni
cambia el intérprete de QGIS. Reinicia QGIS al sustituir una versión de GeoMorphX
que ya estuviera cargada.

El rango declarado es **QGIS 3.28–3.x**. La integración se ha comprobado en
**QGIS 3.44.12, Windows y Python 3.12**. Faltan ensayos en otras plataformas y
versiones. El complemento aún no se ha enviado al repositorio oficial de QGIS.

## Empezar con un DEM

1. Añade al proyecto un DEM local de una banda, con CRS proyectado, grilla norte
   arriba y las mismas unidades horizontales y de elevación.
2. Selecciónalo en el panel y elige un método y sus parámetros.
3. Pulsa **Add product** para cada resultado deseado. Cada producto utiliza el
   DEM original; la lista no encadena derivadas.
4. Elige la carpeta de salida y pulsa **Run and add layers**.
5. Revisa las capas, metadatos y **Run log**. Las clases geomorphon reciben una
   leyenda categorizada.

Cada ejecución del panel crea una carpeta con GeoTIFF, metadatos y manifiestos
JSON. Los productos completados se conservan ante fallo o cancelación. Esta se
comprueba entre productos: el cálculo actual termina primero.

## Herramientas

| Familia | Productos incluidos |
| --- | --- |
| Visualización del relieve | Generador y compositor RGB de RRIM clásico; siete variantes RRIM experimentales |
| Iluminación y apertura | Sombreado clásico y multidireccional, aperturas positiva/negativa y sky-view factor |
| Derivadas del terreno | Pendiente, aspecto y curvaturas de perfil, plana y media |
| Contexto local | TPI, relieve local, TRI de Riley y proxy de humedad |
| Formas del terreno | Diez geomorphons por líneas de visión, patrones canónicos y un modelo simplificado heredado separado |
| Hidrología adicional | Relleno, acumulación y TWI D8/MFD, dirección, cuencas por salida y longitud D8 |

Processing ofrece **43 herramientas**: los 32 métodos compartidos como algoritmos
individuales y 11 herramientas de suite, bloques, RRIM clásico, benchmarks y
recetas. Funcionan en lotes y Model Designer. Se conservan los identificadores
previos. La orientación principal es geomorfometría y visualización del relieve.

## Automatizar el mismo flujo

Una receta JSON funciona en el panel, Processing, la CLI y la API. Se siguen
leyendo las recetas antiguas del panel y las recomendaciones por objetivo.
Por ejemplo, en la consola Python de QGIS con GeoMorphX activado:

    import processing

    result = processing.run("geomorphx_rrim_suite:run_recipe", {
        "INPUT_DEM": "D:/datos/dem.tif",
        "RECIPE": "D:/recetas/terreno.json",
        "OUT_DIR": "D:/resultados/corrida_001",
    })

Usa una carpeta nueva por ejecución. La [guía de automatización](docs/AUTOMATIZACION.md)
explica Python, CLI, formatos anteriores, cancelación, manifiestos y ejemplos.

## Estado científico y límites

- Las ventanas y escalas están en píxeles. No se deducen ni convierten unidades
  de elevación: comprueba que coincidan con las horizontales.
- Los productos locales usan bloques con márgenes. RRIM experimental utiliza
  normalización global e intermedios conservados. La hidrología todavía carga
  el DEM completo, incluso si se pide un tamaño de bloque.
- Las siete variantes RRIM del núcleo son composiciones experimentales con
  convención heredada de píxel unitario. No está validada su equivalencia con
  RRIM clásico; el generador y compositor clásicos son herramientas separadas.
- Geomorphons implementa la comparación básica documentada, no todas las
  opciones de GRASS. Faltan comparaciones ejecutables independientes y de campo.

La última suite del checkout pasó **162 pruebas**, con **9 pruebas Rust omitidas**
por falta de la extensión en ese árbol. QGIS real se comprobó con un perfil
aislado y Qt fuera de pantalla, incluidas las 43 herramientas y recetas comunes.
Son controles sintéticos y de integración, no validación de campo. Consulta el
[estado y problemas conocidos](docs/STATUS.md), incluido el diagnóstico del
exportador RGB heredado y los ensayos manuales y de plataformas pendientes.

## Documentación y desarrollo

- [Guía del complemento en español](qgis_plugin/README.es.md)
- [Automatización y recetas](docs/AUTOMATIZACION.md)
- [Método geomorphon y clases](docs/GEOMORPHONS.es.md)
- [Memoria, bloques e hidrología adicional](docs/ESCALABILIDAD_Y_HIDROLOGIA.md)
- [Desarrollo y empaquetado, en inglés](docs/DEVELOPMENT.md)
- [Índice en español](docs/README.es.md) · [English documentation](docs/README.md)

QGIS es la interfaz principal de escritorio. La API y la CLI se mantienen para
automatización; la GUI independiente queda como compatibilidad secundaria.
Rust acelera algunos kernels del paquete Python opcional. Consulta
[LICENSE](LICENSE) para la licencia del software.
