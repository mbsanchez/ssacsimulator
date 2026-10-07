# Estadística pareada — A = `llm_c2:fable-5.1`

Escenarios con fallo de las trazas reservadas, pareados por (traza, estación, forma del fallo). Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples dentro de cada tabla.

## Frente a cada planificador

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 72 | 50 | 22 | 0.00141 | 0.00281 | +0.043 | [-0.013, +0.104] |
| llm_c2:fable-5.1 vs rules_adapt | 72 | 53 | 19 | 8.96e-05 | 0.000269 | +0.062 | [+0.006, +0.125] |
| llm_c2:fable-5.1 vs rules_cal | 72 | 63 | 9 | 2.57e-06 | 1.03e-05 | +0.132 | [+0.087, +0.179] |
| llm_c2:fable-5.1 vs llm_c2 | 72 | 69 | 3 | 3.67e-13 | 1.83e-12 | +0.378 | [+0.309, +0.465] |
| llm_c2:fable-5.1 vs hybrid:fable-5.1 | 72 | 38 | 34 | 0.00352 | 0.00352 | +0.338 | [+0.228, +0.444] |

## Por subgrupo, frente a `rules_adapt_ctx`

| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | Δ recuperación agregada | IC 95% |
|---|---|---|---|---|---|---|---|
| fallo step | 24 | 14 | 10 | 0.345 | 0.458 | +0.012 | [-0.064, +0.097] |
| fallo intermittent | 24 | 21 | 3 | 0.000963 | 0.00481 | +0.212 | [+0.000, +0.417] |
| fallo drift | 24 | 15 | 9 | 0.229 | 0.458 | +0.016 | [-0.058, +0.096] |
| con gemela | 36 | 28 | 8 | 0.00424 | 0.017 | +0.059 | [-0.005, +0.136] |
| sin gemela | 36 | 22 | 14 | 0.0784 | 0.235 | +0.034 | [-0.043, +0.119] |

## Latencia de la primera acción sobre la estación averiada

Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.

| Comparación | pares | A antes | B antes | mediana de la diferencia (min) | p (Wilcoxon) |
|---|---|---|---|---|---|
| llm_c2:fable-5.1 vs rules_adapt_ctx | 57 | 28 | 25 | +0 | 0.172 |
| llm_c2:fable-5.1 vs rules_adapt | 57 | 28 | 25 | +0 | 0.172 |
| llm_c2:fable-5.1 vs rules_cal | 57 | 24 | 31 | +18 | 0.0872 |
| llm_c2:fable-5.1 vs llm_c2 | 57 | 6 | 46 | +96 | 2.46e-09 |
| llm_c2:fable-5.1 vs hybrid:fable-5.1 | 34 | 34 | 0 | -1434 | 3.5e-07 |
