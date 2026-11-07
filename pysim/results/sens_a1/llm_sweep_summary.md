# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-18 19:41. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | -0.07 (50/216) | -0.03 (52/216) | - | -0.01 (55/216) | +0.36 (72/216) |
| con gemela | -0.27 (22/108) | -0.23 (23/108) | - | -0.24 (22/108) | +0.25 (30/108) |
| sin gemela | +0.05 (28/108) | +0.09 (29/108) | - | +0.12 (33/108) | +0.42 (42/108) |
| fallo step | +0.09 (22/72) | +0.09 (22/72) | - | +0.11 (22/72) | +0.31 (21/72) |
| fallo intermittent | -0.68 (8/72) | -0.65 (8/72) | - | -0.63 (11/72) | +0.17 (25/72) |
| fallo drift | +0.05 (20/72) | +0.13 (22/72) | - | +0.14 (22/72) | +0.49 (26/72) |
| traza 100m-200m | +0.17 (28/72) | +0.02 (24/72) | - | +0.06 (27/72) | +0.42 (39/72) |
| traza 200m-300m | -0.29 (11/72) | -0.12 (12/72) | - | -0.18 (12/72) | +0.25 (11/72) |
| traza 500m-600m | -0.28 (11/72) | -0.04 (16/72) | - | +0.01 (16/72) | +0.34 (22/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 122 | 163 | - | 151 | 29 |
| test_cases_200m-300m.td | 165 | 109 | - | 120 | 26 |
| test_cases_500m-600m.td | 166 | 123 | - | 114 | 41 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 76/216 | 5.5 | 218 |
| rules_adapt | 108/216 | 76/216 | 5.9 | 311 |
| rules_adapt_ctx | 108/216 | 77/216 | 5.3 | 311 |
| hybrid:fable-5.1 | 87/216 | 79/216 | 1.7 | 345 |
