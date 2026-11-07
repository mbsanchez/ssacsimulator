# Experimentos solo con reglas (sin LLM)

Escenarios de `llm_sweep.py`: 8 estaciones × 3 formas, fallo ×3 desde el minuto 600, modelo de efectos central. Recuperación agregada = 1 − Σ exceso / Σ exceso sin acción; entre paréntesis, escenarios con beneficio neto. Desarrollo = `test_cases_0-100m.td`; reservadas = las otras tres.

Comprobación: la configuración por defecto reproduce `llm_sweep_rows.csv` — rules_adapt: máx. |Δ exceso| = 0.000 min-pieza en 72 escenarios; rules_adapt_ctx: máx. |Δ exceso| = 0.000 min-pieza en 72 escenarios; rules_cal: máx. |Δ exceso| = 0.000 min-pieza en 72 escenarios.

## A. Planificador ingenuo con el mismo tiempo de espera que el resto

| Tiempo de espera | 4 trazas | reservadas | mant. falsos / escenario | coste falsas alarmas (min-pieza/h, 4 trazas) |
|---|---|---|---|---|
| 120 min | -0.106 (37/96) | -0.345 (18/72) | 122.5 | 342 |
| 240 min | +0.174 (53/96) | +0.016 (32/72) | 86.5 | 255 |

## B. `rules_adapt` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.662 | +0.519 (52/72) | +0.618 | -0.064 | +0.620 | 72/72 / 57/72 / 3,090 | 67 |
| elegida en desarrollo (todas las formas) | `w=60 a=0.01 h=1440` | +0.812 | +0.539 (52/72) | +0.616 | +0.069 | +0.623 | 72/72 / 48/72 / 384 | 78 |
| óptimo en reservadas (cota superior) | `w=60 a=0.01 h=720` | +0.812 | +0.551 (52/72) | +0.625 | +0.096 | +0.632 | 72/72 / 48/72 / 384 | 73 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=60 a=0.0001 h=1440` | +0.832 | +0.546 | `w=60 a=0.01 h=720` | +0.625 |
| intermittent | `w=60 a=0.01 h=1440` | +0.630 | +0.069 | `w=240 a=0.0001 h=720` | +0.127 |
| drift | `w=60 a=0.0001 h=1440` | +0.902 | +0.544 | `w=60 a=0.01 h=720` | +0.632 |

En la rejilla, recuperación en reservadas: mín. +0.377, mediana +0.491, máx. +0.551. Solo intermitente: mín. -0.145, mediana +0.016, máx. +0.127.

## B. `rules_adapt_ctx` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.674 | +0.538 (53/72) | +0.632 | -0.021 | +0.635 | 72/72 / 57/72 / 3,090 | 64 |
| elegida en desarrollo (todas las formas) | `w=60 a=0.01 h=1440` | +0.829 | +0.543 (52/72) | +0.620 | +0.063 | +0.631 | 72/72 / 54/72 / 3,024 | 73 |
| óptimo en reservadas (cota superior) | `w=120 a=0.0001 h=1440` | +0.632 | +0.564 (55/72) | +0.642 | +0.083 | +0.651 | 72/72 / 57/72 / 3,270 | 52 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=60 a=0.0001 h=1440` | +0.851 | +0.550 | `w=120 a=0.0001 h=1440` | +0.642 |
| intermittent | `w=60 a=0.01 h=1440` | +0.666 | +0.063 | `w=240 a=0.0001 h=720` | +0.156 |
| drift | `w=60 a=0.0001 h=1440` | +0.926 | +0.548 | `w=120 a=0.0001 h=1440` | +0.651 |

En la rejilla, recuperación en reservadas: mín. +0.363, mediana +0.504, máx. +0.564. Solo intermitente: mín. -0.141, mediana +0.034, máx. +0.156.

## B. `rules_cal` — 15 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001` | +0.585 | +0.449 (52/72) | +0.564 | -0.197 | +0.555 | 72/72 / 32/72 / 222 | 108 |
| elegida en desarrollo (todas las formas) | `w=60 a=0.0001` | +0.687 | +0.489 (53/72) | +0.594 | -0.098 | +0.585 | 72/72 / 38/72 / 192 | 95 |
| óptimo en reservadas (cota superior) | `w=60 a=0.0001` | +0.687 | +0.489 (53/72) | +0.594 | -0.098 | +0.585 | 72/72 / 38/72 / 192 | 95 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=360 a=0.0001` | +0.755 | +0.572 | `w=60 a=0.0001` | +0.594 |
| intermittent | `w=60 a=0.0001` | +0.336 | -0.098 | `w=60 a=0.0001` | -0.098 |
| drift | `w=60 a=0.0001` | +0.781 | +0.585 | `w=60 a=0.0001` | +0.585 |

En la rejilla, recuperación en reservadas: mín. +0.329, mediana +0.416, máx. +0.489. Solo intermitente: mín. -0.440, mediana -0.240, máx. -0.098.

## Comparación con los planificadores LLM (reservadas, mismos 72 escenarios)

| Planificador | todas | escalón | intermitente | deriva |
|---|---|---|---|---|
| rules_adapt_ctx por defecto | +0.538 | +0.632 | -0.021 | +0.635 |
| rules_adapt elegida en desarrollo `w=60 a=0.01 h=1440` | +0.539 | +0.616 | +0.069 | +0.623 |
| rules_adapt especializada en intermitente (desarrollo) `w=60 a=0.01 h=1440` | +0.539 | +0.616 | +0.069 | +0.623 |
| rules_adapt_ctx elegida en desarrollo `w=60 a=0.01 h=1440` | +0.543 | +0.620 | +0.063 | +0.631 |
| rules_adapt_ctx especializada en intermitente (desarrollo) `w=60 a=0.01 h=1440` | +0.543 | +0.620 | +0.063 | +0.631 |
| llm_c2:fable-5.1 | +0.581 | +0.644 | +0.191 | +0.651 |
| hybrid:fable-5.1 | +0.242 | +0.284 | +0.127 | +0.239 |
| llm_c2 | +0.203 | +0.362 | -0.692 | +0.349 |

## C2 con Fable 5.1 frente a reglas reajustadas (emparejado)

Δ = recuperación(Fable) − recuperación(regla), IC 95 % bootstrap estratificado por traza (10 000, semilla 0, como `stats.py`); Wilcoxon sobre el exceso por escenario, sin ajuste.

| Regla | Configuración | Formas | Δ | IC 95 % | Fable mejor en | p | r |
|---|---|---|---|---|---|---|---|
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | todas | +0.062 | [+0.006, +0.125] | 53/72 | 0.000 | +0.53 |
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.255 | [+0.040, +0.464] | 21/24 | 0.000 | +0.79 |
| rules_adapt | elegida en desarrollo `w=60 a=0.01 h=1440` | todas | +0.041 | [-0.010, +0.096] | 43/72 | 0.008 | +0.36 |
| rules_adapt | elegida en desarrollo `w=60 a=0.01 h=1440` | intermitente | +0.122 | [-0.048, +0.280] | 16/24 | 0.021 | +0.53 |
| rules_adapt | óptimo en reservadas `w=60 a=0.01 h=720` | todas | +0.030 | [-0.022, +0.083] | 41/72 | 0.106 | +0.22 |
| rules_adapt | óptimo en reservadas `w=60 a=0.01 h=720` | intermitente | +0.096 | [-0.072, +0.250] | 16/24 | 0.025 | +0.52 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | todas | +0.043 | [-0.013, +0.104] | 50/72 | 0.001 | +0.43 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.212 | [+0.000, +0.417] | 21/24 | 0.001 | +0.73 |
| rules_adapt_ctx | elegida en desarrollo `w=60 a=0.01 h=1440` | todas | +0.037 | [-0.015, +0.093] | 48/72 | 0.022 | +0.31 |
| rules_adapt_ctx | elegida en desarrollo `w=60 a=0.01 h=1440` | intermitente | +0.129 | [-0.043, +0.296] | 18/24 | 0.016 | +0.56 |
| rules_adapt_ctx | óptimo en reservadas `w=120 a=0.0001 h=1440` | todas | +0.017 | [-0.042, +0.080] | 32/72 | 0.884 | -0.02 |
| rules_adapt_ctx | óptimo en reservadas `w=120 a=0.0001 h=1440` | intermitente | +0.108 | [-0.096, +0.301] | 14/24 | 0.290 | +0.25 |
