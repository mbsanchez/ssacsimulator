# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-17 14:01. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | -2.48 (9/216) | -2.55 (3/216) | - | -1.75 (8/216) | -0.56 (29/216) |
| con gemela | -3.36 (5/108) | -3.34 (1/108) | - | -2.35 (2/108) | -0.81 (15/108) |
| sin gemela | -1.95 (4/108) | -2.08 (2/108) | - | -1.39 (6/108) | -0.40 (14/108) |
| fallo step | -1.57 (8/72) | -1.81 (1/72) | - | -1.18 (2/72) | -0.36 (15/72) |
| fallo intermittent | -5.73 (0/72) | -5.81 (0/72) | - | -4.27 (0/72) | -1.61 (1/72) |
| fallo drift | -1.93 (1/72) | -1.83 (2/72) | - | -1.20 (6/72) | -0.27 (13/72) |
| traza 100m-200m | -1.66 (7/72) | -2.49 (0/72) | - | -1.53 (2/72) | -0.24 (16/72) |
| traza 200m-300m | -3.49 (0/72) | -2.66 (2/72) | - | -1.85 (3/72) | -1.09 (4/72) |
| traza 500m-600m | -2.99 (2/72) | -2.56 (1/72) | - | -2.04 (3/72) | -0.62 (9/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 506 | 713 | - | 486 | 118 |
| test_cases_200m-300m.td | 645 | 450 | - | 344 | 189 |
| test_cases_500m-600m.td | 726 | 691 | - | 531 | 253 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 76/216 | 5.3 | 218 |
| rules_adapt | 106/216 | 73/216 | 6.0 | 317 |
| rules_adapt_ctx | 107/216 | 74/216 | 5.4 | 305 |
| hybrid:fable-5.1 | 87/216 | 79/216 | 1.9 | 345 |
