# Geomorphons por líneas de visión

[English](GEOMORPHONS.md) | Español

Implementado el 25 de octubre de 2026 en el núcleo Python, API, CLI,
aplicación independiente y suite de QGIS. El algoritmo simplificado de QGIS
conserva su identificador y sus nueve clases; el nuevo utiliza diez clases.

## Métodos y parámetros

| Método | Producto |
| --- | --- |
| geomorphons | Diez clases de forma, con códigos 1–10 |
| geomorphon_ternary | Código mínimo bajo las ocho rotaciones y sus reflexiones; 498 patrones posibles |

La API emplea window como diámetro de ventana impar. El radio es window // 2.
El mínimo admitido es window=5; se recomienda al menos 7, porque el radio 2
puede dejar un único punto por dirección y producir empates angulares.

| Parámetro | Convención |
| --- | --- |
| flatness_deg | Umbral angular en grados; predeterminado 1, estrictamente entre 0 y 90 |
| geomorphon_skip | Cantidad de pasos interiores excluidos de cada perfil; predeterminado 0 |
| cell_size | Tamaños físicos (dy, dx), inferidos del GeoTIFF o explícitos para arrays |
| window | Predeterminado 9; las ventanas pares se convierten a la siguiente impar |

CLI:

    geomorphx compute --dem dem.tif --out formas.tif --method geomorphons --window 15 --flatness-deg 1 --geomorphon-skip 0

Patrones: cambie el método por geomorphon_ternary. El objetivo de recetas
landforms genera formas, patrón ternario y pendiente física.

En QGIS se puede usar Suite Compute o el nuevo algoritmo
gmx_geomorphons_los, que produce formas y patrones con metadatos.

## Modelo numérico

Se recorren ocho perfiles, desde el norte en sentido horario. Se conserva el
ángulo de elevación máximo y mínimo dentro de una distancia física estrictamente
menor que radio por máximo(dy, dx). La distancia a cada muestra tiene en cuenta
la diagonal y los píxeles rectangulares. El halo de bloques aumenta cuando los
píxeles son rectangulares para no recortar el círculo físico.

La regla básica anglev1 convierte cada perfil en signo positivo, negativo o
neutral comparando el valor absoluto de sus extremos angulares. Si ambos están
bajo el umbral, o sus valores absolutos coinciden exactamente, el signo es neutral.
Los conteos de signos positivos y negativos se convierten a las diez formas
con la matriz metodológica publicada.

Los empates importan: un plano matemático de gradiente constante puede resultar
plano bajo anglev1. Este comportamiento se prueba explícitamente, coincide con
la regla consultada y no debe confundirse con una estimación independiente de
pendiente. La receta incluye pendiente para facilitar la revisión.

## Leyenda

| Código | Forma |
| --- | --- |
| 1 | Plano |
| 2 | Pico |
| 3 | Cresta |
| 4 | Hombro |
| 5 | Espolón |
| 6 | Ladera |
| 7 | Concavidad de ladera |
| 8 | Pie de ladera |
| 9 | Valle |
| 10 | Depresión |

## Bordes y NoData

NoData termina el perfil: el algoritmo no mira a través de un hueco. También
se detiene al salir del ráster. Para asignar una forma o patrón se requiere
al menos una muestra válida en cada una de las ocho direcciones; de lo contrario,
la salida es NaN. Esto puede excluir el borde y las celdas contiguas a huecos.

geomorphon_components devuelve además conteos de signos y cobertura de perfiles.
La cobertura es la fracción de direcciones con muestras, no una probabilidad de
que la clase sea correcta. El componente confidence del simplificado sigue siendo
solo el contraste de signos heredado.

## Verificación y alcance

Se verifican las diez formas con perfiles sintéticos construidos, los 6.561
patrones ternarios y su reducción a 498 clases, invariancia por rotación,
umbrales, salto interior, NoData y equivalencia entre bloques y DEM completo.
Además de las pruebas de adaptadores con API anfitriona sustituida, se ejecutó
QGIS 3.44.12 real en Windows con perfil aislado y Qt fuera de pantalla. Se
comprobaron los algoritmos y una capa categorizada. Sigue pendiente una sesión
manual completa y la comparación científica independiente.

No se implementan corrección extendida de formas, distancias de relajación del
umbral, comparación anglev2/anglev2_distance ni métricas geométricas adicionales.
No se afirma equivalencia completa de salidas con GRASS: la política de NoData
y el radio físico en grillas rectangulares se han definido explícitamente aquí.

## Referencias

- [GRASS r.geomorphon: método y parámetros](https://grass.osgeo.org/grass-stable/manuals/r.geomorphon.html).
- [GRASS: regla de horizontes anglev1](https://github.com/OSGeo/grass/blob/main/raster/r.geomorphon/pattern.c).
- [GRASS: matriz de formas y patrones canónicos](https://github.com/OSGeo/grass/blob/main/raster/r.geomorphon/geom.c).
- [WhiteboxTools: implementación de geomorphons](https://github.com/jblindsay/whitebox-tools/blob/master/whitebox-tools-app/src/tools/terrain_analysis/geomorphons.rs).
