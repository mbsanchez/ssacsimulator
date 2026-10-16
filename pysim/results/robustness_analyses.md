# Análisis de robustez (resultados almacenados, sin llamadas al modelo)

## A. Probabilidad de veto según el tamaño de la alarma (trazas reservadas, desde el inicio del fallo)

Cada candidato propuesto por el test en una llamada posterior al inicio del fallo; veto = no se actúa sobre él. Tamaño = estaciones nombradas en la alarma que dispara la llamada.

| Modelo | estaciones en la alarma | candidatos: averiada | vetada | candidatos: sanas | vetadas |
|---|---|---|---|---|---|
| fable | 1 | 66 | 17% | 329 | 40% |
| fable | 2 | 25 | 32% | 319 | 64% |
| fable | 3 | 23 | 57% | 314 | 93% |
| fable | 4 | 8 | 38% | 172 | 91% |
| fable | ≥5 | 17 | 88% | 363 | 91% |
| qwen | 1 | 44 | 2% | 298 | 17% |
| qwen | 2 | 29 | 3% | 199 | 11% |
| qwen | 3 | 18 | 6% | 266 | 17% |
| qwen | 4 | 12 | 0% | 165 | 8% |
| qwen | ≥5 | 19 | 26% | 385 | 16% |

## B. Bootstrap por conglomerados traza × estación

| Comparación (A − B) | conjunto | Δ | IC 95 % | conglomerados |
|---|---|---|---|---|
| hybrid:fable-5.1 − rules_adapt_ctx | reservadas | +0.208 | [+0.134, +0.294] | 24 |
| hybrid:fable-5.1 − hybrid | reservadas | +0.123 | [+0.053, +0.197] | 24 |
| hybrid:fable-5.1 − llm_c2:fable-5.1 | reservadas | +0.274 | [+0.195, +0.371] | 24 |
| hybrid:fable-5.1 − rules_cal_rt | validación | +0.117 | [+0.067, +0.177] | 40 |
| hybrid:fable-5.1 − rules_adapt_ctx | validación | +0.322 | [+0.232, +0.445] | 40 |

## C. Distribución por escenario del retraso añadido frente a no hacer nada (min-pieza; negativo = mejor)

| Planificador | conjunto | p5 | p25 | mediana | p75 | p95 | peor | escenarios peor que no hacer nada |
|---|---|---|---|---|---|---|---|---|
| rules_adapt_ctx | reservadas | -12,912 | -1,451 | 0 | 1,779 | 2,832 | 7,902 | 90 |
| hybrid | reservadas | -13,920 | -1,936 | 0 | 1,374 | 2,739 | 6,084 | 84 |
| llm_c2:fable-5.1 | reservadas | -12,811 | -1,176 | 0 | 1,887 | 4,698 | 6,069 | 97 |
| hybrid:fable-5.1 | reservadas | -11,943 | -2,658 | 0 | 519 | 1,452 | 2,031 | 75 |
| rules_cal_rt | validación | -13,923 | -3,611 | 0 | 1,464 | 3,009 | 6,477 | 159 |
| rules_adapt_ctx | validación | -12,226 | -2,845 | 60 | 3,405 | 5,865 | 9,756 | 184 |
| hybrid | validación | -13,026 | -2,756 | 0 | 2,790 | 5,007 | 10,077 | 177 |
| hybrid:fable-5.1 | validación | -14,922 | -4,644 | 0 | 981 | 2,151 | 5,202 | 128 |

## D. Recuperación con un coste fijo por reparación (min-pieza añadidos por cada reparación en 24 h)

| Planificador | conjunto | 0 | 60 | 240 | 960 |
|---|---|---|---|---|---|
| rules_adapt_ctx | reservadas | +0.204 | +0.130 | -0.093 | -0.983 |
| hybrid | reservadas | +0.289 | +0.219 | +0.008 | -0.836 |
| llm_c2:fable-5.1 | reservadas | +0.139 | +0.043 | -0.243 | -1.388 |
| hybrid:fable-5.1 | reservadas | +0.413 | +0.386 | +0.305 | -0.017 |
| rules_cal_rt | validación | +0.370 | +0.320 | +0.170 | -0.432 |
| rules_adapt_ctx | validación | +0.165 | +0.075 | -0.194 | -1.273 |
| hybrid | validación | +0.232 | +0.150 | -0.096 | -1.078 |
| hybrid:fable-5.1 | validación | +0.487 | +0.453 | +0.350 | -0.062 |
