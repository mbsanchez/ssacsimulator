# Estadística pareada — A = `hybrid:fable-5.1`

Diseño v2. Escenarios con fallo de las trazas reservadas (3 inicios cada uno), pareados por (traza, estación, forma, inicio); retraso en exceso dentro del horizonte tras el inicio. Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples dentro de cada tabla.

## Frente a cada planificador

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| hybrid:fable-5.1 vs rules_adapt_ctx | 216 | 139 | 18 | 2.85e-17 | 7.88e-17 | +0.78 | +0.208 | [+0.138, +0.280] |
| hybrid:fable-5.1 vs rules_adapt | 216 | 144 | 14 | 7.55e-19 | 3.02e-18 | +0.81 | +0.246 | [+0.174, +0.322] |
| hybrid:fable-5.1 vs rules_cal | 216 | 138 | 22 | 2.63e-17 | 7.88e-17 | +0.77 | +0.282 | [+0.201, +0.369] |
| hybrid:fable-5.1 vs hybrid | 216 | 133 | 25 | 1.65e-13 | 1.65e-13 | +0.68 | +0.123 | [+0.057, +0.189] |
| hybrid:fable-5.1 vs llm_c2:fable-5.1 | 216 | 141 | 20 | 1.12e-19 | 5.61e-19 | +0.82 | +0.274 | [+0.195, +0.354] |

## Por subgrupo, frente a `rules_adapt_ctx`

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| fallo step | 72 | 42 | 7 | 9.42e-05 | 9.42e-05 | +0.64 | +0.093 | [-0.021, +0.216] |
| fallo intermittent | 72 | 49 | 5 | 5.15e-08 | 1.54e-07 | +0.85 | +0.487 | [+0.352, +0.635] |
| fallo drift | 72 | 48 | 6 | 1.21e-07 | 2.42e-07 | +0.83 | +0.200 | [+0.134, +0.274] |

Con y sin gemela (familia aparte):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| con gemela | 108 | 67 | 9 | 7.1e-09 | 7.1e-09 | +0.76 | +0.282 | [+0.144, +0.425] |
| sin gemela | 108 | 72 | 9 | 6.97e-10 | 1.39e-09 | +0.79 | +0.164 | [+0.090, +0.240] |

Por traza (exploratorio, sin ajuste):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| traza 100m-200m | 72 | 56 | 6 | 2.54e-08 | 7.62e-08 | +0.81 | +0.233 | [+0.170, +0.304] |
| traza 200m-300m | 72 | 39 | 8 | 0.000121 | 0.000121 | +0.64 | +0.150 | [-0.066, +0.423] |
| traza 500m-600m | 72 | 44 | 4 | 4.82e-08 | 9.63e-08 | +0.90 | +0.216 | [+0.148, +0.313] |

Por traza y forma (Δ recuperación agregada; A mejor / n):

| Traza | step | intermittent | drift |
|---|---|---|---|
| 100m-200m | +0.142 (16/24) | +0.356 (19/24) | +0.262 (21/24) |
| 200m-300m | -0.127 (12/24) | +1.121 (14/24) | +0.130 (13/24) |
| 500m-600m | +0.169 (14/24) | +0.402 (16/24) | +0.174 (14/24) |

## Latencia de la primera acción sobre la estación averiada

Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.

Latencia desde el inicio del fallo. Medianas marginales: sobre todos los escenarios en que cada uno actúa.

| Comparación | pares | A antes | B antes | mediana A / B en los pares (min) | diferencia: p10 / mediana / p75 | p (Wilcoxon) | marginal A (n) | marginal B (n) |
|---|---|---|---|---|---|---|---|---|
| hybrid:fable-5.1 vs rules_adapt_ctx | 87 | 19 | 25 | 345 / 216 | -6 / +0 / +6 | 0.00784 | 345 (87) | 311 (108) |
| hybrid:fable-5.1 vs rules_adapt | 87 | 16 | 26 | 345 / 214 | -6 / +0 / +6 | 0.00264 | 345 (87) | 311 (108) |
| hybrid:fable-5.1 vs rules_cal | 83 | 37 | 38 | 311 / 202 | -18 / +0 / +18 | 0.0677 | 345 (87) | 218 (101) |
| hybrid:fable-5.1 vs hybrid | 86 | 13 | 27 | 345 / 214 | -6 / +0 / +6 | 0.000736 | 345 (87) | 305 (106) |
| hybrid:fable-5.1 vs llm_c2:fable-5.1 | 87 | 18 | 55 | 345 / 208 | -18 / +12 / +48 | 5.57e-06 | 345 (87) | 208 (105) |

## Aciertos sobre la estación averiada

Actúa: al menos una reparación de la estación averiada. Específico (±w min): además, la misma política sin fallo no la reparó en ±w min. Por forma: actúa / específico (±120).

| Planificador | actúa | específico ±60 | específico ±120 | específico ±240 | step | intermittent | drift |
|---|---|---|---|---|---|---|---|
| rules_cal | 101/216 | 83/216 | 76/216 | 67/216 | 25 / 18 | 44 / 34 | 32 / 24 |
| rules_adapt | 108/216 | 81/216 | 76/216 | 60/216 | 29 / 18 | 44 / 35 | 35 / 23 |
| rules_adapt_ctx | 108/216 | 80/216 | 76/216 | 65/216 | 29 / 18 | 44 / 34 | 35 / 24 |
| rules_twin | 60/216 | 24/216 | 13/216 | 6/216 | 17 / 3 | 21 / 7 | 22 / 3 |
| llm_c1 | 90/216 | 49/216 | 41/216 | 32/216 | 24 / 11 | 35 / 18 | 31 / 12 |
| llm_c2 | 117/216 | 55/216 | 51/216 | 28/216 | 34 / 16 | 45 / 18 | 38 / 17 |
| hybrid | 106/216 | 82/216 | 78/216 | 64/216 | 28 / 19 | 43 / 35 | 35 / 24 |
| llm_c2:fable-5.1 | 105/216 | 85/216 | 81/216 | 71/216 | 26 / 20 | 44 / 35 | 35 / 26 |
| hybrid:fable-5.1 | 87/216 | 80/216 | 79/216 | 77/216 | 21 / 19 | 37 / 33 | 29 / 27 |

## Razones de los vetos del híbrido

Veto: llamada en la que al menos una estación elegible no recibe acción. Estricto: `burst|line-wide|line wide|common (upstream )?cause|systemic`. Amplio: `burst|line-wide|line wide|common|shared|simultaneous|many stations|all stations|systemic|cascade|upstream`. Insensible a mayúsculas.

| Planificador | llamadas | con veto | estricto | amplio | vetos de la estación averiada | de ellos, estricto |
|---|---|---|---|---|---|---|
| hybrid | 3711 | 567 | 0 (0.0%) | 0 (0.0%) | 17 | 0 |
| hybrid:fable-5.1 | 4348 | 2833 | 2587 (91.3%) | 2663 (94.0%) | 142 | 139 |

## Caché de respuestas

| Planificador | llamadas | servidas desde caché |
|---|---|---|
| hybrid | 3711 | 3342 (90%) |
| hybrid:fable-5.1 | 4348 | 3921 (90%) |
| llm_c1 | 29223 | 26936 (92%) |
| llm_c1:fable-5.1 | 33052 | 30566 (92%) |
| llm_c2 | 14282 | 13389 (94%) |
| llm_c2:fable-5.1 | 26933 | 24530 (91%) |
