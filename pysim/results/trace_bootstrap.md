# Incertidumbre con la traza como unidad de remuestreo

Diseño v2. Δ = recuperación agregada a 24 h (A) − ídem (B) en las trazas reservadas. «Exacto»: las 27 extracciones ordenadas de 3 trazas con reemplazo; se dan el mínimo, el máximo y la fracción con Δ ≤ 0. «Dos niveles»: trazas con reemplazo y luego escenarios dentro de cada traza, 10 000 remuestras, semilla 0, IC 95 % percentil. Con tres conglomerados ningún intervalo es fiable; el objetivo es mostrar cuánto se ensancha respecto del bootstrap estratificado de `stats.md`.

| A | B | Formas | Δ | exacto: mín – máx | exacto: P(Δ ≤ 0) | dos niveles: IC 95 % | sin 100m-200m | sin 200m-300m | sin 500m-600m |
|---|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 | rules_adapt_ctx | todas | +0.090 | -0.011 – +0.283 | 1/27 | [-0.016, +0.283] | +0.181 | +0.029 | +0.089 |
| llm_c2:fable-5.1 | rules_adapt_ctx | escalón | +0.055 | -0.057 – +0.297 | 4/27 | [-0.076, +0.295] | +0.150 | -0.012 | +0.056 |
| llm_c2:fable-5.1 | rules_adapt_ctx | intermitente | +0.229 | +0.073 – +0.629 | 0/27 | [+0.075, +0.630] | +0.414 | +0.157 | +0.196 |
| llm_c2:fable-5.1 | rules_adapt_ctx | deriva | +0.063 | -0.009 – +0.196 | 4/27 | [-0.054, +0.227] | +0.123 | +0.004 | +0.074 |
| hybrid:fable-5.1 | rules_adapt_ctx | todas | +0.051 | -0.077 – +0.327 | 7/27 | [-0.097, +0.321] | +0.165 | -0.038 | +0.060 |
| hybrid:fable-5.1 | rules_adapt_ctx | escalón | +0.007 | -0.128 – +0.381 | 11/27 | [-0.170, +0.360] | +0.076 | -0.097 | +0.071 |
| hybrid:fable-5.1 | rules_adapt_ctx | intermitente | +0.374 | +0.168 – +0.733 | 0/27 | [+0.147, +0.864] | +0.617 | +0.309 | +0.293 |
| hybrid:fable-5.1 | rules_adapt_ctx | deriva | -0.052 | -0.214 – +0.196 | 17/27 | [-0.261, +0.240] | +0.082 | -0.163 | -0.047 |
| hybrid | rules_adapt_ctx | todas | -0.019 | -0.044 – -0.007 | 27/27 | [-0.105, +0.069] | -0.027 | -0.022 | -0.009 |
| hybrid | rules_adapt_ctx | escalón | -0.101 | -0.232 – -0.001 | 27/27 | [-0.285, +0.045] | -0.185 | -0.097 | -0.038 |
| hybrid | rules_adapt_ctx | intermitente | +0.147 | +0.100 – +0.303 | 0/27 | [+0.017, +0.369] | +0.203 | +0.119 | +0.145 |
| hybrid | rules_adapt_ctx | deriva | -0.010 | -0.077 – +0.104 | 16/27 | [-0.163, +0.159] | +0.046 | -0.015 | -0.046 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | todas | -0.040 | -0.067 – +0.044 | 23/27 | [-0.111, +0.052] | -0.016 | -0.066 | -0.029 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | escalón | -0.048 | -0.181 – +0.085 | 20/27 | [-0.190, +0.088] | -0.074 | -0.085 | +0.015 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | intermitente | +0.145 | +0.095 – +0.253 | 0/27 | [+0.029, +0.355] | +0.203 | +0.152 | +0.097 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | deriva | -0.115 | -0.204 – +0.000 | 26/27 | [-0.253, +0.027] | -0.041 | -0.167 | -0.121 |
| llm_c2 | rules_adapt_ctx | todas | -0.132 | -0.413 – +0.127 | 20/27 | [-0.451, +0.116] | -0.363 | -0.077 | -0.019 |
| llm_c2 | rules_adapt_ctx | escalón | -0.137 | -0.492 – +0.091 | 23/27 | [-0.533, +0.081] | -0.332 | -0.039 | -0.096 |
| llm_c2 | rules_adapt_ctx | intermitente | -0.330 | -0.901 – +0.106 | 23/27 | [-1.091, +0.104] | -0.846 | -0.257 | -0.079 |
| llm_c2 | rules_adapt_ctx | deriva | -0.035 | -0.391 – +0.175 | 17/27 | [-0.381, +0.173] | -0.209 | -0.020 | +0.076 |
