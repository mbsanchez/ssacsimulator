# Análisis adicionales (diseño v2, detector por estación salvo indicación)

## A. Escenarios sin coste y descomposición del retraso (trazas reservadas)

78 de 216 escenarios tienen coste nulo sin acción en las 24 h: 73 porque la estación averiada no tiene ninguna transición en la ventana y el resto porque todas caen en la fase apagada de un fallo intermitente. Por traza: 100m-200m 8, 200m-300m 48, 500m-600m 22; por forma: step 31, intermittent 25, drift 22.

Fallo restante y coste de las acciones: fracciones del coste sin acción, sobre los escenarios con coste (recuperación = 1 − fallo − acciones).

| Planificador | recuperación, todos | recuperación, con coste [IC 95 %] | fallo restante | coste de las acciones | coste de las acciones en escenarios sin coste (min-pieza) |
|---|---|---|---|---|---|
| rules_cal | +0.131 | +0.225 [+0.125, +0.319] | 0.342 | 0.433 | 99,591 |
| rules_adapt | +0.167 | +0.234 [+0.127, +0.330] | 0.309 | 0.457 | 70,818 |
| rules_adapt_ctx | +0.204 | +0.268 [+0.166, +0.362] | 0.312 | 0.420 | 67,785 |
| rules_twin | -0.200 | -0.121 [-0.205, -0.034] | 0.687 | 0.434 | 83,736 |
| llm_c1 | -0.051 | +0.047 [-0.054, +0.142] | 0.454 | 0.499 | 103,989 |
| llm_c2 | -0.247 | -0.057 [-0.178, +0.051] | 0.230 | 0.827 | 200,013 |
| hybrid | +0.289 | +0.348 [+0.249, +0.437] | 0.315 | 0.338 | 61,989 |
| llm_c1:fable-5.1 | +0.083 | +0.084 [+0.037, +0.139] | 0.907 | 0.009 | 405 |
| llm_c2:fable-5.1 | +0.139 | +0.237 [+0.140, +0.327] | 0.327 | 0.436 | 103,719 |
| hybrid:fable-5.1 | +0.413 | +0.442 [+0.350, +0.529] | 0.437 | 0.121 | 30,645 |

Sobre los escenarios con coste:

| Comparación (A − B) | Δ recuperación 24 h | IC 95 % estratificado | IC 95 % dos niveles | A mejor / peor | p Wilcoxon | extracciones de trazas con Δ ≤ 0 | Δ por traza |
|---|---|---|---|---|---|---|---|
| hybrid:fable-5.1 − rules_adapt_ctx | +0.173 | [+0.109, +0.238] | [+0.031, +0.250] | 107 / 18 | 1e-12 | 0/27 | +0.233, +0.047, +0.182 |
| hybrid:fable-5.1 − hybrid | +0.094 | [+0.032, +0.154] | [-0.068, +0.171] | 102 / 24 | 2.5e-09 | 1/27 | +0.149, -0.069, +0.140 |
| hybrid:fable-5.1 − llm_c2:fable-5.1 | +0.204 | [+0.136, +0.272] | [+0.076, +0.283] | 111 / 18 | 1.1e-14 | 0/27 | +0.238, +0.089, +0.247 |

## B. Sensibilidad: fallo leve (k = 1,5), trazas reservadas

| Planificador | recuperación 24 h [IC 95 %] | sobre escenarios con coste | step | intermittent | drift |
|---|---|---|---|---|---|
| rules_cal | -1.511 [-1.853, -1.229] | -1.133 | -0.889 | -3.633 | -1.181 |
| rules_adapt | -1.465 [-1.792, -1.195] | -1.197 | -0.983 | -3.517 | -1.024 |
| rules_adapt_ctx | -1.302 [-1.614, -1.044] | -1.045 | -0.841 | -3.222 | -0.900 |
| rules_twin | -1.753 [-2.034, -1.526] | -1.435 | -1.251 | -3.513 | -1.465 |
| hybrid | -0.952 [-1.215, -0.738] | -0.717 | -0.604 | -2.510 | -0.599 |
| hybrid:fable-5.1 | -0.066 [-0.205, +0.055] | +0.050 | +0.019 | -0.666 | +0.121 |

| Comparación (A − B) | Δ recuperación 24 h | IC 95 % estratificado | IC 95 % dos niveles | A mejor / peor | p Wilcoxon | extracciones de trazas con Δ ≤ 0 | Δ por traza |
|---|---|---|---|---|---|---|---|
| hybrid:fable-5.1 − rules_adapt_ctx | +1.236 | [+1.045, +1.464] | [+0.976, +1.520] | 154 / 3 | 2.1e-26 | 0/27 | +1.301, +1.348, +1.034 |
| hybrid:fable-5.1 − hybrid | +0.886 | [+0.735, +1.059] | [+0.672, +1.058] | 148 / 9 | 4.5e-24 | 0/27 | +0.958, +0.776, +0.861 |

## C. Ablaciones del veto (híbrido Fable, trazas reservadas)

| Detector | texto de alarmas | pista de ráfagas | recuperación 24 h [IC 95 %] | llamadas | con veto | vetos que citan ráfagas |
|---|---|---|---|---|---|---|
| por estación | v3 | sí | +0.413 [+0.318, +0.501] | 4348 | 2833 | 91% |
| por estación | v2 | sí | +0.413 [+0.317, +0.505] | 4515 | 2601 | 88% |
| por estación | v3 | no | +0.314 [+0.211, +0.413] | 4030 | 1409 | 44% |
| heredado | v2 | sí | +0.033 [-0.009, +0.077] | 1812 | 1607 | 99% |
| heredado | v3 | sí | +0.031 [-0.002, +0.068] | 1865 | 1784 | 97% |

| Comparación (A − B) | Δ recuperación 24 h | IC 95 % estratificado | IC 95 % dos niveles | A mejor / peor | p Wilcoxon | extracciones de trazas con Δ ≤ 0 | Δ por traza |
|---|---|---|---|---|---|---|---|
| con pista − sin pista (por estación) | +0.098 | [+0.066, +0.132] | [+0.054, +0.138] | 121 / 33 | 4.3e-13 | 0/27 | +0.121, +0.073, +0.082 |
| texto v3 − texto v2 (por estación) | -0.001 | [-0.046, +0.029] | [-0.085, +0.035] | 83 / 8 | 2.4e-10 | 17/27 | +0.031, -0.063, -0.001 |
| texto v2 − texto v3 (heredado) | +0.001 | [-0.025, +0.029] | [-0.057, +0.039] | 21 / 24 | 0.37 | 10/27 | +0.013, -0.055, +0.029 |

## D. Validación en cinco trazas nuevas (todo congelado)

360 escenarios con fallo; 138 sin coste.

| Planificador | recuperación 24 h [IC 95 %] | sobre escenarios con coste | step | intermittent | drift |
|---|---|---|---|---|---|
| rules_cal | +0.274 [+0.188, +0.350] | +0.398 | +0.384 | -0.312 | +0.378 |
| rules_adapt | +0.103 [-0.002, +0.192] | +0.290 | +0.214 | -0.640 | +0.267 |
| rules_adapt_ctx | +0.165 [+0.066, +0.248] | +0.343 | +0.265 | -0.509 | +0.315 |
| rules_twin | -0.312 [-0.411, -0.227] | -0.155 | -0.233 | -1.029 | -0.121 |
| rules_cal_rt | +0.370 [+0.296, +0.436] | +0.456 | +0.455 | -0.051 | +0.438 |
| rules_adapt_ctx_rt | +0.187 [+0.090, +0.267] | +0.354 | +0.292 | -0.491 | +0.332 |
| hybrid | +0.232 [+0.141, +0.312] | +0.376 | +0.293 | -0.354 | +0.393 |
| hybrid:fable-5.1 | +0.487 [+0.422, +0.547] | +0.546 | +0.510 | +0.153 | +0.593 |

| Comparación (A − B) | Δ recuperación 24 h | IC 95 % estratificado | IC 95 % dos niveles | A mejor / peor | p Wilcoxon | extracciones de trazas con Δ ≤ 0 | Δ por traza |
|---|---|---|---|---|---|---|---|
| hybrid:fable-5.1 − rules_cal_rt | +0.117 | [+0.080, +0.159] | [+0.052, +0.194] | 217 / 70 | 2.3e-18 | 0/3125 | +0.133, +0.052, +0.131, +0.062, +0.202 |
| hybrid:fable-5.1 − rules_cal | +0.213 | [+0.172, +0.259] | [+0.137, +0.322] | 259 / 44 | 5.1e-30 | 0/3125 | +0.345, +0.157, +0.353, +0.098, +0.245 |
| hybrid:fable-5.1 − rules_adapt_ctx | +0.322 | [+0.255, +0.396] | [+0.222, +0.489] | 268 / 31 | 1.5e-35 | 0/3125 | +0.597, +0.213, +0.419, +0.405, +0.237 |
| hybrid:fable-5.1 − rules_adapt_ctx_rt | +0.300 | [+0.236, +0.372] | [+0.213, +0.448] | 267 / 33 | 1.3e-34 | 0/3125 | +0.437, +0.261, +0.492, +0.326, +0.198 |
| hybrid:fable-5.1 − hybrid | +0.255 | [+0.192, +0.323] | [+0.172, +0.384] | 262 / 36 | 6.6e-31 | 0/3125 | +0.470, +0.167, +0.333, +0.291, +0.211 |

Vetos del híbrido Fable en las trazas nuevas: 5136 de 7276 llamadas; 92% citan ráfagas.
