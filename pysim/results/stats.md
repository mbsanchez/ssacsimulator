# Estadística pareada — A = `llm_c2:fable-5.1`

Diseño v2. Escenarios con fallo de las trazas reservadas (3 inicios cada uno), pareados por (traza, estación, forma, inicio); retraso en exceso dentro del horizonte tras el inicio. Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples dentro de cada tabla.

## Frente a cada planificador

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 216 | 100 | 37 | 1.1e-07 | 2.19e-07 | +0.52 | +0.090 | [+0.036, +0.145] |
| llm_c2:fable-5.1 vs rules_adapt | 216 | 107 | 30 | 5.48e-08 | 2.19e-07 | +0.54 | +0.106 | [+0.046, +0.169] |
| llm_c2:fable-5.1 vs rules_cal | 216 | 78 | 41 | 0.000124 | 0.000124 | +0.41 | +0.106 | [+0.052, +0.166] |
| llm_c2:fable-5.1 vs llm_c2 | 216 | 103 | 54 | 6.51e-08 | 2.19e-07 | +0.50 | +0.222 | [+0.139, +0.314] |

## Por subgrupo, frente a `rules_adapt_ctx`

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| fallo step | 72 | 28 | 16 | 0.0405 | 0.0405 | +0.35 | +0.055 | [-0.027, +0.136] |
| fallo intermittent | 72 | 36 | 8 | 2.13e-06 | 6.4e-06 | +0.82 | +0.229 | [+0.141, +0.336] |
| fallo drift | 72 | 36 | 13 | 0.00613 | 0.0123 | +0.45 | +0.063 | [-0.026, +0.159] |

Con y sin gemela (familia aparte):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| con gemela | 108 | 52 | 13 | 4.51e-06 | 9.03e-06 | +0.65 | +0.180 | [+0.106, +0.266] |
| sin gemela | 108 | 48 | 24 | 0.00406 | 0.00406 | +0.39 | +0.036 | [-0.033, +0.105] |

Por traza (exploratorio, sin ajuste):

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|---|
| traza 100m-200m | 72 | 36 | 9 | 0.0109 | 0.0218 | +0.43 | -0.011 | [-0.082, +0.054] |
| traza 200m-300m | 72 | 31 | 8 | 2.93e-05 | 8.78e-05 | +0.77 | +0.283 | [+0.147, +0.495] |
| traza 500m-600m | 72 | 33 | 20 | 0.0206 | 0.0218 | +0.37 | +0.094 | [+0.001, +0.206] |

Por traza y forma (Δ recuperación agregada; A mejor / n):

| Traza | step | intermittent | drift |
|---|---|---|---|
| 100m-200m | -0.057 (9/24) | +0.073 (11/24) | -0.009 (16/24) |
| 200m-300m | +0.297 (10/24) | +0.629 (9/24) | +0.196 (12/24) |
| 500m-600m | +0.052 (9/24) | +0.306 (16/24) | +0.029 (8/24) |

## Latencia de la primera acción sobre la estación averiada

Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.

Latencia desde el inicio del fallo. Medianas marginales: sobre todos los escenarios en que cada uno actúa.

| Comparación | pares | A antes | B antes | mediana A / B en los pares (min) | diferencia: p10 / mediana / p75 | p (Wilcoxon) | marginal A (n) | marginal B (n) |
|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 53 | 14 | 33 | 730 / 631 | -24 / +6 / +72 | 0.000906 | 730 (54) | 784 (75) |
| llm_c2:fable-5.1 vs rules_adapt | 54 | 15 | 32 | 730 / 725 | -24 / +6 / +72 | 0.00329 | 730 (54) | 800 (77) |
| llm_c2:fable-5.1 vs rules_cal | 51 | 25 | 19 | 730 / 790 | -66 / +0 / +36 | 0.666 | 730 (54) | 826 (62) |
| llm_c2:fable-5.1 vs llm_c2 | 53 | 7 | 41 | 730 / 619 | -6 / +30 / +108 | 1.49e-06 | 730 (54) | 688 (104) |

## Aciertos sobre la estación averiada

Actúa: al menos una reparación de la estación averiada. Específico (±w min): además, la misma política sin fallo no la reparó en ±w min. Por forma: actúa / específico (±120).

| Planificador | actúa | específico ±60 | específico ±120 | específico ±240 | step | intermittent | drift |
|---|---|---|---|---|---|---|---|
| rules_cal | 62/216 | 43/216 | 42/216 | 42/216 | 19 / 11 | 19 / 13 | 24 / 18 |
| rules_adapt | 77/216 | 52/216 | 52/216 | 52/216 | 26 / 19 | 23 / 13 | 28 / 20 |
| rules_adapt_ctx | 75/216 | 50/216 | 50/216 | 50/216 | 26 / 19 | 22 / 12 | 27 / 19 |
| rules_twin | 47/216 | 28/216 | 26/216 | 21/216 | 14 / 9 | 14 / 4 | 19 / 13 |
| llm_c1 | 49/216 | 30/216 | 25/216 | 23/216 | 14 / 7 | 14 / 5 | 21 / 13 |
| llm_c2 | 104/216 | 64/216 | 58/216 | 53/216 | 33 / 20 | 34 / 17 | 37 / 21 |
| hybrid | 51/216 | 39/216 | 38/216 | 38/216 | 16 / 14 | 14 / 7 | 21 / 17 |
| llm_c2:fable-5.1 | 54/216 | 40/216 | 38/216 | 37/216 | 18 / 12 | 17 / 10 | 19 / 16 |
| hybrid:fable-5.1 | 24/216 | 24/216 | 24/216 | 23/216 | 12 / 12 | 6 / 6 | 6 / 6 |

## Razones de los vetos del híbrido

Veto: llamada en la que al menos una estación elegible no recibe acción. Estricto: `burst|line-wide|line wide|common (upstream )?cause|systemic`. Amplio: `burst|line-wide|line wide|common|shared|simultaneous|many stations|all stations|systemic|cascade|upstream`. Insensible a mayúsculas.

| Planificador | llamadas | con veto | estricto | amplio | vetos de la estación averiada | de ellos, estricto |
|---|---|---|---|---|---|---|
| hybrid | 1740 | 902 | 4 (0.4%) | 385 (42.7%) | 76 | 0 |
| hybrid:fable-5.1 | 1812 | 1607 | 1596 (99.3%) | 1596 (99.3%) | 148 | 148 |

## Caché de respuestas

| Planificador | llamadas | servidas desde caché |
|---|---|---|
| hybrid | 1740 | 1583 (91%) |
| hybrid:fable-5.1 | 1812 | 1673 (92%) |
| llm_c1 | 15718 | 15316 (97%) |
| llm_c2 | 12676 | 12426 (98%) |
| llm_c2:fable-5.1 | 17333 | 16804 (97%) |
