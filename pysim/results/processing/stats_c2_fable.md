# Estadística pareada — A = `llm_c2:fable-5.1`

Diseño v2. Escenarios con fallo de las trazas reservadas (3 inicios cada uno), pareados por (traza, estación, forma, inicio); retraso en exceso dentro del horizonte tras el inicio. Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples dentro de cada tabla.

## Frente a cada planificador

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 216 | 69 | 92 | 0.0156 | 0.0626 | -0.22 | -0.065 | [-0.113, -0.021] |
| llm_c2:fable-5.1 vs rules_adapt | 216 | 78 | 83 | 0.727 | 1 | -0.03 | -0.028 | [-0.075, +0.017] |
| llm_c2:fable-5.1 vs rules_cal | 216 | 82 | 78 | 0.787 | 1 | +0.02 | +0.008 | [-0.028, +0.044] |
| llm_c2:fable-5.1 vs llm_c2 | 216 | 153 | 17 | 9.61e-22 | 4.81e-21 | +0.85 | +0.386 | [+0.307, +0.478] |
| llm_c2:fable-5.1 vs llm_c1:fable-5.1 | 216 | 54 | 107 | 0.0674 | 0.202 | -0.17 | +0.055 | [-0.062, +0.165] |

## Por subgrupo, frente a `rules_adapt_ctx`

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| fallo step | 72 | 24 | 27 | 0.555 | 0.555 | -0.10 | -0.029 | [-0.090, +0.026] |
| fallo intermittent | 72 | 23 | 33 | 0.193 | 0.386 | -0.20 | -0.058 | [-0.176, +0.049] |
| fallo drift | 72 | 22 | 32 | 0.0171 | 0.0512 | -0.37 | -0.107 | [-0.193, -0.027] |

Con y sin gemela (familia aparte):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| con gemela | 108 | 32 | 46 | 0.0937 | 0.134 | -0.22 | -0.068 | [-0.158, +0.015] |
| sin gemela | 108 | 37 | 46 | 0.067 | 0.134 | -0.23 | -0.064 | [-0.122, -0.014] |

Por traza (exploratorio; p Holm sobre las tres trazas):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| traza 100m-200m | 72 | 29 | 33 | 0.661 | 0.661 | -0.06 | -0.006 | [-0.042, +0.027] |
| traza 200m-300m | 72 | 21 | 26 | 0.177 | 0.354 | -0.23 | -0.097 | [-0.237, +0.014] |
| traza 500m-600m | 72 | 19 | 33 | 0.0245 | 0.0734 | -0.36 | -0.136 | [-0.262, -0.026] |

Por traza y forma (Δ recuperación agregada; A mejor / n):

| Traza | step | intermittent | drift |
|---|---|---|---|
| 100m-200m | +0.050 (13/24) | -0.057 (8/24) | -0.038 (8/24) |
| 200m-300m | -0.131 (6/24) | +0.073 (8/24) | -0.110 (7/24) |
| 500m-600m | -0.072 (5/24) | -0.125 (7/24) | -0.234 (7/24) |

## Latencia de la primera acción sobre la estación averiada

Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.

Latencia desde el inicio del fallo. Medianas marginales: sobre todos los escenarios en que cada uno actúa.

| Comparación | pares | A antes | B antes | mediana A / B en los pares (min) | diferencia: p10 / mediana / p75 | p (Wilcoxon) | marginal A (n) | marginal B (n) |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 100 | 48 | 38 | 218 / 226 | -42 / +0 / +12 | 0.313 | 208 (105) | 311 (108) |
| llm_c2:fable-5.1 vs rules_adapt | 100 | 47 | 40 | 218 / 217 | -30 / +0 / +12 | 0.43 | 208 (105) | 311 (108) |
| llm_c2:fable-5.1 vs rules_cal | 97 | 67 | 17 | 187 / 205 | -30 / -12 / +0 | 3.82e-05 | 208 (105) | 218 (101) |
| llm_c2:fable-5.1 vs llm_c2 | 102 | 17 | 78 | 228 / 219 | -108 / +12 / +42 | 0.000233 | 208 (105) | 281 (117) |
| llm_c2:fable-5.1 vs llm_c1:fable-5.1 | 19 | 15 | 4 | 187 / 408 | -876 / -174 / -12 | 0.00169 | 208 (105) | 408 (19) |

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
