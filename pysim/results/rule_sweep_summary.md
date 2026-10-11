# Experimentos solo con reglas (sin LLM)

Diseño v2: 8 estaciones × 3 formas × 3 inicios, fallo ×3, modelo de efectos central. Recuperación agregada a 24 h = 1 − Σ exceso en [t0, t0+24 h) / Σ ídem sin acción; entre paréntesis, escenarios con beneficio neto. Desarrollo = `test_cases_0-100m.td`; reservadas = las otras tres.

Comprobación: la configuración por defecto reproduce `llm_sweep_rows.csv` — rules_adapt: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios; rules_adapt_ctx: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios; rules_cal: máx. |Δ exceso| = 0.000 min-pieza en 216 escenarios.

## A. Planificador ingenuo con el mismo tiempo de espera que el resto

| Tiempo de espera | 4 trazas | reservadas | mant. falsos / escenario | coste falsas alarmas (min-pieza/h, 4 trazas) |
|---|---|---|---|---|
| 120 min | -0.190 (38/288) | -0.490 (38/216) | 11.3 | 342 |
| 240 min | -0.099 (44/288) | -0.253 (44/216) | 8.4 | 255 |

## B. `rules_adapt` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.000 | -0.033 (42/216) | +0.057 | -0.437 | +0.058 | 77/216 / 52/216 / 800 | 67 |
| elegida en desarrollo (todas las formas) | `w=120 a=0.0001 h=1440` | +0.000 | +0.002 (40/216) | +0.091 | -0.383 | +0.087 | 74/216 / 52/216 / 784 | 59 |
| óptimo en reservadas (cota superior) | `w=60 a=0.0001 h=2880` | +0.000 | +0.013 (44/216) | +0.089 | -0.333 | +0.093 | 77/216 / 55/216 / 784 | 63 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=120 a=0.0001 h=1440` | +0.000 | +0.091 | `w=60 a=0.01 h=720` | +0.093 |
| intermittent | `w=120 a=0.0001 h=1440` | +0.000 | -0.383 | `w=360 a=0.0001 h=720` | -0.258 |
| drift | `w=120 a=0.0001 h=1440` | +0.000 | +0.087 | `w=240 a=0.0001 h=720` | +0.124 |

En la rejilla, recuperación en reservadas: mín. -0.098, mediana -0.030, máx. +0.013. Solo intermitente: mín. -0.525, mediana -0.414, máx. -0.258.

## B. `rules_adapt_ctx` — 45 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001 h=1440` | +0.000 | -0.018 (40/216) | +0.079 | -0.399 | +0.056 | 75/216 / 50/216 / 784 | 64 |
| elegida en desarrollo (todas las formas) | `w=120 a=0.0001 h=1440` | +0.000 | +0.011 (41/216) | +0.098 | -0.351 | +0.086 | 74/216 / 52/216 / 784 | 52 |
| óptimo en reservadas (cota superior) | `w=60 a=0.0001 h=2880` | +0.000 | +0.037 (42/216) | +0.116 | -0.301 | +0.111 | 76/216 / 54/216 / 784 | 59 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=120 a=0.0001 h=1440` | +0.000 | +0.098 | `w=60 a=0.01 h=720` | +0.123 |
| intermittent | `w=120 a=0.0001 h=1440` | +0.000 | -0.351 | `w=360 a=0.0001 h=720` | -0.251 |
| drift | `w=120 a=0.0001 h=1440` | +0.000 | +0.086 | `w=240 a=0.0001 h=720` | +0.143 |

En la rejilla, recuperación en reservadas: mín. -0.097, mediana -0.018, máx. +0.037. Solo intermitente: mín. -0.512, mediana -0.385, máx. -0.251.

## B. `rules_cal` — 15 configuraciones

| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| por defecto | `w=120 a=0.001` | +0.000 | -0.034 (34/216) | +0.042 | -0.375 | +0.043 | 62/216 / 42/216 / 826 | 108 |
| elegida en desarrollo (todas las formas) | `w=120 a=0.0001` | +0.000 | -0.025 (37/216) | +0.050 | -0.325 | +0.036 | 59/216 / 41/216 / 829 | 105 |
| óptimo en reservadas (cota superior) | `w=360 a=0.0001` | +0.000 | +0.007 (39/216) | +0.036 | -0.220 | +0.082 | 53/216 / 42/216 / 824 | 98 |

Selección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):

| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |
|---|---|---|---|---|---|
| step | `w=120 a=0.0001` | +0.000 | +0.050 | `w=60 a=0.0001` | +0.095 |
| intermittent | `w=120 a=0.0001` | +0.000 | -0.325 | `w=360 a=0.0001` | -0.220 |
| drift | `w=120 a=0.0001` | +0.000 | +0.036 | `w=180 a=0.0001` | +0.084 |

En la rejilla, recuperación en reservadas: mín. -0.105, mediana -0.046, máx. +0.007. Solo intermitente: mín. -0.492, mediana -0.378, máx. -0.220.

## Comparación con los planificadores LLM (reservadas, mismos 72 escenarios)

| Planificador | todas | escalón | intermitente | deriva |
|---|---|---|---|---|
| rules_adapt_ctx por defecto | -0.018 | +0.079 | -0.399 | +0.056 |
| rules_adapt elegida en desarrollo `w=120 a=0.0001 h=1440` | +0.002 | +0.091 | -0.383 | +0.087 |
| rules_adapt especializada en intermitente (desarrollo) `w=120 a=0.0001 h=1440` | +0.002 | +0.091 | -0.383 | +0.087 |
| rules_adapt_ctx elegida en desarrollo `w=120 a=0.0001 h=1440` | +0.011 | +0.098 | -0.351 | +0.086 |
| rules_adapt_ctx especializada en intermitente (desarrollo) `w=120 a=0.0001 h=1440` | +0.011 | +0.098 | -0.351 | +0.086 |
| llm_c2:fable-5.1 | +0.023 | +0.083 | -0.238 | +0.076 |

## C2 con Fable 5.1 frente a reglas reajustadas (emparejado)

Δ = recuperación(Fable) − recuperación(regla), IC 95 % bootstrap estratificado por traza (10 000, semilla 0, como `stats.py`); Wilcoxon sobre el exceso por escenario, sin ajuste.

| Regla | Configuración | Formas | Δ | IC 95 % | Fable mejor en | p | r |
|---|---|---|---|---|---|---|---|
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | todas | +0.101 | [+0.035, +0.172] | 95/194 | 0.000 | +0.54 |
| rules_adapt | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.262 | [+0.152, +0.408] | 33/65 | 0.000 | +0.87 |
| rules_adapt | elegida en desarrollo `w=120 a=0.0001 h=1440` | todas | +0.065 | [+0.007, +0.123] | 91/194 | 0.000 | +0.47 |
| rules_adapt | elegida en desarrollo `w=120 a=0.0001 h=1440` | intermitente | +0.199 | [+0.112, +0.309] | 31/65 | 0.000 | +0.77 |
| rules_adapt | óptimo en reservadas `w=60 a=0.0001 h=2880` | todas | +0.042 | [-0.022, +0.108] | 71/194 | 0.030 | +0.23 |
| rules_adapt | óptimo en reservadas `w=60 a=0.0001 h=2880` | intermitente | +0.109 | [-0.001, +0.238] | 23/65 | 0.192 | +0.25 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | todas | +0.087 | [+0.026, +0.148] | 88/194 | 0.000 | +0.52 |
| rules_adapt_ctx | por defecto `w=120 a=0.001 h=1440` | intermitente | +0.221 | [+0.122, +0.352] | 30/65 | 0.000 | +0.79 |
| rules_adapt_ctx | elegida en desarrollo `w=120 a=0.0001 h=1440` | todas | +0.061 | [+0.004, +0.119] | 84/194 | 0.000 | +0.45 |
| rules_adapt_ctx | elegida en desarrollo `w=120 a=0.0001 h=1440` | intermitente | +0.177 | [+0.090, +0.287] | 28/65 | 0.000 | +0.70 |
| rules_adapt_ctx | óptimo en reservadas `w=60 a=0.0001 h=2880` | todas | +0.013 | [-0.050, +0.075] | 69/194 | 0.089 | +0.18 |
| rules_adapt_ctx | óptimo en reservadas `w=60 a=0.0001 h=2880` | intermitente | +0.074 | [-0.025, +0.180] | 23/65 | 0.338 | +0.18 |
