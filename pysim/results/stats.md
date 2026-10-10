# Estadística pareada — A = `llm_c2:fable-5.1`

Escenarios con fallo de las trazas reservadas, pareados por (traza, estación, forma del fallo). Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples dentro de cada tabla.

## Frente a cada planificador

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 72 | 50 | 22 | 0.00141 | 0.00141 | +0.43 | +0.043 | [-0.013, +0.104] |
| llm_c2:fable-5.1 vs rules_adapt | 72 | 53 | 19 | 8.96e-05 | 0.000179 | +0.53 | +0.062 | [+0.006, +0.125] |
| llm_c2:fable-5.1 vs rules_cal | 72 | 63 | 9 | 2.57e-06 | 7.7e-06 | +0.64 | +0.132 | [+0.087, +0.179] |
| llm_c2:fable-5.1 vs llm_c2 | 72 | 69 | 3 | 3.67e-13 | 1.83e-12 | +0.99 | +0.378 | [+0.309, +0.465] |
| llm_c2:fable-5.1 vs llm_c1:fable-5.1 | 72 | 55 | 17 | 3.8e-08 | 1.52e-07 | +0.75 | +0.581 | [+0.508, +0.637] |

## Por subgrupo, frente a `rules_adapt_ctx`

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| fallo step | 24 | 14 | 10 | 0.345 | 0.458 | +0.23 | +0.012 | [-0.064, +0.097] |
| fallo intermittent | 24 | 21 | 3 | 0.000963 | 0.00289 | +0.73 | +0.212 | [+0.000, +0.417] |
| fallo drift | 24 | 15 | 9 | 0.229 | 0.458 | +0.29 | +0.016 | [-0.058, +0.096] |

Con y sin gemela (familia aparte):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| con gemela | 36 | 28 | 8 | 0.00424 | 0.00848 | +0.55 | +0.059 | [-0.005, +0.136] |
| sin gemela | 36 | 22 | 14 | 0.0784 | 0.0784 | +0.34 | +0.034 | [-0.043, +0.119] |

Por traza (exploratorio, sin ajuste):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| traza 100m-200m | 24 | 16 | 8 | 0.0014 | 0.0042 | +0.71 | +0.087 | [+0.031, +0.170] |
| traza 200m-300m | 24 | 14 | 10 | 0.753 | 0.753 | +0.07 | -0.015 | [-0.198, +0.168] |
| traza 500m-600m | 24 | 20 | 4 | 0.00722 | 0.0144 | +0.63 | +0.036 | [-0.017, +0.085] |

Por traza y forma (Δ recuperación agregada; A mejor / n):

| Traza | step | intermittent | drift |
|---|---|---|---|
| 100m-200m | +0.045 (5/8) | +0.418 (7/8) | +0.013 (4/8) |
| 200m-300m | -0.035 (3/8) | -0.068 (6/8) | +0.022 (5/8) |
| 500m-600m | +0.009 (6/8) | +0.184 (8/8) | +0.012 (6/8) |

## Latencia de la primera acción sobre la estación averiada

Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.

Latencia desde el inicio del fallo. Medianas marginales: sobre todos los escenarios en que cada uno actúa.

| Comparación | pares | A antes | B antes | mediana A / B en los pares (min) | diferencia: p10 / mediana / p75 | p (Wilcoxon) | marginal A (n) | marginal B (n) |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 57 | 28 | 25 | 402 / 3,048 | -3,150 / +0 / +66 | 0.172 | 402 (57) | 3,090 (72) |
| llm_c2:fable-5.1 vs rules_adapt | 57 | 28 | 25 | 402 / 3,048 | -3,150 / +0 / +66 | 0.172 | 402 (57) | 3,090 (72) |
| llm_c2:fable-5.1 vs rules_cal | 57 | 24 | 31 | 402 / 372 | -66 / +18 / +42 | 0.0872 | 402 (57) | 222 (72) |
| llm_c2:fable-5.1 vs llm_c2 | 57 | 6 | 46 | 402 / 330 | -12 / +96 / +114 | 2.46e-09 | 402 (57) | 360 (72) |
| llm_c2:fable-5.1 vs llm_c1:fable-5.1 | 0 | 0 | 0 | nan / nan | +nan / +nan / +nan | nan | 402 (57) | nan (0) |

## Aciertos sobre la estación averiada

Actúa: al menos una reparación de la estación averiada. Específico (±w min): además, la misma política sin fallo no la reparó en ±w min. Por forma: actúa / específico (±120).

| Planificador | actúa | específico ±60 | específico ±120 | específico ±240 | step | intermittent | drift |
|---|---|---|---|---|---|---|---|
| rules_cal | 72/72 | 34/72 | 32/72 | 32/72 | 24 / 11 | 24 / 10 | 24 / 11 |
| rules_adapt | 72/72 | 57/72 | 57/72 | 57/72 | 24 / 19 | 24 / 19 | 24 / 19 |
| rules_adapt_ctx | 72/72 | 57/72 | 57/72 | 57/72 | 24 / 19 | 24 / 19 | 24 / 19 |
| rules_twin | 36/72 | 9/72 | 9/72 | 8/72 | 12 / 3 | 12 / 3 | 12 / 3 |
| llm_c1 | 57/72 | 22/72 | 22/72 | 21/72 | 19 / 7 | 19 / 8 | 19 / 7 |
| llm_c2 | 72/72 | 40/72 | 31/72 | 28/72 | 24 / 11 | 24 / 10 | 24 / 10 |
| hybrid | 59/72 | 50/72 | 50/72 | 50/72 | 21 / 18 | 18 / 15 | 20 / 17 |
| llm_c2:fable-5.1 | 57/72 | 44/72 | 39/72 | 37/72 | 20 / 14 | 18 / 12 | 19 / 13 |
| hybrid:fable-5.1 | 34/72 | 34/72 | 34/72 | 33/72 | 13 / 13 | 9 / 9 | 12 / 12 |

## Razones de los vetos del híbrido

Veto: llamada en la que al menos una estación elegible no recibe acción. Estricto: `burst|line-wide|line wide|common (upstream )?cause|systemic`. Amplio: `burst|line-wide|line wide|common|shared|simultaneous|many stations|all stations|systemic|cascade|upstream`. Insensible a mayúsculas.

| Planificador | llamadas | con veto | estricto | amplio | vetos de la estación averiada | de ellos, estricto |
|---|---|---|---|---|---|---|
| hybrid | 1215 | 519 | 7 (1.3%) | 173 (33.3%) | 50 | 2 |
| hybrid:fable-5.1 | 1437 | 1256 | 1233 (98.2%) | 1237 (98.5%) | 167 | 167 |

## Caché de respuestas

| Planificador | llamadas | servidas desde caché |
|---|---|---|
| hybrid | 1215 | 816 (67%) |
| hybrid:fable-5.1 | 1437 | 895 (62%) |
| llm_c1 | 7326 | 6381 (87%) |
| llm_c1:fable-5.1 | 8394 | 7121 (85%) |
| llm_c2 | 5224 | 4615 (88%) |
| llm_c2:fable-5.1 | 7869 | 6147 (78%) |
