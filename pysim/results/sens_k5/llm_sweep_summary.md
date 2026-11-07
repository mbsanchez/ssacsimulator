# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-18 19:28. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | +0.37 (83/216) | +0.41 (84/216) | - | +0.43 (87/216) | +0.50 (84/216) |
| con gemela | +0.29 (37/108) | +0.33 (38/108) | - | +0.34 (39/108) | +0.46 (41/108) |
| sin gemela | +0.42 (46/108) | +0.45 (46/108) | - | +0.48 (48/108) | +0.52 (43/108) |
| fallo step | +0.36 (23/72) | +0.37 (24/72) | - | +0.38 (24/72) | +0.40 (20/72) |
| fallo intermittent | +0.22 (31/72) | +0.24 (29/72) | - | +0.29 (31/72) | +0.46 (33/72) |
| fallo drift | +0.45 (29/72) | +0.52 (31/72) | - | +0.53 (32/72) | +0.61 (31/72) |
| traza 100m-200m | +0.55 (48/72) | +0.52 (47/72) | - | +0.54 (47/72) | +0.61 (46/72) |
| traza 200m-300m | +0.27 (13/72) | +0.33 (14/72) | - | +0.34 (15/72) | +0.38 (12/72) |
| traza 500m-600m | +0.17 (22/72) | +0.28 (23/72) | - | +0.31 (25/72) | +0.42 (26/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 88 | 119 | - | 105 | 20 |
| test_cases_200m-300m.td | 116 | 80 | - | 78 | 24 |
| test_cases_500m-600m.td | 116 | 96 | - | 83 | 33 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 100/216 | 77/216 | 5.5 | 216 |
| rules_adapt | 107/216 | 79/216 | 5.9 | 234 |
| rules_adapt_ctx | 107/216 | 79/216 | 5.5 | 234 |
| hybrid:fable-5.1 | 90/216 | 83/216 | 1.8 | 329 |
