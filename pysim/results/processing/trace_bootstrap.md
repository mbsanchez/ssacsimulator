# Incertidumbre con la traza como unidad de remuestreo

Diseño v2. Δ = recuperación agregada a 24 h (A) − ídem (B) en las trazas reservadas. «Exacto»: las 27 extracciones ordenadas de 3 trazas con reemplazo; se dan el mínimo, el máximo y la fracción con Δ ≤ 0. «Dos niveles»: trazas con reemplazo y luego escenarios dentro de cada traza, 10 000 remuestras, semilla 0, IC 95 % percentil. Con tres conglomerados ningún intervalo es fiable; el objetivo es mostrar cuánto se ensancha respecto del bootstrap estratificado de `stats.md`.

| A | B | Formas | Δ | exacto: mín – máx | exacto: P(Δ ≤ 0) | dos niveles: IC 95 % | sin 100m-200m | sin 200m-300m | sin 500m-600m |
|---|---|---|---|---|---|---|---|---|---|
| llm_c2:fable-5.1 | rules_adapt_ctx | todas | -0.065 | -0.136 – -0.006 | 27/27 | [-0.171, -0.003] | -0.118 | -0.055 | -0.037 |
| llm_c2:fable-5.1 | rules_adapt_ctx | escalón | -0.029 | -0.131 – +0.050 | 20/27 | [-0.173, +0.052] | -0.096 | -0.000 | -0.008 |
| llm_c2:fable-5.1 | rules_adapt_ctx | intermitente | -0.058 | -0.125 – +0.073 | 26/27 | [-0.204, +0.121] | -0.059 | -0.081 | -0.028 |
| llm_c2:fable-5.1 | rules_adapt_ctx | deriva | -0.107 | -0.234 – -0.038 | 27/27 | [-0.272, -0.023] | -0.164 | -0.105 | -0.067 |
| hybrid:fable-5.1 | rules_adapt_ctx | todas | +0.208 | +0.150 – +0.233 | 0/27 | [+0.105, +0.278] | +0.186 | +0.227 | +0.205 |
| hybrid:fable-5.1 | rules_adapt_ctx | escalón | +0.093 | -0.127 – +0.169 | 4/27 | [-0.135, +0.215] | +0.050 | +0.153 | +0.056 |
| hybrid:fable-5.1 | rules_adapt_ctx | intermitente | +0.487 | +0.356 – +1.121 | 0/27 | [+0.290, +1.070] | +0.642 | +0.373 | +0.525 |
| hybrid:fable-5.1 | rules_adapt_ctx | deriva | +0.200 | +0.130 – +0.262 | 0/27 | [+0.092, +0.285] | +0.149 | +0.232 | +0.209 |
| hybrid | rules_adapt_ctx | todas | +0.085 | +0.049 – +0.130 | 0/27 | [+0.048, +0.130] | +0.086 | +0.070 | +0.099 |
| hybrid | rules_adapt_ctx | escalón | +0.059 | +0.019 – +0.108 | 0/27 | [+0.019, +0.110] | +0.055 | +0.045 | +0.078 |
| hybrid | rules_adapt_ctx | intermitente | +0.168 | +0.112 – +0.339 | 0/27 | [+0.098, +0.325] | +0.187 | +0.137 | +0.193 |
| hybrid | rules_adapt_ctx | deriva | +0.074 | +0.053 – +0.099 | 0/27 | [+0.036, +0.112] | +0.079 | +0.063 | +0.081 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | todas | +0.274 | +0.240 – +0.353 | 0/27 | [+0.178, +0.396] | +0.304 | +0.282 | +0.242 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | escalón | +0.121 | +0.004 – +0.241 | 0/27 | [-0.065, +0.300] | +0.146 | +0.154 | +0.064 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | intermitente | +0.545 | +0.413 – +1.048 | 0/27 | [+0.359, +1.065] | +0.701 | +0.454 | +0.553 |
| hybrid:fable-5.1 | llm_c2:fable-5.1 | deriva | +0.307 | +0.241 – +0.407 | 0/27 | [+0.212, +0.447] | +0.313 | +0.337 | +0.276 |
| llm_c2 | rules_adapt_ctx | todas | -0.451 | -0.594 – -0.372 | 27/27 | [-0.628, -0.342] | -0.474 | -0.406 | -0.483 |
| llm_c2 | rules_adapt_ctx | escalón | -0.311 | -0.525 – -0.202 | 27/27 | [-0.592, -0.168] | -0.331 | -0.252 | -0.364 |
| llm_c2 | rules_adapt_ctx | intermitente | -0.862 | -1.287 – -0.764 | 27/27 | [-1.436, -0.636] | -0.979 | -0.786 | -0.879 |
| llm_c2 | rules_adapt_ctx | deriva | -0.407 | -0.486 – -0.345 | 27/27 | [-0.559, -0.299] | -0.425 | -0.372 | -0.427 |
