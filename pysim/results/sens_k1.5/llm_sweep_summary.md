# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-17 18:46. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | -1.51 (13/216) | -1.47 (9/216) | -1.75 (2/216) | -1.30 (11/216) | -0.07 (44/216) |
| con gemela | -2.19 (3/108) | -2.12 (1/108) | -1.96 (2/108) | -2.01 (1/108) | -0.28 (17/108) |
| sin gemela | -1.10 (10/108) | -1.07 (8/108) | -1.63 (0/108) | -0.87 (10/108) | +0.06 (27/108) |
| fallo step | -0.89 (8/72) | -0.98 (4/72) | -1.25 (1/72) | -0.84 (5/72) | +0.02 (16/72) |
| fallo intermittent | -3.63 (0/72) | -3.52 (0/72) | -3.51 (0/72) | -3.22 (0/72) | -0.67 (9/72) |
| fallo drift | -1.18 (5/72) | -1.02 (5/72) | -1.47 (1/72) | -0.90 (6/72) | +0.12 (19/72) |
| traza 100m-200m | -1.01 (8/72) | -1.43 (2/72) | -1.62 (0/72) | -1.26 (3/72) | +0.04 (24/72) |
| traza 200m-300m | -2.23 (2/72) | -1.82 (2/72) | -2.24 (2/72) | -1.73 (3/72) | -0.38 (6/72) |
| traza 500m-600m | -1.73 (3/72) | -1.23 (5/72) | -1.56 (0/72) | -1.01 (5/72) | +0.02 (14/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 88 | 119 | 122 | 105 | 20 |
| test_cases_200m-300m.td | 116 | 80 | 91 | 78 | 24 |
| test_cases_500m-600m.td | 116 | 96 | 112 | 83 | 33 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 92/216 | 66/216 | 5.5 | 228 |
| rules_adapt | 100/216 | 59/216 | 5.9 | 353 |
| rules_twin | 59/216 | 10/216 | 6.2 | 362 |
| rules_adapt_ctx | 98/216 | 62/216 | 5.5 | 371 |
| hybrid:fable-5.1 | 73/216 | 63/216 | 1.7 | 241 |
