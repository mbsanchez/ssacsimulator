# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-18 19:38. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | +0.37 (84/216) | +0.41 (89/216) | - | +0.46 (92/216) | +0.46 (81/216) |
| con gemela | +0.33 (40/108) | +0.39 (44/108) | - | +0.46 (45/108) | +0.44 (39/108) |
| sin gemela | +0.40 (44/108) | +0.42 (45/108) | - | +0.47 (47/108) | +0.48 (42/108) |
| fallo step | +0.40 (23/72) | +0.40 (25/72) | - | +0.44 (26/72) | +0.39 (21/72) |
| fallo intermittent | +0.20 (33/72) | +0.21 (31/72) | - | +0.31 (33/72) | +0.41 (31/72) |
| fallo drift | +0.42 (28/72) | +0.51 (33/72) | - | +0.56 (33/72) | +0.57 (29/72) |
| traza 100m-200m | +0.50 (45/72) | +0.51 (49/72) | - | +0.59 (50/72) | +0.59 (45/72) |
| traza 200m-300m | +0.34 (14/72) | +0.37 (16/72) | - | +0.40 (16/72) | +0.29 (11/72) |
| traza 500m-600m | +0.18 (25/72) | +0.28 (24/72) | - | +0.31 (26/72) | +0.40 (25/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 53 | 63 | - | 45 | 11 |
| test_cases_200m-300m.td | 54 | 46 | - | 41 | 21 |
| test_cases_500m-600m.td | 60 | 58 | - | 51 | 23 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 80/216 | 5.1 | 216 |
| rules_adapt | 108/216 | 77/216 | 5.6 | 311 |
| rules_adapt_ctx | 108/216 | 77/216 | 5.2 | 311 |
| hybrid:fable-5.1 | 87/216 | 79/216 | 1.8 | 345 |
