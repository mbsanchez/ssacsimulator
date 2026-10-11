# Incertidumbre con la traza como unidad de remuestreo

Δ = recuperación agregada(A) − recuperación agregada(B) en las trazas reservadas. «Exacto»: las 27 extracciones ordenadas de 3 trazas con reemplazo; se dan el mínimo, el máximo y la fracción con Δ ≤ 0. «Dos niveles»: trazas con reemplazo y luego escenarios dentro de cada traza, 10 000 remuestras, semilla 0, IC 95 % percentil. Con tres conglomerados ningún intervalo es fiable; el objetivo es mostrar cuánto se ensancha respecto del bootstrap estratificado de `stats.md`.

| A | B | Formas | Δ | exacto: mín – máx | exacto: P(Δ ≤ 0) | dos niveles: IC 95 % | sin 100m-200m | sin 200m-300m | sin 500m-600m |
|---|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 | rules_adapt_ctx | todas | +0.043 | -0.015 – +0.087 | 1/27 | [-0.052, +0.109] | +0.011 | +0.065 | +0.045 |
| llm_c2:fable-5.1 | rules_adapt_ctx | escalón | +0.012 | -0.035 – +0.045 | 10/27 | [-0.104, +0.096] | -0.012 | +0.030 | +0.013 |
| llm_c2:fable-5.1 | rules_adapt_ctx | intermitente | +0.212 | -0.068 – +0.418 | 1/27 | [-0.142, +0.470] | +0.064 | +0.319 | +0.224 |
| llm_c2:fable-5.1 | rules_adapt_ctx | deriva | +0.016 | +0.012 – +0.022 | 0/27 | [-0.068, +0.110] | +0.017 | +0.013 | +0.017 |
| llm_c2:fable-5.1 | rules_adapt | todas | +0.062 | +0.041 – +0.086 | 0/27 | [-0.011, +0.127] | +0.044 | +0.070 | +0.068 |
| llm_c2:fable-5.1 | rules_adapt | escalón | +0.026 | +0.008 – +0.045 | 0/27 | [-0.073, +0.117] | +0.013 | +0.033 | +0.030 |
| llm_c2:fable-5.1 | rules_adapt | intermitente | +0.255 | +0.064 – +0.417 | 0/27 | [-0.055, +0.493] | +0.139 | +0.328 | +0.276 |
| llm_c2:fable-5.1 | rules_adapt | deriva | +0.031 | +0.013 – +0.067 | 0/27 | [-0.043, +0.139] | +0.044 | +0.017 | +0.035 |
| llm_c2 | rules_adapt_ctx | todas | -0.335 | -0.562 – -0.202 | 27/27 | [-0.570, -0.204] | -0.430 | -0.246 | -0.348 |
| llm_c2 | rules_adapt_ctx | escalón | -0.270 | -0.485 – -0.160 | 27/27 | [-0.515, -0.158] | -0.350 | -0.187 | -0.290 |
| llm_c2 | rules_adapt_ctx | intermitente | -0.672 | -1.243 – -0.259 | 27/27 | [-1.270, -0.245] | -0.967 | -0.453 | -0.651 |
| llm_c2 | rules_adapt_ctx | deriva | -0.286 | -0.410 – -0.228 | 27/27 | [-0.457, -0.212] | -0.326 | -0.236 | -0.303 |
| hybrid:fable-5.1 | rules_adapt_ctx | todas | -0.296 | -0.542 – -0.093 | 27/27 | [-0.540, -0.037] | -0.120 | -0.353 | -0.383 |
| hybrid:fable-5.1 | rules_adapt_ctx | escalón | -0.348 | -0.537 – -0.152 | 27/27 | [-0.600, -0.085] | -0.212 | -0.376 | -0.433 |
| hybrid:fable-5.1 | rules_adapt_ctx | intermitente | +0.147 | -0.070 – +0.338 | 1/27 | [-0.145, +0.508] | +0.302 | +0.074 | +0.093 |
| hybrid:fable-5.1 | rules_adapt_ctx | deriva | -0.397 | -0.718 – -0.159 | 27/27 | [-0.724, -0.035] | -0.171 | -0.483 | -0.498 |
