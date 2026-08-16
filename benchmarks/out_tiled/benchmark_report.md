# GeoMorphX Benchmark Report

- Source: `synthetic:128`
- DEM shape: `128 x 128`
- Tile size: `0` (0 = disabled)

## Ranking (Fastest to Slowest)

1. `rrim_baseline` - 67.132 ms
2. `rrim_anisotropic` - 70.355 ms
3. `rrim_anisotropic_multiscale` - 134.790 ms
4. `rrim_multiscale` - 135.959 ms
5. `rrim_structural` - 207.625 ms
6. `rrim_plus` - 494.971 ms

## Results Table

| method | repeats | runtime_ms_mean | runtime_ms_std | output_min | output_max | output_mean | output_std |
|---|---:|---:|---:|---:|---:|---:|---:|
| rrim_baseline | 1 | 67.131700 | 0.000000 | 0.035496 | 0.999895 | 0.676827 | 0.140607 |
| rrim_multiscale | 1 | 135.959300 | 0.000000 | 0.066545 | 0.973621 | 0.677834 | 0.133460 |
| rrim_anisotropic | 1 | 70.355000 | 0.000000 | 0.014840 | 0.999108 | 0.473352 | 0.181971 |
| rrim_anisotropic_multiscale | 1 | 134.790200 | 0.000000 | 0.027259 | 0.979300 | 0.473754 | 0.178086 |
| rrim_structural | 1 | 207.624800 | 0.000000 | 0.000000 | 1.000000 | 0.557930 | 0.290791 |
| rrim_plus | 1 | 494.970900 | 0.000000 | 0.000000 | 1.000000 | 0.497424 | 0.186585 |