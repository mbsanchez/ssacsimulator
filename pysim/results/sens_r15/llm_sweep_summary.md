# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 15:51. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | +0.54 (94/216) | +0.58 (98/216) | - | +0.58 (98/216) | +0.56 (85/216) |
| con gemela | +0.55 (46/108) | +0.60 (46/108) | - | +0.59 (46/108) | +0.51 (39/108) |
| sin gemela | +0.54 (48/108) | +0.57 (52/108) | - | +0.57 (52/108) | +0.59 (46/108) |
| fallo step | +0.51 (25/72) | +0.52 (27/72) | - | +0.52 (27/72) | +0.48 (22/72) |
| fallo intermittent | +0.53 (38/72) | +0.58 (38/72) | - | +0.56 (38/72) | +0.57 (34/72) |
| fallo drift | +0.58 (31/72) | +0.65 (33/72) | - | +0.64 (33/72) | +0.63 (29/72) |
| traza 100m-200m | +0.65 (52/72) | +0.65 (51/72) | - | +0.64 (51/72) | +0.65 (48/72) |
| traza 200m-300m | +0.58 (17/72) | +0.62 (19/72) | - | +0.63 (19/72) | +0.51 (12/72) |
| traza 500m-600m | +0.33 (25/72) | +0.43 (28/72) | - | +0.43 (28/72) | +0.44 (25/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 19 | 27 | - | 30 | 5 |
| test_cases_200m-300m.td | 23 | 15 | - | 14 | 5 |
| test_cases_500m-600m.td | 28 | 22 | - | 23 | 9 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 76/216 | 5.3 | 218 |
| rules_adapt | 107/216 | 75/216 | 6.1 | 299 |
| rules_adapt_ctx | 107/216 | 75/216 | 6.1 | 299 |
| hybrid:fable-5.1 | 89/216 | 81/216 | 1.8 | 329 |
