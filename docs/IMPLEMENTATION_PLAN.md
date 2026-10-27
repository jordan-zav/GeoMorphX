# Plan de implementación

Estado revisado el 26 de octubre de 2026. Consulte AUDITORIA_Y_ESTADO.md para
los hallazgos, decisiones numéricas y límites de la validación.

## Implementado

1. Siete variantes experimentales RRIM, incluida estructura multiescala.
2. Derivadas de terreno, aperturas, SVF y sombreado multidireccional.
3. TRI de Riley, rango local explícito y conservación del alias tri heredado.
4. Priority-Flood, acumulación D8 y TWI D8 con pruebas de conservación.
5. API, CLI, escritorio y suite QGIS con catálogo común de 32 métodos.
6. Recetas, comparación y benchmarks reproducibles; objetivo hidrológico nuevo.
7. Kernels Rust de rango, desviación, media y respuesta direccional con Rayon.
8. Procesamiento local y de las siete variantes RRIM por bloques con normalización global y pruebas de equivalencia.
9. Protección NoData, escala física para derivadas y JSON de parámetros efectivos.
10. Compilación y pruebas del wheel instalado; workflow de integración continua.
11. Flujo múltiple Freeman, TWI MFD, dirección, cuencas y longitud de drenaje D8.
12. Recetas validadas contra la resolución real y manifiestos con hashes SHA-256.
13. ZIP QGIS con núcleo Python incluido y notebook sintético ejecutado con figuras PNG/PDF.
14. QGIS como interfaz principal: panel acoplable, selección de capas, productos,
    recetas JSON, tareas en segundo plano, registro y leyenda de geomorphons.
15. 32 métodos como algoritmos individuales y diez herramientas históricas,
    manteniendo identificadores y modelos guardados.
16. I/O compartido con alternativa GDAL nativa para QGIS sin Rasterio.
17. Validación del ZIP en QGIS 3.44.12 real con perfil aislado y Qt fuera de pantalla.
18. Recetas geomorphx-recipe 1.0 compartidas por panel, API, CLI y Processing;
    lectura de los dos formatos anteriores y guardado canónico.
19. API pública de creación, lectura, validación y ejecución; guía, JSON Schema
    y ejemplos incluidos en el ZIP. Proveedor ampliado a 43 algoritmos.

## Próxima fase científica

1. Validar RRIM contra literatura y DEM de referencia; revisar escala física y azimut.
2. Comparar geomorphons LOS con una referencia ejecutable y ampliar las opciones metodológicas.
3. Validar derivados del terreno con DEM reales y referencias independientes,
   además de los ensayos de integración sintéticos.
4. Ampliar el notebook sintético con comparación externa, ablación RRIM+ y DEM de referencia.
5. Incorporar entradas geológicas/estructurales externas con contratos explícitos.

## Próxima fase de escalabilidad

1. Optimizar I/O y espacio de las pasadas RRIM; añadir reanudación de pipelines y gestión explícita de intermedios.
2. Hidrología con conectividad global sobre datos mayores que la memoria disponible.
3. Ampliar los kernels Rust medidos por perfiles de rendimiento.
4. Benchmarks regionales que midan memoria, igualdad numérica y paralelismo.

## Próxima fase de distribución

1. Ampliar a Linux, macOS y otras versiones de QGIS; ejecutar la matriz CI remota.
2. Sesiones manuales de uso con DEM reales y perfiles QGIS limpios, además de las
   pruebas automatizadas reales de bloques, catálogo y panel.
3. Preparar la candidatura del plugin al repositorio oficial cuando se cierren
   los límites científicos prioritarios. La GUI independiente queda secundaria.
4. Completar manuscrito y preparar una publicación con límites científicos explícitos.

## Alcance adicional diferido

Las herramientas hidrológicas existentes se conservan para compatibilidad.
Su validación con DEM reales y posibles ampliaciones como D-infinity, puntos
de aforo o redes vectoriales son ideas adicionales, no la prioridad de esta
fase. El producto se centra en geomorfometría y visualización del relieve.
