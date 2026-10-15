# Tablas del artículo (trazas reservadas, diseño v2)

## Detector heredado

216 escenarios con fallo, 3 trazas reservadas.

| Planificador | recuperación 24 h [IC 95 %] | escalón | intermitente | deriva | actúa (24 h) | mediana latencia (min) | reparaciones falsas / escenario (24 h) | coste falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| rules_cal | -0.034 [-0.117, +0.041] | +0.042 | -0.375 | +0.043 | 62/216 | 826 | 4.4 | 108 |
| rules_adapt | -0.033 [-0.137, +0.059] | +0.057 | -0.437 | +0.058 | 77/216 | 800 | 6.2 | 67 |
| rules_adapt_ctx | -0.018 [-0.116, +0.070] | +0.079 | -0.399 | +0.056 | 75/216 | 784 | 5.9 | 64 |
| rules_twin | -0.353 [-0.450, -0.265] | -0.257 | -0.758 | -0.266 | 47/216 | 646 | 7.1 | 142 |
| llm_c1 | -0.205 [-0.300, -0.120] | -0.129 | -0.628 | -0.091 | 49/216 | 654 | 6.4 | 136 |
| llm_c2 | -0.150 [-0.272, -0.045] | -0.058 | -0.729 | +0.021 | 104/216 | 688 | 9.5 | 159 |
| hybrid | -0.037 [-0.099, +0.026] | -0.021 | -0.252 | +0.046 | 51/216 | 970 | 4.0 | 38 |
| llm_c2:fable-5.1 | +0.072 [-0.003, +0.141] | +0.134 | -0.170 | +0.119 | 54/216 | 730 | 3.9 | 58 |
| hybrid:fable-5.1 | +0.033 [-0.010, +0.077] | +0.086 | -0.026 | +0.004 | 24/216 | 1,060 | 0.9 | 7 |

## Detector por estación

216 escenarios con fallo, 3 trazas reservadas.

| Planificador | recuperación 24 h [IC 95 %] | escalón | intermitente | deriva | actúa (24 h) | mediana latencia (min) | reparaciones falsas / escenario (24 h) | coste falsas alarmas (min-pieza/h) |
|---|---|---|---|---|---|---|---|---|
| rules_cal | +0.131 [+0.013, +0.235] | +0.231 | -0.292 | +0.220 | 101/216 | 218 | 5.5 | 107 |
| rules_adapt | +0.167 [+0.049, +0.270] | +0.227 | -0.268 | +0.304 | 108/216 | 311 | 5.9 | 98 |
| rules_adapt_ctx | +0.204 [+0.091, +0.303] | +0.258 | -0.195 | +0.332 | 108/216 | 311 | 5.5 | 89 |
| rules_twin | -0.200 [-0.296, -0.107] | -0.074 | -0.642 | -0.128 | 60/216 | 362 | 6.2 | 108 |
| llm_c1 | -0.051 [-0.171, +0.057] | +0.063 | -0.547 | +0.057 | 90/216 | 390 | 7.6 | 121 |
| llm_c2 | -0.247 [-0.419, -0.103] | -0.054 | -1.058 | -0.076 | 117/216 | 281 | 14.0 | 203 |
| hybrid | +0.289 [+0.181, +0.382] | +0.316 | -0.027 | +0.406 | 106/216 | 305 | 5.2 | 74 |
| llm_c1:fable-5.1 | +0.083 [+0.035, +0.142] | +0.023 | +0.100 | +0.138 | 19/216 | 408 | 0.1 | 1 |
| llm_c2:fable-5.1 | +0.139 [+0.022, +0.240] | +0.229 | -0.253 | +0.225 | 105/216 | 208 | 7.1 | 100 |
| hybrid:fable-5.1 | +0.413 [+0.315, +0.501] | +0.350 | +0.292 | +0.532 | 87/216 | 345 | 1.8 | 25 |

## Diseño de evaluación: v1 frente a v2

v1: fallo a 600 min del primer evento, una reparación elimina también fallos iniciados durante ella, recuperación sobre la traza completa, 72 escenarios. v2: 3 inicios aleatorios, solo se eliminan fallos activos al empezar la reparación, recuperación a 24 h, 216 escenarios.

| Planificador | v1 (detector heredado) | v2, detector heredado | v2, detector por estación |
|---|---|---|---|
| rules_cal | +0.45 | -0.03 | +0.13 |
| rules_adapt | +0.52 | -0.03 | +0.17 |
| rules_adapt_ctx | +0.54 | -0.02 | +0.20 |
| rules_twin | -0.31 | -0.35 | -0.20 |
| llm_c1 | +0.15 | -0.21 | -0.05 |
| llm_c2 | +0.20 | -0.15 | -0.25 |
| hybrid | +0.41 | -0.04 | +0.29 |
| llm_c1:fable-5.1 | +0.00 | – | +0.08 |
| llm_c2:fable-5.1 | +0.58 | +0.07 | +0.14 |
| hybrid:fable-5.1 | +0.24 | +0.03 | +0.41 |

## Sensibilidad (reglas, detector por estación, solo trazas reservadas)

| | rules_naive | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|---|
| central, todas | -0.28 | +0.13 | +0.17 | -0.20 |
| central, escalón | -0.07 | +0.23 | +0.23 | -0.07 |
| central, intermitente | -1.12 | -0.29 | -0.27 | -0.64 |
| central, deriva | -0.10 | +0.22 | +0.30 | -0.13 |
| alpha=0 | – | +0.37 | +0.41 | +0.22 |
| alpha=1 | – | -0.07 | -0.03 | -0.61 |
| factor=1.5 | – | -1.51 | -1.47 | -1.75 |
| factor=5 | – | +0.37 | +0.41 | +0.03 |
| mode=stop | – | -2.48 | -2.55 | -0.81 |
| repair_min=15 | – | +0.54 | +0.58 | +0.20 |
| repair_min=240 | – | -1.22 | -1.22 | -1.73 |
