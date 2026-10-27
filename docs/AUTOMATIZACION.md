# Automatización de GeoMorphX

[English](AUTOMATION.md) | Español

El mismo JSON funciona en el panel QGIS, Processing, la CLI y la API Python.
Todas las interfaces validan y ejecutan las recetas mediante geomorphx.recipes;
no mantienen motores numéricos ni validadores de parámetros separados.

## Elegir una vía

| Entorno | Vía recomendada |
| --- | --- |
| QGIS sin programar | Guardar/cargar una receta del panel o usar lotes y Model Designer |
| Consola o script de QGIS | processing.run con geomorphx_rrim_suite:run_recipe |
| Terminal y tareas programadas | geomorphx run-recipe |
| Programa Python o notebook | API pública execute_recipe |

Son interfaces locales. No hay que iniciar un servicio web ni exponer puertos.
El plugin activado prepara el núcleo Python en QGIS. Fuera de QGIS se necesita
el paquete Python instalado o el entorno de desarrollo del repositorio; el
ZIP del complemento es la distribución principal para usuarios de QGIS.

## Una receta reutilizable

El formato nuevo se identifica con format igual a geomorphx-recipe y
schema_version igual a 1.0. Cada producto indica un método del catálogo y sus
parámetros. Cada cálculo parte del DEM original; no encadena productos previos.

    {
      "format": "geomorphx-recipe",
      "schema_version": "1.0",
      "input_assumptions": {},
      "products": [
        {"method": "slope", "parameters": {"tile_size": 512}},
        {"method": "geomorphons", "parameters": {"window": 9}}
      ]
    }

Los parámetros omitidos reciben los valores predeterminados del formato 1.0.
Guardar la receta con save_recipe o desde el panel escribe todos los parámetros
explícitos, de modo que se puedan revisar antes de ejecutar. El JSON Schema está
en docs/recipe.schema.json y se incluye como recipe.schema.json en el ZIP.
Los ejemplos completos están en examples/automation y se incluyen en el ZIP.

Las ventanas y escalas están en píxeles. Para exigir una resolución concreta,
añade pixel_size_m a input_assumptions. La ejecución comprobará ambos ejes en
metros antes de crear productos. Si cambias de DEM, revisa esa condición y las
escalas físicas; una receta no ajusta automáticamente las ventanas al nuevo DEM.
Se requiere un DEM local de una banda, proyectado, y elevaciones en las mismas
unidades que las coordenadas horizontales.

## Desde el panel QGIS

Elige el DEM, añade productos y pulsa Save recipe. Ese archivo puede abrirse en
la CLI o en Processing sin conversión manual. Load recipe acepta también los
documentos antiguos del panel y las recomendaciones generadas por objetivos.
Al importar una recomendación se conservan su resolución exigida, roles y
justificación. Guardarla vuelve a producir el formato común.

## Desde Processing

Activa GeoMorphX y ejecuta en la consola Python de QGIS:

    import processing

    result = processing.run("geomorphx_rrim_suite:run_recipe", {
        "INPUT_DEM": "D:/datos/dem.tif",
        "RECIPE": "D:/recetas/terreno.json",
        "OUT_DIR": "D:/resultados/corrida_001",
    })
    print(result["MANIFEST"])

La herramienta Run portable recipe devuelve una carpeta de salida y un
manifiesto. El panel añade además las capas al proyecto. Aparece en Automation. También
puedes incorporarla a Model Designer o ejecutarla por lotes con una tabla de
DEM, recetas y carpetas de salida. Usa una carpeta distinta por ejecución.

## Desde la terminal

Con la CLI de GeoMorphX disponible en el entorno:

    geomorphx validate-recipe --recipe terreno.json
    geomorphx run-recipe --recipe terreno.json --dem dem.tif --out-dir corrida_001

Para generar una receta por objetivo o convertir una antigua al formato común:

    geomorphx recommend --objective landforms --pixel-size-m 2 --out formas.json
    geomorphx validate-recipe --recipe antigua.json --out portable.json

validate-recipe comprueba el documento completo sin abrir el DEM ni calcular
productos. La resolución real se comprueba cuando se ejecuta run-recipe.
El código de salida es cero en una ejecución normal y distinto de cero si
el proceso falla; conserva los registros de tu programador de tareas.
Desde un checkout de desarrollo, python -m cli.geomorphx_cli admite los mismos
argumentos sin instalar el comando geomorphx.

## Desde Python

    from geomorphx import create_recipe, save_recipe, execute_recipe

    recipe = create_recipe([
        {"method": "slope", "parameters": {"tile_size": 512}},
        {"method": "tri_riley"},
    ])
    save_recipe(recipe, "terreno.json")
    outputs, manifest = execute_recipe(
        "terreno.json", dem_path="dem.tif", out_dir="corrida_001",
    )

La API pública también expone load_recipe y normalize_recipe. Esta última
devuelve una copia validada con valores predeterminados y no crea archivos.
Para integración en una aplicación, execute_recipe admite progress como función
que recibe un porcentaje y cancelled como función que devuelve un booleano.
La cancelación se comprueba entre productos: el kernel actual termina primero.

recommend sigue devolviendo su estructura histórica para mantener los programas
existentes. save_recipe la transforma al formato común; execute_recipe y el panel
aceptan ambos formatos directamente. La entrada histórica
geomorphx.recommendations.execute_recipe continúa disponible como adaptador.

## Valores predeterminados

El formato de receta usa window=9, scales=[5,15,45], azimuth_deg=0, tile_size=0,
flatness_deg=1 y geomorphon_skip=0. Los pesos directional, anisotropy, roughness
y structural son 0.5, 0.35, 0.25 y 0.15, respectivamente.

El panel comienza con azimut 45 y bloque 512, y guarda esos valores explícitos.
Las herramientas de cómputo directo de Processing conservan valores históricos:
azimut 45 y pesos directional=0.6, anisotropy=0.3 y structural=0.2. Al comparar
una llamada directa con una receta, fija los parámetros explícitamente. Las
interfaces comparten motor numérico, pero no todos sus valores iniciales de GUI.
run_recipe usa los valores del archivo.

## Resultados, errores y conservación

Cada producto genera un GeoTIFF y su archivo meta.json. recipe_run_manifest.json
registra la receta normalizada, validación y SHA-256 del DEM, productos completados,
parámetros, hashes de salidas y estado complete, cancelled o failed.
El panel conserva además workflow.json como acceso compatible a ese registro.

Se validan todos los productos antes del primer cálculo. Una receta inválida o
una resolución incompatible no produce resultados mediante la API. Si falla un
producto después de empezar, se guardan el manifiesto de fallo y los productos
que ya terminaron, y la API vuelve a lanzar el error. Si se cancela, devuelve
las salidas completadas y el manifiesto con estado cancelled; comprueba ese
estado antes de considerar completa la tarea.

No se sobrescriben resultados ni manifiestos anteriores. Una reserva creada de
forma exclusiva, recipe_run.reservation.json, impide que dos trabajos usen la
misma carpeta simultáneamente. Se conserva incluso tras un fallo: usa una carpeta
nueva para reintentar. No se limpian resultados automáticamente ni se reanuda
una corrida incompleta.
Esta protección contra sobrescritura pertenece al ejecutor de recetas; no debe
atribuirse automáticamente a todas las funciones de cómputo de bajo nivel.

## Compatibilidad y límites

Se leen geomorphx-workbench versión 1 y recomendaciones schema_version 1.0;
los archivos nuevos se escriben como geomorphx-recipe 1.0. Otros formatos o
versiones se rechazan. Los nombres de métodos y sus identificadores Processing
previos se conservan. La nueva herramienta eleva el proveedor a 43 algoritmos.

La automatización no cambia los límites científicos: RRIM sigue siendo
experimental, geomorphons implementa el modo básico documentado y la hidrología
necesita contexto global en memoria. Comprueba resultados, escala y unidades
antes de utilizarlos para interpretación. La integración QGIS se verifica con
perfil aislado y Qt fuera de pantalla; no reemplaza la validación de campo.
