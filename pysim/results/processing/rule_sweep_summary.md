# Experimentos solo con reglas (sin LLM)

Diseño v2: 8 estaciones × 3 formas × 3 inicios, fallo ×3, modelo de efectos central. Recuperación agregada a 24 h = 1 − Σ exceso en [t0, t0+24 h) / Σ ídem sin acción; entre paréntesis, escenarios con beneficio neto. Desarrollo = `test_cases_0-100m.td`; reservadas = las otras tres.

Comprobación: la configuración por defecto reproduce `llm_sweep_rows.csv` — rules_adapt: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios; rules_adapt_ctx: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios; rules_cal: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios.

## A. Planificador ingenuo con el mismo tiempo de espera que el resto

| Tiempo de espera | 4 trazas | reservadas | mant. falsos / escenario | coste falsas alarmas (min-pieza/h, 4 trazas) |
|---|---|---|---|---|
| 120 min | -0.277 (56/288) | -0.551 (32/216) | 28.4 | 433 |
| 240 min | -0.029 (84/288) | -0.277 (46/216) | 21.2 | 349 |

## B. `rules_adapt` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.856 | +0.167 (65/216) | +0.227 | -0.268 | +0.304 | 108/216 / 76/216 / 311 | 98 |
| elegida en desarrollo (todas las formas) | `w=240 a=0.001 h=1440` | +0.903 | +0.139 (64/216) | +0.201 | -0.298 | +0.274 | 109/216 / 77/216 / 329 | 96 |
| óptimo en reservadas (cota superior) | `w=180 a=0.0001 h=720` | +0.797 | +0.247 (70/216) | +0.312 | +0.005 | +0.291 | 97/216 / 81/216 / 224 | 64 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=180 a=0.0001 h=2880` | +0.922 | +0.236 | `w=180 a=0.0001 h=720` | +0.312 |
| intermittent | `w=240 a=0.001 h=1440` | +0.791 | -0.298 | `w=180 a=0.0001 h=720` | +0.005 |
| drift | `w=240 a=0.001 h=1440` | +0.931 | +0.274 | `w=120 a=0.0001 h=1440` | +0.334 |

En la rejilla, recuperación en reservadas: mín. -0.031, mediana +0.113, máx. +0.247. Solo intermitente: mín. -0.610, mediana -0.309, máx. +0.005.

## B. `rules_adapt_ctx` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.842 | +0.204 (70/216) | +0.258 | -0.195 | +0.332 | 108/216 / 76/216 / 311 | 89 |
| elegida en desarrollo (todas las formas) | `w=240 a=0.001 h=1440` | +0.900 | +0.183 (69/216) | +0.236 | -0.222 | +0.313 | 110/216 / 80/216 / 329 | 86 |
| óptimo en reservadas (cota superior) | `w=180 a=0.0001 h=720` | +0.809 | +0.281 (72/216) | +0.331 | +0.071 | +0.326 | 96/216 / 82/216 / 224 | 60 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=180 a=0.0001 h=2880` | +0.919 | +0.272 | `w=180 a=0.0001 h=720` | +0.331 |
| intermittent | `w=240 a=0.001 h=1440` | +0.790 | -0.222 | `w=180 a=0.0001 h=720` | +0.071 |
| drift | `w=240 a=0.001 h=1440` | +0.925 | +0.313 | `w=120 a=0.0001 h=1440` | +0.382 |

En la rejilla, recuperación en reservadas: mín. +0.041, mediana +0.174, máx. +0.281. Solo intermitente: mín. -0.520, mediana -0.222, máx. +0.071.

## B. `rules_cal` — 15 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001` | +0.772 | +0.131 (65/216) | +0.231 | -0.292 | +0.220 | 101/216 / 76/216 / 218 | 107 |
| elegida en desarrollo (todas las formas) | `w=240 a=0.0001` | +0.832 | +0.266 (72/216) | +0.318 | +0.047 | +0.314 | 96/216 / 85/216 / 223 | 69 |
| óptimo en reservadas (cota superior) | `w=360 a=0.0001` | +0.787 | +0.273 (74/216) | +0.324 | +0.034 | +0.329 | 95/216 / 83/216 / 229 | 65 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=240 a=0.0001` | +0.872 | +0.318 | `w=360 a=0.0001` | +0.324 |
| intermittent | `w=240 a=0.0001` | +0.650 | +0.047 | `w=240 a=0.0001` | +0.047 |
| drift | `w=180 a=0.0001` | +0.862 | +0.292 | `w=360 a=0.0001` | +0.329 |

En la rejilla, recuperación en reservadas: mín. +0.001, mediana +0.150, máx. +0.273. Solo intermitente: mín. -0.580, mediana -0.210, máx. +0.047.

## Comparación con los planificadores LLM (reservadas, mismos 72 escenarios)

| Planificador | todas | escalón | intermitente | deriva |
|---|---|---|---|---|
| rules_adapt_ctx por defecto | +0.204 | +0.258 | -0.195 | +0.332 |
| rules_adapt elegida en desarrollo `w=240 a=0.001 h=1440` | +0.139 | +0.201 | -0.298 | +0.274 |
| rules_adapt especializada en intermitente (desarrollo) `w=240 a=0.001 h=1440` | +0.139 | +0.201 | -0.298 | +0.274 |
| rules_adapt_ctx elegida en desarrollo `w=240 a=0.001 h=1440` | +0.183 | +0.236 | -0.222 | +0.313 |
| rules_adapt_ctx especializada en intermitente (desarrollo) `w=240 a=0.001 h=1440` | +0.183 | +0.236 | -0.222 | +0.313 |
| llm_c2:fable-5.1 | +0.358 | +0.537 | +0.001 | +0.243 |

## C2 con Fable 5.1 frente a reglas reajustadas (emparejado)

Δ = recuperación(Fable) − recuperación(regla), IC 95 % bootstrap estratificado por traza (10 000, semilla 0, como `stats.py`); Wilcoxon sobre el exceso por escenario, sin ajuste.

| Regla | Configuración | Formas | Δ | IC 95 % | Fable mejor en | p | r |
|---|---|---|---|---|---|---|---|
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | todas | +0.091 | [+0.004, +0.219] | 6/12 | 0.160 | +0.53 |
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.109 | [-0.064, +0.415] | 2/3 | 0.500 | +0.67 |
| rules_adapt | elegida en desarrollo `w=240 a=0.001 h=1440` | todas | +0.055 | [-0.061, +0.186] | 7/12 | 0.375 | +0.35 |
| rules_adapt | elegida en desarrollo `w=240 a=0.001 h=1440` | intermitente | -0.051 | [-0.239, +0.405] | 1/3 | 0.750 | -0.33 |
| rules_adapt | óptimo en reservadas `w=180 a=0.0001 h=720` | todas | -0.068 | [-0.161, +0.029] | 3/12 | 0.492 | -0.27 |
| rules_adapt | óptimo en reservadas `w=180 a=0.0001 h=720` | intermitente | -0.130 | [-0.312, +0.216] | 1/3 | 0.750 | -0.33 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | todas | +0.073 | [-0.019, +0.190] | 6/12 | 0.232 | +0.45 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.004 | [-0.144, +0.369] | 1/3 | 1.000 | +0.00 |
| rules_adapt_ctx | elegida en desarrollo `w=240 a=0.001 h=1440` | todas | +0.026 | [-0.087, +0.154] | 6/12 | 0.770 | +0.13 |
| rules_adapt_ctx | elegida en desarrollo `w=240 a=0.001 h=1440` | intermitente | -0.059 | [-0.218, +0.387] | 1/3 | 0.750 | -0.33 |
| rules_adapt_ctx | óptimo en reservadas `w=180 a=0.0001 h=720` | todas | -0.128 | [-0.221, -0.037] | 3/12 | 0.037 | -0.75 |
| rules_adapt_ctx | óptimo en reservadas `w=180 a=0.0001 h=720` | intermitente | -0.210 | [-0.352, +0.194] | 1/3 | 0.500 | -0.67 |
